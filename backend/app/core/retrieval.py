import numpy as np
from typing import Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.core.embeddings import get_embedding_provider
from app.config import settings


class HybridRetriever:
    def __init__(self, chroma_collection):
        self.collection = chroma_collection
        self.embedder = get_embedding_provider()
        self._tfidf_vectorizer = None
        self._tfidf_matrix = None
        self._chunk_texts = []
        self._chunk_ids = []

    def _ensure_tfidf(self):
        if self._tfidf_vectorizer is None:
            all_data = self.collection.get(include=["documents"])
            if all_data and all_data["documents"]:
                self._chunk_texts = all_data["documents"]
                self._chunk_ids = all_data["ids"]
                self._tfidf_vectorizer = TfidfVectorizer(
                    max_features=5000,
                    stop_words='english',
                    ngram_range=(1, 2),
                    sublinear_tf=True,
                )
                self._tfidf_matrix = self._tfidf_vectorizer.fit_transform(self._chunk_texts)

    def retrieve(self, query: str, k: int = None, document_ids: Optional[list[str]] = None) -> list[dict]:
        if k is None:
            k = settings.TOP_K_RETRIEVAL

        query_embedding = self.embedder.embed_query(query)

        where_filter = None
        if document_ids:
            where_filter = {"document_id": {"$in": document_ids}}

        try:
            dense_results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=k * 2,
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )
        except Exception:
            return []

        dense_hits = {}
        if dense_results and dense_results["ids"] and len(dense_results["ids"]) > 0:
            for i, chunk_id in enumerate(dense_results["ids"][0]):
                distance = dense_results["distances"][0][i] if dense_results["distances"] else 0
                dense_score = 1.0 - (distance ** 2) / 2.0
                dense_score = max(0.0, min(1.0, dense_score))
                dense_hits[chunk_id] = {
                    "chunk_id": chunk_id,
                    "content": dense_results["documents"][0][i] if dense_results["documents"] else "",
                    "metadata": dense_results["metadatas"][0][i] if dense_results["metadatas"] else {},
                    "dense_score": dense_score,
                }

        sparse_hits = {}
        self._ensure_tfidf()
        if self._tfidf_vectorizer is not None and len(self._chunk_texts) > 0:
            try:
                query_vec = self._tfidf_vectorizer.transform([query])
                sparse_scores = cosine_similarity(query_vec, self._tfidf_matrix).flatten()
                top_sparse_idx = np.argsort(sparse_scores)[-k * 2:][::-1]
                for idx in top_sparse_idx:
                    if sparse_scores[idx] > 0:
                        chunk_id = self._chunk_ids[idx]
                        sparse_hits[chunk_id] = {
                            "chunk_id": chunk_id,
                            "sparse_score": float(sparse_scores[idx]),
                        }
            except Exception:
                pass

        all_chunk_ids = set(dense_hits.keys()) | set(sparse_hits.keys())
        results = []
        for cid in all_chunk_ids:
            entry = dense_hits.get(cid, {})
            sparse_entry = sparse_hits.get(cid, {})
            dense_score = entry.get("dense_score", 0)
            sparse_score = sparse_entry.get("sparse_score", 0)

            if dense_score + sparse_score == 0:
                continue

            combined_score = 0.6 * dense_score + 0.4 * sparse_score

            results.append({
                "chunk_id": cid,
                "content": entry.get("content", ""),
                "metadata": entry.get("metadata", {}),
                "dense_score": round(dense_score, 4),
                "sparse_score": round(sparse_score, 4),
                "combined_score": round(combined_score, 4),
            })

        results.sort(key=lambda x: x["combined_score"], reverse=True)
        return results[:k]

    def invalidate_cache(self):
        self._tfidf_vectorizer = None
        self._tfidf_matrix = None
        self._chunk_texts = []
        self._chunk_ids = []
