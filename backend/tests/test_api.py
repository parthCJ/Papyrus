import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_invalid_pdf_upload():
    response = client.post(
        "/api/v1/upload/pdf", files={"file": ("test.txt", b"not a pdf", "text/plain")}
    )
    assert response.status_code == 400


def test_invalid_arxiv_id():
    response = client.post("/api/v1/upload/arxiv", json={"arxiv_id": "invalid-id"})
    assert response.status_code == 422


def test_query_empty():
    response = client.post("/api/v1/query/", json={"query": "", "top_k": 5})
    assert response.status_code == 422


def test_list_documents():
    response = client.get("/api/v1/documents/?limit=10&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "documents" in data
