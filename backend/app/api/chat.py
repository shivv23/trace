import uuid
import json
import time
import asyncio
import logging
from collections import deque
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from fastapi.responses import StreamingResponse

from app.config import settings

from app.models.schemas import ChatRequest, ChatResponse, SourceChunk, ConfidenceScore
from app.models.db import (
    a_get_conversation, a_create_conversation, a_add_message,
    a_get_conversation_messages, a_update_conversation_title,
    a_search_messages
)
from app.core.retrieval import HybridRetriever
from app.core.reranking import Reranker
from app.core.generation import generate_answer, stream_answer, detect_language
from app.core.confidence import compute_confidence
from app.core.auth import get_current_user
from app.core.web_search import search_web, format_web_results
from app.utils.moderation import moderate_input
from app.utils.pii import redact_pii

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


def _generate_suggested_questions(query: str, context_chunks: list[dict]) -> list[str]:
    doc_names = list(dict.fromkeys(
        s.get("metadata", {}).get("document_name", "")
        for s in context_chunks if s.get("metadata", {}).get("document_name")
    ))
    questions = []
    if doc_names:
        questions.append(f"Summarize the key information from {doc_names[0]}")
        if len(doc_names) > 1:
            questions.append(f"How does {doc_names[0]} relate to {doc_names[1]}?")
    if "summar" in query.lower() or "overview" in query.lower():
        questions.append("What are the specific details or data points?")
    elif "how" in query.lower():
        questions.append("What are the best practices for this?")
    elif "what" in query.lower():
        questions.append("Can you explain how this works in more detail?")
    else:
        questions.append("Can you provide more specific details?")
    questions.append("What are the key takeaways from this information?")
    return questions[:3]

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


@router.post("/stream")
async def chat_stream(request: ChatRequest, fastapi_request: Request, user: dict = Depends(get_current_user)):
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

    detected_lang = detect_language(request.message)

    has_sources = len(reranked[:5]) > 0
    top_score = max((s.get("rerank_score", s.get("combined_score", 0)) for s in reranked[:5]), default=0)
    grounded = has_sources and top_score >= settings.CONFIDENCE_THRESHOLD_MEDIUM

    web_results_text = ""
    web_results = []
    web_search_used = False
    if not grounded or top_score < settings.CONFIDENCE_THRESHOLD_MEDIUM:
        try:
            web_results = search_web(request.message, max_results=4)
            if web_results:
                web_results_text = format_web_results(web_results)
                web_search_used = True
                logger.info(f"Web search used for query: {request.message[:60]}... ({len(web_results)} results)")
        except Exception as e:
            logger.warning(f"Web search skipped: {e}")

    await a_add_message(conversation_id, "user", redact_pii(request.message), user_id=user["id"])

    was_new = not conv
    if was_new:
        title = request.message[:80] + ("..." if len(request.message) > 80 else "")
        await a_update_conversation_title(conversation_id, title)

    sources_json = json.dumps([
        {"chunk_id": s["chunk_id"], "document_id": s.get("metadata", {}).get("document_id", ""),
         "document_name": s.get("metadata", {}).get("document_name", "Unknown"),
         "content": s["content"][:500],
         "relevance_score": s.get("rerank_score", s.get("combined_score", 0)),
         "page_number": s.get("metadata", {}).get("page_number"),
         "chunk_index": s.get("metadata", {}).get("chunk_index", 0),
         "file_type": s.get("metadata", {}).get("file_type", "")}
        for s in reranked[:5]
    ])
    confidence_json = json.dumps({
        **confidence,
        "_lang": detected_lang,
        "_web": web_search_used,
    })

    async def event_generator():
        full_answer = ""
        for token_data in stream_answer(request.message, reranked, history, web_results_text, detected_lang):
            yield f"data: {token_data}\n\n"
            try:
                parsed = json.loads(token_data)
                if parsed.get("type") == "token":
                    full_answer += parsed.get("text", "")
            except json.JSONDecodeError:
                pass

        processing_time = (time.monotonic() - start_time) * 1000
        await a_add_message(conversation_id, "assistant", redact_pii(full_answer),
                            sources=sources_json, confidence=confidence_json, user_id=user["id"])

        suggested = _generate_suggested_questions(request.message, reranked)

        metadata = json.dumps({
            "type": "metadata",
            "sources": [{
                "chunk_id": s["chunk_id"],
                "document_id": s.get("metadata", {}).get("document_id", ""),
                "document_name": s.get("metadata", {}).get("document_name", "Unknown"),
                "content": s["content"][:500],
                "relevance_score": s.get("rerank_score", s.get("combined_score", 0)),
                "page_number": s.get("metadata", {}).get("page_number"),
                "chunk_index": s.get("metadata", {}).get("chunk_index", 0),
                "file_type": s.get("metadata", {}).get("file_type", ""),
            } for s in reranked[:5]],
            "confidence": confidence,
            "conversation_id": conversation_id,
            "processing_time_ms": round(processing_time, 1),
            "grounded": grounded,
            "suggested_questions": suggested,
            "language": detected_lang,
            "web_search_used": web_search_used,
            "web_results": web_results[:3] if web_results else [],
        })
        yield f"data: {metadata}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


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

    was_new = not conv
    if was_new:
        title = request.message[:80] + ("..." if len(request.message) > 80 else "")
        await a_update_conversation_title(conversation_id, title)

    history = await a_get_conversation_messages(conversation_id)

    start_time = time.monotonic()

    doc_filter = request.document_ids if request.document_ids else None
    retrieved = _retriever.retrieve(request.message, document_ids=doc_filter)
    reranked = _reranker.rerank(request.message, retrieved)
    confidence = compute_confidence(request.message, reranked)

    detected_lang = detect_language(request.message)
    has_sources = len(reranked[:5]) > 0
    top_score = max((s.get("rerank_score", s.get("combined_score", 0)) for s in reranked[:5]), default=0)
    grounded = has_sources and top_score >= settings.CONFIDENCE_THRESHOLD_MEDIUM

    web_results_text = ""
    web_result_items = []
    web_search_used = False
    if not grounded or top_score < settings.CONFIDENCE_THRESHOLD_MEDIUM:
        try:
            web_result_items = search_web(request.message, max_results=4)
            if web_result_items:
                web_results_text = format_web_results(web_result_items)
                web_search_used = True
        except Exception:
            pass

    answer = generate_answer(request.message, reranked, history, web_results_text, detected_lang)

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
    confidence_json = json.dumps({
        **confidence,
        "_lang": detected_lang,
        "_web": web_search_used,
    })

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
        language=detected_lang,
        web_search_used=web_search_used,
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


