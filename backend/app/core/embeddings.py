import os
import threading
import numpy as np
from google import genai as new_genai

from app.config import settings

GEMINI_EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSION = 3072


class EmbeddingProvider:
    _instances = {}
    _instances_lock = threading.Lock()

    def __new__(cls, model_name: str = GEMINI_EMBEDDING_MODEL):
        with cls._instances_lock:
            if model_name not in cls._instances:
                instance = super().__new__(cls)
                instance._model_name = model_name
                instance._client = None
                instance._lock = threading.Lock()
                cls._instances[model_name] = instance
        return cls._instances[model_name]

    def _get_client(self):
        if self._client is None:
            with self._lock:
                if self._client is None:
                    api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
                    self._client = new_genai.Client(api_key=api_key, http_options={"timeout": 60 * 1000})
        return self._client

    def embed(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, EMBEDDING_DIMENSION), dtype=np.float32)
        client = self._get_client()
        result = client.models.embed_content(
            model=self._model_name,
            contents=texts,
        )
        vectors = [e.values for e in result.embeddings]
        return np.array(vectors, dtype=np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        return self.embed([text])[0]

    @property
    def dimension(self) -> int:
        return EMBEDDING_DIMENSION

    @property
    def model_name(self) -> str:
        return self._model_name


def get_embedding_provider(model_name: str = GEMINI_EMBEDDING_MODEL) -> EmbeddingProvider:
    return EmbeddingProvider(model_name)
