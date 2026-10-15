import os
from dotenv import load_dotenv
import numpy as np
import json
import PyPDF2
from sentence_transformers import SentenceTransformer
from pymongo import MongoClient
from openai import OpenAI

# Load .env from backend directory
load_dotenv("backend/.env")

# ─── MongoDB Atlas Setup ─────────────────────────────────────────────────────
# Expects your Atlas connection string in the MONGODB_URI environment variable:
#   export MONGODB_URI="mongodb+srv://<user>:<pass>@cluster0.xyz.mongodb.net/?retryWrites=true&w=majority"
MONGO_URI = os.getenv("MONGO_URI") 
OpenAI.api_key = os.getenv("OPENAI_API_KEY")
if not MONGO_URI:
    raise RuntimeError("Set the MONGODB_URI environment variable to your Atlas URI")
ai_client = OpenAI()
# Create a single, global client & collection reference
client = MongoClient(MONGO_URI)  # Removed tls=True since it's already in the URI
db = client["Tootur"]  # Changed from pdf_chunks_db to Tootur
chunks_coll = db["chunks"]  # Collection name remains the same


def extract_text_from_pdf(pdf_path):
    """
    Extract all text from a PDF file.
    """
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
    return text


def chunk_text(text, max_length=2000, overlap=200):
    """
    Split text into chunks of approximately max_length characters with overlap.
    This approach preserves more context at chunk boundaries.
    """
    chunks = []
    if len(text) <= max_length:
        chunks.append(text)
    else:
        current_idx = 0
        while current_idx < len(text):
            chunk_end = min(current_idx + max_length, len(text))

            if chunk_end < len(text):
                # try to break on a paragraph
                paragraph_break = text.rfind('\n\n', current_idx, chunk_end)
                if paragraph_break != -1 and paragraph_break > current_idx + max_length//2:
                    chunk_end = paragraph_break + 2
                else:
                    # fallback: break on sentence end
                    sentence_break = max(
                        text.rfind('. ', current_idx, chunk_end),
                        text.rfind('! ', current_idx, chunk_end),
                        text.rfind('? ', current_idx, chunk_end)
                    )
                    if sentence_break != -1 and sentence_break > current_idx + max_length//2:
                        chunk_end = sentence_break + 2

            chunk = text[current_idx:chunk_end].strip()
            if chunk:
                chunks.append(chunk)

            current_idx = max(current_idx + max_length - overlap, chunk_end)
    return chunks


def index_pdfs(pdf_directory, model, chunk_size=500):
    """
    Process each PDF in the directory:
    1. Extract text.
    2. Chunk the text.
    3. Generate an embedding for each chunk.
    4. Collect embeddings and metadata.
    
    Returns:
        None, metadata_list
    """
    metadata = []

    for filename in os.listdir(pdf_directory):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(pdf_directory, filename)
            print(f"Processing {filename}...")
            text = extract_text_from_pdf(pdf_path)
            if not text.strip():
                continue

            chunks = chunk_text(text, max_length=chunk_size)
            for i, chunk in enumerate(chunks):
                embedding = model.encode(chunk)
                metadata.append({
                    'pdf_file': filename,
                    'chunk_index': i,
                    'chunk_text': chunk,
                    'embedding': embedding.tolist()
                })

    if metadata:
        print(f"Prepared {len(metadata)} chunks from PDFs.")
        return None, metadata
    else:
        print("No chunks to index.")
        return None, None


def save_index_and_metadata(faiss_index, metadata, index_file="faiss_index.index", metadata_file="metadata.json"):
    """
    Persist the chunk documents into MongoDB Atlas with duplicate checking.
    """
    # Check for duplicates before inserting
    for chunk in metadata:
        # Create a query to check if this exact chunk already exists
        query = {
            'pdf_file': chunk['pdf_file'],
            'chunk_index': chunk['chunk_index']
        }
        
        # Use update_one with upsert=True to insert only if not exists
        chunks_coll.update_one(
            query,
            {'$setOnInsert': chunk},
            upsert=True
        )
    
    print(f"Processed {len(metadata)} chunks into MongoDB collection '{db.name}.{chunks_coll.name}'.")

def load_index_and_metadata(index_file="faiss_index.index", metadata_file="metadata.json"):
    """
    Load chunk documents back from MongoDB Atlas.
    """
    docs = list(chunks_coll.find({}, {'_id': False}))
    print(f"Loaded {len(docs)} chunks from MongoDB collection '{db.name}.{chunks_coll.name}'.")
    return None, docs


