from unittest.mock import patch, MagicMock

import pytest
from pypdf.errors import WrongPasswordError, EmptyFileError, PdfStreamError

from translator.pdf_reader import extract_text_from_pdf


def test_extract_text_from_pdf_raises_on_missing():
    with pytest.raises(FileNotFoundError):
        extract_text_from_pdf("non_existent_file.pdf")


@patch("translator.pdf_reader.PdfReader")
def test_extract_text_from_pdf_password_protected(mock_reader):
    mock_reader.side_effect = WrongPasswordError("password required")
    with pytest.raises(ValueError, match="senha"):
        extract_text_from_pdf("protected.pdf")


@patch("translator.pdf_reader.PdfReader")
def test_extract_text_from_pdf_empty(mock_reader):
    mock_reader.side_effect = EmptyFileError("empty")
    with pytest.raises(ValueError, match="vazio"):
        extract_text_from_pdf("empty.pdf")


@patch("translator.pdf_reader.PdfReader")
def test_extract_text_from_pdf_corrupted(mock_reader):
    mock_reader.side_effect = PdfStreamError("corrupted")
    with pytest.raises(ValueError, match="corrompido|inválido"):
        extract_text_from_pdf("bad.pdf")


@patch("translator.pdf_reader.PdfReader")
def test_extract_text_from_pdf_no_extractable_text(mock_reader):
    mock_instance = MagicMock()
    mock_instance.pages = [MagicMock()]
    mock_instance.pages[0].extract_text.return_value = ""
    mock_reader.return_value = mock_instance

    with pytest.raises(ValueError, match="Nenhum texto extraível|escaneado"):
        extract_text_from_pdf("scanned.pdf")


@patch("translator.pdf_reader.PdfReader")
def test_extract_text_from_pdf_empty_pages(mock_reader):
    mock_instance = MagicMock()
    mock_instance.pages = []
    mock_reader.return_value = mock_instance

    with pytest.raises(ValueError, match="vazio"):
        extract_text_from_pdf("no_pages.pdf")
