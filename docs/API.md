# API Reference

Base URL: `http://localhost:8000` (dev) or `https://your-deployment.railway.app` (production)

## Authentication

Most endpoints require a JWT token in the `Authorization` header:

```
Authorization: Bearer <token>
```

Get a token by logging in:

```
POST /api/auth/login
Content-Type: application/json

{"username": "admin", "password": "admin123"}
```

Returns:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user_id": "uuid",
  "username": "admin",
  "is_admin": true
}
```

### Auth Endpoints

#### Register

```
POST /api/auth/register
```

**Request:**
```json
{
  "username": "newuser",
  "password": "securepass123"
}
```

**Response:** Same as login — returns token directly.

#### Login

```
POST /api/auth/login
```

**Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

#### Get Current User

```
GET /api/auth/me
Authorization: Bearer <token>
```

**Response:**
```json
{
  "user_id": "uuid",
  "username": "admin",
  "is_admin": true
}
```

---

## Health Check

```
GET /api/health
```

Returns system status and configuration (no auth required).

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "documents_indexed": 3,
  "llm_provider": "groq",
  "gemini_configured": true,
  "gemini_model": "gemini-2.0-flash",
  "embedding_model": "all-MiniLM-L6-v2",
  "auth_enabled": true
}
```

---

## Chat

All chat endpoints require `Authorization: Bearer <token>`.

### Send Message

```
POST /api/chat
```

**Request Body:**
```json
{
  "message": "What features does your product have?",
  "conversation_id": null,
  "document_ids": null
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `message` | string | Yes | The user's question (1-4000 chars) |
| `conversation_id` | string | No | Continue existing conversation |
| `document_ids` | array[string] | No | Filter search to specific documents |

**Response:**
```json
{
  "answer": "Based on the documentation, the key features include:\n\n1. **Dashboard Analytics** — Real-time business metrics [Source 1]\n2. **Automated Workflows** — Trigger-based process automation [Source 2]\n3. **API Integration** — REST and webhook support [Source 1]",
  "sources": [
    {
      "chunk_id": "abc123_0",
      "document_id": "abc123",
      "document_name": "product_docs.pdf",
      "content": "Dashboard Analytics provides real-time visualization...",
      "relevance_score": 0.89,
      "page_number": null,
      "chunk_index": 0
    }
  ],
  "confidence": {
    "overall": 0.823,
    "relevance_score": 0.85,
    "semantic_similarity": 0.78,
    "source_quality": 0.72,
    "support_count": 3,
    "label": "high"
  },
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "processing_time_ms": 1243.5
}
```

### Get Conversation History

```
GET /api/chat/{conversation_id}
```

**Response:**
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "What features do you have?",
      "created_at": "2026-06-25T12:00:00"
    },
    {
      "id": 2,
      "role": "assistant",
      "content": "Based on the documentation...",
      "sources": [...],
      "confidence": {...},
      "created_at": "2026-06-25T12:00:01"
    }
  ]
}
```

---

## Documents

All document endpoints require `Authorization: Bearer <token>`. Documents are scoped per user.

### List Documents

```
GET /api/documents
```

### Upload Document

```
POST /api/documents/upload
```

**Request:** `multipart/form-data` with field `file`

Supported types: `.pdf`, `.docx`, `.txt`, `.md`, `.json`, `.csv`, `.html`, `.htm`

Max size: 20 MB

**Response:**
```json
{
  "id": "abc123",
  "name": "product_docs.pdf",
  "type": ".pdf",
  "chunk_count": 47,
  "status": "ready",
  "message": "Successfully processed product_docs.pdf into 47 chunks"
}
```

### Get Document

```
GET /api/documents/{doc_id}
```

### Delete Document

```
DELETE /api/documents/{doc_id}
```

---

## Feedback

Requires `Authorization: Bearer <token>`.

### Submit Feedback

```
POST /api/feedback
```

**Request Body:**
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "message_index": 0,
  "rating": 1,
  "corrected_answer": null
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `conversation_id` | string | Yes | Target conversation |
| `message_index` | integer | Yes | Which assistant message (0-based) |
| `rating` | integer | Yes | 1 (thumbs up) or 0 (thumbs down) |
| `corrected_answer` | string | No | User's correction for wrong answers |

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error description"
}
```

Common HTTP status codes:
- `400` — Bad request (toxic content, invalid file type, missing fields)
- `401` — Unauthorized (missing or invalid auth token)
- `403` — Forbidden (access denied)
- `404` — Resource not found
- `409` — Conflict (duplicate file, duplicate username)
- `413` — File too large (exceeds 20 MB)
- `422` — Validation error (schema mismatch)
- `429` — Rate limit exceeded
- `500` — Internal server error
- `503` — Service unavailable (engine not initialized)
