# Trace — Transparent Support AI

> **FlowZint AI Hackathon 2026 · Support Chat Bot**

[![Python](https://img.shields.io/badge/Python-3.11-3b82f6?style=flat-square)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61dafb?style=flat-square)](https://react.dev)

**Trace** is a transparent support AI assistant that doesn't just answer questions — it **shows its work**. Every response includes cited sources, relevance scores, and a confidence gauge, so users and support teams can trust (and verify) every answer.

---

## Problem Statement

Support chatbots today are black boxes. Users get an answer but have no idea if it's correct, where it came from, or how confident the system is. Support teams can't audit or improve responses. **Trace solves this** by making every answer fully transparent.

---

## Key Features

### 🔐 Authenticated Multi-User
JWT-based authentication with user-scoped documents, conversations, and feedback. Each user sees only their own data.

### 🎯 Transparent RAG Pipeline
Multi-stage retrieval augmented generation that cites every source with page numbers, relevance scores, and content previews.

### 📊 Confidence Scoring
Multi-factor confidence gauge (high/medium/low) based on best-match score, source consensus, and source quality — so users know how much to trust each answer.

### 📁 Multi-Format Ingestion
Upload PDF, DOCX, TXT, Markdown, JSON, CSV, and HTML files. Trace extracts, chunks, and indexes them automatically.

### 🔄 Hybrid Search
Combines dense vector embeddings (Gemini embedding API) with sparse keyword search (TF-IDF) for maximum retrieval quality.

### 💬 Conversational Memory
Maintains conversation context across multiple turns. Ask follow-up questions naturally.

### 👍 Feedback Loop
Rate responses thumbs up/down. Feedback is logged for future model improvement and weight tuning.

### 🛡️ Safety Built-In
PII redaction (phone, email, Aadhaar, PAN, credit cards) and content moderation to filter toxic input.

---

## Architecture

```
User → Login → JWT Token → React Frontend → FastAPI Backend → Hybrid Retriever → ChromaDB
                                 ↓                    ↓
                              TF-IDF Reranker
                                 ↓
                           Confidence Scorer → LLM (Gemini/Groq)
                                 ↓
                     Response + Sources + Confidence → User
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for full system design.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS, Framer Motion |
| Backend | FastAPI, Uvicorn, SQLite (async via aiosqlite) |
| Embeddings | Gemini embedding-001 API (3072-dim) |
| Vector Store | ChromaDB (local persistent) |
| LLM | Google Gemini 2.0 Flash / Groq Llama 3.3 (auto fallback) |
| Retrieval | Hybrid dense + sparse (TF-IDF) |
| Reranking | TF-IDF cosine similarity |
| Auth | JWT (python-jose) + bcrypt |
| Container | Docker + docker-compose |

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (optional)

### Local Development

```bash
# 1. Backend
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
source venv/bin/activate
pip install -r requirements.txt
# Create .env with your API keys (see .env.example):
# GEMINI_API_KEY=your_key_here
# GROQ_API_KEY=your_key_here
uvicorn app.main:app --reload

# 2. Frontend (in another terminal)
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000` — login with the admin credentials, then upload documents and chat.

### Docker

```bash
docker-compose up --build
```

Visit `http://localhost:8080`.

---

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|---|
| `GET` | `/api/health` | No | System health check |
| `POST` | `/api/auth/register` | No | Create new account |
| `POST` | `/api/auth/login` | No | Get JWT token |
| `POST` | `/api/auth/change-password` | Yes | Change account password |
| `GET` | `/api/auth/me` | Yes | Current user info |
| `POST` | `/api/chat` | Yes | Send a message (non-streaming) |
| `POST` | `/api/chat/stream` | Yes | Send a message with SSE streaming |
| `GET` | `/api/chat/{id}` | Yes | Get conversation history |
| `GET` | `/api/chat/search?q=` | Yes | Search message content |
| `PUT` | `/api/chat/{id}/rename` | Yes | Rename a conversation |
| `POST` | `/api/chat/{id}/share` | Yes | Create shareable link |
| `DELETE` | `/api/chat/{id}/share` | Yes | Remove shareable link |
| `DELETE` | `/api/chat/{id}` | Yes | Delete a conversation |
| `GET` | `/api/documents` | Yes | List all indexed documents |
| `POST` | `/api/documents/upload` | Yes | Upload a document |
| `DELETE` | `/api/documents/{id}` | Yes | Delete a document |
| `POST` | `/api/feedback` | Yes | Submit feedback on a response |
| `GET` | `/api/admin/stats` | Admin | System usage statistics |
| `GET` | `/api/admin/feedback-stats` | Admin | Feedback satisfaction data |
| `GET` | `/api/shared/{share_id}` | No | View shared conversation |

All authenticated endpoints require: `Authorization: Bearer <token>`

See [docs/API.md](docs/API.md) for full API reference.

---

## Project Structure

```
trace/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI route handlers (chat, documents, feedback, auth)
│   │   ├── core/          # AI pipeline (RAG, embeddings, confidence, auth)
│   │   ├── models/        # Pydantic schemas, DB models
│   │   ├── utils/         # PII redaction, content moderation
│   │   └── main.py        # FastAPI app entry
│   ├── tests/             # Pytest tests
│   ├── .env.example       # Environment variable template
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/    # React components (Chat, Knowledge, Login)
│   │   ├── hooks/         # Custom React hooks
│   │   ├── utils/         # API client with auth headers
│   │   ├── App.jsx        # Root component with auth flow
│   │   └── main.jsx       # Entry point
│   ├── package.json
│   └── vite.config.js
├── docs/                  # Architecture, API, edge cases docs
├── sample_data/           # Example documents to test with
├── docker-compose.yml
└── README.md
```

---

## Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

31 of 32 tests should pass (1 pre-existing test isolation issue with async lifespan).

---

## Evaluation Criteria Alignment

| Criterion | Weight | How Trace Excels |
|---|---|---|
| **Model Innovation** | 30% | Custom hybrid retrieval + multi-factor confidence scoring + transparent citation pipeline. Not a generic LLM wrapper — built retrieval, reranking, and confidence systems from scratch on open-source components. |
| **Real-World Applicability** | 25% | Every SaaS company needs better support. Reduces ticket volume, improves CSAT, gives support teams auditability. JWT auth enables multi-user deployment. |
| **Technical Architecture** | 25% | Clean layered architecture, async FastAPI, hybrid fallbacks at every layer, comprehensive error handling, PII redaction, content moderation, non-blocking DB. |
| **Documentation Clarity** | 20% | This README + full architecture docs + API reference + edge cases guide + demo video. |

---

## Hackathon Context

- **Event:** FlowZint AI Hackathon 2026
- **Category:** Support Chat Bot
- **Track:** AI-powered transparent support
- **Submission:** https://flowzint.in/2026/ai/hackothon/

---

## License

MIT
