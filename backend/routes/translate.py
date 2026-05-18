import asyncio
import glob
import json
import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from backend.task_manager import create_task, run_task_in_background, get_task, cancel_task
from translator.types import TranslationConfig
from translator.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", ".uploads")


class TranslateRequest(BaseModel):
    file_id: str
    api_key: str
    out_format: str = "pdf"
    model: str = "gpt-4o-mini"
    chunk_chars: int = 4000
    temperature: float = 0
    top_p: float = 1.0
    max_tokens: int | None = None
    parallel_chunks: int = 1


@router.post("/translate")
async def translate(req: TranslateRequest):
    if not req.api_key.startswith("sk-"):
        raise HTTPException(status_code=400, detail="API key inválida")

    upload_dir = UPLOAD_DIR
    ext = ".pdf"
    import glob
    matches = list(glob.glob(os.path.join(upload_dir, f"{req.file_id}.*")))
    if not matches:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado. Faça upload primeiro.")

    input_path = matches[0]
    ext = os.path.splitext(input_path)[1].lower()

    if not os.path.exists(input_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado no servidor.")

    out_dir = os.path.join(upload_dir, "output")
    os.makedirs(out_dir, exist_ok=True)

    cfg = TranslationConfig(
        input_path=input_path,
        output_dir=out_dir,
        out_format=req.out_format,
        chunk_chars=req.chunk_chars,
        model=req.model,
        api_key=req.api_key,
        temperature=req.temperature,
        top_p=req.top_p,
        max_tokens=req.max_tokens,
        parallel_chunks=req.parallel_chunks,
    )

    task = create_task(req.file_id)
    run_task_in_background(task, cfg)

    return {"task_id": task.id, "status": task.status.value}


@router.get("/translate/{task_id}")
async def translate_stream(task_id: str):
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task não encontrada")

    async def event_generator():
        yield {"event": "status", "data": json.dumps({"status": task.status.value})}

        while task.status in ("pending", "running"):
            try:
                msg_type, payload = await asyncio.wait_for(task.queue.get(), timeout=2.0)
            except asyncio.TimeoutError:
                yield {"event": "ping", "data": ""}
                continue

            if msg_type == "token":
                yield {"event": "token", "data": json.dumps({"text": payload})}
            elif msg_type == "progress":
                yield {
                    "event": "progress",
                    "data": json.dumps({
                        "idx": payload.idx,
                        "total": payload.total,
                        "elapsed": round(payload.elapsed, 1),
                        "eta": round(payload.eta, 1),
                        "avg_per_part": round(payload.avg_per_part, 1),
                        "speed_parts_per_min": round(payload.speed_parts_per_min, 2),
                    }),
                }
            elif msg_type in ("done", "error"):
                break

        yield {
            "event": "result",
            "data": json.dumps({
                "status": task.status.value,
                "error": task.error,
                "task_id": task.id,
            }),
        }

    return EventSourceResponse(event_generator())


@router.get("/translate/{task_id}/status")
async def translate_status(task_id: str):
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task não encontrada")

    return {
        "task_id": task.id,
        "status": task.status.value,
        "error": task.error,
        "progress": {
            "idx": task.progress.idx if task.progress else 0,
            "total": task.progress.total if task.progress else 0,
            "elapsed": round(task.progress.elapsed, 1) if task.progress else 0,
            "eta": round(task.progress.eta, 1) if task.progress else 0,
        } if task.progress else None,
        "result_path": task.result_path,
    }


@router.post("/translate/{task_id}/cancel")
async def translate_cancel(task_id: str):
    if cancel_task(task_id):
        return {"status": "cancelled"}
    raise HTTPException(status_code=404, detail="Task não encontrada ou já finalizada")