def retrieve_relevant_chunks(query, model, top_k=5, similarity_threshold=0.3):
    """
    Retrieve the top_k most similar chunks for a given query, filtered by a similarity threshold.
    """
    query_emb = model.encode(query).astype(np.float32)

    # Load all vectors and metadata from MongoDB
    cursor = chunks_coll.find({}, {"embedding": 1, "pdf_file": 1, "chunk_index": 1, "chunk_text": 1})
    metadata, embeddings = [], []
    for doc in cursor:
        embeddings.append(doc["embedding"])
        metadata.append({
            "pdf_file": doc["pdf_file"],
            "chunk_index": doc["chunk_index"],
            "chunk_text": doc["chunk_text"]
        })

    embeddings = np.array(embeddings, dtype=np.float32)

    # Compute cosine similarity
    similarities = np.dot(embeddings, query_emb) / (
        np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_emb)
    )
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    print("Top 10 similarity scores:", np.sort(similarities)[-10:])
    # Filter by similarity threshold
    results = []
    for idx in top_indices:
        if similarities[idx] >= similarity_threshold:
            results.append({**metadata[idx], "score": float(similarities[idx])})
    return results

def generate_rag_response(query, retrieved_chunks):
    """
    Generate a response using GPT with retrieved chunks as context,
    via the openai-python >=1.0.0 ChatCompletion client.
    """
    # 1. Build the context string
    context = "\n\n".join(
        f"Chunk {i+1}: {chunk['chunk_text']}"
        for i, chunk in enumerate(retrieved_chunks)
    )

    # 2. Assemble messages
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert assistant. Use the provided context to answer "
                "the user's question accurately, quoting from the context when helpful."
            )
        },
        {
            "role": "system",
            "content": f"Context:\n{context}"
        },
        {
            "role": "user",
            "content": query
        }
    ]

    try:
        response = ai_client.chat.completions.create(
            model="gpt-4",            # Changed from gpt-4o-mini to gpt-4
            messages=messages,
            max_tokens=300,           # Changed max_completion_tokens to max_tokens
            temperature=0.7
        )
        # Extract the assistant's reply
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Error generating response: {e}")
        return None


def rag_pipeline(query, model, top_k=5, similarity_threshold=0.3):
    """
    Full RAG pipeline: retrieve relevant chunks and generate a response.
    """
    # Step 1: Retrieve relevant chunks
    retrieved_chunks = retrieve_relevant_chunks(query, model, top_k, similarity_threshold)
    if not retrieved_chunks:
        return "No relevant information found."

    # Step 2: Generate a response using the retrieved chunks
    response = generate_rag_response(query, retrieved_chunks)
    return response


def run_pdf_indexing(pdf_directory="downloaded_files", chunk_size=2000):
    """
    Build the chunk documents, store them in MongoDB Atlas, and
    allow a user to query them interactively with RAG.
    """
    model = SentenceTransformer("all-MiniLM-L6-v2")


    # Ensure there are PDFs to process
    if not any(fn.lower().endswith(".pdf") for fn in os.listdir(pdf_directory)):
        print(f"No PDF files found in {pdf_directory}. Please add some PDF files and run the script again.")
        return

    # Extract, chunk, encode, and store
    _, metadata = index_pdfs(pdf_directory, model, chunk_size=chunk_size)
    if not metadata:
        return
    save_index_and_metadata(None, metadata)

    # Interactive query with RAG
    # while True:
    #     query = input("Enter your search query (or type 'exit' to quit): ")
    #     if query.lower() == "exit":
    #         break
    #     response = rag_pipeline(query, model, top_k=5, similarity_threshold=0.3)
    #     print(f"\nResponse:\n{response}\n")

def test_retrieval():
    print("Loading SentenceTransformer model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    # Test query
    test_query = "What are the main topics covered in the AP curriculum?"
    print(f"\nTest query: {test_query}")
    
    # Retrieve relevant chunks
    print("\nRetrieving relevant chunks...")
    chunks = retrieve_relevant_chunks(test_query, model, top_k=3, similarity_threshold=0.3)
    
    if not chunks:
        print("No relevant chunks found in the database.")
        return
        
    print(f"\nFound {len(chunks)} relevant chunks:")
    for i, chunk in enumerate(chunks, 1):
        print(f"\nChunk {i}:")
        print(f"From file: {chunk['pdf_file']}")
        print(f"Similarity score: {chunk['score']:.3f}")
        print("Content:")
        print(chunk['chunk_text'][:300] + "..." if len(chunk['chunk_text']) > 300 else chunk['chunk_text'])
    
    # Generate RAG response
    print("\nGenerating response using retrieved chunks...")
    response = generate_rag_response(test_query, chunks)
    print("\nGenerated Response:")
    print(response)

if __name__ == "__main__":
    test_retrieval()
