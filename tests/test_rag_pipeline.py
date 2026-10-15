import numpy as np
import pytest
from backend.models.rag_handler import (
    RAGHandler,
    chunk_text_sliding_window,
    compute_cosine_similarities,
    evaluate_retrieval_metrics,
)


class DummyEmbedder:
    def encode(self, text: str) -> np.ndarray:
        t = text.lower()
        if "calculus" in t or "derivative" in t:
            return np.array([1.0, 0.0, 0.0], dtype=np.float32)
        if "history" in t or "reconstruction" in t:
            return np.array([0.0, 1.0, 0.0], dtype=np.float32)
        return np.array([0.0, 0.0, 1.0], dtype=np.float32)


class DummyChoiceMessage:
    def __init__(self, content: str):
        self.content = content


class DummyChoice:
    def __init__(self, content: str):
        self.message = DummyChoiceMessage(content)


class DummyCompletions:
    def create(self, **kwargs):
        msgs = kwargs["messages"]
        ctx = msgs[1]["content"]
        return type("Resp", (), {"choices": [DummyChoice(f"Grounded answer from {ctx.splitlines()[1]}")]})()


class DummyOpenAI:
    def __init__(self):
        self.api_key = "test-key"
        self.chat = type("Chat", (), {"completions": DummyCompletions()})()


def test_chunk_text_sliding_window_overlaps_and_boundaries():
    words = [f"w{i}" for i in range(10)]
    text = " ".join(words)
    chunks = chunk_text_sliding_window(text, chunk_size=4, overlap=2)
    assert chunks == [
        "w0 w1 w2 w3",
        "w2 w3 w4 w5",
        "w4 w5 w6 w7",
        "w6 w7 w8 w9",
    ]
    assert chunk_text_sliding_window("   ") == []
    with pytest.raises(ValueError):
        chunk_text_sliding_window("a b c", chunk_size=3, overlap=3)


def test_compute_cosine_similarities_zero_norm_safe():
    embeddings = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],  # zero vector chunk
            [0.0, 1.0, 0.0],
        ],
        dtype=np.float32,
    )
    query = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    sims = compute_cosine_similarities(embeddings, query)
    assert np.allclose(sims, [1.0, 0.0, 0.0])

    zero_query_sims = compute_cosine_similarities(embeddings, np.zeros(3, dtype=np.float32))
    assert np.allclose(zero_query_sims, [0.0, 0.0, 0.0])


def test_rag_handler_retrieve_and_generate_offline():
    chunks = [
        {
            "pdf_file": "AP_Calc_AB.pdf",
            "chunk_index": 0,
            "chunk_text": "The chain rule computes the derivative of composite functions.",
            "embedding": [0.98, 0.05, 0.0],
        },
        {
            "pdf_file": "AP_USH.pdf",
            "chunk_index": 1,
            "chunk_text": "Reconstruction amendments transformed constitutional citizenship.",
            "embedding": [0.02, 0.99, 0.0],
        },
    ]
    handler = RAGHandler(model=DummyEmbedder(), chunks_collection=chunks, ai_client=DummyOpenAI())
    results = handler.retrieve_relevant_chunks("How do I take a derivative in calculus?", top_k=2, similarity_threshold=0.5)
    assert len(results) == 1
    assert results[0]["pdf_file"] == "AP_Calc_AB.pdf"
    assert results[0]["score"] > 0.95

    answer = handler.generate_response_with_context("Explain the derivative rule")
    assert "Grounded answer from Chunk 1: The chain rule" in answer


def test_evaluate_retrieval_metrics():
    retrieved = ["doc_calc_1", "doc_bio_2", "doc_calc_2", "doc_chem_1"]
    relevant = {"doc_calc_1", "doc_calc_2"}
    metrics = evaluate_retrieval_metrics(retrieved, relevant, k=3)
    assert metrics["recall_at_k"] == 1.0
    assert metrics["precision_at_k"] == pytest.approx(2.0 / 3.0, abs=1e-5)
    assert metrics["mrr"] == 1.0
    assert 0.9 < metrics["ndcg_at_k"] <= 1.0
