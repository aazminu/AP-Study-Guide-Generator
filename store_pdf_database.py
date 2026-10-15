import os
import PyPDF2
import asyncio
from sentence_transformers import SentenceTransformer
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

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

async def process_pdf(pdf_path, model, chunks_collection):
    """Process a single PDF: extract text, chunk it, and store in MongoDB."""
    print(f"Processing {pdf_path}...")
    
    # Extract text
    text = extract_text_from_pdf(pdf_path)
    if not text.strip():
        print(f"No text extracted from {pdf_path}")
        return
    
    # Chunk text
    chunks = chunk_text(text)
    print(f"Created {len(chunks)} chunks")
    
    # Store chunks with embeddings
    for i, chunk in enumerate(chunks):
        embedding = model.encode(chunk).astype('float32').tolist()
        chunk_doc = {
            "pdf_file": os.path.basename(pdf_path),
            "chunk_index": i,
            "chunk_text": chunk,
            "embedding": embedding
        }
        await chunks_collection.insert_one(chunk_doc)
    
    print(f"Stored {len(chunks)} chunks in MongoDB")

async def process_all_pdfs(pdf_directory="downloaded_files"):
    """Process all PDFs in the directory and store in MongoDB."""
    if not os.path.exists(pdf_directory):
        print(f"Directory {pdf_directory} does not exist")
        return
    
    # Initialize MongoDB connection
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        print("MONGO_URI not found in environment variables")
        return
        
    client = AsyncIOMotorClient(mongo_uri)
    db = client.pdf_chunks_db
    chunks_collection = db.chunks
    
    # Create vector search index if it doesn't exist
    # Note: You'll need to create this index in MongoDB Atlas UI
    # or using MongoDB Compass
    
    # Initialize the sentence transformer model
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    try:
        # Process each PDF
        for filename in os.listdir(pdf_directory):
            if filename.lower().endswith(".pdf"):
                pdf_path = os.path.join(pdf_directory, filename)
                await process_pdf(pdf_path, model, chunks_collection)
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(process_all_pdfs())
