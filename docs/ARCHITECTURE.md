# Architecture

## System Overview

Trace follows a clean layered architecture with clear separation of concerns:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React + Vite)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │ Chat Widget  │  │ Knowledge    │  │ Login        │  │ Welcome    │  │
│  │ (MessageBub- │  │ Panel        │  │ Screen       │  │ Screen     │  │
│  │ ble, Source- │  │ (FileUpload, │  │ (Auth)       │  │            │  │
│  │ Card, Confi- │  │ DocumentList)│  │              │  │            │  │
│  │ denceGauge)  │  │              │  │              │  │            │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬─────┘  │
│         └─────────────────┴──────────────────┴─────────────────┘        │
│                           │ REST + JWT Bearer Token                      │
├───────────────────────────┼──────────────────────────────────────────────┤
│                    FASTAPI BACKEND                                       │
│  ┌────────────────────────┼───────────────────────────────────────────┐  │
│  │                    AUTH MIDDLEWARE                                   │  │
│  │  ┌──────────────┐ ┌───────────────────┐ ┌──────────────────────┐   │  │
│  │  │ JWT Validation│ │ Password Hashing  │ │ get_current_user    │   │  │
│  │  │ (python-jose) │ │ (bcrypt)          │ │ FastAPI dependency   │   │  │
│  │  └──────────────┘ └───────────────────┘ └──────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌────────────────────────┼───────────────────────────────────────────┐  │
│  │                    API LAYER                                          │  │
│  │  ┌──────────┐ ┌────────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐  │  │
│  │  │ /api/auth│ │ /api/chat  │ │ /api/docu-│ │ /api/    │ │ /api/  │  │  │
│  │  │ (login,  │ │            │ │ ments     │ │ feedback │ │ health │  │  │
│  │  │ register)│ │            │ │           │ │          │ │        │  │  │
│  │  └────┬─────┘ └────┬───────┘ └─────┬─────┘ └────┬─────┘ └────────┘  │  │
│  └───────┼────────────┼───────────────┼────────────┼──────────────────────┘  │
│          │            │               │            │                        │
│  ┌───────┴────────────┴───────────────┴────────────┴──────────────────────┐  │
│  │                    ORCHESTRATION LAYER                                  │  │
│  │  ┌───────────────────────────────────────────────────────────────────┐  │  │
│  │  │  Chat Flow:                                                       │  │  │
│  │  │  0. Authenticate (JWT token validation)                          │  │  │
│  │  │  1. Moderate input (toxicity check)                              │  │  │
│  │  │  2. Manage conversation (create/retrieve)                        │  │  │
│  │  │  3. Retrieve relevant chunks (hybrid search)                     │  │  │
│  │  │  4. Rerank results (cross-encoder / TF-IDF)                      │  │  │
│  │  │  5. Compute confidence score                                     │  │  │
│  │  │  6. Generate answer (LLM / fallback)                             │  │  │
│  │  │  7. Redact PII                                                    │  │  │
│  │  │  8. Store in conversation history                                │  │  │
│  │  │  9. Return response + sources + confidence                       │  │  │
│  │  └───────────────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                   │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                    CORE AI LAYER                                          │  │
│  │                                                                           │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────────────┐   │  │
│  │  │Ingestion │  │Chunking  │  │Embeddings│  │Hybrid                 │   │  │
│  │  │(PDF/DOCX │  │(Recursive│  │(sentence-│  │Retrieval              │   │  │
│  │  │/HTML/...)│  │/Semantic)│  │transform)│  │(Dense+Sparse)         │   │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┬────────────┘   │  │
│  │                                                        │               │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┴────────────┐  │  │
│  │  │Reranker  │  │Confidence│  │Generation│  │Content                │  │  │
│  │  │(Cross-   │  │Scorer    │  │(Gemini / │  │Moderation             │  │  │
│  │  │encoder)  │  │(Multi-   │  │Groq /    │  │& PII                  │  │  │
│  │  │          │  │factor)   │  │Fallback) │  │Redaction              │  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └───────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                   │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                    DATA LAYER                                             │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────────────┐  │  │
│  │  │ SQLite       │  │ ChromaDB     │  │ File System                   │  │  │
│  │  │ (Users,      │  │ (Vector      │  │ (Uploaded Documents)          │  │  │
│  │  │ Conversations│  │  Store)      │  │                               │  │  │
│  │  │ Documents,   │  │              │  │                               │  │  │
│  │  │ Feedback)    │  │              │  │                               │  │  │
│  │  └──────────────┘  └──────────────┘  └───────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Request Flow (Chat)

