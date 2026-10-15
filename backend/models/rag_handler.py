from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict
from pymongo import MongoClient
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

class RAGHandler:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.mongo_uri = os.getenv("MONGO_URI")
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client["pdf_chunks_db"]
        self.chunks_collection = self.db["chunks"]
        self.ai_client = OpenAI()
        self.ai_client.api_key = os.getenv("OPENAI_API_KEY")

    def retrieve_relevant_chunks(self, query: str, top_k: int = 5, similarity_threshold: float = 0.3) -> List[Dict]:
        """Retrieve the most relevant chunks for a given query using cosine similarity."""
        try:
            print(f"\n[RAG] Processing query: {query}")
            query_emb = self.model.encode(query).astype(np.float32)

            # Load all vectors and metadata from MongoDB
            print("[RAG] Attempting to fetch chunks from MongoDB...")
            try:
                cursor = self.chunks_collection.find({}, {"embedding": 1, "pdf_file": 1, "chunk_index": 1, "chunk_text": 1})
                metadata, embeddings = [], []
                for doc in cursor:
                    embeddings.append(doc["embedding"])
                    metadata.append({
                        "pdf_file": doc["pdf_file"],
                        "chunk_index": doc["chunk_index"],
                        "chunk_text": doc["chunk_text"]
                    })
            except Exception as db_error:
                print(f"[RAG] Database error: {str(db_error)}")
                raise

            if not embeddings:
                print("[RAG] No chunks found in the database!")
                return []

            print(f"[RAG] Found {len(embeddings)} total chunks in database")
            embeddings = np.array(embeddings, dtype=np.float32)

            # Compute cosine similarity
            print("[RAG] Computing similarities...")
            similarities = np.dot(embeddings, query_emb) / (
                np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_emb)
            )
            top_indices = np.argsort(similarities)[-top_k:][::-1]

            # Filter by similarity threshold
            results = []
            for idx in top_indices:
                if similarities[idx] >= similarity_threshold:
                    results.append({**metadata[idx], "score": float(similarities[idx])})
                    print(f"\n[RAG] Retrieved chunk from {metadata[idx]['pdf_file']}")
                    print(f"[RAG] Similarity score: {similarities[idx]:.3f}")
                    print(f"[RAG] Preview: {metadata[idx]['chunk_text'][:200]}...")

            print(f"\n[RAG] Retrieved {len(results)} relevant chunks above threshold {similarity_threshold}")
            return results
        except Exception as e:
            print(f"[RAG] Error in retrieve_relevant_chunks: {str(e)}")
            raise

    def generate_response_with_context(self, query: str) -> str:
        """Generate a response using RAG - retrieve relevant chunks and use them as context."""
        try:
            # Get relevant chunks
            print("\n[RAG] Starting retrieval process...")
            relevant_chunks = self.retrieve_relevant_chunks(query)
            
            if not relevant_chunks:
                print("[RAG] No relevant chunks found, returning default response")
                return "I couldn't find any relevant information to answer your question. Could you please rephrase or ask something else?"

            # Build context from relevant chunks
            context = "\n\n".join(
                f"Chunk {i+1}: {chunk['chunk_text']}"
                for i, chunk in enumerate(relevant_chunks)
            )

            print("\n[RAG] Sending chunks to LLM for response generation...")
            print(f"[RAG] OpenAI API Key present: {bool(self.ai_client.api_key)}")

            # Create messages for the chat completion
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
                print("[RAG] Making API call to OpenAI...")
                response = self.ai_client.chat.completions.create(
                    model="gpt-4",
                    messages=messages,
                    max_tokens=300,
                    temperature=0.7
                )
                print("[RAG] Successfully received response from OpenAI")
                return response.choices[0].message.content.strip()
            except Exception as api_error:
                print(f"[RAG] OpenAI API error: {str(api_error)}")
                return f"I encountered an error while generating the response: {str(api_error)}"
        except Exception as e:
            print(f"[RAG] Error in generate_response_with_context: {str(e)}")
            return f"An unexpected error occurred: {str(e)}"

    def close(self):
        """Close the MongoDB connection."""
        self.client.close() 