import os
import numpy as np
import faiss
import json
import PyPDF2
from sentence_transformers import SentenceTransformer

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
                paragraph_break = text.rfind('\n\n', current_idx, chunk_end)
                if paragraph_break != -1 and paragraph_break > current_idx + max_length//2:
                    chunk_end = paragraph_break + 2
                else:
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
        faiss_index: FAISS index with all chunk embeddings.
        metadata: List of metadata dictionaries corresponding to each embedding.
    """
    embedding_list = []
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
                embedding_list.append(embedding)
                metadata.append({
                    'pdf_file': filename,
                    'chunk_index': i,
                    'chunk_text': chunk
                })

    if embedding_list:
        embeddings_array = np.array(embedding_list, dtype=np.float32)
        dimension = embeddings_array.shape[1]
        faiss_index = faiss.IndexFlatL2(dimension)
        faiss_index.add(embeddings_array)
        print(f"Indexed {faiss_index.ntotal} chunks from PDFs.")
        return faiss_index, metadata
    else:
        print("No embeddings to index.")
        return None, None

def save_index_and_metadata(faiss_index, metadata, index_file="faiss_index.index", metadata_file="metadata.json"):
    """
    Persist the FAISS index and the metadata mapping to disk.
    """
    faiss.write_index(faiss_index, index_file)
    print(f"FAISS index saved to {index_file}.")
    
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
    print(f"Metadata saved to {metadata_file}.")

def load_index_and_metadata(index_file="faiss_index.index", metadata_file="metadata.json"):
    """
    Load the FAISS index and metadata from disk.
    """
    faiss_index = faiss.read_index(index_file)
    with open(metadata_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    return faiss_index, metadata

def retrieve_relevant_chunks(query, model, faiss_index, metadata, top_k=5):
    """
    Given a query, encode it, then use FAISS to retrieve top_k most similar chunk embeddings.
    Returns metadata for the retrieved chunks.
    """
    query_embedding = model.encode(query).astype(np.float32)
    query_embedding = np.expand_dims(query_embedding, axis=0)
    distances, indices = faiss_index.search(query_embedding, top_k)
    results = []
    for idx in indices[0]:
        if idx != -1:
            results.append(metadata[idx])
    return results

def run_pdf_indexing(pdf_directory="downloaded_files", chunk_size=2000):
    """
    Build the FAISS index and metadata from the PDFs in the provided directory,
    and then allow a user to query the index.
    """
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    if not os.path.exists(pdf_directory):
        os.makedirs(pdf_directory)
        print(f"Created directory: {pdf_directory}")
        print("Please place your PDF files in this directory before continuing.")
        return
        
    if not any(filename.lower().endswith(".pdf") for filename in os.listdir(pdf_directory)):
        print(f"No PDF files found in {pdf_directory}. Please add some PDF files and run the script again.")
        return
    
    faiss_index, metadata = index_pdfs(pdf_directory, model, chunk_size=chunk_size)
    if faiss_index is None:
        return
    
    save_index_and_metadata(faiss_index, metadata)
    
    query = input("Enter your search query (e.g., 'create an APUSH study guide'): ")
    print(f"\nQuery: {query}")
    relevant_chunks = retrieve_relevant_chunks(query, model, faiss_index, metadata, top_k=5)
    
    print("\nRelevant chunks:")
    for chunk in relevant_chunks:
        print(f"File: {chunk['pdf_file']}, Chunk: {chunk['chunk_index']}")
        print(f"Snippet: {chunk['chunk_text'][:200]}...\n")

# Command-line execution
if __name__ == "__main__":
    run_pdf_indexing()
