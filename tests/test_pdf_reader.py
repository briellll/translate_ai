import pytest

from translator.pdf_reader import extract_text_from_pdf


def test_extract_text_from_pdf_raises_on_missing():
    path = "non_existent_file.pdf"
    with pytest.raises(FileNotFoundError):
        extract_text_from_pdf(path)
