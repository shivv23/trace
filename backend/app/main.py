import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.models.db import init_db, list_documents, delete_document as db_delete_doc, create_user, get_user_by_username
from app.core.embeddings import EmbeddingProvider, get_embedding_provider
from app.core.auth import hash_password, get_current_user
from app.api.chat import router as chat_router, init_chat_engine
from app.api.documents import router as documents_router, init_document_engine, set_retriever_ref
from app.api.feedback import router as feedback_router
from app.api.auth import router as auth_router
from app.core.retrieval import HybridRetriever
from app.core.reranking import Reranker

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")

    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    settings.CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    init_db()

    chroma_client = _init_chroma()
    init_document_engine(chroma_client)

    retriever, reranker = _init_rag_engine(chroma_client)
    init_chat_engine(retriever, reranker)
    set_retriever_ref(retriever)

    _seed_admin_user()

    try:
        logger.info("Warming up embedding model...")
        embedder = get_embedding_provider()
        embedder.embed(["warmup"])
        logger.info("Embedding model ready")
    except Exception as e:
        logger.warning(f"Embedding model warmup failed: {e}")

    try:
        logger.info("Warming up reranker...")
        reranker.warmup()
        logger.info("Reranker ready")
    except Exception as e:
        logger.warning(f"Reranker warmup failed: {e}")

    doc_count = len(list_documents())
    logger.info(f"Ready — {doc_count} documents indexed, LLM: {settings.LLM_PROVIDER}")

    _cleanup_orphaned_docs(chroma_client)

    yield

    logger.info("Shutting down — checkpointing WAL")
    try:
        from app.models.db import close_all
        close_all()
    except Exception:
        pass


def _seed_admin_user():
    try:
        existing = get_user_by_username(settings.ADMIN_USERNAME)
        if not existing:
            import uuid
            user_id = str(uuid.uuid4())
            hashed = hash_password(settings.ADMIN_PASSWORD)
            create_user(user_id, settings.ADMIN_USERNAME, hashed, is_admin=True)
            logger.info(f"Admin user '{settings.ADMIN_USERNAME}' created")
        else:
            logger.info(f"Admin user '{settings.ADMIN_USERNAME}' already exists")
    except Exception as e:
        logger.warning(f"Failed to seed admin user: {e}")


def _init_chroma():
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(settings.CHROMA_DIR))
        logger.info(f"ChromaDB initialized at {settings.CHROMA_DIR}")
        return client
    except Exception as e:
        logger.warning(f"ChromaDB init failed: {e}. Using in-memory fallback.")
        import chromadb
        return chromadb.Client()


def _init_rag_engine(chroma_client):
    try:
        collection_name = "trace_knowledge"
        try:
            collection = chroma_client.get_collection(collection_name)
        except Exception:
            collection = chroma_client.create_collection(collection_name)

        retriever = HybridRetriever(collection)
        reranker = Reranker()
        logger.info("RAG engine initialized")
        return retriever, reranker
    except Exception as e:
        logger.error(f"RAG engine init failed: {e}")
        raise


def _cleanup_orphaned_docs(chroma_client):
    try:
        collection = chroma_client.get_collection("trace_knowledge")
    except Exception:
        return

    stale_docs = [d for d in list_documents() if d["status"] in ("processing", "error")]
    if not stale_docs:
        return

    logger.info(f"Cleaning up {len(stale_docs)} stale documents from previous run")
    for doc in stale_docs:
        doc_id = doc["id"]
        try:
            collection.delete(where={"document_id": doc_id})
        except Exception:
            pass
        filepath = settings.UPLOAD_DIR / f"{doc_id}{doc['type']}"
        if filepath.exists():
            try:
                filepath.unlink()
            except Exception:
                pass
        try:
            db_delete_doc(doc_id)
        except Exception:
            pass
        logger.info(f"Cleaned up stale document: {doc['name']} ({doc_id})")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(feedback_router)


@app.get("/api/admin/stats")
async def admin_stats(user: dict = Depends(get_current_user)):
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    from app.models.db import a_get_admin_stats
    return await a_get_admin_stats()


@app.get("/api/health")
async def health_check():
    from app.models.db import list_documents
    has_key = bool(settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY"))
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "documents_indexed": len(list_documents()),
        "llm_provider": settings.LLM_PROVIDER or "fallback (no key)",
        "gemini_configured": has_key,
        "gemini_model": settings.GEMINI_MODEL,
        "embedding_model": settings.EMBEDDING_MODEL,
        "auth_enabled": True,
    }


frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
