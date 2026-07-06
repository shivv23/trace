import math
import numpy as np

from app.config import settings


def _sigmoid(x: float) -> float:
    try:
        return 1.0 / (1.0 + math.exp(-x))
    except OverflowError:
        return 1.0 if x > 0 else 0.0


def compute_confidence(query: str, results: list[dict], top_k: int = 5) -> dict:
    if not results:
        return {
            "overall": 0.0,
            "relevance_score": 0.0,
            "semantic_similarity": 0.0,
            "source_quality": 0.0,
            "support_count": 0,
            "label": "low",
        }

    top_results = results[:top_k]

    relevance_scores = [r.get("rerank_score", r.get("combined_score", 0)) for r in top_results]
    relevance_score = float(np.mean(relevance_scores)) if relevance_scores else 0.0

    support_count = sum(1 for s in relevance_scores if s > 0.3)
    support_ratio = support_count / top_k

    semantic_similarity = relevance_score

    source_names = set()
    for r in top_results:
        meta = r.get("metadata", {})
        doc_name = meta.get("document_name", meta.get("source", ""))
        if doc_name:
            source_names.add(doc_name)
    source_diversity = min(len(source_names) / 3, 1.0)

    score_std = float(np.std(relevance_scores)) if len(relevance_scores) > 1 else 0
    consistency = 1.0 - min(score_std, 1.0)

    source_quality = 0.5 * source_diversity + 0.5 * consistency

    overall = (
        0.35 * relevance_score +
        0.25 * semantic_similarity +
        0.20 * source_quality +
        0.20 * support_ratio
    )
    overall = max(0.0, min(1.0, overall))

    if overall >= settings.CONFIDENCE_THRESHOLD_HIGH:
        label = "high"
    elif overall >= settings.CONFIDENCE_THRESHOLD_MEDIUM:
        label = "medium"
    else:
        label = "low"

    return {
        "overall": round(overall, 3),
        "relevance_score": round(relevance_score, 3),
        "semantic_similarity": round(semantic_similarity, 3),
        "source_quality": round(source_quality, 3),
        "support_count": support_count,
        "label": label,
    }
