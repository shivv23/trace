import sys
sys.path.insert(0, 'backend')

from app.core.confidence import compute_confidence


def test_empty_results():
    confidence = compute_confidence("test query", [])
    assert confidence["overall"] == 0.0
    assert confidence["label"] == "low"
    assert confidence["support_count"] == 0


def test_high_confidence():
    results = [
        {"rerank_score": 0.9, "combined_score": 0.85, "metadata": {"document_name": "doc1.pdf"}},
        {"rerank_score": 0.85, "combined_score": 0.8, "metadata": {"document_name": "doc1.pdf"}},
        {"rerank_score": 0.8, "combined_score": 0.75, "metadata": {"document_name": "doc2.pdf"}},
        {"rerank_score": 0.75, "combined_score": 0.7, "metadata": {"document_name": "doc2.pdf"}},
        {"rerank_score": 0.7, "combined_score": 0.65, "metadata": {"document_name": "doc3.pdf"}},
    ]
    confidence = compute_confidence("test query", results)
    assert confidence["overall"] >= 0.5
    assert confidence["support_count"] == 5


def test_low_confidence():
    results = [
        {"rerank_score": -2.0, "combined_score": -1.0, "metadata": {"document_name": "doc1.pdf"}},
    ]
    confidence = compute_confidence("test query", results)
    assert confidence["overall"] < 0.5
    assert confidence["label"] == "low"
    assert confidence["support_count"] == 0


def test_rerank_score_preferred():
    results = [
        {"rerank_score": 0.9, "combined_score": 0.1, "metadata": {"document_name": "doc1.pdf"}},
    ]
    confidence = compute_confidence("test query", results)
    assert confidence["overall"] > 0.3
    assert confidence["support_count"] == 1
