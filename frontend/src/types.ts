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
  base_url: string | null;
}

export interface Provider {
  id: string;
  label: string;
  models: string[];
  base_url: string;
}

export const PROVIDERS: Provider[] = [
  {
    id: "openai",
    label: "OpenAI",
    models: ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "o3-mini"],
    base_url: "",
  },
  {
    id: "groq",
    label: "Groq",
    models: ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"],
    base_url: "https://api.groq.com/openai/v1",
  },
  {
    id: "together",
    label: "Together AI",
    models: ["mistralai/Mixtral-8x7B-Instruct-v0.1", "meta-llama/Llama-3.3-70B-Instruct-Turbo"],
    base_url: "https://api.together.xyz/v1",
  },
  {
    id: "deepseek",
    label: "DeepSeek",
    models: ["deepseek-chat", "deepseek-reasoner"],
    base_url: "https://api.deepseek.com/v1",
  },
  {
    id: "custom",
    label: "Custom (URL própria)",
    models: [],
    base_url: "",
  },
];

