import uuid
import json
import time
import asyncio
import logging
from collections import deque
from fastapi import APIRouter, HTTPException, Request, Depends

from app.config import settings

from app.models.schemas import ChatRequest, ChatResponse, SourceChunk, ConfidenceScore
from app.models.db import (
    a_get_conversation, a_create_conversation, a_add_message,
    a_get_conversation_messages
)
from app.core.retrieval import HybridRetriever
from app.core.reranking import Reranker
from app.core.generation import generate_answer
from app.core.confidence import compute_confidence
from app.core.auth import get_current_user
from app.utils.moderation import moderate_input
from app.utils.pii import redact_pii

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])

_retriever: HybridRetriever = None
_reranker: Reranker = None

_rate_limit_buckets: dict[str, deque] = {}
_rate_limit_lock = asyncio.Lock()


async def _check_rate_limit(client_ip: str) -> None:
    limit = settings.RATE_LIMIT_PER_MINUTE
    if limit <= 0:
        return
    now = time.monotonic()
    async with _rate_limit_lock:
        _evict_stale_buckets()
        bucket = _rate_limit_buckets.get(client_ip)
        if bucket is None:
            bucket = deque()
            _rate_limit_buckets[client_ip] = bucket
        while bucket and now - bucket[0] > 60:
            bucket.popleft()
        if len(bucket) >= limit:
            raise HTTPException(status_code=429, detail=f"Rate limit exceeded ({limit} req/min). Please slow down.")
        bucket.append(now)


def _evict_stale_buckets():
    cutoff = time.monotonic() - 120
    stale = [ip for ip, bucket in _rate_limit_buckets.items() if not bucket or bucket[-1] < cutoff]
    for ip in stale:
        del _rate_limit_buckets[ip]


def init_chat_engine(retriever: HybridRetriever, reranker: Reranker):
    global _retriever, _reranker
    _retriever = retriever
    _reranker = reranker


@router.post("")
async def chat(request: ChatRequest, fastapi_request: Request, user: dict = Depends(get_current_user)):
    client_ip = fastapi_request.client.host if fastapi_request.client else "unknown"
    await _check_rate_limit(client_ip)

    if _retriever is None:
        raise HTTPException(status_code=503, detail="Chat engine not initialized. Upload documents first.")

    mod_result = moderate_input(request.message)
    if mod_result["is_toxic"]:
        raise HTTPException(status_code=400, detail=f"Message blocked: {mod_result['reason']}")

    conversation_id = request.conversation_id or str(uuid.uuid4())
    conv = await a_get_conversation(conversation_id)
    if not conv:
        await a_create_conversation(conversation_id, user["id"])

    history = await a_get_conversation_messages(conversation_id)

    start_time = time.monotonic()

    doc_filter = request.document_ids if request.document_ids else None
    retrieved = _retriever.retrieve(request.message, document_ids=doc_filter)
    reranked = _reranker.rerank(request.message, retrieved)
    confidence = compute_confidence(request.message, reranked)
    answer = generate_answer(request.message, reranked, history)

    processing_time = (time.monotonic() - start_time) * 1000

    await a_add_message(conversation_id, "user", redact_pii(request.message), user_id=user["id"])

    sources_json = json.dumps([
        {
            "chunk_id": s["chunk_id"],
            "document_id": s.get("metadata", {}).get("document_id", ""),
            "document_name": s.get("metadata", {}).get("document_name", "Unknown"),
            "content": s["content"][:500],
            "relevance_score": s.get("rerank_score", s.get("combined_score", 0)),
            "page_number": s.get("metadata", {}).get("page_number"),
            "chunk_index": s.get("metadata", {}).get("chunk_index", 0),
            "file_type": s.get("metadata", {}).get("file_type", ""),
        }
        for s in reranked[:5]
    ])
    confidence_json = json.dumps(confidence)

    await a_add_message(conversation_id, "assistant", redact_pii(answer), sources=sources_json, confidence=confidence_json, user_id=user["id"])

    source_chunks = [
        SourceChunk(
            chunk_id=s["chunk_id"],
            document_id=s.get("metadata", {}).get("document_id", ""),
            document_name=s.get("metadata", {}).get("document_name", "Unknown"),
            content=s["content"][:500],
            relevance_score=s.get("rerank_score", s.get("combined_score", 0)),
            page_number=s.get("metadata", {}).get("page_number"),
            chunk_index=s.get("metadata", {}).get("chunk_index", 0),
            file_type=s.get("metadata", {}).get("file_type", ""),
        )
        for s in reranked[:5]
    ]

    return ChatResponse(
        answer=answer,
        sources=source_chunks,
        confidence=ConfidenceScore(**confidence),
        conversation_id=conversation_id,
        processing_time_ms=round(processing_time, 1),
    )


@router.get("/{conversation_id}")
async def get_history(conversation_id: str, user: dict = Depends(get_current_user)):
    conv = await a_get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv.get("user_id") and conv["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    messages = await a_get_conversation_messages(conversation_id)
    return {"conversation_id": conversation_id, "messages": messages}
