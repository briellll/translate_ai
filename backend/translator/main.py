import argparse
import logging
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import List

from .types import TranslationConfig
from .pipeline import run_translation
from .logger import get_logger
from tqdm import tqdm

logger = get_logger(__name__)


def process(
    input_path: str,
    out_path: str,
    chunk_chars: int = 4000,
    model: str = "gpt-4o-mini",
    api_key: str | None = None,
    show_text: bool = False,
    preview_chars: int = 400,
    temperature: float = 0,
    top_p: float = 1.0,
    max_tokens: int | None = None,
    parallel_chunks: int = 1,
) -> None:
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {input_path}")

    cfg = TranslationConfig(
        input_path=input_path,
        output_dir=os.path.dirname(out_path) or os.getcwd(),
        out_format="pdf",
        chunk_chars=chunk_chars,
        model=model,
        api_key=api_key,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        parallel_chunks=parallel_chunks,
    )
    def on_chunk_start(idx: int, total: int):
        if show_text:
            tqdm.write(f"\n===== Parte {idx}/{total} =====")
    def on_token(tok: str):
        if show_text:
            tqdm.write(tok)
    def on_progress(stats):
        pass
    final_out = run_translation(cfg, on_chunk_start=on_chunk_start, on_token=on_token, on_progress=on_progress)
    print(f"Pronto! Arquivo salvo em: {final_out}")
    logger.info("CLI concluída: %s", final_out)


def get_downloads_dir() -> str:
    """Resolve the user's Downloads directory and ensure it exists."""
    downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    os.makedirs(downloads, exist_ok=True)
    return downloads


def gui_select_and_process(chunk_chars: int = 4000, model: str = "gpt-4o-mini") -> None:
    root = tk.Tk()
    root.withdraw()
    input_path = filedialog.askopenfilename(
        title="Selecione o arquivo",
        filetypes=[("Documentos", "*.pdf *.epub"), ("PDF", "*.pdf"), ("EPUB", "*.epub")]
    )
    if not input_path:
        logger.info("Nenhum arquivo selecionado na GUI. Encerrando.")
        return

    base_name = os.path.splitext(os.path.basename(input_path))[0]
    out_path = os.path.join(get_downloads_dir(), f"{base_name}_traduzido.pdf")

    try:
        # GUI principal oferece campo de chave; na CLI, use --api-key
        process(input_path, out_path, chunk_chars=chunk_chars, model=model, api_key=None, show_text=False)
        try:
            messagebox.showinfo("Tradução concluída", f"Arquivo salvo em:\n{out_path}")
        except Exception:
            # ignore messagebox errors in headless environments
            pass
    except Exception as e:
        try:
            messagebox.showerror("Erro na tradução", str(e))
        except Exception:
            pass
        raise


def cli():
    if len(sys.argv) == 1:
        gui_select_and_process()
        return

    parser = argparse.ArgumentParser(description="Traduz PDF ou EPUB para PDF usando OpenAI")
    parser.add_argument("input", help="Caminho de entrada (.pdf ou .epub)")
    parser.add_argument("out", help="Caminho de saída .pdf, ex.: traduzido.pdf")
    parser.add_argument("--chunk-chars", type=int, default=4000, help="Caracteres aproximados por chunk")
    parser.add_argument("--model", type=str, default="gpt-4o-mini", help="Modelo OpenAI, ex.: 'gpt-4o-mini'")
    parser.add_argument("--api-key", type=str, default=None, help="Chave da API OpenAI (se não usar GUI)")
    parser.add_argument("--show-text", action="store_true", help="Mostrar trecho traduzido no terminal")
    parser.add_argument("--preview-chars", type=int, default=400, help="Quantidade de caracteres mostrados por parte")
    parser.add_argument("--temperature", type=float, default=0, help="Temperatura do modelo (0-2)")
    parser.add_argument("--top-p", type=float, default=1.0, help="Top-p sampling (0-1)")
    parser.add_argument("--max-tokens", type=int, default=None, help="Máximo de tokens por resposta")
    parser.add_argument("--parallel", type=int, default=1, help="Número de traduções em paralelo")
    args = parser.parse_args()
    process(
        args.input, args.out,
        chunk_chars=args.chunk_chars,
        model=args.model,
        api_key=args.api_key,
        show_text=args.show_text,
        preview_chars=args.preview_chars,
        temperature=args.temperature,
        top_p=args.top_p,
        max_tokens=args.max_tokens,
        parallel_chunks=args.parallel,
    )


if __name__ == "__main__":
    cli()
