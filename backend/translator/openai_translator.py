from openai import OpenAI
from typing import Iterator, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import (
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
    InternalServerError,
)

from .logger import get_logger

logger = get_logger(__name__)

RETRYABLE_ERRORS = (
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
    InternalServerError,
)


def _retry_decorator():
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        retry=retry_if_exception_type(RETRYABLE_ERRORS),
        before_sleep=lambda retry_state: logger.warning(
            "Tentativa %d/%d falhou. Retentando em %.1fs...",
            retry_state.attempt_number,
            retry_state.retry_object.stop.max_attempt_number,
            retry_state.next_action.sleep if retry_state.next_action else 0,
        ),
    )


def _build_client(api_key: str, base_url: str | None = None) -> OpenAI:
    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    return OpenAI(**kwargs)


def _build_messages(chunk: str, temperature: float = 0) -> list[dict]:
    return [
        {
            "role": "system",
            "content": (
                "You are a precise technical translator. "
                "Translate to Portuguese preserving technical terms and formatting. "
                "Return only the translated text."
            ),
        },
        {"role": "user", "content": chunk},
    ]


@_retry_decorator()
def translate_chunk_with_openai(
    chunk: str,
    model: str = "gpt-4o-mini",
    api_key: Optional[str] = None,
    temperature: float = 0,
    top_p: float = 1.0,
    max_tokens: Optional[int] = None,
    base_url: Optional[str] = None,
) -> str:
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY ausente")
    logger.info(
        "Traduzindo chunk (non-streaming) | modelo=%s | chars=%d | temp=%.1f",
        model, len(chunk), temperature,
    )
    client = _build_client(api_key, base_url)
    kwargs = dict(
        model=model,
        messages=_build_messages(chunk, temperature),
        temperature=temperature,
        top_p=top_p,
    )
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens

    try:
        resp = client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content or ""
    except Exception as exc:
        logger.error("Falha na tradução non-streaming: %s", exc, exc_info=True)
        raise


@_retry_decorator()
def stream_translate_chunk_with_openai(
    chunk: str,
    model: str = "gpt-4o-mini",
    api_key: Optional[str] = None,
    temperature: float = 0,
    top_p: float = 1.0,
    max_tokens: Optional[int] = None,
    base_url: Optional[str] = None,
) -> Iterator[str]:
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY ausente")
    logger.info(
        "Traduzindo chunk (streaming) | modelo=%s | chars=%d | temp=%.1f",
        model, len(chunk), temperature,
    )
    client = _build_client(api_key, base_url)
    kwargs = dict(
        model=model,
        messages=_build_messages(chunk, temperature),
        temperature=temperature,
        top_p=top_p,
        stream=True,
    )
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens

    try:
        stream = client.chat.completions.create(**kwargs)
        for part in stream:
            delta = part.choices[0].delta
            if delta and getattr(delta, "content", None):
                yield delta.content
    except Exception as exc:
        logger.error("Falha no streaming: %s", exc, exc_info=True)
        raise
