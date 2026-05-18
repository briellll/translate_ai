import io
import os
import re
from typing import List, Optional
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image as RLImage
from ebooklib import epub
from html import escape


_MARKDOWN_RE = re.compile(
    r"(?P<bold_italic>\*\*\*(.+?)\*\*\*)"
    r"|(?P<bold>\*\*(.+?)\*\*)"
    r"|(?P<italic>\*(.+?)\*)"
    r"|(?P<mono>`(.+?)`)"
    r"|(?P<heading>^(#{1,6})\s+(.+?)$)"
    r"|(?P<rule>^---+$)",
    re.MULTILINE,
)


def _markup_to_reportlab(text: str) -> str:
    def _replacer(m: re.Match) -> str:
        if m.group("bold_italic"):
            return f'<b><i>{escape(m.group(2))}</i></b>'
        elif m.group("bold"):
            return f'<b>{escape(m.group(4))}</b>'
        elif m.group("italic"):
            return f'<i>{escape(m.group(6))}</i>'
        elif m.group("mono"):
            return f'<font face="Courier">{escape(m.group(8))}</font>'
        elif m.group("heading"):
            content = m.group("heading").lstrip("# ")
            return f'<b>{escape(content.strip())}</b>'
        elif m.group("rule"):
            return "<hr/>"
        return escape(m.group(0))

    return _MARKDOWN_RE.sub(_replacer, text)


def _validate_out_path(path: str) -> None:
    if not path:
        raise ValueError("Caminho de saída não informado.")
    out_dir = os.path.dirname(path) or os.getcwd()
    if not os.path.isdir(out_dir):
        raise ValueError(f"Diretório de saída não existe: {out_dir}")
    if os.path.isdir(path):
        raise ValueError(f"Caminho de saída é um diretório: {path}")


def export_to_pdf(chunks_translated: List[str], out_path: str, images: Optional[List[List]] = None):
    _validate_out_path(out_path)

    if not chunks_translated:
        chunks_translated = [""]

    styles = {
        "Normal": ParagraphStyle("Normal", fontSize=11, leading=15, spaceAfter=6),
        "H1": ParagraphStyle("H1", fontSize=20, leading=26, spaceAfter=10, spaceBefore=14),
        "H2": ParagraphStyle("H2", fontSize=17, leading=22, spaceAfter=8, spaceBefore=12),
        "H3": ParagraphStyle("H3", fontSize=14, leading=19, spaceAfter=6, spaceBefore=10),
        "Code": ParagraphStyle("Code", fontSize=9, fontName="Courier", leading=13, spaceAfter=6,
                                leftIndent=12, backColor=HexColor("#f0f0f0")),
    }

    story = []
    max_h = 540
    margin = 50
    page_w = A4[0] - 2 * margin
    used_y = [0]

    def _place_image(img_block, max_y: float) -> bool:
        x0, y0, x1, y1 = img_block.bbox
        img_w = min(x1 - x0, page_w - 20)
        scale = img_w / (x1 - x0) if (x1 - x0) > 0 else 1
        img_h = min((y1 - y0) * scale, 400)

        if max_y + img_h > max_h:
            story.append(PageBreak())
            used_y[0] = 0

        try:
            rl_img = RLImage(io.BytesIO(img_block.data), width=img_w, height=img_h)
            story.append(Spacer(1, 4))
            story.append(rl_img)
            story.append(Spacer(1, 4))
            used_y[0] += img_h + 12
            return True
        except Exception:
            return False

    for chunk_idx, chunk in enumerate(chunks_translated):
        chunk_images = []
        if images and chunk_idx < len(images):
            chunk_images = images[chunk_idx]

        text_lines = [l for l in chunk.split("\n")]

        items = []
        for img in chunk_images:
            items.append(("image", img))
        for line in text_lines:
            items.append(("text", line))

        items.sort(key=lambda it: (
            it[1].y if it[0] == "image" and hasattr(it[1], "y") else
            float(it[1].split("|")[0]) if "|" in it[1] else 0
        ) if False else 0)

        for it_type, it_data in items:
            if it_type == "image":
                _place_image(it_data, used_y[0])
                continue

            line = it_data.strip()
            if not line:
                story.append(Spacer(1, 4))
                continue

            rl_text = _markup_to_reportlab(line)

            if line.startswith("##### "):
                p = Paragraph(rl_text.replace("##### ", ""), styles["H3"])
            elif line.startswith("#### "):
                p = Paragraph(rl_text.replace("#### ", ""), styles["H3"])
            elif line.startswith("### "):
                p = Paragraph(rl_text.replace("### ", ""), styles["H2"])
            elif line.startswith("## "):
                p = Paragraph(rl_text.replace("## ", ""), styles["H2"])
            elif line.startswith("# "):
                p = Paragraph(rl_text.replace("# ", ""), styles["H1"])
            elif line.startswith("---"):
                story.append(Spacer(1, 6))
                story.append(Paragraph("<hr/>", styles["Normal"]))
                story.append(Spacer(1, 6))
                continue
            elif "`" in line:
                p = Paragraph(rl_text, styles["Code"])
            else:
                p = Paragraph(rl_text, styles["Normal"])

            story.append(p)

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
            for c in chunks_translated:
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

        for i, chunk in enumerate(chunks_translated, 1):
            body = []
            for line in chunk.split("\n"):
                html_line = _markdown_to_html(line)
                body.append(html_line)

            if not body:
                body.append("<p></p>")
            html_content = "<body>" + "\n".join(body) + "</body>"
            ch = epub.EpubHtml(title=safe_title, file_name=f"part_{i}.xhtml", lang="pt")
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


def _markdown_to_html(text: str) -> str:
    if not text.strip():
        return "<p></p>"

    def _replacer(m: re.Match) -> str:
        if m.group("bold_italic"):
            return f"<b><i>{escape(m.group(2))}</i></b>"
        elif m.group("bold"):
            return f"<b>{escape(m.group(4))}</b>"
        elif m.group("italic"):
            return f"<i>{escape(m.group(6))}</i>"
        elif m.group("mono"):
            return f"<code>{escape(m.group(8))}</code>"
        elif m.group("heading"):
            level = len(m.group("heading").split(" ")[0])
            content = m.group("heading").lstrip("# ")
            return f"<h{level}>{escape(content.strip())}</h{level}>"
        return escape(m.group(0))

    html = _MARKDOWN_RE.sub(_replacer, text)
    return f"<p>{html}</p>"
