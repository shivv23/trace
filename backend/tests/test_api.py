import sys
import uuid
sys.path.insert(0, 'backend')

from fastapi.testclient import TestClient

from app.models.db import init_db

init_db()

from app.main import app
from app.core.auth import get_current_user

app.dependency_overrides[get_current_user] = lambda: {"id": "test-user", "username": "test", "is_admin": 1}

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "documents_indexed" in data


def test_chat_empty_body():
    response = client.post("/api/chat", json={}, headers={"Authorization": "Bearer test"})
    assert response.status_code == 422


def test_chat_invalid_message():
    response = client.post("/api/chat", json={"message": ""}, headers={"Authorization": "Bearer test"})
    assert response.status_code == 422


def test_list_documents():
    response = client.get("/api/documents", headers={"Authorization": "Bearer test"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_upload_no_file():
    response = client.post("/api/documents/upload", headers={"Authorization": "Bearer test"})
    assert response.status_code == 422


def test_upload_invalid_type():
    response = client.post(
        "/api/documents/upload",
        files={"file": ("test.exe", b"fake content", "application/x-msdownload")},
        headers={"Authorization": "Bearer test"},
    )
    assert response.status_code == 400
    assert "not supported" in response.json()["detail"].lower()


def test_upload_and_delete_cycle():
    with TestClient(app) as c:
        content = b"Trace supports PDF, DOCX, TXT, MD, JSON, CSV, HTML files."
        response = c.post(
            "/api/documents/upload",
            files={"file": ("test_upload.txt", content, "text/plain")},
            headers={"Authorization": "Bearer test"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["chunk_count"] > 0
        assert data["type"] == ".txt"
        doc_id = data["id"]

        list_resp = c.get("/api/documents", headers={"Authorization": "Bearer test"})
        assert list_resp.status_code == 200
        ids = [d["id"] for d in list_resp.json()]
        assert doc_id in ids

        dup_resp = c.post(
            "/api/documents/upload",
            files={"file": ("test_dup.txt", content, "text/plain")},
            headers={"Authorization": "Bearer test"},
        )
        assert dup_resp.status_code == 409
        assert "duplicate" in dup_resp.json()["detail"].lower()

        del_resp = c.delete(f"/api/documents/{doc_id}", headers={"Authorization": "Bearer test"})
        assert del_resp.status_code == 200
        assert del_resp.json()["success"] is True

        list_resp2 = c.get("/api/documents", headers={"Authorization": "Bearer test"})
        ids2 = [d["id"] for d in list_resp2.json()]
        assert doc_id not in ids2


def test_delete_nonexistent():
    response = client.delete("/api/documents/nonexistent-id", headers={"Authorization": "Bearer test"})
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_auth_register_and_login():
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    response = client.post("/api/auth/register", json={"username": username, "password": "newpass123"})
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["username"] == username

    response = client.post("/api/auth/login", json={"username": username, "password": "newpass123"})
    assert response.status_code == 200
    data = response.json()
    assert "token" in data

    response = client.post("/api/auth/login", json={"username": username, "password": "wrongpass"})
    assert response.status_code == 401

    response = client.post("/api/auth/register", json={"username": username, "password": "anotherpass"})
    assert response.status_code == 409
