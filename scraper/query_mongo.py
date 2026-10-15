import os
from dotenv import load_dotenv
import numpy as np
from sentence_transformers import SentenceTransformer
from pymongo import MongoClient
import certifi

# Load environment variables
load_dotenv()

# MongoDB Atlas connection with correct parameters
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("Set the MONGODB_URI environment variable to your Atlas URI")

try:
    # Use the recommended configuration for PyMongo 4.x
    client = MongoClient(
        MONGO_URI,
        tls=True,
        tlsCAFile=certifi.where(),
        tlsAllowInvalidCertificates=True,  # This can help bypass certificate validation issues
        connectTimeoutMS=30000,
        socketTimeoutMS=30000,
        serverSelectionTimeoutMS=30000
    )
    
    # Access the database and collection
    db = client["pdf_chunks_db"]
    chunks_coll = db["chunks"]
    
    print("Successfully initialized MongoDB client")
    
except Exception as e:
    print(f"Error initializing MongoDB client: {e}")
    raise

def query_pdf_database(query, top_k=5):
    """
    Query the MongoDB database for chunks relevant to the given query.
    """
    try:
        # Load the same model used for indexing
        model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Test connection before proceeding
        print("Testing MongoDB connection...")
        db.command('ping')
        print("MongoDB connection successful!")
        
        # Load the chunks from MongoDB
        print("Fetching documents from MongoDB...")
        metadata = list(chunks_coll.find({}, {'_id': 0}))
        print(f"Found {len(metadata)} documents")
        
        if not metadata:
            print("No documents found in the database. Please check if data was properly indexed.")
            return []
        
        # Retrieve relevant chunks
        print(f"Processing query: '{query}'")
        query_emb = model.encode(query).astype(np.float32)
        
        # Calculate distances manually
        distances = [
            np.linalg.norm(np.array(doc['embedding'], dtype=np.float32) - query_emb)
            for doc in metadata
        ]
        
        # Get top_k indices with smallest distances
        top_idxs = np.argsort(distances)[:top_k]
        relevant_chunks = [metadata[i] for i in top_idxs]
        
        return relevant_chunks
        
    except Exception as e:
        print(f"Error during query: {e}")
        return []

def display_results(results):
    """
    Display search results in a readable format.
    """
    if not results:
        print("\nNo relevant results found.")
        return
        
    print("\nSearch Results:")
    print("=" * 80)
    
    for i, chunk in enumerate(results, 1):
        print(f"Result {i}:")
        print(f"Source: {chunk['pdf_file']}")
        print(f"Chunk Index: {chunk['chunk_index']}")
        print("-" * 50)
        print(chunk['chunk_text'][:500] + "..." if len(chunk['chunk_text']) > 500 else chunk['chunk_text'])
        print("=" * 80)

if __name__ == "__main__":
    print("PDF Database Query Interface")
    print("Automatically searching for 'apush' with 5 results")
    
    # Set fixed query and number of results
    query = "apush"
    top_k = 5
    
    # Execute query
    results = query_pdf_database(query, top_k)
    
    # Display results
    display_results(results)
    
    print("\nSearch completed. Press Enter to exit.")
    input()