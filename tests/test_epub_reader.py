import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from translator.epub_reader import extract_text_from_epub


def _make_mock_item(name: str, content_prefix: str, item_type: int = 9):
    content = f"<html><body><p>{content_prefix} {'.' * 400}</p></body></html>"
    item = MagicMock()
    item.get_name.return_value = name
    item.file_name = name
    item.get_type.return_value = item_type
    item.get_content.return_value = content.encode("utf-8")
    return item


@patch("translator.epub_reader.epub.read_epub")
def test_extract_text_from_epub_returns_pages(mock_read):
    mock_book = MagicMock()
    mock_book.spine = [("id1", True), ("id2", True)]

    item1 = _make_mock_item("chapter1.xhtml", "Texto do capítulo um.")
    item2 = _make_mock_item("chapter2.xhtml", "Texto do capítulo dois.")

    mock_book.get_item_with_id.side_effect = lambda i: {"id1": item1, "id2": item2}.get(i)
    mock_read.return_value = mock_book

    pages = extract_text_from_epub("fake.epub")
    assert len(pages) == 2
    assert "capítulo um" in pages[0].lower()
    assert "capítulo dois" in pages[1].lower()


@patch("translator.epub_reader.epub.read_epub")
def test_extract_text_from_epub_skips_short_pages(mock_read):
    mock_book = MagicMock()
    mock_book.spine = [("id1", True), ("id2", True)]

    short_content = "<html><body><p>Oi</p></body></html>"
    item_short = MagicMock()
    item_short.get_name.return_value = "short.xhtml"
    item_short.file_name = "short.xhtml"
    item_short.get_type.return_value = 9
    item_short.get_content.return_value = short_content.encode("utf-8")

    long_content = f"<html><body><p>{'A' * 500}</p></body></html>"
    item_long = MagicMock()
    item_long.get_name.return_value = "long.xhtml"
    item_long.file_name = "long.xhtml"
    item_long.get_type.return_value = 9
    item_long.get_content.return_value = long_content.encode("utf-8")

    mock_book.get_item_with_id.side_effect = lambda i: {"id1": item_short, "id2": item_long}.get(i)
    mock_read.return_value = mock_book

    pages = extract_text_from_epub("fake.epub")
    assert len(pages) == 1
    assert len(pages[0]) >= 300


@patch("translator.epub_reader.epub.read_epub")
def test_extract_text_from_epub_skips_toc_and_nav(mock_read):
    mock_book = MagicMock()
    mock_book.spine = [("toc", True), ("nav", True), ("content", True)]

    item_toc = _make_mock_item("toc.xhtml", "<p>Table of Contents</p>")
    item_nav = _make_mock_item("nav.xhtml", "<p>Navigation</p>")
    item_content = _make_mock_item("content.xhtml", "<p>" + "B" * 500 + "</p>")

    mock_book.get_item_with_id.side_effect = lambda i: {"toc": item_toc, "nav": item_nav, "content": item_content}.get(i)
    mock_read.return_value = mock_book

    pages = extract_text_from_epub("fake.epub")
    assert len(pages) == 1
    assert "conteúdo" not in pages[0].lower() or "content" not in pages[0].lower()


@patch("translator.epub_reader.epub.read_epub")
def test_extract_text_from_epub_raises_on_missing_file(mock_read):
    mock_read.side_effect = FileNotFoundError("Arquivo não encontrado")
    with pytest.raises(FileNotFoundError):
        extract_text_from_epub("missing.epub")
