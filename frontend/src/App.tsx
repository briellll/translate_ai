import { useState, useCallback, useRef } from "react";
import { uploadFile, startTranslation, cancelTranslation, createTranslationStream, getDownloadUrl } from "./api";
import type { ProgressData, TaskStatus } from "./types";
import FileUpload from "./components/FileUpload";
import ConfigForm from "./components/ConfigForm";
import PreviewPane from "./components/PreviewPane";
import ProgressPanel from "./components/ProgressPanel";
import Toast from "./components/Toast";

type AppStatus = "idle" | "uploading" | "translating" | "completed" | "error";

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [fileId, setFileId] = useState<string | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [status, setStatus] = useState<AppStatus>("idle");
  const [translatedText, setTranslatedText] = useState("");
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [errorMsg, setErrorMsg] = useState("");
  const abortRef = useRef<AbortController | null>(null);

  const handleUpload = useCallback(async (f: File) => {
    setFile(f);
    setStatus("uploading");
    setErrorMsg("");
    try {
      const { file_id } = await uploadFile(f);
      setFileId(file_id);
      setStatus("idle");
    } catch (err: any) {
      setErrorMsg(err.message || "Falha no upload");
      setStatus("error");
    }
  }, []);

  const handleTranslate = useCallback(async (config: {
    model: string;
    chunk_chars: number;
    temperature: number;
    out_format: string;
  }) => {
    if (!fileId || !apiKey) return;

    setStatus("translating");
    setTranslatedText("");
    setProgress(null);
    setErrorMsg("");

    let tid = "";
    try {
      const { task_id } = await startTranslation({
        file_id: fileId,
        api_key: apiKey,
        out_format: config.out_format,
        model: config.model,
        chunk_chars: config.chunk_chars,
        temperature: config.temperature,
        top_p: 1.0,
        max_tokens: null,
        parallel_chunks: 1,
      });
      tid = task_id;
      setTaskId(tid);
    } catch (err: any) {
      setErrorMsg(err.message || "Falha ao iniciar tradução");
      setStatus("error");
      return;
    }

    abortRef.current = createTranslationStream(
      tid,
      (text) => setTranslatedText((prev) => prev + text),
      (data) => setProgress(data),
      (result) => {
        if (result.status === "completed") {
          setStatus("completed");
        } else if (result.status === "cancelled") {
          setStatus("idle");
        } else {
          setErrorMsg(result.error || "Erro na tradução");
          setStatus("error");
        }
      },
      (err) => {
        setErrorMsg(err.message);
        setStatus("error");
      },
    );
  }, [fileId, apiKey]);

  const handleCancel = useCallback(async () => {
    if (taskId) {
      abortRef.current?.abort();
      await cancelTranslation(taskId).catch(() => {});
      setStatus("idle");
    }
  }, [taskId]);

  const handleReset = useCallback(() => {
    setFile(null);
    setFileId(null);
    setTaskId(null);
    setTranslatedText("");
    setProgress(null);
    setStatus("idle");
    setErrorMsg("");
  }, []);

  const downloadUrl = taskId && status === "completed" ? getDownloadUrl(taskId) : null;

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-4 md:p-8">
      <div className="mx-auto max-w-4xl">
        <header className="mb-8">
          <h1 className="text-2xl font-bold text-green-400">Tradutor AI</h1>
          <p className="text-sm text-gray-400 mt-1">
            Traduza PDF ou EPUB para português usando OpenAI
          </p>
        </header>

        <div className="space-y-6">
          <FileUpload
            file={file}
            disabled={status === "translating"}
            onUpload={handleUpload}
            onRemove={handleReset}
          />

          <ConfigForm
            apiKey={apiKey}
            onApiKeyChange={setApiKey}
            disabled={!fileId || status === "translating"}
            translating={status === "translating"}
            onTranslate={handleTranslate}
            onCancel={handleCancel}
          />

          {progress && <ProgressPanel data={progress} />}

          {translatedText && <PreviewPane text={translatedText} />}

          {downloadUrl && (
            <div className="flex gap-3 items-center">
              <a
                href={downloadUrl}
                download
                className="inline-flex items-center gap-2 rounded-lg bg-green-600 px-4 py-2 text-sm font-medium hover:bg-green-500 transition-colors"
              >
                Baixar tradução
              </a>
              <button
                onClick={handleReset}
                className="rounded-lg border border-gray-600 px-4 py-2 text-sm font-medium hover:bg-gray-800 transition-colors"
              >
                Nova tradução
              </button>
            </div>
          )}

          {errorMsg && (
            <Toast message={errorMsg} onDismiss={() => setErrorMsg("")} />
          )}
        </div>
      </div>
    </div>
  );
}
