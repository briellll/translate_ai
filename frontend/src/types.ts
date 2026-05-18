export interface ProgressData {
  idx: number;
  total: number;
  elapsed: number;
  eta: number;
  avg_per_part: number;
  speed_parts_per_min: number;
}

export interface TaskStatus {
  status: "pending" | "running" | "completed" | "cancelled" | "error";
  error?: string | null;
  task_id?: string;
}

export interface TranslationConfig {
  api_key: string;
  out_format: "pdf" | "epub" | "txt";
  model: string;
  chunk_chars: number;
  temperature: number;
  top_p: number;
  max_tokens: number | null;
  parallel_chunks: number;
}
