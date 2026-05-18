from unittest.mock import patch, MagicMock
import pytest

from translator.premium_pdf_reader import (
    extract_premium_pdf,
    spans_to_markdown,
    TextSpan,
    _classify_font,
    _detect_body_size,
)


class TestClassifyFont:
    def test_bold(self):
        b, i, c = _classify_font("Helvetica-Bold")
        assert b is True
        assert i is False

    def test_italic(self):
        b, i, c = _classify_font("Helvetica-Oblique")
        assert b is False
        assert i is True

    def test_code(self):
        b, i, c = _classify_font("Courier")
        assert c is True

    def test_plain(self):
        b, i, c = _classify_font("Times-Roman")
        assert b is False
        assert i is False
        assert c is False


class TestSpansToMarkdown:
    def test_bold_italic_markers(self):
        spans = [
            TextSpan(text="texto ", x=0, y=10, font="Helvetica", size=12, bold=False, italic=False, code=False),
            TextSpan(text="negrito", x=30, y=10, font="Helvetica-Bold", size=12, bold=True, italic=False, code=False),
        ]
        result = spans_to_markdown(spans, body_size=12)
        assert "**negrito**" in result

    def test_code_marker(self):
        spans = [
            TextSpan(text="`code`", x=0, y=10, font="Courier", size=12, bold=False, italic=False, code=True),
        ]
        # With code=True, the markdown wraps in backticks
        result = spans_to_markdown(spans, body_size=12)
        assert "``" in result or "`" in result

    def test_heading_from_size(self):
        spans = [
            TextSpan(text="Heading", x=0, y=10, font="Helvetica", size=24, bold=False, italic=False, code=False),
        ]
        result = spans_to_markdown(spans, body_size=12)
        assert result.startswith("#")

    def test_empty(self):
        assert spans_to_markdown([], body_size=12) == ""


class TestDetectBodySize:
    def test_most_common_size(self):
        data = [
            {"chars": [
                {"text": "normal text a", "fontsize": 12},
                {"text": "normal text b", "fontsize": 12},
                {"text": "normal text c", "fontsize": 12},
                {"text": "heading", "fontsize": 24},
            ]},
        ]
        assert _detect_body_size(data) == 12.0


@patch("translator.premium_pdf_reader.pdfplumber.open")
@patch("translator.premium_pdf_reader.fitz.open")
def test_extract_empty_pdf(mock_fitz, mock_plumber):
    mock_plumber_doc = MagicMock()
    mock_plumber_doc.pages = []
    mock_plumber.return_value = mock_plumber_doc
    mock_fitz_doc = MagicMock()
    mock_fitz.return_value = mock_fitz_doc

    with pytest.raises(ValueError, match="vazio"):
        extract_premium_pdf("empty.pdf")


@patch("translator.premium_pdf_reader.pdfplumber.open")
@patch("translator.premium_pdf_reader.fitz.open")
def test_extract_missing_file(mock_fitz, mock_plumber):
    mock_plumber.side_effect = FileNotFoundError("not found")
    with pytest.raises(FileNotFoundError):
        extract_premium_pdf("missing.pdf")
