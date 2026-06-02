import { Card } from './Card';
import type { TerminalSnapshot } from '../types';

interface HeatmapTerminalProps {
  snapshot: TerminalSnapshot;
}

function cellColor(liquidity: number, absorption: number, sweepRisk: number) {
  if (sweepRisk > 72) return 'from-rose-500/50 to-orange-500/10 border-rose-300/30';
  if (liquidity > 78 && absorption > 68) return 'from-cyan-400/50 to-emerald-400/10 border-cyan-300/40';
  if (liquidity > 70) return 'from-blue-400/35 to-cyan-400/10 border-blue-300/30';
  return 'from-slate-700/70 to-slate-900/50 border-slate-700/70';
}

export function HeatmapTerminal({ snapshot }: HeatmapTerminalProps) {
  return (
    <Card title="Institutional Liquidity Heatmap" eyebrow="Clusters, gamma walls, stop density, sweep zones">
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
        {snapshot.heatmap.map((cell) => (
          <div key={cell.id} className={`rounded-2xl border bg-gradient-to-br p-3 ${cellColor(cell.liquidity, cell.absorption, cell.sweepRisk)}`}>
            <div className="flex items-center justify-between">
              <p className="font-mono text-sm font-bold text-white">{cell.strike}</p>
              <span className="rounded-full bg-black/30 px-2 py-0.5 text-[10px] font-bold text-slate-200">{cell.side}</span>
            </div>
            <p className="mt-1 text-[11px] uppercase tracking-[0.18em] text-slate-300">{cell.label}</p>
            <div className="mt-3 space-y-2 text-xs">
              <div className="flex justify-between"><span className="text-slate-400">Liquidity</span><span>{cell.liquidity}</span></div>
              <div className="flex justify-between"><span className="text-slate-400">Absorption</span><span>{cell.absorption}</span></div>
              <div className="flex justify-between"><span className="text-slate-400">Gamma</span><span>{cell.gammaWall}</span></div>
              <div className="flex justify-between"><span className="text-slate-400">SL Density</span><span>{cell.stopDensity}</span></div>
              <div className="h-1.5 overflow-hidden rounded-full bg-black/30"><div className="h-full rounded-full bg-cyan-200" style={{ width: `${cell.sweepRisk}%` }} /></div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
