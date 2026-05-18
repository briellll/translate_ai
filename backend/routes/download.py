import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.task_manager import get_task
from translator.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/download/{task_id}")
async def download_result(task_id: str):
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task não encontrada")

    if task.status != "completed":
        raise HTTPException(status_code=400, detail="Tradução ainda não foi concluída")

    if not task.result_path or not os.path.exists(task.result_path):
        raise HTTPException(status_code=404, detail="Arquivo de resultado não encontrado")

    filename = os.path.basename(task.result_path)
    return FileResponse(
        task.result_path,
        media_type="application/octet-stream",
        filename=filename,
    )
