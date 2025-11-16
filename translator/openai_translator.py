from openai import OpenAI
from typing import Iterator, Optional

def translate_chunk_with_openai(chunk: str, model: str = "gpt-4o-mini", api_key: Optional[str] = None) -> str:
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY ausente")
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a precise technical translator. Translate to Portuguese preserving technical terms and formatting. Return only the translated text."},
            {"role": "user", "content": chunk},
        ],
        temperature=0,
    )
    return resp.choices[0].message.content or ""

def stream_translate_chunk_with_openai(chunk: str, model: str = "gpt-4o-mini", api_key: Optional[str] = None) -> Iterator[str]:
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY ausente")
    client = OpenAI(api_key=api_key)
    stream = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a precise technical translator. Translate to Portuguese preserving technical terms and formatting. Return only the translated text."},
            {"role": "user", "content": chunk},
        ],
        temperature=0,
        stream=True,
    )
    for part in stream:
        delta = part.choices[0].delta
        if delta and getattr(delta, "content", None):
            yield delta.content
