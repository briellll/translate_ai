const LIMITATIONS = [
  {
    icon: "📄",
    title: "PDF",
    items: [
      "Negrito, itálico, títulos e código → PRESERVADOS (detecção automática por fonte)",
      "Imagens, tabelas e layout visual → PERDIDOS",
      "PDF escaneado (imagem) → NÃO FUNCIONA (sem OCR)",
      "Numeração de páginas, cabeçalhos e rodapés → PODEM APARECER NO MEIO DO TEXTO",
    ],
  },
  {
    icon: "📖",
    title: "EPUB",
    items: [
      "Negrito, itálico, títulos e código → PRESERVADOS",
      "Estrutura de capítulos → PRESERVADA",
      "Imagens → IGNORADAS",
    ],
  },
  {
    icon: "⚙",
    title: "Gerais",
    items: [
      "Traduz APENAS para português",
      "Consome tokens da sua API (custo por uso — você fornece a chave)",
      "Pode cometer erros em jargões técnicos ou contextos ambíguos",
      "Limite de 200 MB por arquivo",
      "Textos muito longos (acima de ~50k tokens) podem falhar — reduza chars por chunk",
    ],
  },
];

interface Props {
  sidebar?: boolean;
}

export default function LimitationsBanner({ sidebar }: Props) {
  const content = (
    <div className="space-y-3">
      <p className="text-xs text-yellow-200/70 leading-relaxed">
        Esta ferramenta traduz o <strong>texto extraído</strong> do documento original.
        Toda formatação visual (negrito, itálico, fontes, cores, layout, imagens e tabelas)
        é descartada no processo de extração e <strong>não aparece</strong> no arquivo traduzido.
      </p>

      {LIMITATIONS.map((group) => (
        <div key={group.title}>
          <h4 className="text-xs font-semibold text-yellow-300 mb-1">
            {group.icon} {group.title}
          </h4>
          <ul className="space-y-0.5">
            {group.items.map((item, i) => {
              const isWarn = item.includes("PERDIDA") || item.includes("IGNORAD") || item.includes("NÃO FUNCIONA");
              const isInfo = item.includes("PRESERVADA");
              return (
                <li
                  key={i}
                  className={`text-xs pl-3 border-l-2 ${
                    isWarn
                      ? "border-red-700 text-red-200/80"
                      : isInfo
                      ? "border-green-700 text-green-200/80"
                      : "border-yellow-700 text-yellow-200/70"
                  }`}
                >
                  {item}
                </li>
              );
            })}
          </ul>
        </div>
      ))}

      <p className="text-xs text-yellow-200/50 pt-1">
        Para melhor resultado, use arquivos <strong>EPUB</strong> com texto selecionável,
        pois a formatação básica é preservada.
      </p>
    </div>
  );

  if (sidebar) {
    return (
      <div className="rounded-lg border border-yellow-800 bg-yellow-950/20 p-4">
        <h3 className="text-sm font-semibold text-yellow-300 mb-3 flex items-center gap-2">
          <span>⚠</span> Limitações
        </h3>
        {content}
      </div>
    );
  }

  return (
    <details className="rounded-lg border border-yellow-800 bg-yellow-950/20 lg:hidden">
      <summary className="flex items-center gap-2 px-4 py-3 text-sm text-yellow-300 cursor-pointer hover:bg-yellow-950/30 transition-colors">
        <span>⚠</span>
        <span className="flex-1 font-medium">Limitações da ferramenta</span>
      </summary>
      <div className="px-4 pb-4">
        {content}
      </div>
    </details>
  );
}
