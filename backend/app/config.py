import os
import secrets
import logging
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

logger = logging.getLogger(__name__)


class Settings:
    APP_NAME: str = "Trace - Transparent Support AI"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    DATA_DIR: Path = BASE_DIR / "data"
    UPLOAD_DIR: Path = DATA_DIR / "uploads"
    CHROMA_DIR: Path = DATA_DIR / "chroma"

    _raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    CORS_ORIGINS: list[str] = [o.strip() for o in _raw_origins.split(",") if o.strip()]

    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY")

    EMBEDDING_MODEL: str = "gemini-embedding-001"

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

    _raw_secret = os.getenv("JWT_SECRET", "")
    JWT_SECRET: str = _raw_secret if _raw_secret and len(_raw_secret) >= 16 else secrets.token_hex(32)
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 1440

    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")

    _raw_admin_pw = os.getenv("ADMIN_PASSWORD", "")
    ADMIN_PASSWORD: str = _raw_admin_pw if _raw_admin_pw else "admin123"


settings = Settings()

if settings.DEBUG:
    logger.warning("DEBUG mode enabled — not suitable for production")

if not settings.GEMINI_API_KEY or "your-" in str(settings.GEMINI_API_KEY):
    logger.warning("GEMINI_API_KEY not configured — Gemini provider will not work")

if not settings.GROQ_API_KEY or "your-" in str(settings.GROQ_API_KEY):
    logger.warning("GROQ_API_KEY not configured — Groq provider will not work")
