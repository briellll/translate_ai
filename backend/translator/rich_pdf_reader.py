from typing import List, Dict, Any
import fitz


BOLD_FONTS = {"bold", "black", "heavy", "demi", "extra bold"}
ITALIC_FONTS = {"italic", "oblique", "slanted"}
CODE_FONTS = {"courier", "monospace", "mono", "consolas", "menlo", "source code"}


def _classify_span(span: Dict[str, Any], body_size: float) -> Dict[str, Any]:
    font = (span.get("font", "") or "").lower()
    size = span.get("size", body_size)
    flags = span.get("flags", 0)
    color = span.get("color", (0, 0, 0))

    is_bold = bool(flags & 2) or any(kw in font for kw in BOLD_FONTS)
    is_italic = bool(flags & 1) or any(kw in font for kw in ITALIC_FONTS)
    is_code = any(kw in font for kw in CODE_FONTS)
    is_heading = size > body_size * 1.25

    return {
        "text": span.get("text", ""),
        "font": font,
        "size": size,
        "bold": is_bold,
        "italic": is_italic,
        "code": is_code,
        "heading": is_heading,
        "color": color,
        "origin": span.get("origin", (0, 0)),
    }


def _extract_body_size_from_page(page: fitz.Page) -> float:
    blocks = page.get_text("dict").get("blocks", [])
    sizes: Dict[float, int] = {}

    for block in blocks:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            origin_y = line.get("bbox", [0, 0, 0, 0])[1]
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                if len(text) > 3:
                    size = round(span.get("size", 12), 1)
                    sizes[size] = sizes.get(size, 0) + len(text)

    if not sizes:
        return 12.0

    return max(sizes, key=sizes.get)


def extract_rich_pdf(path: str) -> List[List[Dict[str, Any]]]:
    try:
        doc = fitz.open(path)
    except FileNotFoundError:
        raise
    except Exception as exc:
        raise ValueError(f"Não foi possível abrir o PDF: {exc}")

    if doc.page_count == 0:
        raise ValueError("PDF vazio.")

    pages_blocks: List[List[Dict[str, Any]]] = []

    for page_num in range(doc.page_count):
        page = doc[page_num]
        body_size = _extract_body_size_from_page(page)
        blocks_data = page.get_text("dict").get("blocks", [])
        page_spans: List[Dict[str, Any]] = []

        for block in blocks_data:
            if block.get("type") != 0:
                continue

            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if not text:
                        continue
                    classified = _classify_span(span, body_size)
                    page_spans.append(classified)

        if page_spans:
            pages_blocks.append(page_spans)

    doc.close()

    if not pages_blocks:
        raise ValueError(
            "Nenhum texto extraível encontrado no PDF. "
            "Pode ser um PDF escaneado (imagem)."
        )

    return pages_blocks


def spans_to_markdown(spans: List[Dict[str, Any]]) -> str:
    parts: List[str] = []
    prev_y = 0
    prev_heading = False

    for s in spans:
        text = s["text"]
        _, y = s["origin"]

        if y - prev_y > 12 and prev_y > 0:
            parts.append("\n")
            prev_heading = False

        if s["code"]:
            text = f"`{text}`"

        if s["bold"] and s["italic"]:
            text = f"***{text}***"
        elif s["bold"]:
            text = f"**{text}**"
        elif s["italic"]:
            text = f"*{text}*"

        if s["heading"] and not prev_heading:
            heading_size = s["size"]
            body = 12.0
            level = min(max(int(6 - (heading_size / body)), 1), 6)
            text = f"{'#' * level} {text}"
            prev_heading = True
        elif not s["heading"]:
            prev_heading = False

        parts.append(text)
        prev_y = y

    text = " ".join(parts)
    return text.strip()
