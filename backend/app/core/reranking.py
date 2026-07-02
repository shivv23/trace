import torch
import numpy as np
from typing import Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import settings


class Reranker:
    def __init__(self):
        self._cross_encoder = None
        self._tfidf = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2),
            sublinear_tf=True,
        )

    def _load_cross_encoder(self):
        if self._cross_encoder is None:
            try:
                from transformers import AutoModelForSequenceClassification, AutoTokenizer
                model_name = settings.CROSS_ENCODER_MODEL
                self._cross_encoder_tokenizer = AutoTokenizer.from_pretrained(model_name)
                self._cross_encoder = AutoModelForSequenceClassification.from_pretrained(model_name)
                self._cross_encoder.eval()
            except Exception:
                self._cross_encoder = False

    def warmup(self):
        self._load_cross_encoder()

    def rerank(self, query: str, results: list[dict], k: int = None) -> list[dict]:
        if k is None:
            k = settings.TOP_K_RERANK
        if not results:
            return []

        try:
            return self._rerank_with_cross_encoder(query, results, k)
        except Exception:
            return self._rerank_with_tfidf(query, results, k)

    def _rerank_with_cross_encoder(self, query: str, results: list[dict], k: int) -> list[dict]:
        self._load_cross_encoder()
        if not self._cross_encoder or self._cross_encoder is False:
            return self._rerank_with_tfidf(query, results, k)

        pairs = [(query, r["content"]) for r in results]
        inputs = self._cross_encoder_tokenizer(
            pairs, padding=True, truncation=True, max_length=512, return_tensors="pt"
        )
        with torch.no_grad():
            scores = self._cross_encoder(**inputs).logits.flatten().tolist()

        for i, r in enumerate(results):
            r["rerank_score"] = float(scores[i]) if i < len(scores) else r.get("combined_score", 0)

        results.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
        return results[:k]

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
