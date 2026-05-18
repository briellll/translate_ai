import { useState, useMemo } from "react";
import { PROVIDERS, type Provider } from "../types";

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
    base_url: string | null;
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
  const [provider, setProvider] = useState<Provider>(PROVIDERS[0]);
  const [model, setModel] = useState(provider.models[0] || "");
  const [customModel, setCustomModel] = useState("");
  const [customBaseUrl, setCustomBaseUrl] = useState("");
  const [chunkChars, setChunkChars] = useState(4000);
  const [temperature, setTemperature] = useState(0);
  const [outFormat, setOutFormat] = useState<"pdf" | "epub" | "txt">("pdf");

  const isCustom = provider.id === "custom";
  const activeModel = isCustom ? customModel : model;

  const baseUrlError = isCustom && customBaseUrl.length > 0
    ? (!customBaseUrl.startsWith("http://") && !customBaseUrl.startsWith("https://")
      ? "URL deve começar com http:// ou https://"
      : !customBaseUrl.endsWith("/v1")
        ? "A maioria das APIs espera URL terminando em /v1"
        : "")
    : "";

  const handleProviderChange = (id: string) => {
    const p = PROVIDERS.find((pr) => pr.id === id) || PROVIDERS[0];
    setProvider(p);
    if (p.models.length > 0) {
      setModel(p.models[0]);
    } else {
      setCustomModel("");
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const baseUrl = isCustom ? customBaseUrl || null : provider.base_url || null;
    onTranslate({
      model: activeModel,
      chunk_chars: chunkChars,
      temperature,
      out_format: outFormat,
      base_url: baseUrl,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border border-gray-800 bg-gray-900 p-5 space-y-4">
      <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">
        Configuração
      </h2>

      <div>
        <label className="block text-xs text-gray-400 mb-1">API Key</label>
        <p className="text-xs text-gray-500 mb-1">
          Chave de API do provedor escolhido. Fica salva só nesta sessão.
        </p>
        <input
          type="password"
          value={apiKey}
          onChange={(e) => onApiKeyChange(e.target.value)}
          placeholder={provider.id === "openai" ? "sk-..." : "Chave da API..."}
          disabled={translating}
          className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm outline-none focus:border-green-500 transition-colors disabled:opacity-50"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs text-gray-400 mb-1">Provedor</label>
          <p className="text-xs text-gray-500 mb-1">Serviço de IA que processará a tradução.</p>
          <select
            value={provider.id}
            onChange={(e) => handleProviderChange(e.target.value)}
            disabled={translating}
            className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm outline-none focus:border-green-500 transition-colors disabled:opacity-50"
          >
            {PROVIDERS.map((p) => (
              <option key={p.id} value={p.id}>{p.label}</option>
            ))}
          </select>
        </div>

        <div>
          {isCustom ? (
            <>
              <label className="block text-xs text-gray-400 mb-1">Modelo</label>
              <p className="text-xs text-gray-500 mb-1">Digite o nome do modelo compatível com a URL informada.</p>
              <input
                type="text"
                value={customModel}
                onChange={(e) => setCustomModel(e.target.value)}
                placeholder="ex: gpt-4o-mini"
                disabled={translating}
                className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm outline-none focus:border-green-500 transition-colors disabled:opacity-50"
              />
            </>
          ) : (
            <>
              <label className="block text-xs text-gray-400 mb-1">Modelo</label>
              <p className="text-xs text-gray-500 mb-1">Modelo do provedor usado na tradução.</p>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                disabled={translating || provider.models.length === 0}
                className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm outline-none focus:border-green-500 transition-colors disabled:opacity-50"
              >
                {provider.models.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </>
          )}
        </div>

        {isCustom && (
          <div className="md:col-span-2">
            <label className="block text-xs text-gray-400 mb-1">URL base da API</label>
            <p className="text-xs text-gray-500 mb-1">Endpoint compatível com OpenAI. Ex: <code className="text-gray-400">https://api.seuservico.com/v1</code>. URL errada resulta em erro de conexão.</p>
            <input
              type="text"
              value={customBaseUrl}
              onChange={(e) => setCustomBaseUrl(e.target.value)}
              placeholder="https://api.seuservico.com/v1"
              disabled={translating}
              className={`w-full rounded-lg border px-3 py-2 text-sm outline-none transition-colors disabled:opacity-50 ${
                baseUrlError && customBaseUrl.length > 0
                  ? "border-yellow-600 bg-gray-800 focus:border-yellow-500"
                  : "border-gray-700 bg-gray-800 focus:border-green-500"
              }`}
            />
            {baseUrlError && (
              <p className="text-xs text-yellow-400 mt-1">{baseUrlError}</p>
            )}
          </div>
        )}

        {!isCustom && provider.base_url && (
          <div className="md:col-span-2">
            <p className="text-xs text-gray-500">
              URL: <code className="text-gray-400">{provider.base_url}</code>
            </p>
          </div>
        )}

        <div>
          <label className="block text-xs text-gray-400 mb-1">Formato de saída</label>
          <p className="text-xs text-gray-500 mb-1">PDF preserva layout, EPUB para leitores, TXT puro.</p>
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
          <p className="text-xs text-gray-500 mb-1">O documento é dividido em partes (chunks) para tradução. Cada chunk é enviado separadamente para a API. Valor maior = menos requisições, mas mais risco de estourar o limite de tokens do modelo. Reduza se o modelo demorar muito ou der erro de contexto. Valor menor = mais requisições, mas cada uma processa mais rápido.</p>
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
          <p className="text-xs text-gray-500 mb-1">0 = mais literal, 2 = mais criativo.</p>
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
            disabled={disabled || !apiKey || !activeModel || !!baseUrlError}
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
