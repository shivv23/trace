import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    APP_NAME: str = "Trace - Transparent Support AI"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    DATA_DIR: Path = BASE_DIR / "data"
    UPLOAD_DIR: Path = DATA_DIR / "uploads"
    CHROMA_DIR: Path = DATA_DIR / "chroma"

    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8080"]

    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY")

    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    CROSS_ENCODER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-4-v2"

    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64
    TOP_K_RETRIEVAL: int = 10
    TOP_K_RERANK: int = 5
    CONFIDENCE_THRESHOLD_HIGH: float = 0.75
    CONFIDENCE_THRESHOLD_MEDIUM: float = 0.45

    MAX_UPLOAD_SIZE_MB: int = 20
    ALLOWED_EXTENSIONS: set[str] = {".pdf", ".docx", ".txt", ".md", ".json", ".csv", ".html", ".htm"}

    RATE_LIMIT_PER_MINUTE: int = 30
    MAX_CONVERSATION_HISTORY: int = 50

    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 1024

    ENABLE_CONTENT_MODERATION: bool = True
    ENABLE_PII_REDACTION: bool = True

    JWT_SECRET: str = os.getenv("JWT_SECRET", secrets.token_hex(32))
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 1440

    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")

    class Config:
        env_file = ".env"

settings = Settings()