from app.models.db import a_list_user_conversations, a_delete_conversation, a_set_share_id, a_clear_share_id, a_get_conversation_by_share_id, migrate_add_share_id, a_rename_conversation


@router.get("/search")
async def search_conversations(q: str, user: dict = Depends(get_current_user)):
    if not q or len(q.strip()) < 2:
        return {"results": []}
    results = await a_search_messages(q.strip(), user["id"])
    return {"results": results, "query": q.strip()}


@router.post("/{conversation_id}/share")
async def share_conversation(conversation_id: str, user: dict = Depends(get_current_user)):
    conv = await a_get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv.get("user_id") and conv["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    share_id = uuid.uuid4().hex[:12]
    await a_set_share_id(conversation_id, share_id)
    return {"share_id": share_id, "share_url": f"/shared/{share_id}"}


@router.delete("/{conversation_id}/share")
async def unshare_conversation(conversation_id: str, user: dict = Depends(get_current_user)):
    conv = await a_get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv.get("user_id") and conv["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    await a_clear_share_id(conversation_id)
    return {"success": True}


class RenameRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


@router.put("/{conversation_id}/rename")
async def rename_conversation_endpoint(conversation_id: str, req: RenameRequest, user: dict = Depends(get_current_user)):
    conv = await a_get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv.get("user_id") and conv["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    await a_rename_conversation(conversation_id, req.title.strip(), user["id"])
    return {"success": True, "title": req.title.strip()}


@router.get("/conversations/list")
async def list_conversations(user: dict = Depends(get_current_user)):
    convs = await a_list_user_conversations(user["id"])
    return {"conversations": convs}


@router.delete("/{conversation_id}")
async def delete_conversation_endpoint(conversation_id: str, user: dict = Depends(get_current_user)):
    conv = await a_get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv.get("user_id") and conv["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    await a_delete_conversation(conversation_id)
    return {"success": True, "message": "Conversation deleted"}
