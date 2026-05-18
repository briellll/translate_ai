import os
import tempfile

from translator.validation import validate_config
from translator.types import TranslationConfig


def test_validate_config_valid():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "test.pdf")
        with open(input_path, "w") as f:
            f.write("dummy content")

        cfg = TranslationConfig(
            input_path=input_path,
            output_dir=tmpdir,
            out_format="pdf",
            api_key="sk-test123",
        )
        errors = validate_config(cfg)
        assert errors == []


def test_validate_config_missing_input():
    cfg = TranslationConfig(
        input_path="",
        output_dir="/tmp",
        out_format="pdf",
        api_key="sk-test",
    )
    errors = validate_config(cfg)
    assert any("não informado" in e.lower() or "não encontrado" in e.lower() for e in errors)


def test_validate_config_missing_api_key():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "test.pdf")
        with open(input_path, "w") as f:
            f.write("dummy")
        cfg = TranslationConfig(
            input_path=input_path,
            output_dir=tmpdir,
            out_format="pdf",
            api_key=None,
        )
        errors = validate_config(cfg)
        assert any("api key" in e.lower() for e in errors)


def test_validate_config_invalid_api_key():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "test.pdf")
        with open(input_path, "w") as f:
            f.write("dummy")
        cfg = TranslationConfig(
            input_path=input_path,
            output_dir=tmpdir,
            out_format="pdf",
            api_key="invalid-key",
        )
        errors = validate_config(cfg)
        assert any("sk-" in e for e in errors)


def test_validate_config_wrong_extension():
    cfg = TranslationConfig(
        input_path="doc.docx",
        output_dir="/tmp",
        out_format="pdf",
        api_key="sk-test",
    )
    errors = validate_config(cfg)
    assert any("docx" in e.lower() or "suportado" in e.lower() for e in errors)


def test_validate_config_invalid_out_format():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "test.pdf")
        with open(input_path, "w") as f:
            f.write("dummy")
        cfg = TranslationConfig(
            input_path=input_path,
            output_dir=tmpdir,
            out_format="docx",
            api_key="sk-test",
        )
        errors = validate_config(cfg)
        assert any("formato de saída" in e.lower() for e in errors)


def test_validate_config_invalid_temperature():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "test.pdf")
        with open(input_path, "w") as f:
            f.write("dummy")
        cfg = TranslationConfig(
            input_path=input_path,
            output_dir=tmpdir,
            out_format="pdf",
            api_key="sk-test",
            temperature=3.0,
        )
        errors = validate_config(cfg)
        assert any("temperature" in e.lower() for e in errors)


def test_validate_config_chunk_chars_too_low():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "test.pdf")
        with open(input_path, "w") as f:
            f.write("dummy")
        cfg = TranslationConfig(
            input_path=input_path,
            output_dir=tmpdir,
            out_format="pdf",
            api_key="sk-test",
            chunk_chars=100,
        )
        errors = validate_config(cfg)
        assert any("chars" in e.lower() for e in errors)
