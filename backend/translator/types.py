from dataclasses import dataclass, field


@dataclass
class TranslationConfig:
    input_path: str
    output_dir: str
    out_format: str = "pdf"  # 'pdf' | 'epub' | 'txt'
    chunk_chars: int = 4000
    model: str = "gpt-4o-mini"
    api_key: str | None = None
    temperature: float = 0
    top_p: float = 1.0
    max_tokens: int | None = None
    parallel_chunks: int = 1  # >1 habilita tradução paralela
    task_id: str | None = None  # para persistência de progresso
    resume: bool = False


@dataclass
class ProgressStats:
    idx: int
    total: int
    elapsed: float
    eta: float
    avg_per_part: float
    speed_parts_per_min: float

