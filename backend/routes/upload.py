import os
import uuid

from fastapi import APIRouter, UploadFile, File, HTTPException

from translator.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", ".uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".epub"}
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200 MB


def _sanitize_filename(filename: str) -> str:
    sane = "".join(c for c in filename if c.isalnum() or c in "._- ")
    return sane.strip() or "arquivo"


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nome do arquivo não informado.")

    original_name = _sanitize_filename(file.filename)
    ext = os.path.splitext(original_name)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato '{ext}' não suportado. Use PDF ou EPUB.",
        )

    file_id = uuid.uuid4().hex[:12]
    save_path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")

    total_bytes = 0
    try:
        with open(save_path, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > MAX_FILE_SIZE:
                    f.close()
                    os.remove(save_path)
                    raise HTTPException(
                        status_code=413,
                        detail=f"Arquivo muito grande. Limite: {MAX_FILE_SIZE // (1024*1024)} MB.",
                    )
                f.write(chunk)
    except HTTPException:
        raise
    except Exception as exc:
        if os.path.exists(save_path):
            try:
                os.remove(save_path)
            except OSError:
                pass
        raise HTTPException(status_code=500, detail=f"Erro ao salvar arquivo: {exc}")

    logger.info("Upload: %s → %s (%.1f KB)", original_name, save_path, total_bytes / 1024)

    return {
        "file_id": file_id,
        "filename": original_name,
        "size_kb": round(total_bytes / 1024, 1),
    }
