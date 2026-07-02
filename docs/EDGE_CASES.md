# Edge Cases & Failure Modes

This document describes how Trace handles every known edge case and failure mode.

---

## Retrieval Failures

### No results found

**Scenario**: Query has no semantic or keyword overlap with any indexed chunk.

**Handling**: Returns empty results list → confidence score is 0.0 (low) → answer is "I couldn't find any relevant information in the knowledge base to answer your question."

### Single chunk retrieved

**Scenario**: Only one chunk barely matches.

**Handling**: Confidence score penalized (support_ratio = 1/5 = 0.2). If score < 0.45, label is "low" and answer includes "I found limited information" caveat.

### TF-IDF cache miss

**Scenario**: First query after upload (TF-IDF cache invalidated on every upload).

**Handling**: Cache rebuilt lazily on next query — loads all documents from ChromaDB, fits TF-IDF vectorizer, transforms query. Adds ~200ms to first query after upload.

### ChromaDB search timeout

**Scenario**: Vector search hangs or takes too long.

**Handling**: No explicit timeout on ChromaDB queries — FastAPI's timeout is the only boundary. Future: add `asyncio.wait_for` wrapper.

---

## LLM Failures

### Both API keys missing

**Scenario**: Neither GEMINI_API_KEY nor GROQ_API_KEY is set.

**Handling**: `generate_answer` checks `api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")`. If both are None/empty, skips LLM and returns extractive answer (best matching chunk text with "I found this in the knowledge base:" prefix).

### Gemini API returns error

**Scenario**: Quota exceeded, network error, or model overloaded.

**Handling**: Try Gemini → on any exception → try Groq → on any exception → fallback to extractive answer. Each fallback is logged.

### Groq API returns error

**Scenario**: Rate limited or service down.

**Handling**: Falls through to extractive answer. User sees a knowledge-base-sourced response without AI rewrite.

### LLM returns empty string

**Scenario**: Model returns `""` or whitespace-only response.

**Handling**: `generate_answer` checks `if len(answer.strip()) < 10` and falls back to extractive answer.

### LLM context overflow

**Scenario**: Retrieved chunks + conversation history exceed model's context window.

**Handling**: Conversation history is limited to last 6 exchanges. Chunk content is truncated to 500 chars per source in the prompt. No explicit token counting — relies on the LLM API's own truncation (Gemini silently truncates, Groq returns error).

---

## Upload Failures

### Invalid file type

**Scenario**: User uploads `.exe`, `.sh`, `.zip`, or other unsupported type.

**Handling**: Checked by `Path(file.filename).suffix.lower() in settings.ALLOWED_EXTENSIONS`. Returns 400.

### Duplicate file (same content, different name)

**Scenario**: User re-uploads the same file with a different filename.

**Handling**: SHA-256 hash computed during `process_upload`. Checked via `get_document_by_hash()` before indexing. Returns 409 Conflict with original filename and date.

### File too large

**Scenario**: Upload exceeds 20 MB limit.

**Handling**: Checked in `process_upload` — `file_size > MAX_UPLOAD_SIZE_MB * 1024 * 1024`. Returns 400.

### Upload interrupted mid-stream

**Scenario**: Network drops during multipart upload.

**Handling**: Starlette/FastAPI handles the multipart stream. If the connection drops, the handler raises — the `except` clause cleans up: deletes file from disk, removes ChromaDB vectors (if any were added), sets document status to `error`.

### Corrupted file

**Scenario**: PDF is password-protected, DOCX is damaged.

**Handling**: Parser (PyPDF2, python-docx) raises exception → caught by `except Exception` → status set to `error`, file deleted, 500 returned.

### Double extension bypass

**Scenario**: File named `script.txt.exe`.

**Handling**: Uses `Path(file.filename).suffix.lower()` which returns only the last extension (`.exe`). Allowed extensions list rejects it.

---

## PII Redaction

### Phone numbers

**Scenario**: User message contains "Contact me at 555-123-4567".

**Handling**: Pattern `\b\d{3}[-.]?\d{3}[-.]?\d{4}\b` matches → replaced with `[PHONE REDACTED]`.

### Email addresses

**Scenario**: "Email support@example.com for help."

