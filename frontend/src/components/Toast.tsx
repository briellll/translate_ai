interface Props {
  message: string;
  onDismiss: () => void;
}

export default function Toast({ message, onDismiss }: Props) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-red-800 bg-red-950/50 p-4">
      <span className="text-red-400 text-lg">⚠</span>
      <p className="flex-1 text-sm text-red-200">{message}</p>
      <button
        onClick={onDismiss}
        className="text-sm text-gray-400 hover:text-white transition-colors"
      >
        Fechar
      </button>
    </div>
  );
}
