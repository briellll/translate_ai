from typing import List
from pypdf import PdfReader
from pypdf.errors import PdfStreamError, WrongPasswordError, FileNotDecryptedError, EmptyFileError, PyPdfError


def extract_text_from_pdf(path: str) -> List[str]:
    pages = []
    try:
        reader = PdfReader(path)
    except FileNotFoundError:
        raise
    except (WrongPasswordError, FileNotDecryptedError):
        raise ValueError("PDF protegido por senha. Remova a senha antes de traduzir.")
    except EmptyFileError:
        raise ValueError("PDF vazio.")
    except PdfStreamError:
        raise ValueError("PDF corrompido ou inválido. Verifique o arquivo.")
    except PyPdfError as exc:
        raise ValueError(f"Erro ao ler PDF: {exc}")
    except Exception as exc:
        raise ValueError(f"Não foi possível abrir o PDF: {exc}")

    if not reader.pages:
        raise ValueError("PDF vazio — nenhuma página encontrada.")

    for i, p in enumerate(reader.pages):
        try:
            text = p.extract_text() or ""
            if not text.strip():
                text = ""
            pages.append(text)
        except Exception:
            pages.append("")

    if all(p == "" for p in pages):
        raise ValueError(
            "Nenhum texto extraível encontrado no PDF. "
            "Pode ser um PDF escaneado (imagem). "
            "Tente usar um arquivo com texto selecionável."
        )

    return pages
