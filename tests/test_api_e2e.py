import os
import tempfile
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_e2e_upload_and_translate_flow():
    with tempfile.TemporaryDirectory() as tmpdir:
        upload_dir = os.path.join(tmpdir, "uploads")
        out_dir = os.path.join(tmpdir, "output")
        os.makedirs(upload_dir)
        os.makedirs(out_dir)

        with patch("backend.routes.upload.UPLOAD_DIR", upload_dir):
            content = b"%PDF-1.4 fake pdf\n" * 20
            resp = client.post("/upload", files={"file": ("doc.pdf", content, "application/pdf")})
            assert resp.status_code == 200
            file_id = resp.json()["file_id"]

        with (
            patch("backend.routes.translate.UPLOAD_DIR", upload_dir),
            patch("backend.task_manager.run_translation") as mock_run,
        ):
            mock_run.return_value = os.path.join(out_dir, "doc_traduzido.txt")

            resp = client.post("/translate", json={
                "file_id": file_id,
                "api_key": "sk-test-valid",
                "out_format": "txt",
            })
            assert resp.status_code == 200
            task_id = resp.json()["task_id"]
            assert task_id

            status_resp = client.get(f"/translate/{task_id}/status")
            assert status_resp.status_code == 200
            data = status_resp.json()
            assert data["task_id"] == task_id
            assert data["status"] in ("pending", "running", "completed")


def test_e2e_cancel_during_translation():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        upload_dir = os.path.join(tmpdir, "uploads")
        os.makedirs(upload_dir)

        with patch("backend.routes.upload.UPLOAD_DIR", upload_dir):
            resp = client.post("/upload", files={"file": ("doc.pdf", b"%PDF-1.4\n" * 10, "application/pdf")})
            file_id = resp.json()["file_id"]

        with patch("backend.routes.translate.UPLOAD_DIR", upload_dir):
            translate_resp = client.post("/translate", json={
                "file_id": file_id,
                "api_key": "sk-test-cancel",
                "out_format": "txt",
            })
            task_id = translate_resp.json()["task_id"]

            cancel_resp = client.post(f"/translate/{task_id}/cancel")
            assert cancel_resp.status_code == 200
            assert cancel_resp.json()["status"] in ("cancelled", "completed")


def test_e2e_download_before_complete():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        upload_dir = os.path.join(tmpdir, "uploads")
        os.makedirs(upload_dir)

        with patch("backend.routes.upload.UPLOAD_DIR", upload_dir):
            resp = client.post("/upload", files={"file": ("doc.pdf", b"%PDF-1.4\n", "application/pdf")})
            file_id = resp.json()["file_id"]

        with patch("backend.routes.translate.UPLOAD_DIR", upload_dir):
            translate_resp = client.post("/translate", json={
                "file_id": file_id,
                "api_key": "sk-test-dl",
                "out_format": "pdf",
            })
            task_id = translate_resp.json()["task_id"]

            dl_resp = client.get(f"/download/{task_id}")
            if dl_resp.status_code == 400:
                assert "concluída" in dl_resp.json()["detail"].lower()
            else:
                assert dl_resp.status_code in (200, 404)


def test_e2e_unsupported_file_extension():
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("backend.routes.upload.UPLOAD_DIR", tmpdir):
            resp = client.post("/upload", files={"file": ("doc.docx", b"hello", "application/octet-stream")})
            assert resp.status_code == 400
            assert "não suportado" in resp.json()["detail"].lower()
