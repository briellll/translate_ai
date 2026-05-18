import asyncio
import os
import threading
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from translator.pipeline import run_translation
from translator.types import TranslationConfig, ProgressStats
from translator.logger import get_logger

logger = get_logger(__name__)


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


@dataclass
class Task:
    id: str
    status: TaskStatus = TaskStatus.PENDING
    config: Optional[TranslationConfig] = None
    file_id: str = ""
    result_path: Optional[str] = None
    error: Optional[str] = None
    progress: Optional[ProgressStats] = None
    cancel_event: threading.Event = field(default_factory=threading.Event)
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)


_tasks: dict[str, Task] = {}
_lock = threading.Lock()


def create_task(file_id: str) -> Task:
    task_id = uuid.uuid4().hex[:12]
    task = Task(id=task_id, file_id=file_id)
    with _lock:
        _tasks[task_id] = task
    logger.info("Task criada: %s (file_id=%s)", task_id, file_id)
    return task


def get_task(task_id: str) -> Optional[Task]:
    with _lock:
        return _tasks.get(task_id)


def run_task_in_background(task: Task, cfg: TranslationConfig) -> None:
    def _run():
        task.status = TaskStatus.RUNNING
        task.config = cfg

        async def _put_token(msg: str):
            await task.queue.put(("token", msg))

        def _on_token(tok: str):
            try:
                loop = asyncio.new_event_loop()
                loop.run_until_complete(_put_token(tok))
                loop.close()
            except Exception:
                pass

        def _on_progress(stats: ProgressStats):
            task.progress = stats
            try:
                loop = asyncio.new_event_loop()
                loop.run_until_complete(task.queue.put(("progress", stats)))
                loop.close()
            except Exception:
                pass

        try:
            out_path = run_translation(
                cfg,
                on_token=_on_token,
                on_progress=_on_progress,
                should_cancel=lambda: task.cancel_event.is_set(),
            )
            if task.cancel_event.is_set():
                task.status = TaskStatus.CANCELLED
                task.queue.put_nowait(("done", None))
            elif out_path:
                task.status = TaskStatus.COMPLETED
                task.result_path = out_path
                task.queue.put_nowait(("done", out_path))
            else:
                task.status = TaskStatus.ERROR
                task.error = "Tradução retornou sem resultado"
                task.queue.put_nowait(("done", None))
        except Exception as exc:
            logger.error("Task %s falhou: %s", task.id, exc, exc_info=True)
            task.status = TaskStatus.ERROR
            task.error = str(exc)
            try:
                loop = asyncio.new_event_loop()
                loop.run_until_complete(task.queue.put(("error", str(exc))))
                loop.close()
            except Exception:
                pass
            task.queue.put_nowait(("done", None))

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()


def cancel_task(task_id: str) -> bool:
    task = get_task(task_id)
    if task and task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
        task.cancel_event.set()
        logger.info("Cancelamento solicitado para task %s", task_id)
        return True
    return False
