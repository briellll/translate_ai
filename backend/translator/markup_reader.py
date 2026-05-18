import re
from typing import List, Optional, Tuple
from pypdf import PdfReader
from pypdf.errors import PdfStreamError, WrongPasswordError
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup, NavigableString, Tag


BOLD_FONTS = {"bold", "black", "heavy", "demi"}
ITALIC_FONTS = {"italic", "oblique", "slanted"}
MONO_FONTS = {"courier", "monospace", "mono", "consolas", "menlo"}


def _font_style(name: str, size: float) -> dict:
    name_lower = (name or "").lower()
    styles = {"bold": False, "italic": False, "mono": False, "heading": False, "size": size}

    for kw in BOLD_FONTS:
        if kw in name_lower:
            styles["bold"] = True
            break

    for kw in ITALIC_FONTS:
        if kw in name_lower:
            styles["italic"] = True
            break

    for kw in MONO_FONTS:
        if kw in name_lower:
            styles["mono"] = True
            break

    return styles


def extract_text_from_pdf_with_marks(path: str) -> List[str]:
    try:
        reader = PdfReader(path)
    except FileNotFoundError:
        raise
    except WrongPasswordError:
        raise ValueError("PDF protegido por senha. Remova a senha antes de traduzir.")
    except Exception as exc:
        raise ValueError(f"Não foi possível abrir o PDF: {exc}")

    if not reader.pages:
        raise ValueError("PDF vazio.")

    # Estimate body font size from first page with content
    body_size = 12.0
    for p in reader.pages:
        try:
            text = p.extract_text() or ""
            if text.strip():
                visitor = _SizeVisitor()
                p.extract_text(visitor_text=visitor.visit)
                if visitor.sizes:
                    body_size = sorted(visitor.sizes.items(), key=lambda x: x[1], reverse=True)[0][0]
                break
        except Exception:
            continue

    pages_marked: List[str] = []

    for page in reader.pages:
        try:
            visitor = _MarkupVisitor(body_size)
            page.extract_text(visitor_text=visitor.visit)
            marked = visitor.get_text()
            if marked.strip():
                pages_marked.append(marked)
        except Exception:
            continue

    if not pages_marked:
        raise ValueError(
            "Nenhum texto extraível encontrado no PDF. "
            "Pode ser um PDF escaneado (imagem)."
        )

    return pages_marked


class _SizeVisitor:
    def __init__(self):
        self.sizes: dict[float, int] = {}

    def visit(self, text: str, cm, tm, font_dict: Optional[dict], font_size: float):
        if text.strip():
            self.sizes[round(font_size, 1)] = self.sizes.get(round(font_size, 1), 0) + len(text.strip())


class _MarkupVisitor:
    def __init__(self, body_size: float = 12.0):
        self._parts: List[str] = []
        self._body_size = body_size

    def visit(self, text: str, cm, tm, font_dict: Optional[dict], font_size: float):
        if not text:
            return

        name = (font_dict or {}).get("/BaseFont", "") or ""
        style = _font_style(name, font_size)

        chunk = text

        if style["bold"] and style["italic"]:
            chunk = f"***{chunk}***"
        elif style["bold"]:
            chunk = f"**{chunk}**"
        elif style["italic"]:
            chunk = f"*{chunk}*"

        if style["mono"]:
            chunk = f"`{chunk}`"

        if not style["bold"] and not style["italic"] and font_size > self._body_size * 1.3:
            level = "#" * min(max(int(6 - (font_size / self._body_size)), 1), 6)
            chunk = f"{level} {chunk.strip()}"

        self._parts.append(chunk)

    def get_text(self) -> str:
        raw = "".join(self._parts)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        return raw.strip()


def extract_html_tree_from_epub(path: str) -> List[Tuple[str, BeautifulSoup]]:
    try:
        book = epub.read_epub(path)
    except FileNotFoundError:
        raise
    except Exception as exc:
        raise ValueError(f"Não foi possível abrir o EPUB: {exc}")

    chapters: List[Tuple[str, BeautifulSoup]] = []
    total = 0

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

        total += 1

        name = (getattr(item, "get_name", lambda: "")() or "").lower()
        href = (getattr(item, "file_name", "") or "").lower()
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
        except Exception:
            continue

        try:
            html_str = content.decode(errors="replace")
            soup = BeautifulSoup(html_str, "html.parser")
            text_len = len(soup.get_text("\n").strip())
            if text_len < 300:
                continue
            chapters.append((html_str, soup))
        except Exception:
            continue

    if total == 0:
        raise ValueError("EPUB vazio ou sem itens no espinhaço.")
    if not chapters:
        raise ValueError("Nenhum capítulo com conteúdo textual suficiente.")

    return chapters


def translate_html_soup(soup: BeautifulSoup, translate_fn) -> str:
    for element in soup.find_all(["script", "style"]):
        element.decompose()

    def _walk(node):
        for child in list(node.children):
            if isinstance(child, NavigableString) and child.strip():
                translated = translate_fn(child.strip())
                child.replace_with(NavigableString(translated))
            elif isinstance(child, Tag):
                _walk(child)

    _walk(soup)
    return str(soup)
