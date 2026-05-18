from translator.chunker import chunk_pages, chunk_pages_by_tokens, count_tokens


def test_chunk_pages_returns_list(sample_pages):
    result = chunk_pages(sample_pages, chunk_chars=5000)
    assert isinstance(result, list)
    assert len(result) >= 1


def test_chunk_pages_respects_char_limit(sample_pages):
    result = chunk_pages(sample_pages, chunk_chars=50)
    for chunk in result:
        assert len(chunk) <= 80, f"Chunk exceeded limit: {len(chunk)} chars"


def test_chunk_pages_empty_input():
    assert chunk_pages([], chunk_chars=1000) == []


def test_chunk_pages_skips_empty_pages():
    pages = ["", "texto valido", ""]
    result = chunk_pages(pages, chunk_chars=1000)
    assert len(result) >= 1
    assert "texto valido" in result[0]


def test_count_tokens_short_text():
    tokens = count_tokens("hello world")
    assert isinstance(tokens, int)
    assert tokens > 0


def test_chunk_pages_by_tokens_basic():
    pages = [
        "Primeira página com conteúdo extenso para testar o chunking por tokens. " * 10,
        "Segunda página com mais texto repetido para garantir que os chunks funcionem. " * 10,
    ]
    result = chunk_pages_by_tokens(pages, max_tokens=100)
    assert isinstance(result, list)
    assert len(result) >= 1
    for chunk in result:
        assert count_tokens(chunk) <= 200


def test_chunk_pages_by_tokens_empty():
    assert chunk_pages_by_tokens([], max_tokens=1000) == []


def test_chunk_pages_by_tokens_small_overlap():
    pages = [
        "Texto pequeno A.",
        "Texto pequeno B.",
        "Texto pequeno C.",
    ]
    result = chunk_pages_by_tokens(pages, max_tokens=10, overlap_tokens=5)
    assert len(result) >= 1
