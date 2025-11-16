from typing import List


def chunk_pages(pages: List[str], chunk_chars: int = 3000) -> List[str]:
    """Create chunks from list of page texts. Approximates tokenization by characters.
    chunk_chars: target maximum characters per chunk.
    """
    chunks = []
    buffer = []
    buf_len = 0

    for page in pages:
        if not page:
            continue
        # split page into paragraphs to avoid breaking mid-sentence
        paras = [p.strip() for p in page.split('\n') if p.strip()]
        for p in paras:
            if buf_len + len(p) + 1 > chunk_chars and buffer:
                chunks.append('\n\n'.join(buffer))
                buffer = [p]
                buf_len = len(p)
            else:
                buffer.append(p)
                buf_len += len(p) + 2

    if buffer:
        chunks.append('\n\n'.join(buffer))

    return chunks

