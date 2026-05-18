import json
import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from translator.pipeline import run_translation, _save_state, _load_state, _cleanup_state
from translator.types import TranslationConfig


def test_save_and_load_state():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = os.path.join(tmpdir, "progress.json")
        _save_state(state_path, 5, 10, ["a", "b", "c", "d", "e"])
        loaded = _load_state(state_path)
        assert loaded is not None
        assert loaded["idx"] == 5
        assert loaded["total"] == 10
        assert loaded["translated"] == ["a", "b", "c", "d", "e"]


def test_load_missing_state():
    assert _load_state("nonexistent.json") is None


def test_cleanup_state_removes_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = os.path.join(tmpdir, "progress.json")
        with open(state_path, "w") as f:
            json.dump({"idx": 1, "total": 1, "translated": ["x"]}, f)
        assert os.path.exists(state_path)
        _cleanup_state(state_path)
        assert not os.path.exists(state_path)


def test_cleanup_state_missing_file_does_not_raise():
    _cleanup_state("nonexistent.json")


@patch("translator.pipeline.extract_text_from_pdf")
@patch("translator.pipeline.chunk_pages")
@patch("translator.pipeline._translate_single_chunk")
@patch("translator.pipeline.export_to_pdf")
def test_run_translation_sequential(
    mock_export, mock_translate, mock_chunk, mock_extract
):
    mock_extract.return_value = ["page1", "page2"]
    mock_chunk.return_value = ["chunk1", "chunk2"]
    mock_translate.side_effect = ["traduzido1", "traduzido2"]

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "test.pdf")
        with open(input_path, "w") as f:
            f.write("dummy")

        cfg = TranslationConfig(
            input_path=input_path,
            output_dir=tmpdir,
            out_format="pdf",
            api_key="sk-test",
        )
        result = run_translation(cfg)

        expected = os.path.join(tmpdir, "test_traduzido.pdf")
        assert result == expected
        assert mock_translate.call_count == 2
        mock_export.assert_called_once()


@patch("translator.pipeline.extract_text_from_pdf")
@patch("translator.pipeline.chunk_pages")
@patch("translator.pipeline._translate_single_chunk")
def test_run_translation_cancel(
    mock_translate, mock_chunk, mock_extract
):
    mock_extract.return_value = ["page1", "page2", "page3"]
    mock_chunk.return_value = ["chunk1", "chunk2", "chunk3"]

    cancel_state = {"cancelled": True}

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "test.pdf")
        with open(input_path, "w") as f:
            f.write("dummy")

        cfg = TranslationConfig(
            input_path=input_path,
            output_dir=tmpdir,
            out_format="txt",
            api_key="sk-test",
        )

        result = run_translation(cfg, should_cancel=lambda: cancel_state["cancelled"])

        assert result is None
        assert mock_translate.call_count == 0


def test_run_translation_invalid_config():
    cfg = TranslationConfig(
        input_path="nonexistent.pdf",
        output_dir="/tmp",
        out_format="pdf",
        api_key=None,
    )
    with pytest.raises(ValueError):
        run_translation(cfg)
