import json
import sqlite3
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "trace.db"

import contextlib


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


@contextlib.contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        try:
            conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
        except Exception:
            pass
        conn.close()


def close_all():
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=5)
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.close()
    except Exception:
        pass


def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            chunk_count INTEGER DEFAULT 0,
            uploaded_at TEXT NOT NULL,
            status TEXT DEFAULT 'processing',
            file_hash TEXT DEFAULT '',
            user_id TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            message_count INTEGER DEFAULT 0,
            user_id TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            sources TEXT,
            confidence TEXT,
            rating INTEGER,
            corrected_answer TEXT,
            created_at TEXT NOT NULL,
            user_id TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        );

        CREATE TABLE IF NOT EXISTS feedback_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            message_id INTEGER,
            rating INTEGER NOT NULL,
            previous_confidence REAL,
            created_at TEXT NOT NULL,
            user_id TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        );
    """)
    conn.commit()
    for col in ["user_id TEXT NOT NULL DEFAULT ''"]:
        for table in ["documents", "conversations", "messages", "feedback_log"]:
            try:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col}")
                conn.commit()
            except Exception:
                pass
    for col in ["title TEXT DEFAULT ''"]:
        try:
            conn.execute(f"ALTER TABLE conversations ADD COLUMN {col}")
            conn.commit()
        except Exception:
            pass
    conn.execute("CREATE INDEX IF NOT EXISTS idx_docs_hash ON documents(file_hash)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_docs_status ON documents(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_docs_user ON documents(user_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
    conn.close()


def create_user(user_id: str, username: str, hashed_password: str, is_admin: bool = False):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO users (id, username, hashed_password, is_admin, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, username, hashed_password, 1 if is_admin else 0, datetime.now(timezone.utc).isoformat()),
        )


def get_user_by_username(username: str) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    return dict(row) if row else None


def get_user_by_id(user_id: str) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def upsert_document(doc_id: str, name: str, doc_type: str, size_bytes: int,
                     chunk_count: int = 0, status: str = "ready", file_hash: str = "",
                     user_id: str = ""):
    with get_db() as conn:
        conn.execute("""
            INSERT INTO documents (id, name, type, size_bytes, chunk_count, uploaded_at, status, file_hash, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name, type=excluded.type, size_bytes=excluded.size_bytes,
                chunk_count=excluded.chunk_count, status=excluded.status, file_hash=excluded.file_hash
        """, (doc_id, name, doc_type, size_bytes, chunk_count, datetime.now(timezone.utc).isoformat(), status, file_hash, user_id))


def get_document(doc_id: str) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    return dict(row) if row else None


def get_document_by_hash(file_hash: str, user_id: str = "") -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM documents WHERE file_hash = ? AND user_id = ? AND status IN ('ready', 'processing') LIMIT 1",
            (file_hash, user_id),
        ).fetchone()
    return dict(row) if row else None


def list_documents(user_id: str = "") -> list[dict]:
    with get_db() as conn:
        if user_id:
            rows = conn.execute("SELECT * FROM documents WHERE user_id = ? ORDER BY uploaded_at DESC", (user_id,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM documents ORDER BY uploaded_at DESC").fetchall()
    return [dict(r) for r in rows]


def delete_document(doc_id: str):
    with get_db() as conn:
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))


def create_conversation(conv_id: str, user_id: str = "", title: str = "") -> dict:
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        conn.execute("INSERT INTO conversations (id, created_at, updated_at, user_id, title) VALUES (?, ?, ?, ?, ?)",
                     (conv_id, now, now, user_id, title))
    return {"id": conv_id, "created_at": now, "updated_at": now, "message_count": 0, "user_id": user_id, "title": title}


def update_conversation_title(conv_id: str, title: str):
    with get_db() as conn:
        conn.execute("UPDATE conversations SET title = ? WHERE id = ?", (title, conv_id))


def get_conversation(conv_id: str) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,)).fetchone()
    return dict(row) if row else None


def get_conversation_messages(conv_id: str, limit: int = None) -> list[dict]:
    if limit is None:
        from app.config import settings as _settings
        limit = _settings.MAX_CONVERSATION_HISTORY
    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
            LIMIT ?
        """, (conv_id, limit)).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        if d.get("sources"):
            try:
                d["sources"] = json.loads(d["sources"])
            except (json.JSONDecodeError, TypeError):
                d["sources"] = []
        if d.get("confidence"):
            try:
                d["confidence"] = json.loads(d["confidence"])
            except (json.JSONDecodeError, TypeError):
                d["confidence"] = None
        result.append(d)
    return result


