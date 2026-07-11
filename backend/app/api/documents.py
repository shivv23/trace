from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends

from app.models.schemas import DocumentInfo, UploadResponse, DeleteResponse
from app.models.db import (
    a_upsert_document, a_get_document, a_get_document_by_hash,
    a_list_documents, a_delete_document as a_db_delete_doc
)
from app.core.ingestion import process_upload, extract_text
from app.core.chunking import chunk_text
from app.core.embeddings import get_embedding_provider
from app.core.auth import get_current_user
from app.config import settings

router = APIRouter(prefix="/api/documents", tags=["documents"])

_chroma_client = None
_retriever_ref = None


def init_document_engine(chroma_client):
    global _chroma_client
    _chroma_client = chroma_client


def set_retriever_ref(retriever):
    global _retriever_ref
    _retriever_ref = retriever


def _cleanup_failed_upload(doc_id: str, ext: str):
    filepath = settings.UPLOAD_DIR / f"{doc_id}{ext}"
    if filepath.exists():
        filepath.unlink()
    try:
        collection = get_or_create_collection()
        collection.delete(where={"document_id": doc_id})
    except Exception:
        pass


def get_or_create_collection(name: str = "trace_knowledge"):
    if _chroma_client is None:
        raise RuntimeError("Chroma client not initialized")
    try:
        return _chroma_client.get_collection(name)
    except Exception:
        return _chroma_client.create_collection(name)


@router.get("")
async def list_all_documents(user: dict = Depends(get_current_user)):
    docs = await a_list_documents(user["id"])
    return [DocumentInfo(
        id=d["id"],
        name=d["name"],
        type=d["type"],
        size_bytes=d["size_bytes"],
        chunk_count=d["chunk_count"],
        uploaded_at=d["uploaded_at"],
        status=d["status"],
    ) for d in docs]


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not supported. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    doc_id = file_hash = None
    filepath = ""
    size_bytes = 0
    try:
        doc_id, filepath, size_bytes, ext, file_hash = process_upload(file.file, file.filename)

        existing = await a_get_document_by_hash(file_hash, user["id"])
        if existing:
            Path(filepath).unlink(missing_ok=True)
            raise HTTPException(
                status_code=409,
                detail=f"Duplicate file: '{existing['name']}' already uploaded on {existing['uploaded_at'][:10]}"
            )

        await a_upsert_document(doc_id, file.filename, ext, size_bytes, status="processing", file_hash=file_hash, user_id=user["id"])

        raw_text = extract_text(filepath, file.filename)

        embedder = get_embedding_provider()
        chunks = chunk_text(raw_text, strategy="recursive",
                            chunk_size=settings.CHUNK_SIZE,
                            chunk_overlap=settings.CHUNK_OVERLAP)

        collection = get_or_create_collection()

        chunk_texts = [c["content"] for c in chunks]
        chunk_embeddings = embedder.embed(chunk_texts)
        chunk_ids = [f"{doc_id}_{c['chunk_index']}" for c in chunks]
        metadatas = []
        for c in chunks:
            metadatas.append({
                "document_id": doc_id,
                "document_name": file.filename,
                "chunk_index": c["chunk_index"],
                "chunk_size": len(c["content"]),
                "file_type": ext,
            })

        batch_size = 100
        for i in range(0, len(chunk_ids), batch_size):
            end = min(i + batch_size, len(chunk_ids))
            collection.add(
                ids=chunk_ids[i:end],
                embeddings=chunk_embeddings[i:end].tolist(),
                documents=chunk_texts[i:end],
                metadatas=metadatas[i:end],
            )

        if _retriever_ref is not None:
            _retriever_ref.invalidate_cache()

        await a_upsert_document(doc_id, file.filename, ext, size_bytes,
                                chunk_count=len(chunks), status="ready", file_hash=file_hash, user_id=user["id"])

        return UploadResponse(
            id=doc_id,
            name=file.filename,
            type=ext,
            chunk_count=len(chunks),
            status="ready",
            message=f"Successfully processed {file.filename} into {len(chunks)} chunks",
        )

    except ValueError as e:
        if doc_id:
            await a_upsert_document(doc_id, file.filename, ext, size_bytes, status="error", file_hash=file_hash, user_id=user["id"])
            _cleanup_failed_upload(doc_id, ext)
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        if doc_id:
            await a_upsert_document(doc_id, file.filename, ext, size_bytes, status="error", file_hash=file_hash, user_id=user["id"])
            _cleanup_failed_upload(doc_id, ext)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.delete("/{doc_id}", response_model=DeleteResponse)
async def delete_document(doc_id: str, user: dict = Depends(get_current_user)):
    doc = await a_get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.get("user_id") and doc["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    errors = []

    try:
        collection = get_or_create_collection()
        collection.delete(where={"document_id": doc_id})
    except Exception as e:
        errors.append(f"vector index: {e}")

    try:
        await a_db_delete_doc(doc_id)
    except Exception as e:
        errors.append(f"database: {e}")

    if _retriever_ref is not None:
        _retriever_ref.invalidate_cache()

    filepath = settings.UPLOAD_DIR / f"{doc_id}{doc['type']}"
    if filepath.exists():
        try:
            filepath.unlink()
        except Exception as e:
            errors.append(f"file: {e}")

    if errors:
        raise HTTPException(status_code=500, detail=f"Partial delete: {'; '.join(errors)}")

    return DeleteResponse(success=True, message=f"Deleted {doc['name']}")


@router.get("/{doc_id}")
async def get_document_info(doc_id: str, user: dict = Depends(get_current_user)):
    doc = await a_get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.get("user_id") and doc["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return DocumentInfo(
        id=doc["id"],
        name=doc["name"],
        type=doc["type"],
        size_bytes=doc["size_bytes"],
        chunk_count=doc["chunk_count"],
        uploaded_at=doc["uploaded_at"],
        status=doc["status"],
    )