**Handling**: Pattern `\b[\w.+-]+@[\w-]+\.[\w.]+` matches → replaced with `[EMAIL REDACTED]`.

### Aadhaar numbers (India)

**Scenario**: "My Aadhaar is 1234 5678 9012".

**Handling**: Context-aware pattern — only redacts 12-digit numbers near keywords like "aadhaar" or "आधार". Prevents false positives on things like order numbers.

### Credit card numbers

**Scenario**: "Card: 4111-1111-1111-1111".

**Handling**: Pattern matches spaced, dashed, or compact 16-digit sequences starting with common IIN ranges. Replaced with `[CREDIT CARD REDACTED]`.

### API keys

**Scenario**: "The API key is sk-1234...".

**Handling**: Pattern `api[._-]?key` match triggers redaction of the surrounding value.

---

## Authentication & Authorization

### Missing token

**Scenario**: Request without `Authorization: Bearer <token>` header.

**Handling**: FastAPI HTTPBearer returns 401 Unauthorized. Frontend redirects to login screen.

### Expired token

**Scenario**: Token is valid but past `exp` claim (24h default).

**Handling**: python-jose raises `JWTError` → 401 Unauthorized. Frontend catches this in `handleAuthError`, clears stored token, and reloads to show login screen.

### Invalid token

**Scenario**: Token is tampered with, wrong algorithm, or random string.

**Handling**: JWT decode fails → 401 Unauthorized.

### Wrong username/password

**Scenario**: Login with invalid credentials.

**Handling**: bcrypt `checkpw` fails → 401 "Invalid username or password". Note: no timing difference between "user doesn't exist" and "wrong password" (bcrypt runs on both paths).

### Duplicate registration

**Scenario**: Register with a username that already exists.

**Handling**: UNIQUE constraint on `users.username` → 409 Conflict.

### Rate limiting

**Scenario**: More than 30 chat requests per minute from same IP.

**Handling**: IP-based token bucket with `asyncio.Lock` — returns 429 "Rate limit exceeded". Stale IPs evicted after 120s of inactivity.

### Cross-user access

**Scenario**: User A tries to read User B's conversation by guessing its UUID.

**Handling**: `get_history` checks `conv["user_id"]` matches the authenticated user. Returns 403 Forbidden on mismatch. Documents are similarly scoped — each user sees only their own documents.

---

## Content Moderation

### Toxic message

**Scenario**: User sends profanity or hate speech.

**Handling**: Regex-based pattern matching with DOTALL flag. Returns 400 with reason.

### Spam detection

**Scenario**: User repeatedly sends the same message.

**Handling**: Pattern match counts repeated substrings. Length penalty applied only after a pattern matches (avoids false positives on long legitimate messages).

### Non-toxic message with long text

**Scenario**: Legitimate 3000-character question.

**Handling**: Length penalty only activates if a pattern matched first. Clean messages pass through regardless of length.

---

## System Failures

### ChromaDB corruption

**Scenario**: Database files corrupted or locked.

**Handling**: `_init_chroma` wraps initialization in try/except — falls back to in-memory ChromaClient. Data lost on restart but system stays online.

### Disk full

**Scenario**: Upload directory fills up.

**Handling**: No explicit handler. OS will fail writes. Future: check available disk space before upload.

### SQLite WAL corruption

**Scenario**: Power loss during write.

**Handling**: SQLite WAL mode handles crash recovery. `PRAGMA wal_checkpoint` runs on shutdown and after each DB context manager exits.

### Graceful shutdown

**Scenario**: Server is stopped (SIGTERM).

**Handling**: Lifespan shutdown handler runs `close_all()` which checkpoints the WAL and closes connections.

### Orphaned documents from crash

**Scenario**: Server crashes during upload — document is in "processing" state.

**Handling**: On next startup, `_cleanup_orphaned_docs` finds documents with status "processing" or "error", deletes their ChromaDB vectors and files, and removes the DB records.

---

## Future Work

### Multi-tenancy improvements

- Password reset flow
- Email verification
- Team/invite-based account creation
- Rate limiting per user (not per IP)

### Performance

- Connection pooling for SQLite
- Token-aware chunking instead of character-based
- Incremental TF-IDF updates (instead of full rebuild)
- Async ChromaDB client for non-blocking vector search
