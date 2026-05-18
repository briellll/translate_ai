import asyncio
import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from translator.pipeline import run_translation
from translator.types import TranslationConfig, ProgressStats
from translator.logger import get_logger

logger = get_logger(__name__)

TASK_MAX_AGE_SECONDS = 3600  # 1 hora


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
    created_at: float = field(default_factory=time.time)


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


def cancel_task(task_id: str) -> bool:
    task = get_task(task_id)
    if task and task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
        task.cancel_event.set()
        task.status = TaskStatus.CANCELLED
        logger.info("Task %s cancelada.", task_id)
        return True
    return False


def cleanup_old_tasks() -> int:
    now = time.time()
    to_delete: list[str] = []
    with _lock:
        for tid, task in list(_tasks.items()):
            if task.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.ERROR):
                if now - task.created_at > TASK_MAX_AGE_SECONDS:
                    to_delete.append(tid)
        for tid in to_delete:
            del _tasks[tid]
    if to_delete:
        logger.info("Limpeza: %d tasks antigas removidas.", len(to_delete))
    return len(to_delete)


def run_task_in_background(task: Task, cfg: TranslationConfig) -> None:
    def _run():
        task.status = TaskStatus.RUNNING
        task.config = cfg

        def _on_token(tok: str):
            if task.cancel_event.is_set():
                return
            try:
                loop = asyncio.new_event_loop()
                loop.run_until_complete(task.queue.put(("token", tok)))
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
            if task.cancel_event.is_set():
                task.status = TaskStatus.CANCELLED
                _safe_put(task.queue, ("done", None))
                return

            out_path = run_translation(
                cfg,
                on_token=_on_token,
                on_progress=_on_progress,
                should_cancel=lambda: task.cancel_event.is_set(),
            )

            if task.cancel_event.is_set():
                task.status = TaskStatus.CANCELLED
            elif out_path:
                task.status = TaskStatus.COMPLETED
                task.result_path = out_path
            else:
                task.status = TaskStatus.ERROR
                task.error = "Tradução retornou sem resultado."

            _safe_put(task.queue, ("done", task.result_path))

        except Exception as exc:
            logger.error("Task %s falhou: %s", task.id, exc, exc_info=True)
            task.status = TaskStatus.ERROR
            task.error = str(exc)
            _safe_put(task.queue, ("error", str(exc)))
            _safe_put(task.queue, ("done", None))

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()


def _safe_put(queue: asyncio.Queue, item) -> None:
    try:
        queue.put_nowait(item)
    except Exception:
        pass