```
POST /api/chat
  │
  ├─ 0. Authenticate ──────────────────────────── core/auth.py
  │     ├─ Extract Bearer token
  │     ├─ Validate JWT (exp, signature)
  │     └─ Load user from DB
  │
  ├─ 1. Rate limit check ───────────────────────── api/chat.py
  │     └─ IP-based token bucket (30 req/min)
  │
  ├─ 2. Moderate input ─────────────────────────── utils/moderation.py
  │     └─ Toxic? → 400 Blocked
  │
  ├─ 3. Get/Create conversation ────────────────── models/db.py
  │
  ├─ 4. Hybrid Retrieval ───────────────────────── core/retrieval.py
  │     ├─ Dense: query → embed → chroma search
  │     └─ Sparse: query → TF-IDF → cosine similarity
  │     └─ Combine scores (60/40 weighted)
  │
  ├─ 5. Rerank ─────────────────────────────────── core/reranking.py
  │     ├─ Try cross-encoder (transformers)
  │     └─ Fallback to TF-IDF reranking
  │
  ├─ 6. Confidence Scoring ─────────────────────── core/confidence.py
  │     ├─ Relevance score (rerank scores)
  │     ├─ Semantic similarity
  │     ├─ Source quality (diversity + consistency)
  │     └─ Support ratio
  │
  ├─ 7. Generate Answer ────────────────────────── core/generation.py
  │     ├─ Build prompt with context + history
  │     ├─ Try Gemini 2.0 Flash
  │     ├─ Fallback to Groq Llama 3.3
  │     └─ Final fallback: extractive answer
  │
  ├─ 8. Redact PII ─────────────────────────────── utils/pii.py
  │
  └─ 9. Return response ────────────────────────── schemas.py
        ├─ answer (markdown string)
        ├─ sources (top 5 chunks with scores)
        ├─ confidence (multi-factor score)
        └─ conversation_id
```

## Fallback Strategy

Every critical system has a fallback:

| Component | Primary | Fallback 1 | Fallback 2 |
|---|---|---|---|
| Auth | JWT (python-jose) | n/a | n/a |
| Retrieval | Dense (Chroma) | Sparse (TF-IDF) | N/A (combined) |
| Reranking | Cross-encoder | TF-IDF similarity | Original order |
| LLM | Gemini 2.0 Flash | Groq Llama 3.3 | Extractive (chunk preview) |
| Vector DB | Persistent Chroma | Ephemeral Chroma | N/A |
| Frontend | React + Vite | Static HTML (served by FastAPI) | N/A |

## Key Design Decisions

1. **SQLite over PostgreSQL**: Zero-config, file-based, perfect for hackathon scale. Async wrappers via `asyncio.to_thread()` prevent event loop blocking.

2. **ChromaDB over Pinecone/Weaviate**: Free, local, persistent, no API keys needed. Data stays on your machine.

3. **sentence-transformers over OpenAI embeddings**: Free, local, no API costs. All-MiniLM-L6-v2 is 80MB and runs on CPU.

4. **Gemini 2.0 Flash as primary LLM**: 1.5M context window, 60 requests/minute free tier, no credit card required.

5. **Custom hybrid retrieval over pure vector search**: Combines semantic understanding (dense) with keyword precision (sparse) for better support query matching.

6. **JWT auth over session-based**: Stateless, no server-side session storage, works with API clients. Token stored in localStorage for simplicity (httpOnly cookies recommended for production).

7. **bcrypt over passlib**: Direct bcrypt usage avoids compatibility issues with newer bcrypt library versions. Industry-standard password hashing.
