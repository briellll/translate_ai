from typing import List, Optional
import tiktoken


def _get_tokenizer(model: str) -> tiktoken.Encoding:
    try:
        return tiktoken.encoding_for_model(model)
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    tokenizer = _get_tokenizer(model)
    return len(tokenizer.encode(text))


def chunk_pages(pages: List[str], chunk_chars: int = 3000) -> List[str]:
    if not pages:
        return []

    chunks = []
    buffer = []
    buf_len = 0

    for page in pages:
        page = page.strip() if page else ""
        if not page:
            continue

        paras = [p.strip() for p in page.split("\n") if p.strip()]
        if not paras:
            continue

        for p in paras:
            if len(p) > chunk_chars:
                while len(p) > chunk_chars:
                    if buffer:
                        chunks.append("\n\n".join(buffer))
                        buffer = []
                        buf_len = 0
                    chunks.append(p[:chunk_chars])
                    p = p[chunk_chars:]
                if p:
                    buffer.append(p)
                    buf_len = len(p)
            elif buf_len + len(p) + 1 > chunk_chars and buffer:
                chunks.append("\n\n".join(buffer))
                buffer = [p]
                buf_len = len(p)
            else:
                buffer.append(p)
                buf_len += len(p) + 2

    if buffer:
        chunks.append("\n\n".join(buffer))

    if not chunks:
        return [""]

    return chunks


def chunk_pages_by_tokens(
    pages: List[str],
    model: str = "gpt-4o-mini",
    max_tokens: int = 8000,
    overlap_tokens: int = 100,
) -> List[str]:
    if not pages:
        return []

    tokenizer = _get_tokenizer(model)
    chunks = []
    buffer: List[str] = []
    buf_tokens = 0

    for page in pages:
        page = page.strip() if page else ""
        if not page:
            continue

        paras = [p.strip() for p in page.split("\n") if p.strip()]
        if not paras:
            continue

        for p in paras:
            p_tokens = len(tokenizer.encode(p))

            if p_tokens > max_tokens:
                if buffer:
                    chunks.append("\n\n".join(buffer))
                    buffer = []
                    buf_tokens = 0
                encoded = tokenizer.encode(p)
                for i in range(0, len(encoded), max_tokens):
                    chunk_tokens = encoded[i:i + max_tokens]
                    chunks.append(tokenizer.decode(chunk_tokens))
                continue

            if buf_tokens + p_tokens > max_tokens and buffer:
                chunk_text = "\n\n".join(buffer)
                chunks.append(chunk_text)

                if overlap_tokens > 0 and buffer:
                    overlap: List[str] = []
                    overlap_tok = 0
                    for prev in reversed(buffer):
                        t = len(tokenizer.encode(prev))
                        if overlap_tok + t > overlap_tokens:
                            break
                        overlap.insert(0, prev)
                        overlap_tok += t
                    buffer = overlap + [p]
                    buf_tokens = overlap_tok + p_tokens
                else:
                    buffer = [p]
                    buf_tokens = p_tokens
            else:
                buffer.append(p)
                buf_tokens += p_tokens

    if buffer:
        chunks.append("\n\n".join(buffer))

    if not chunks:
        return [""]

    return chunks
