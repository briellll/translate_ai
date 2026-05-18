from unittest.mock import patch, MagicMock, ANY
import pytest

from translator.markup_reader import (
    extract_text_from_pdf_with_marks,
    extract_html_tree_from_epub,
    _font_style,
)


class TestFontStyle:
    def test_bold(self):
        assert _font_style("Helvetica-Bold", 12)["bold"] is True

    def test_italic(self):
        assert _font_style("Helvetica-Oblique", 12)["italic"] is True

    def test_bold_italic(self):
        style = _font_style("Helvetica-BoldOblique", 12)
        assert style["bold"] is True
        assert style["italic"] is True

    def test_mono(self):
        assert _font_style("Courier", 12)["mono"] is True

    def test_heading_sized(self):
        assert _font_style("Helvetica", 24)["heading"] is False  # detected by size in visitor


@patch("translator.markup_reader.PdfReader")
def test_extract_with_marks_password(mock_reader):
    from pypdf.errors import WrongPasswordError
    mock_reader.side_effect = WrongPasswordError("pwd")
    with pytest.raises(ValueError, match="senha"):
        extract_text_from_pdf_with_marks("protected.pdf")


@patch("translator.markup_reader.PdfReader")
def test_extract_with_marks_empty(mock_reader):
    mock_instance = MagicMock()
    mock_instance.pages = []
    mock_reader.return_value = mock_instance
    with pytest.raises(ValueError, match="vazio"):
        extract_text_from_pdf_with_marks("empty.pdf")


@patch("translator.markup_reader.epub.read_epub")
def test_extract_html_tree_empty_spine(mock_read):
    mock_book = MagicMock()
    mock_book.spine = []
    mock_read.return_value = mock_book
    with pytest.raises(ValueError, match="vazio"):
        extract_html_tree_from_epub("empty.epub")


@patch("translator.markup_reader.epub.read_epub")
def test_extract_html_tree_missing(mock_read):
    mock_read.side_effect = FileNotFoundError("missing")
    with pytest.raises(FileNotFoundError):
        extract_html_tree_from_epub("missing.epub")
