import type { ProgressData } from "../types";

interface Props {
  data: ProgressData;
}

function fmt(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}m ${s}s`;
}

export default function ProgressPanel({ data }: Props) {
  const pct = data.total > 0 ? (data.idx / data.total) * 100 : 0;

  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900 p-4 space-y-3">
      <div className="flex items-center gap-3">
        <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-green-500 rounded-full transition-all duration-300"
            style={{ width: `${pct}%` }}
          />
        </div>
        <span className="text-xs text-gray-400 tabular-nums">
          {data.idx}/{data.total}
        </span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
        <div>
          <span className="text-gray-500">Decorrido</span>
          <p className="text-gray-200 tabular-nums">{fmt(data.elapsed)}</p>
        </div>
        <div>
          <span className="text-gray-500">ETA</span>
          <p className="text-gray-200 tabular-nums">{fmt(data.eta)}</p>
        </div>
        <div>
          <span className="text-gray-500">Média</span>
          <p className="text-gray-200 tabular-nums">{data.avg_per_part.toFixed(1)}s</p>
        </div>
        <div>
          <span className="text-gray-500">Velocidade</span>
          <p className="text-gray-200 tabular-nums">{data.speed_parts_per_min.toFixed(1)}/min</p>
        </div>
      </div>
    </div>
  );
}
