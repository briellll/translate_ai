from unittest.mock import patch, MagicMock

import pytest

from translator.openai_translator import (
    translate_chunk_with_openai,
    stream_translate_chunk_with_openai,
)


def test_translate_chunk_without_api_key():
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY ausente"):
        translate_chunk_with_openai("hello", api_key=None)


def test_stream_translate_chunk_without_api_key():
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY ausente"):
        next(stream_translate_chunk_with_openai("hello", api_key=None))


@patch("translator.openai_translator.OpenAI")
def test_translate_chunk_returns_text(mock_openai):
    mock_instance = MagicMock()
    mock_openai.return_value = mock_instance

    mock_choice = MagicMock()
    mock_choice.message.content = "olá"
    mock_instance.chat.completions.create.return_value.choices = [mock_choice]

    result = translate_chunk_with_openai("hello", api_key="sk-test")

    assert result == "olá"
    mock_instance.chat.completions.create.assert_called_once()


@patch("translator.openai_translator.OpenAI")
def test_translate_chunk_empty_response(mock_openai):
    mock_instance = MagicMock()
    mock_openai.return_value = mock_instance

    mock_choice = MagicMock()
    mock_choice.message.content = None
    mock_instance.chat.completions.create.return_value.choices = [mock_choice]

    result = translate_chunk_with_openai("hello", api_key="sk-test")

    assert result == ""


@patch("translator.openai_translator.OpenAI")
def test_translate_chunk_api_error(mock_openai):
    mock_instance = MagicMock()
    mock_openai.return_value = mock_instance
    mock_instance.chat.completions.create.side_effect = Exception("API error")

    with pytest.raises(Exception, match="API error"):
        translate_chunk_with_openai("hello", api_key="sk-test")


@patch("translator.openai_translator.OpenAI")
def test_translate_chunk_custom_params(mock_openai):
    mock_instance = MagicMock()
    mock_openai.return_value = mock_instance

    mock_choice = MagicMock()
    mock_choice.message.content = "test"
    mock_instance.chat.completions.create.return_value.choices = [mock_choice]

    translate_chunk_with_openai(
        "hello",
        api_key="sk-test",
        temperature=0.5,
        top_p=0.9,
        max_tokens=500,
    )

    call_kwargs = mock_instance.chat.completions.create.call_args.kwargs
    assert call_kwargs["temperature"] == 0.5
    assert call_kwargs["top_p"] == 0.9
    assert call_kwargs["max_tokens"] == 500


def _make_stream_event(delta_content: str | None):
    part = MagicMock()
    delta = MagicMock()
    delta.content = delta_content
    part.choices = [MagicMock(delta=delta)]
    return part


@patch("translator.openai_translator.OpenAI")
def test_stream_translate_chunk_yields_tokens(mock_openai):
    mock_instance = MagicMock()
    mock_openai.return_value = mock_instance

    events = [
        _make_stream_event("ol"),
        _make_stream_event("á "),
        _make_stream_event("mundo"),
        _make_stream_event(None),
    ]
    mock_instance.chat.completions.create.return_value = events

    result = list(stream_translate_chunk_with_openai("hello world", api_key="sk-test"))

    assert result == ["ol", "á ", "mundo"]
    mock_instance.chat.completions.create.assert_called_once()


@patch("translator.openai_translator.OpenAI")
def test_stream_translate_chunk_api_error(mock_openai):
    mock_instance = MagicMock()
    mock_openai.return_value = mock_instance
    mock_instance.chat.completions.create.side_effect = Exception("Stream error")

    with pytest.raises(Exception, match="Stream error"):
        next(stream_translate_chunk_with_openai("hello", api_key="sk-test"))


@patch("translator.openai_translator.OpenAI")
def test_stream_translate_chunk_custom_params(mock_openai):
    mock_instance = MagicMock()
    mock_openai.return_value = mock_instance
    mock_instance.chat.completions.create.return_value = []

    list(stream_translate_chunk_with_openai(
        "hello",
        api_key="sk-test",
        temperature=0.7,
        top_p=0.95,
        max_tokens=1000,
    ))

    call_kwargs = mock_instance.chat.completions.create.call_args.kwargs
    assert call_kwargs["temperature"] == 0.7
    assert call_kwargs["top_p"] == 0.95
    assert call_kwargs["max_tokens"] == 1000
