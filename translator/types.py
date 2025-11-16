from dataclasses import dataclass


@dataclass
class TranslationConfig:
    input_path: str
    output_dir: str
    out_format: str  # 'pdf' | 'epub' | 'txt'
    chunk_chars: int = 4000
    model: str = "gpt-4o-mini"
    api_key: str | None = None


@dataclass
class ProgressStats:
    idx: int
    total: int
    elapsed: float
    eta: float
    avg_per_part: float
    speed_parts_per_min: float

