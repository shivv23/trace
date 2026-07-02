from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SourceChunk(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    content: str
    relevance_score: float
    page_number: Optional[int] = None
    chunk_index: int
    file_type: Optional[str] = None


class ConfidenceScore(BaseModel):
    overall: float
    relevance_score: float
    semantic_similarity: float
    source_quality: float
    support_count: int
    label: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: Optional[str] = None
    document_ids: Optional[list[str]] = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    confidence: ConfidenceScore
    conversation_id: str
    processing_time_ms: float
    language: str = "en"
    web_search_used: bool = False


class FeedbackRequest(BaseModel):
    conversation_id: str
    message_index: int
    rating: int = Field(..., ge=0, le=1)
    corrected_answer: Optional[str] = None


class DocumentInfo(BaseModel):
    id: str
    name: str
    type: str
    size_bytes: int
    chunk_count: int
    uploaded_at: str
    status: str


class UploadResponse(BaseModel):
    id: str
    name: str
    type: str
    chunk_count: int
    status: str
    message: str


class DeleteResponse(BaseModel):
    success: bool
    message: str


class HealthResponse(BaseModel):
    status: str
    version: str
    documents_indexed: int
    llm_provider: str
    gemini_configured: bool = False
    gemini_model: str = ""
    embedding_model: str
    auth_enabled: bool = True
