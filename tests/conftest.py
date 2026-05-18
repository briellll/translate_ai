from typing import List
import pytest


@pytest.fixture
def sample_pages() -> List[str]:
    return [
        "Primeira página do documento. Aqui temos texto introdutório.",
        "Segunda página com informações técnicas importantes.",
        "Terceira página concluindo o documento.",
    ]


@pytest.fixture
def sample_chunk() -> str:
    return (
        "This is a technical document about software development. "
        "It covers various programming concepts and best practices. "
        "The goal is to provide accurate translations."
    )
