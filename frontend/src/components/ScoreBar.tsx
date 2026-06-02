interface ScoreBarProps {
  value: number;
  label?: string;
  dangerBelow?: number;
}

export function ScoreBar({ value, label, dangerBelow = 55 }: ScoreBarProps) {
  const color = value < dangerBelow ? 'bg-rose-400' : value < 75 ? 'bg-amber-300' : 'bg-cyan-300';
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-xs text-slate-400">
        <span>{label}</span>
        <span className="font-mono text-slate-200">{Math.round(value)}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-800">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${Math.max(3, Math.min(100, value))}%` }} />
      </div>
    </div>
  );
}
