import io
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional

import fitz
import pdfplumber


BOLD_FONTS = {"bold", "black", "heavy", "demi", "extrabold", "extra bold"}
ITALIC_FONTS = {"italic", "oblique", "slanted"}
CODE_FONTS = {"courier", "monospace", "mono", "consolas", "menlo", "source code", "fira code"}


@dataclass
class TextSpan:
    text: str
    x: float
    y: float
    font: str
    size: float
    bold: bool
    italic: bool
    code: bool
    color: Tuple[float, float, float] = (0, 0, 0)


@dataclass
class ImageBlock:
    bbox: Tuple[float, float, float, float]
    data: bytes
    ext: str


@dataclass
class PageContent:
    page_num: int
    spans: List[TextSpan] = field(default_factory=list)
    images: List[ImageBlock] = field(default_factory=list)
    width: float = 0
    height: float = 0


def _classify_font(font_name: str) -> Tuple[bool, bool, bool]:
    name = (font_name or "").lower()
    bold = any(kw in name for kw in BOLD_FONTS)
    italic = any(kw in name for kw in ITALIC_FONTS)
    code = any(kw in name for kw in CODE_FONTS)
    return bold, italic, code


def _parse_rgb(color) -> Tuple[float, float, float]:
    try:
        if color is None:
            return (0, 0, 0)
        if hasattr(color, "rgb"):
            return tuple(round(c, 3) for c in color.rgb)
        if isinstance(color, (list, tuple)) and len(color) >= 3:
            return (float(color[0]), float(color[1]), float(color[2]))
    except Exception:
        pass
    return (0, 0, 0)


def _extract_images_from_page(fitz_page: fitz.Page, page_height: float) -> List[ImageBlock]:
    images: List[ImageBlock] = []
    try:
        for img in fitz_page.get_images(full=True):
            try:
                xref = img[0]
                base = fitz.Pixmap(fitz_page.parent, xref)
                bbox = fitz_page.get_image_bbox(img)
                if bbox.is_empty or bbox.width < 20 or bbox.height < 20:
                    continue

                x0, y0, x1, y1 = bbox.x0, page_height - bbox.y1, bbox.x1, page_height - bbox.y0
                ext = "png"
                img_bytes: Optional[bytes] = None

                if base.n < 5:
                    pix = fitz.Pixmap(fitz.csRGB, base)
                    img_bytes = pix.tobytes("png")
                else:
                    pix = fitz.Pixmap(fitz.csRGB, base)
                    img_bytes = pix.tobytes("png")

                if img_bytes and len(img_bytes) > 500:
                    images.append(ImageBlock(bbox=(x0, y0, x1, y1), data=img_bytes, ext=ext))
            except Exception:
                continue
    except Exception:
        pass
    return images


_DEFAULT_BODY_SIZE: float = 12.0


def _detect_body_size(all_pages_data: List[Dict]) -> float:
    size_counts: Dict[float, int] = defaultdict(int)

    for page_data in all_pages_data:
        for char in page_data["chars"]:
            text = char.get("text", "").strip()
            if len(text) > 2:
                size = round(char.get("fontsize", 12), 1)
                size_counts[size] += 1

    if not size_counts:
        return _DEFAULT_BODY_SIZE

    return max(size_counts, key=size_counts.get)


