import { useRef, useState, type DragEvent } from "react";

interface Props {
  file: File | null;
  disabled: boolean;
  onUpload: (file: File) => void;
  onRemove: () => void;
}

export default function FileUpload({ file, disabled, onUpload, onRemove }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f && (f.name.endsWith(".pdf") || f.name.endsWith(".epub"))) {
      onUpload(f);
    }
  };

  const handleChange = () => {
    const f = inputRef.current?.files?.[0];
    if (f) onUpload(f);
  };

  if (file) {
    return (
      <div className="flex items-center gap-3 rounded-lg border border-green-700 bg-green-950/30 p-4">
        <span className="text-green-400 text-lg">📄</span>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate">{file.name}</p>
          <p className="text-xs text-gray-400">
            {(file.size / 1024).toFixed(0)} KB
          </p>
        </div>
        <button
          onClick={onRemove}
          className="text-sm text-gray-400 hover:text-red-400 transition-colors"
        >
          Remover
        </button>
      </div>
    );
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => !disabled && inputRef.current?.click()}
      className={`cursor-pointer rounded-lg border-2 border-dashed p-8 text-center transition-colors ${
        dragging
          ? "border-green-400 bg-green-950/30"
          : "border-gray-700 hover:border-gray-500"
      } ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.epub"
        className="hidden"
        onChange={handleChange}
        disabled={disabled}
      />
      <p className="text-sm text-gray-400">
        Arraste um arquivo PDF ou EPUB aqui ou clique para selecionar
      </p>
      <p className="text-xs text-gray-500 mt-2">
        Formatos aceitos: <code className="text-gray-400">.pdf</code> e <code className="text-gray-400">.epub</code>.
        PDFs escaneados (imagem) <strong className="text-yellow-400">não funcionam</strong>.
        A formatação original (negrito, itálico, tabelas, imagens) <strong className="text-yellow-400">não é preservada</strong> na saída.
        Para melhor resultado, prefira <code className="text-gray-400">EPUB</code> (formatação básica preservada).
      </p>
    </div>
  );
}
