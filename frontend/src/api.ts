const API_BASE = "/api";

export async function uploadFile(file: File): Promise<{ file_id: string; filename: string }> {
  const form = new FormData();
  form.append("file", file);

  const resp = await fetch(`${API_BASE}/upload`, { method: "POST", body: form });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: "Erro no upload" }));
    throw new Error(err.detail || "Erro no upload");
  }
  return resp.json();
}

export async function startTranslation(config: {
  file_id: string;
  api_key: string;
  out_format: string;
  model: string;
  chunk_chars: number;
  temperature: number;
  top_p: number;
  max_tokens: number | null;
  parallel_chunks: number;
  base_url: string | null;
}, signal?: AbortSignal): Promise<{ task_id: string }> {
  const resp = await fetch(`${API_BASE}/translate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
    signal,
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: "Erro ao iniciar tradução" }));
    throw new Error(err.detail || "Erro ao iniciar tradução");
  }
  return resp.json();
}

export async function cancelTranslation(taskId: string): Promise<void> {
  await fetch(`${API_BASE}/translate/${taskId}/cancel`, { method: "POST" });
}

export function getDownloadUrl(taskId: string): string {
  return `${API_BASE}/download/${taskId}`;
}

export function createTranslationStream(
  taskId: string,
  onToken: (text: string) => void,
  onProgress: (data: ProgressData) => void,
  onResult: (status: TaskStatus) => void,
  onError: (err: Error) => void,
): AbortController {
  const controller = new AbortController();

  fetch(`${API_BASE}/translate/${taskId}`, { signal: controller.signal })
    .then(async (resp) => {
      if (!resp.ok) {
        onError(new Error("Falha ao conectar ao stream"));
        return;
      }

      const reader = resp.body?.getReader();
      if (!reader) {
        onError(new Error("Stream não disponível"));
        return;
      }

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        let currentEvent = "";
        for (const line of lines) {
          if (line.startsWith("event: ")) {
            currentEvent = line.slice(7).trim();
          } else if (line.startsWith("data: ")) {
            const raw = line.slice(6);
            try {
              const data = JSON.parse(raw);

              switch (currentEvent) {
                case "token":
                  onToken(data.text);
                  break;
                case "progress":
                  onProgress(data as ProgressData);
                  break;
                case "result":
                  onResult(data as TaskStatus);
                  break;
              }
            } catch {
              // ignore parse errors in SSE
            }
          }
        }
      }
    })
    .catch((err) => {
      if (err.name !== "AbortError") {
        onError(err);
      }
    });

  return controller;
}
