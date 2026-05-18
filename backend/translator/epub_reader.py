from typing import List
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup


def extract_text_from_epub(path: str) -> List[str]:
    try:
        book = epub.read_epub(path)
    except FileNotFoundError:
        raise
    except Exception as exc:
        raise ValueError(f"Não foi possível abrir o EPUB: {exc}")

    pages: List[str] = []
    total_items = 0

    skip_substrings = [
        "toc", "table of contents", "nav", "titlepage", "title-page",
        "copyright", "acknowledg", "cover", "map", "extras", "preview",
        "about the author", "author", "news", "orbit",
    ]

    for idref, _linear in book.spine:
        try:
            item = book.get_item_with_id(idref)
        except Exception:
            continue

        if not item:
            continue

        total_items += 1

        try:
            name = (getattr(item, "get_name", lambda: "")() or "").lower()
        except Exception:
            name = ""

        try:
            href = (getattr(item, "file_name", "") or "").lower()
        except Exception:
            href = ""

        if any(s in name or s in href for s in skip_substrings):
            continue

        try:
            if item.get_type() != ebooklib.ITEM_DOCUMENT:
                continue
        except Exception:
            continue

        try:
            content = item.get_content()
            if not content:
                continue
            html = content.decode(errors="replace")
        except Exception:
            continue

        try:
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text("\n")
        except Exception:
            continue

        text = text.strip()
        if len(text) < 300:
            continue

        pages.append(text)

    if total_items == 0:
        raise ValueError("EPUB vazio ou sem itens no espinhaço.")

    if not pages:
        raise ValueError(
            "Nenhum capítulo com conteúdo textual suficiente encontrado no EPUB. "
            "O arquivo pode conter apenas imagens ou ter proteção de cópia."
        )

    return pages
