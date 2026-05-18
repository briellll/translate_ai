from typing import List
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

def extract_text_from_epub(path: str) -> List[str]:
    book = epub.read_epub(path)
    pages: List[str] = []

    skip_substrings = [
        "toc", "table of contents", "nav", "titlepage", "title-page",
        "copyright", "acknowledg", "cover", "map", "extras", "preview",
        "about the author", "author", "news", "orbit"
    ]

    for idref, _linear in book.spine:
        item = book.get_item_with_id(idref)
        if not item:
            continue
        name = (getattr(item, "get_name", lambda: "")() or "").lower()
        href = (getattr(item, "file_name", "") or "").lower()
        if any(s in name or s in href for s in skip_substrings):
            continue
        if item.get_type() != ebooklib.ITEM_DOCUMENT:
            continue
        content = item.get_content()
        html = content.decode(errors="ignore")
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text("\n")
        if len(text.strip()) < 300:
            continue
        pages.append(text)
    return pages
