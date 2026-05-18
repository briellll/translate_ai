import { useState } from "react";

interface Props {
  apiKey: string;
  onApiKeyChange: (key: string) => void;
  disabled: boolean;
  translating: boolean;
  onTranslate: (config: {
    model: string;
    chunk_chars: number;
    temperature: number;
    out_format: string;
  }) => void;
  onCancel: () => void;
}

export default function ConfigForm({
  apiKey,
  onApiKeyChange,
  disabled,
  translating,
  onTranslate,
  onCancel,
}: Props) {
  const [model, setModel] = useState("gpt-4o-mini");
  const [chunkChars, setChunkChars] = useState(4000);
  const [temperature, setTemperature] = useState(0);
  const [outFormat, setOutFormat] = useState<"pdf" | "epub" | "txt">("pdf");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onTranslate({ model, chunk_chars: chunkChars, temperature, out_format: outFormat });
  };

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border border-gray-800 bg-gray-900 p-5 space-y-4">
      <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">
        Configuração
      </h2>

      <div>
        <label className="block text-xs text-gray-400 mb-1">API Key</label>
        <p className="text-xs text-gray-500 mb-1">Sua chave da OpenAI. Começa com <code className="text-gray-400">sk-</code>. Fica salva só nesta sessão.</p>
        <input
          type="password"
          value={apiKey}
          onChange={(e) => onApiKeyChange(e.target.value)}
          placeholder="sk-..."
          disabled={translating}
          className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm outline-none focus:border-green-500 transition-colors disabled:opacity-50"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs text-gray-400 mb-1">Modelo</label>
          <p className="text-xs text-gray-500 mb-1">Modelo OpenAI usado na tradução. Ex: <code className="text-gray-400">gpt-4o-mini</code>, <code className="text-gray-400">gpt-4o</code>, <code className="text-gray-400">gpt-4-turbo</code>.</p>
          <input
            type="text"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            disabled={translating}
            placeholder="gpt-4o-mini"
            className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm outline-none focus:border-green-500 transition-colors disabled:opacity-50"
          />
        </div>

        <div>
          <label className="block text-xs text-gray-400 mb-1">Formato de saída</label>
          <p className="text-xs text-gray-500 mb-1">Formato do arquivo traduzido. PDF preserva layout, EPUB para leitores digitais, TXT para texto puro.</p>
          <select
            value={outFormat}
            onChange={(e) => setOutFormat(e.target.value as any)}
            disabled={translating}
            className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm outline-none focus:border-green-500 transition-colors disabled:opacity-50"
          >
            <option value="pdf">PDF</option>
            <option value="epub">EPUB</option>
            <option value="txt">TXT</option>
          </select>
        </div>

        <div>
          <label className="block text-xs text-gray-400 mb-1">
            Chars por chunk: {chunkChars}
          </label>
          <p className="text-xs text-gray-500 mb-1">Quanto maior, mais texto é enviado por requisição. Reduza se o modelo demorar ou der erro de limite de tokens.</p>
          <input
            type="range"
            min={1000}
            max={10000}
            step={500}
            value={chunkChars}
            onChange={(e) => setChunkChars(Number(e.target.value))}
            disabled={translating}
            className="w-full accent-green-500 disabled:opacity-50"
          />
        </div>

        <div>
          <label className="block text-xs text-gray-400 mb-1">
            Temperature: {temperature.toFixed(1)}
          </label>
          <p className="text-xs text-gray-500 mb-1">Controla a criatividade da tradução. 0 = mais literal/padrão, 2 = mais criativo/livre.</p>
          <input
            type="range"
            min={0}
            max={2}
            step={0.1}
            value={temperature}
            onChange={(e) => setTemperature(Number(e.target.value))}
            disabled={translating}
            className="w-full accent-green-500 disabled:opacity-50"
          />
        </div>
      </div>

      <div className="flex gap-3 pt-2">
        {!translating ? (
          <button
            type="submit"
            disabled={disabled || !apiKey}
            className="rounded-lg bg-green-600 px-6 py-2 text-sm font-medium hover:bg-green-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Iniciar tradução
          </button>
        ) : (
          <button
            type="button"
            onClick={onCancel}
            className="rounded-lg bg-red-600 px-6 py-2 text-sm font-medium hover:bg-red-500 transition-colors"
          >
            Cancelar
          </button>
        )}
      </div>
    </form>
  );
}
