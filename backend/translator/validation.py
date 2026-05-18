import os

from .types import TranslationConfig
from .logger import get_logger

logger = get_logger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".epub"}
ALLOWED_OUT_FORMATS = {"pdf", "epub", "txt"}
MAX_FILE_SIZE_MB = 200


def validate_config(cfg: TranslationConfig) -> list[str]:
    errors: list[str] = []

    if not cfg.input_path:
        errors.append("Caminho do arquivo de entrada não informado.")
    elif not os.path.exists(cfg.input_path):
        errors.append(f"Arquivo não encontrado: {cfg.input_path}")
    else:
        ext = os.path.splitext(cfg.input_path)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            errors.append(f"Formato '{ext}' não suportado. Use {', '.join(sorted(ALLOWED_EXTENSIONS))}.")
        else:
            size_mb = os.path.getsize(cfg.input_path) / (1024 * 1024)
            if size_mb > MAX_FILE_SIZE_MB:
                errors.append(f"Arquivo muito grande ({size_mb:.0f} MB). Limite: {MAX_FILE_SIZE_MB} MB.")
            elif size_mb > 50:
                logger.warning("Arquivo grande (%d MB). A tradução pode demorar.", size_mb)

    if not cfg.api_key:
        errors.append("API key da OpenAI não informada.")
    elif not cfg.api_key.startswith("sk-"):
        errors.append("API key parece inválida (deve começar com 'sk-').")

    if cfg.out_format not in ALLOWED_OUT_FORMATS:
        errors.append(f"Formato de saída '{cfg.out_format}' inválido. Use {', '.join(sorted(ALLOWED_OUT_FORMATS))}.")

    if cfg.temperature < 0 or cfg.temperature > 2:
        errors.append("Temperature deve estar entre 0 e 2.")

    if cfg.top_p < 0 or cfg.top_p > 1:
        errors.append("Top_p deve estar entre 0 e 1.")

    if cfg.chunk_chars < 500:
        errors.append("Chars por chunk deve ser no mínimo 500.")
    elif cfg.chunk_chars > 50000:
        errors.append("Chars por chunk deve ser no máximo 50000.")

    if not cfg.output_dir:
        errors.append("Pasta de saída não informada.")
    elif not os.path.isdir(cfg.output_dir):
        errors.append(f"Pasta de saída não existe: {cfg.output_dir}")

    return errors