def add_message(conv_id: str, role: str, content: str,
                sources: str = None, confidence: str = None,
                rating: int = None, corrected_answer: str = None,
                user_id: str = "") -> int:
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        cur = conn.execute("""
            INSERT INTO messages (conversation_id, role, content, sources, confidence, rating, corrected_answer, created_at, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (conv_id, role, content, sources, confidence, rating, corrected_answer, now, user_id))
        conn.execute("UPDATE conversations SET updated_at = ?, message_count = message_count + 1 WHERE id = ?",
                     (now, conv_id))
        message_id = cur.lastrowid
    return message_id


def update_message_feedback(message_id: int, rating: int, corrected_answer: str = None):
    with get_db() as conn:
        if corrected_answer:
            conn.execute("UPDATE messages SET rating = ?, corrected_answer = ? WHERE id = ?",
                         (rating, corrected_answer, message_id))
        else:
            conn.execute("UPDATE messages SET rating = ? WHERE id = ?", (rating, message_id))


def log_feedback(conversation_id: str, message_id: int, rating: int, previous_confidence: float = None,
                 user_id: str = ""):
    with get_db() as conn:
        conn.execute("""
            INSERT INTO feedback_log (conversation_id, message_id, rating, previous_confidence, created_at, user_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (conversation_id, message_id, rating, previous_confidence, datetime.now(timezone.utc).isoformat(), user_id))


_async_lock = asyncio.Lock()


async def a_create_user(*a, **kw):
    async with _async_lock:
        return await asyncio.to_thread(create_user, *a, **kw)


async def a_get_user_by_username(*a, **kw):
    return await asyncio.to_thread(get_user_by_username, *a, **kw)


async def a_get_user_by_id(*a, **kw):
    return await asyncio.to_thread(get_user_by_id, *a, **kw)


async def a_upsert_document(*a, **kw):
    async with _async_lock:
        return await asyncio.to_thread(upsert_document, *a, **kw)


async def a_get_document(*a, **kw):
    return await asyncio.to_thread(get_document, *a, **kw)


async def a_get_document_by_hash(*a, **kw):
    return await asyncio.to_thread(get_document_by_hash, *a, **kw)


async def a_list_documents(*a, **kw):
    return await asyncio.to_thread(list_documents, *a, **kw)


async def a_delete_document(*a, **kw):
    async with _async_lock:
        return await asyncio.to_thread(delete_document, *a, **kw)


async def a_create_conversation(*a, **kw):
    async with _async_lock:
        return await asyncio.to_thread(create_conversation, *a, **kw)


async def a_update_conversation_title(*a, **kw):
    async with _async_lock:
        return await asyncio.to_thread(update_conversation_title, *a, **kw)


async def a_get_conversation(*a, **kw):
    return await asyncio.to_thread(get_conversation, *a, **kw)


async def a_get_conversation_messages(*a, **kw):
    return await asyncio.to_thread(get_conversation_messages, *a, **kw)


async def a_add_message(*a, **kw):
    async with _async_lock:
        return await asyncio.to_thread(add_message, *a, **kw)


async def a_update_message_feedback(*a, **kw):
    async with _async_lock:
        return await asyncio.to_thread(update_message_feedback, *a, **kw)


async def a_log_feedback(*a, **kw):
    async with _async_lock:
        return await asyncio.to_thread(log_feedback, *a, **kw)


def list_user_conversations(user_id: str) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("""
            SELECT c.id, c.created_at, c.updated_at, c.message_count, c.title,
                   (SELECT content FROM messages WHERE conversation_id = c.id AND role = 'user' ORDER BY id ASC LIMIT 1) as first_message
            FROM conversations c WHERE c.user_id = ?
            ORDER BY c.updated_at DESC LIMIT 50
        """, (user_id,)).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        if not d.get("title") and d.get("first_message"):
            d["title"] = d["first_message"][:80] + ("..." if len(d["first_message"]) > 80 else "")
        elif not d.get("title"):
            d["title"] = "New conversation"
        d.pop("first_message", None)
        result.append(d)
    return result


def delete_conversation(conv_id: str):
    with get_db() as conn:
        conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
        conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))


def get_admin_stats() -> dict:
    with get_db() as conn:
        user_count = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
        doc_count = conn.execute("SELECT COUNT(*) as c FROM documents WHERE status='ready'").fetchone()["c"]
        conv_count = conn.execute("SELECT COUNT(*) as c FROM conversations").fetchone()["c"]
        msg_count = conn.execute("SELECT COUNT(*) as c FROM messages").fetchone()["c"]
        fb_count = conn.execute("SELECT COUNT(*) as c FROM feedback_log").fetchone()["c"]
        total_tokens = conn.execute("SELECT COALESCE(SUM(LENGTH(content)), 0) as c FROM messages WHERE role='assistant'").fetchone()["c"]
    return {
        "users": user_count,
        "documents": doc_count,
        "conversations": conv_count,
        "messages": msg_count,
        "feedback_entries": fb_count,
        "total_output_chars": total_tokens,
    }


async def a_list_user_conversations(*a, **kw):
    return await asyncio.to_thread(list_user_conversations, *a, **kw)


async def a_delete_conversation(*a, **kw):
    async with _async_lock:
        return await asyncio.to_thread(delete_conversation, *a, **kw)


async def a_get_admin_stats(*a, **kw):
    return await asyncio.to_thread(get_admin_stats, *a, **kw)
