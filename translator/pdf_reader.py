from typing import List
from PyPDF2 import PdfReader


def extract_text_from_pdf(path: str) -> List[str]:
    """Return list of page texts from a PDF file (no OCR).
    Each list item corresponds to one page's raw text.
    """
    reader = PdfReader(path)
    pages = []
    for p in reader.pages:
        try:
            pages.append(p.extract_text() or "")
        except Exception:
            pages.append("")
    return pages