def _build_repeated_position_filter(all_pages_data: List[Dict], threshold: float = 0.65) -> Dict[float, Set[str]]:
    position_texts: Dict[float, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    total_pages = len(all_pages_data)

    if total_pages < 3:
        return {}

    for page_data in all_pages_data:
        seen: Set[Tuple[float, str]] = set()
        for char in page_data["chars"]:
            text = char.get("text", "").strip()
            if len(text) < 4:
                continue
            y = round(char.get("top", 0), 0)
            key = (y, text.lower())
            if key in seen:
                continue
            seen.add(key)
            position_texts[y][text.lower()] += 1

    repeated: Dict[float, Set[str]] = defaultdict(set)
    for y, texts in position_texts.items():
        for text, count in texts.items():
            if count / total_pages >= threshold and count >= 3:
                repeated[y].add(text)

    return dict(repeated)


def extract_premium_pdf(path: str) -> List[PageContent]:
    try:
        pdfplumber_doc = pdfplumber.open(path)
        fitz_doc = fitz.open(path)
    except FileNotFoundError:
        raise
    except Exception as exc:
        raise ValueError(f"Não foi possível abrir o PDF: {exc}")

    if len(pdfplumber_doc.pages) == 0:
        raise ValueError("PDF vazio.")

    all_pages_chars: List[Dict] = []
    for page in pdfplumber_doc.pages:
        chars = page.chars
        all_pages_chars.append({"chars": chars, "width": page.width, "height": page.height})

    body_size = _detect_body_size(all_pages_chars)
    repeated_filter = _build_repeated_position_filter(all_pages_chars)

    results: List[PageContent] = []
    text_found = False

    for page_num in range(len(pdfplumber_doc.pages)):
        plumber_page = pdfplumber_doc.pages[page_num]
        fitz_page = fitz_doc[page_num]

        width = plumber_page.width
        height = plumber_page.height

        page_spans: List[TextSpan] = []
        chars = plumber_page.chars

        for i, char in enumerate(chars):
            text = char.get("text", "").strip()
            if not text:
                continue

            y = round(char.get("top", 0), 0)
            if y in repeated_filter:
                lower = text.lower()
                if lower in repeated_filter[y]:
                    continue

            x = char.get("x0", 0)
            font = char.get("fontname", "")
            size = char.get("fontsize", body_size)
            bold, italic, code = _classify_font(font)
            color = _parse_rgb(char.get("non_stroking_color", None))

            is_heading = size > body_size * 1.25

            if not page_spans:
                page_spans.append(TextSpan(text=text, x=x, y=y, font=font, size=size,
                                          bold=bold, italic=italic, code=code, color=color))
                continue

            last = page_spans[-1]
            same_line = abs(y - last.y) < size * 0.8
            same_style = (bold == last.bold and italic == last.italic and
                         code == last.code and abs(size - last.size) < 0.5)

            if same_line and same_style:
                last.text += text
            else:
                page_spans.append(TextSpan(text=text, x=x, y=y, font=font, size=size,
                                          bold=bold, italic=italic, code=code, color=color))

        images = _extract_images_from_page(fitz_page, height)

        if page_spans:
            text_found = True

        results.append(PageContent(
            page_num=page_num,
            spans=page_spans,
            images=images,
            width=width,
            height=height,
        ))

    pdfplumber_doc.close()
    fitz_doc.close()

    if not text_found:
        raise ValueError(
            "Nenhum texto extraível encontrado no PDF. "
            "Pode ser um PDF escaneado (imagem)."
        )

    return results


def spans_to_markdown(spans: List[TextSpan], body_size: float = 12.0) -> str:
    if not spans:
        return ""

    parts: List[str] = []
    prev_y = -100
    prev_heading = False

    for s in spans:
        text = s.text
        y = s.y

        if y - prev_y > s.size * 1.5 and prev_y > -50:
            parts.append("\n")
            prev_heading = False

        if s.code:
            text = f"`{text}`"

        if s.bold and s.italic:
            text = f"***{text}***"
        elif s.bold:
            text = f"**{text}**"
        elif s.italic:
            text = f"*{text}*"

        is_heading = s.size > body_size * 1.25
        if is_heading and not prev_heading:
            level = min(max(int(6 - (s.size / body_size)), 1), 6)
            text = f"{'#' * level} {text}"
            prev_heading = True
        elif not is_heading:
            prev_heading = False

        parts.append(text)
        prev_y = y

    return " ".join(parts)
