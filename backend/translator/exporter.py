from typing import List
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from ebooklib import epub
from html import escape

def export_to_pdf(chunks_translated: List[str], out_path: str):
    styles = getSampleStyleSheet()
    story = []
    for i, c in enumerate(chunks_translated):
        for paragraph in c.split('\n'):
            if paragraph.strip():
                story.append(Paragraph(paragraph, styles["Normal"]))
                story.append(Spacer(1, 6))
        story.append(PageBreak())
    doc = SimpleDocTemplate(out_path, pagesize=A4)
    doc.build(story)

def export_to_txt(chunks_translated: List[str], out_path: str):
    with open(out_path, "w", encoding="utf-8", errors="replace") as f:
        for i, c in enumerate(chunks_translated, 1):
            f.write(c)
            f.write("\n\n")

def export_to_epub(chunks_translated: List[str], out_path: str, title: str = "Tradução"):
    book = epub.EpubBook()
    book.set_title(title)
    book.add_author("Tradutor AI")
    chapters = []
    for i, c in enumerate(chunks_translated, 1):
        ch = epub.EpubHtml(title=f"{title}", file_name=f"part_{i}.xhtml", lang="pt")
        html = "".join(f"<p>{escape(u)}</p>" for u in c.split('\n'))
        ch.content = html
        book.add_item(ch)
        chapters.append(ch)
    book.toc = tuple(chapters)
    book.spine = ["nav"] + chapters
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    epub.write_epub(out_path, book)
