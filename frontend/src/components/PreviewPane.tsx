import { useEffect, useRef } from "react";

interface Props {
  text: string;
}

export default function PreviewPane({ text }: Props) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (ref.current) {
      ref.current.scrollTop = ref.current.scrollHeight;
    }
  }, [text]);

  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
      <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
        Prévia da tradução
      </h2>
      <div
        ref={ref}
        className="h-64 overflow-y-auto whitespace-pre-wrap text-sm text-gray-200 leading-relaxed font-mono"
      >
        {text || (
          <span className="text-gray-500 italic">Aguardando tokens...</span>
        )}
      </div>
    </div>
  );
}
