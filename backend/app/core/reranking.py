import numpy as np
from typing import Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import settings


class Reranker:
    def __init__(self):
        self._tfidf = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2),
            sublinear_tf=True,
        )

    def warmup(self):
        pass

    def rerank(self, query: str, results: list[dict], k: int = None) -> list[dict]:
        if k is None:
            k = settings.TOP_K_RERANK
        if not results:
            return []
        return self._rerank_with_tfidf(query, results, k)

    def _rerank_with_tfidf(self, query: str, results: list[dict], k: int) -> list[dict]:
        texts = [r["content"] for r in results]
        try:
            vectors = self._tfidf.fit_transform([query] + texts)
            query_vec = vectors[0:1]
            doc_vecs = vectors[1:]
            scores = cosine_similarity(query_vec, doc_vecs).flatten()
            for i, r in enumerate(results):
                r["rerank_score"] = float(scores[i]) if i < len(scores) else r.get("combined_score", 0)
        except Exception:
            for r in results:
                r["rerank_score"] = r.get("combined_score", 0)

        results.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
        return results[:k]
