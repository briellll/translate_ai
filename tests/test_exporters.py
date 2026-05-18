import os
import tempfile

from translator.exporter import export_to_pdf, export_to_txt, export_to_epub


def test_export_to_txt_creates_content():
    chunks = ["Parte um.", "Parte dois."]
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        path = f.name
    try:
        export_to_txt(chunks, path)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "Parte um." in content
        assert "Parte dois." in content
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_export_to_pdf_creates_file():
    chunks = ["Conteúdo traduzido.", "Mais conteúdo."]
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        path = f.name
    try:
        export_to_pdf(chunks, path)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 100
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_export_to_pdf_empty():
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        path = f.name
    try:
        export_to_pdf([], path)
        assert os.path.exists(path)
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_export_to_epub_creates_file():
    chunks = ["Capítulo um.", "Capítulo dois."]
    with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
        path = f.name
    try:
        export_to_epub(chunks, path, title="Teste")
        assert os.path.exists(path)
        assert os.path.getsize(path) > 100
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_export_to_epub_empty():
    import time
    path = os.path.join(tempfile.gettempdir(), f"test_empty_{time.time()}.epub")
    try:
        export_to_epub([], path, title="Vazio")
        assert os.path.exists(path)
    finally:
        if os.path.exists(path):
            time.sleep(0.1)
            try:
                os.unlink(path)
            except PermissionError:
                pass


def test_export_to_pdf_with_markup():
    chunks = [
        "# Título Principal\n\n**Negrito** e *itálico* e ***ambos***\n\nTexto normal com `código`.\n\n---",
    ]
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        path = f.name
    try:
        export_to_pdf(chunks, path)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 200
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_export_to_epub_with_markup():
    import time
    chunks = [
        "# Capítulo 1\n\n**Texto em negrito** preservado no EPUB.\n\n*Itálico* também funciona.",
    ]
    path = os.path.join(tempfile.gettempdir(), f"test_markup_epub_{time.time()}.epub")
    try:
        export_to_epub(chunks, path, title="Teste Markup")
        assert os.path.exists(path)
        assert os.path.getsize(path) > 200
    finally:
        if os.path.exists(path):
            time.sleep(0.1)
            try:
                os.unlink(path)
            except PermissionError:
                pass
