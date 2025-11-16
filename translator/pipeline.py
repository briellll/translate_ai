import os
import time
from typing import Callable, Optional, List

from .pdf_reader import extract_text_from_pdf
from .epub_reader import extract_text_from_epub
from .chunker import chunk_pages
from .openai_translator import translate_chunk_with_openai, stream_translate_chunk_with_openai
from .exporter import export_to_pdf, export_to_txt, export_to_epub
from .types import TranslationConfig, ProgressStats


def run_translation(
    cfg: TranslationConfig,
    on_chunk_start: Optional[Callable[[int, int], None]] = None,
    on_token: Optional[Callable[[str], None]] = None,
    on_progress: Optional[Callable[[ProgressStats], None]] = None,
    should_cancel: Optional[Callable[[], bool]] = None,
) -> Optional[str]:
    if not os.path.exists(cfg.input_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {cfg.input_path}")

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
    start_t = time.time()

    for idx, ch in enumerate(chunks, 1):
        if should_cancel and should_cancel():
            return None
        if on_chunk_start:
            on_chunk_start(idx, total)

        acc: List[str] = []
        try:
            for tok in stream_translate_chunk_with_openai(ch, model=cfg.model, api_key=cfg.api_key or None):
                if should_cancel and should_cancel():
                    return None
                acc.append(tok)
                if on_token:
                    on_token(tok)
        except Exception:
            pass
        text = "".join(acc) if acc else translate_chunk_with_openai(ch, model=cfg.model, api_key=cfg.api_key or None)
        translated.append(text)

        elapsed = time.time() - start_t
        avg = elapsed / idx
        eta = avg * (total - idx)
        speed = (idx / elapsed * 60) if elapsed > 0 else 0.0
        if on_progress:
            on_progress(ProgressStats(idx=idx, total=total, elapsed=elapsed, eta=eta, avg_per_part=avg, speed_parts_per_min=speed))

    out_path = os.path.join(cfg.output_dir, f"{base}_traduzido.{cfg.out_format}")
    if cfg.out_format == "pdf":
        export_to_pdf(translated, out_path)
    elif cfg.out_format == "txt":
        export_to_txt(translated, out_path)
    else:
        export_to_epub(translated, out_path, title=base)
    return out_path

