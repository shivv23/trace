import os
import threading
import numpy as np


class EmbeddingProvider:
    _instances = {}
    _instances_lock = threading.Lock()

    def __new__(cls, model_name: str = "all-MiniLM-L6-v2"):
        with cls._instances_lock:
            if model_name not in cls._instances:
                instance = super().__new__(cls)
                instance._model_name = model_name
                instance._model = None
                instance._lock = threading.Lock()
                cls._instances[model_name] = instance
        return cls._instances[model_name]

    def _load_model(self):
        if self._model is None:
            with self._lock:
                if self._model is None:
                    try:
                        from sentence_transformers import SentenceTransformer
                        cache_folder = os.getenv("SENTENCE_TRANSFORMERS_HOME", None)
                        self._model = SentenceTransformer(
                            self._model_name,
                            cache_folder=cache_folder
                        )
                    except Exception as e:
                        raise RuntimeError(f"Failed to load embedding model {self._model_name}: {e}")

    def embed(self, texts: list[str]) -> np.ndarray:
        self._load_model()
        embeddings = self._model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        return np.array(embeddings, dtype=np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        return self.embed([text])[0]

    @property
    def dimension(self) -> int:
        self._load_model()
        return self._model.get_sentence_embedding_dimension()

    @property
    def model_name(self) -> str:
        return self._model_name


def get_embedding_provider(model_name: str = "all-MiniLM-L6-v2") -> EmbeddingProvider:
    return EmbeddingProvider(model_name)