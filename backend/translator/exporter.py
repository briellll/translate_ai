import os
from typing import List
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from ebooklib import epub
from html import escape


def _validate_out_path(path: str) -> None:
    if not path:
        raise ValueError("Caminho de saída não informado.")
    out_dir = os.path.dirname(path) or os.getcwd()
    if not os.path.isdir(out_dir):
        raise ValueError(f"Diretório de saída não existe: {out_dir}")
    if os.path.isdir(path):
        raise ValueError(f"Caminho de saída é um diretório: {path}")


def export_to_pdf(chunks_translated: List[str], out_path: str):
    _validate_out_path(out_path)

    if not chunks_translated:
        chunks_translated = [""]

    styles = getSampleStyleSheet()
    story = []
    for i, c in enumerate(chunks_translated):
        for paragraph in c.split("\n"):
            if paragraph.strip():
                try:
                    story.append(Paragraph(paragraph, styles["Normal"]))
                except Exception:
                    story.append(Paragraph(escape(paragraph), styles["Normal"]))
                story.append(Spacer(1, 6))
        story.append(PageBreak())

    try:
        doc = SimpleDocTemplate(out_path, pagesize=A4)
        doc.build(story)
    except (OSError, PermissionError) as exc:
        raise RuntimeError(f"Falha ao gerar PDF: {exc}") from exc


def export_to_txt(chunks_translated: List[str], out_path: str):
    _validate_out_path(out_path)

    if not chunks_translated:
        chunks_translated = [""]

    try:
        with open(out_path, "w", encoding="utf-8", errors="replace") as f:
            for i, c in enumerate(chunks_translated, 1):
                f.write(c)
                f.write("\n\n")
    except (OSError, PermissionError) as exc:
        raise RuntimeError(f"Falha ao escrever TXT: {exc}") from exc


def export_to_epub(chunks_translated: List[str], out_path: str, title: str = "Tradução"):
    _validate_out_path(out_path)

    if not chunks_translated:
        chunks_translated = [""]

    try:
        book = epub.EpubBook()
        book.set_title(title or "Tradução")
        book.add_author("Tradutor AI")

        safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in (title or "Tradução"))
        chapters = []
        for i, c in enumerate(chunks_translated, 1):
            ch = epub.EpubHtml(title=safe_title, file_name=f"part_{i}.xhtml", lang="pt")
            html_content = "".join(f"<p>{escape(u)}</p>" for u in c.split("\n"))
            ch.content = html_content
            book.add_item(ch)
            chapters.append(ch)

        book.toc = tuple(chapters)
        book.spine = ["nav"] + chapters
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        epub.write_epub(out_path, book)
    except (OSError, PermissionError) as exc:
        raise RuntimeError(f"Falha ao gerar EPUB: {exc}") from exc
