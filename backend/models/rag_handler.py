import math
import os
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set
import numpy as np

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # pragma: no cover
    pass


def chunk_text_sliding_window(
    text: str,
    chunk_size: int = 120,
    overlap: int = 30,
) -> List[str]:
    """Split text into overlapping word-level chunks for RAG indexing."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must satisfy 0 <= overlap < chunk_size")
    if not text or not text.strip():
        return []

    words = text.split()
    if len(words) <= chunk_size:
        return [" ".join(words)]

    step = chunk_size - overlap
    chunks: List[str] = []
    for start in range(0, len(words), step):
        window = words[start : start + chunk_size]
        if not window:
            break
        chunks.append(" ".join(window))
        if start + chunk_size >= len(words):
            break
    return chunks


def compute_cosine_similarities(
    embeddings: np.ndarray,
    query_emb: np.ndarray,
) -> np.ndarray:
    """Compute zero-norm-safe cosine similarities between a 2D matrix and a 1D query vector."""
    mat = np.asarray(embeddings, dtype=np.float32)
    q = np.asarray(query_emb, dtype=np.float32).reshape(-1)
    if mat.ndim != 2 or mat.shape[0] == 0:
        return np.zeros((0,), dtype=np.float32)
    if mat.shape[1] != q.shape[0]:
        raise ValueError(f"Dimension mismatch: embeddings have {mat.shape[1]} cols, query has {q.shape[0]}")

    q_norm = float(np.linalg.norm(q))
    if q_norm <= 1e-12:
        return np.zeros((mat.shape[0],), dtype=np.float32)

    row_norms = np.linalg.norm(mat, axis=1)
    denom = row_norms * q_norm
    dots = np.dot(mat, q)
    return np.where(denom > 1e-12, dots / np.where(denom > 1e-12, denom, 1.0), 0.0).astype(np.float32)


def evaluate_retrieval_metrics(
    retrieved_ids: Sequence[str],
    relevant_ids: Set[str],
    k: int = 5,
) -> Dict[str, float]:
    """Compute Recall@K, Precision@K, MRR, and nDCG@K for a ranked retrieval list."""
    if k <= 0:
        raise ValueError("k must be positive")
    if not relevant_ids:
        return {"recall_at_k": 0.0, "precision_at_k": 0.0, "mrr": 0.0, "ndcg_at_k": 0.0}

    top_k = list(retrieved_ids[:k])
    hits = [1 if doc_id in relevant_ids else 0 for doc_id in top_k]
    num_hits = sum(hits)

    recall_at_k = num_hits / float(len(relevant_ids))
    precision_at_k = num_hits / float(k)

    mrr = 0.0
    for idx, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in relevant_ids:
            mrr = 1.0 / float(idx)
            break

    dcg = sum(rel / math.log2(idx + 2) for idx, rel in enumerate(hits))
    ideal_hits = min(len(relevant_ids), k)
    idcg = sum(1.0 / math.log2(idx + 2) for idx in range(ideal_hits))
    ndcg_at_k = (dcg / idcg) if idcg > 0 else 0.0

    return {
        "recall_at_k": round(recall_at_k, 6),
        "precision_at_k": round(precision_at_k, 6),
        "mrr": round(mrr, 6),
        "ndcg_at_k": round(ndcg_at_k, 6),
    }


class RAGHandler:
    def __init__(
        self,
        model: Optional[Any] = None,
        chunks_collection: Optional[Any] = None,
        ai_client: Optional[Any] = None,
    ):
        self.model = model
        self.mongo_uri = os.getenv("MONGO_URI")
        self.client = None
        self.db = None
        self.chunks_collection = chunks_collection
        self.ai_client = ai_client

        if self.model is None:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer("all-MiniLM-L6-v2")

        if self.chunks_collection is None:
            from pymongo import MongoClient
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client["pdf_chunks_db"]
            self.chunks_collection = self.db["chunks"]

        if self.ai_client is None:
            from openai import OpenAI
            self.ai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def _fetch_all_chunks(self) -> Iterable[Dict[str, Any]]:
        if isinstance(self.chunks_collection, list):
            return self.chunks_collection
        return self.chunks_collection.find(
            {},
            {"embedding": 1, "pdf_file": 1, "chunk_index": 1, "chunk_text": 1},
        )

    def retrieve_relevant_chunks(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.3,
    ) -> List[Dict]:
        """Retrieve the most relevant chunks for a given query using cosine similarity."""
        if not query or not query.strip() or top_k <= 0:
            return []

        query_emb = np.asarray(self.model.encode(query), dtype=np.float32)

        metadata, embeddings = [], []
        for doc in self._fetch_all_chunks():
            embeddings.append(doc["embedding"])
            metadata.append(
                {
                    "pdf_file": doc["pdf_file"],
                    "chunk_index": doc["chunk_index"],
                    "chunk_text": doc["chunk_text"],
                }
            )

        if not embeddings:
            return []

        embeddings_arr = np.asarray(embeddings, dtype=np.float32)
        similarities = compute_cosine_similarities(embeddings_arr, query_emb)
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        results = []
        for idx in top_indices:
            if similarities[idx] >= similarity_threshold:
                results.append({**metadata[idx], "score": float(similarities[idx])})

        return results

    def generate_response_with_context(self, query: str) -> str:
        """Generate a response using RAG - retrieve relevant chunks and use them as context."""
        try:
            relevant_chunks = self.retrieve_relevant_chunks(query)
            if not relevant_chunks:
                return (
                    "I couldn't find any relevant information to answer your question. "
                    "Could you please rephrase or ask something else?"
                )

            context = "\n\n".join(
                f"Chunk {i+1}: {chunk['chunk_text']}"
                for i, chunk in enumerate(relevant_chunks)
            )

            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an expert assistant. Use the provided context to answer "
                        "the user's question accurately, quoting from the context when helpful."
                    ),
                },
                {"role": "system", "content": f"Context:\n{context}"},
                {"role": "user", "content": query},
            ]

            try:
                response = self.ai_client.chat.completions.create(
                    model="gpt-4",
                    messages=messages,
                    max_tokens=300,
                    temperature=0.7,
                )
                return response.choices[0].message.content.strip()
            except Exception as api_error:
                return f"I encountered an error while generating the response: {str(api_error)}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"

    def close(self):
        """Close the MongoDB connection."""
        if self.client is not None:
            self.client.close()