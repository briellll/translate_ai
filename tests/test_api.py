import os
import tempfile
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_upload_invalid_extension():
    resp = client.post("/upload", files={"file": ("test.txt", b"hello", "text/plain")})
    assert resp.status_code == 400
    assert "não suportado" in resp.json()["detail"].lower()


def test_upload_valid_pdf():
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("backend.routes.upload.UPLOAD_DIR", tmpdir):
            content = b"%PDF-1.4 fake pdf content for testing upload\n" * 10
            resp = client.post("/upload", files={"file": ("doc.pdf", content, "application/pdf")})
            assert resp.status_code == 200
            data = resp.json()
            assert "file_id" in data
            assert data["filename"] == "doc.pdf"
            assert data["size_kb"] > 0.1

            file_id = data["file_id"]
            expected_path = os.path.join(tmpdir, f"{file_id}.pdf")
            assert os.path.exists(expected_path)


def test_translate_missing_file():
    resp = client.post("/translate", json={
        "file_id": "nonexistent",
        "api_key": "sk-test123",
        "out_format": "txt",
    })
    assert resp.status_code == 404


def test_translate_invalid_api_key():
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("backend.routes.upload.UPLOAD_DIR", tmpdir):
            content = b"%PDF-1.4 fake pdf\n" * 10
            upload_resp = client.post("/upload", files={"file": ("doc.pdf", content, "application/pdf")})
            file_id = upload_resp.json()["file_id"]

        with patch("backend.routes.translate.UPLOAD_DIR", tmpdir):
            resp = client.post("/translate", json={
                "file_id": file_id,
                "api_key": "bad-key",
            })
            assert resp.status_code == 400
            assert "api key" in resp.json()["detail"].lower()


@patch("backend.task_manager.run_translation")
def test_translate_flow(mock_run):
    with tempfile.TemporaryDirectory() as tmpdir:
        file_id = "test123abc"
        file_path = os.path.join(tmpdir, f"{file_id}.pdf")
        with open(file_path, "w") as f:
            f.write("dummy content")

        with patch("backend.routes.translate.UPLOAD_DIR", tmpdir):
            resp = client.post("/translate", json={
                "file_id": file_id,
                "api_key": "sk-test-valid",
                "out_format": "txt",
            })
            assert resp.status_code == 200
            data = resp.json()
            assert "task_id" in data
            assert data["status"] in ("pending", "running", "completed")


def test_translate_status_not_found():
    resp = client.get("/translate/nonexistent/status")
    assert resp.status_code == 404


def test_download_not_found():
    resp = client.get("/download/nonexistent")
    assert resp.status_code == 404
