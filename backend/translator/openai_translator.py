from openai import OpenAI
from typing import Iterator, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import (
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
    InternalServerError,
    BadRequestError,
    AuthenticationError,
    NotFoundError,
    ContentFilterFinishReasonError,
)

from .logger import get_logger

logger = get_logger(__name__)

RETRYABLE_ERRORS = (
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
    InternalServerError,
)

NON_RETRYABLE_MESSAGES = {
    "model_not_found": "Modelo não encontrado. Verifique se o nome está correto e se você tem acesso a ele.",
    "insufficient_quota": "Cota insuficiente. Verifique seu plano e saldo.",
    "invalid_api_key": "API key inválida. Verifique se a chave está correta.",
    "content_filter": "Conteúdo bloqueado pelo filtro de moderação da API.",
    "context_length": "Texto muito longo para o modelo escolhido. Reduza 'Chars por chunk'.",
}


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
    kwargs = {"api_key": api_key, "timeout": 60.0, "max_retries": 0}
    if base_url:
        kwargs["base_url"] = base_url
    return OpenAI(**kwargs)


SYSTEM_PROMPT_BASE = (
    "You are a precise technical translator. "
    "Translate to Portuguese. "
    "Return only the translated text."
)

SYSTEM_PROMPT_WITH_MARKS = (
    "You are a precise technical translator. "
    "Translate to Portuguese. The text contains formatting markers: "
    "**bold**, *italic*, ***bold italic***, `code`, and # headings. "
    "Preserve these markers exactly as they appear in your translation. "
    "Return only the translated text with markers."
)


def _build_messages(chunk: str, preserve_formatting: bool = False) -> list[dict]:
    system = SYSTEM_PROMPT_WITH_MARKS if preserve_formatting else SYSTEM_PROMPT_BASE
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": chunk},
    ]


def _translate_error(exc: Exception) -> str:
    msg = str(exc).lower()

    if isinstance(exc, AuthenticationError):
        return NON_RETRYABLE_MESSAGES["invalid_api_key"]
    if isinstance(exc, NotFoundError):
        return NON_RETRYABLE_MESSAGES["model_not_found"]
    if isinstance(exc, ContentFilterFinishReasonError):
        return NON_RETRYABLE_MESSAGES["content_filter"]
    if isinstance(exc, BadRequestError):
        if "maximum context length" in msg or "context_length_exceeded" in msg:
            return NON_RETRYABLE_MESSAGES["context_length"]
        if "insufficient_quota" in msg:
            return NON_RETRYABLE_MESSAGES["insufficient_quota"]
        if "model_not_found" in msg:
            return NON_RETRYABLE_MESSAGES["model_not_found"]
    if isinstance(exc, RateLimitError):
        return "Limite de requisições excedido. Aguarde alguns segundos e tente novamente."
    if isinstance(exc, APITimeoutError):
        return "Tempo limite excedido. O servidor demorou muito para responder."
    if isinstance(exc, APIConnectionError):
        return "Falha de conexão. Verifique a URL base e sua conexão de rede."

    return f"Erro na tradução: {exc}"


@_retry_decorator()
def translate_chunk_with_openai(
    chunk: str,
    model: str = "gpt-4o-mini",
    api_key: Optional[str] = None,
    temperature: float = 0,
    top_p: float = 1.0,
    max_tokens: Optional[int] = None,
    base_url: Optional[str] = None,
    preserve_formatting: bool = False,
) -> str:
    if not api_key:
        raise RuntimeError("API key não informada.")
    if not chunk.strip():
        return ""

    logger.info(
        "Traduzindo chunk (non-streaming) | modelo=%s | chars=%d | temp=%.1f | fmt=%s",
        model, len(chunk), temperature, preserve_formatting,
    )

    client = _build_client(api_key, base_url)
    kwargs = dict(
        model=model,
        messages=_build_messages(chunk, preserve_formatting),
        temperature=temperature,
        top_p=top_p,
    )
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens

    try:
        resp = client.chat.completions.create(**kwargs)
        content = resp.choices[0].message.content
        return (content or "").strip()
    except tuple(RETRYABLE_ERRORS):
        raise
    except Exception as exc:
        raise RuntimeError(_translate_error(exc)) from exc


@_retry_decorator()
def stream_translate_chunk_with_openai(
    chunk: str,
    model: str = "gpt-4o-mini",
    api_key: Optional[str] = None,
    temperature: float = 0,
    top_p: float = 1.0,
    max_tokens: Optional[int] = None,
    base_url: Optional[str] = None,
    preserve_formatting: bool = False,
) -> Iterator[str]:
    if not api_key:
        raise RuntimeError("API key não informada.")
    if not chunk.strip():
        return

    logger.info(
        "Traduzindo chunk (streaming) | modelo=%s | chars=%d | temp=%.1f | fmt=%s",
        model, len(chunk), temperature, preserve_formatting,
    )

    client = _build_client(api_key, base_url)
    kwargs = dict(
        model=model,
        messages=_build_messages(chunk, preserve_formatting),
        temperature=temperature,
        top_p=top_p,
        stream=True,
    )
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens

    try:
        stream = client.chat.completions.create(**kwargs)
        for part in stream:
            if part.choices and part.choices[0].finish_reason == "content_filter":
                raise ContentFilterFinishReasonError(NON_RETRYABLE_MESSAGES["content_filter"])
            delta = part.choices[0].delta if part.choices else None
            if delta and getattr(delta, "content", None):
                yield delta.content
    except tuple(RETRYABLE_ERRORS):
        raise
    except Exception as exc:
        raise RuntimeError(_translate_error(exc)) from exc
