import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Optional, List

from .chunker import chunk_pages
from .epub_reader import extract_text_from_epub
from .pdf_reader import extract_text_from_pdf
from .exporter import export_to_epub, export_to_pdf, export_to_txt
from .logger import get_logger
from .openai_translator import stream_translate_chunk_with_openai, translate_chunk_with_openai
from .types import ProgressStats, TranslationConfig
from .validation import validate_config

logger = get_logger(__name__)

STATE_FILE_SUFFIX = "_progress.json"


def _state_path(cfg: TranslationConfig) -> str:
    base = os.path.splitext(os.path.basename(cfg.input_path))[0]
    return os.path.join(cfg.output_dir, f"{base}{STATE_FILE_SUFFIX}")


def _save_state(state_path: str, idx: int, total: int, translated: List[str]) -> None:
    try:
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump({"idx": idx, "total": total, "translated": translated}, f, ensure_ascii=False)
    except Exception as exc:
        logger.warning("Falha ao salvar progresso: %s", exc)


def _load_state(state_path: str) -> Optional[dict]:
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _cleanup_state(state_path: str) -> None:
    try:
        if os.path.exists(state_path):
            os.remove(state_path)
    except Exception as exc:
        logger.warning("Falha ao limpar arquivo de estado: %s", exc)


def _translate_single_chunk(
    ch: str,
    idx: int,
    total: int,
    cfg: TranslationConfig,
    should_cancel: Optional[Callable[[], bool]],
    on_token: Optional[Callable[[str], None]],
) -> str:
    if should_cancel and should_cancel():
        return ""

    kwargs = dict(
        model=cfg.model,
        api_key=cfg.api_key or None,
        temperature=cfg.temperature,
        top_p=cfg.top_p,
        max_tokens=cfg.max_tokens,
    )

    acc: List[str] = []
    try:
        for tok in stream_translate_chunk_with_openai(ch, **kwargs):
            if should_cancel and should_cancel():
                return ""
            acc.append(tok)
            if on_token:
                on_token(tok)
    except Exception as exc:
        logger.warning("Streaming falhou no chunk %d/%d: %s. Usando fallback non-streaming.", idx, total, exc)

    if acc:
        return "".join(acc)

    try:
        return translate_chunk_with_openai(ch, **kwargs)
    except Exception as exc:
        logger.error("Fallback non-streaming também falhou no chunk %d/%d: %s", idx, total, exc)
        raise


def run_translation(
    cfg: TranslationConfig,
    on_chunk_start: Optional[Callable[[int, int], None]] = None,
    on_token: Optional[Callable[[str], None]] = None,
    on_progress: Optional[Callable[[ProgressStats], None]] = None,
    should_cancel: Optional[Callable[[], bool]] = None,
) -> Optional[str]:
    errors = validate_config(cfg)
    if errors:
        msg = "; ".join(errors)
        logger.error("Validação falhou: %s", msg)
        raise ValueError(msg)

    base = os.path.splitext(os.path.basename(cfg.input_path))[0]
    ext = os.path.splitext(cfg.input_path)[1].lower()

    if ext == ".pdf":
        pages = extract_text_from_pdf(cfg.input_path)
    elif ext == ".epub":
        pages = extract_text_from_epub(cfg.input_path)
    else:
        raise ValueError("Formato não suportado. Use .pdf ou .epub")

    chunks = chunk_pages(pages, chunk_chars=cfg.chunk_chars)
    total = len(chunks)
    translated: List[str] = []
    start_idx = 0

    state_path = _state_path(cfg)

    if cfg.resume:
        state = _load_state(state_path)
        if state and state.get("total") == total:
            start_idx = state["idx"]
            translated = list(state["translated"])
            logger.info("Retomando do chunk %d/%d", start_idx, total)
        else:
            logger.info("Nenhum estado anterior encontrado. Iniciando do zero.")

    start_t = time.time()
    logger.info(
        "Tradução iniciada | %d chunks | modelo=%s | paralelo=%d | resume=%s",
        total, cfg.model, cfg.parallel_chunks, cfg.resume,
    )

    if cfg.parallel_chunks > 1 and total > 1:
        remaining = [(i, ch) for i, ch in enumerate(chunks[start_idx:], start_idx + 1)]
        with ThreadPoolExecutor(max_workers=cfg.parallel_chunks) as executor:
            future_map = {
                executor.submit(
                    _translate_single_chunk, ch, idx, total, cfg, should_cancel, on_token
                ): (idx, ch)
                for idx, ch in remaining
            }

            for future in as_completed(future_map):
                idx, ch = future_map[future]
                try:
                    text = future.result()
                    translated.append(text)
                    translated.sort(key=lambda t: chunks.index(ch))
                except Exception as exc:
                    logger.error("Falha no chunk %d: %s", idx, exc)
                    raise

                elapsed = time.time() - start_t
                avg = elapsed / (idx - start_idx) if idx > start_idx else 0
                eta = avg * (total - idx)
                speed = ((idx - start_idx) / elapsed * 60) if elapsed > 0 else 0.0
                if on_progress:
                    on_progress(ProgressStats(idx=idx, total=total, elapsed=elapsed, eta=eta, avg_per_part=avg, speed_parts_per_min=speed))

                _save_state(state_path, idx, total, translated)
    else:
        for idx in range(start_idx + 1, total + 1):
            if should_cancel and should_cancel():
                logger.info("Tradução cancelada pelo usuário no chunk %d/%d", idx, total)
                _save_state(state_path, idx - 1, total, translated)
                return None

            ch = chunks[idx - 1]
            if on_chunk_start:
                on_chunk_start(idx, total)

            text = _translate_single_chunk(ch, idx, total, cfg, should_cancel, on_token)
            translated.append(text)

            elapsed = time.time() - start_t
            avg = elapsed / (idx - start_idx) if idx > start_idx else 0
            eta = avg * (total - idx)
            speed = ((idx - start_idx) / elapsed * 60) if elapsed > 0 else 0.0
            if on_progress:
                on_progress(ProgressStats(idx=idx, total=total, elapsed=elapsed, eta=eta, avg_per_part=avg, speed_parts_per_min=speed))

            _save_state(state_path, idx, total, translated)

    out_path = os.path.join(cfg.output_dir, f"{base}_traduzido.{cfg.out_format}")
    logger.info("Exportando resultado para: %s", out_path)

    if cfg.out_format == "pdf":
        export_to_pdf(translated, out_path)
    elif cfg.out_format == "txt":
        export_to_txt(translated, out_path)
    else:
        export_to_epub(translated, out_path, title=base)

    _cleanup_state(state_path)
    logger.info("Tradução concluída: %s", out_path)
    return out_path
