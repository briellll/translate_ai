import os
import uuid

from fastapi import APIRouter, UploadFile, File, HTTPException

from translator.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", ".uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".epub"}


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato '{ext}' não suportado. Use PDF ou EPUB.",
        )

    file_id = uuid.uuid4().hex[:12]
    save_path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")

    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    logger.info("Upload recebido: %s → %s (%.1f KB)", file.filename, save_path, len(content) / 1024)

    return {
        "file_id": file_id,
        "filename": file.filename,
        "size_kb": round(len(content) / 1024, 1),
    }
