import { Card } from './Card';
import { MetricCard } from './MetricCard';
import { ScoreBar } from './ScoreBar';
import type { TerminalSnapshot } from '../types';
import { formatCurrency, formatPct } from '../utils/format';

interface ExecutionHudProps {
  snapshot: TerminalSnapshot;
}

export function ExecutionHud({ snapshot }: ExecutionHudProps) {
  return (
    <div className="grid gap-4 xl:grid-cols-12">
      <div className="grid gap-3 sm:grid-cols-2 xl:col-span-7 xl:grid-cols-4">
        <MetricCard label="AI Confidence" value={`${snapshot.aiConfidence}%`} helper="Multi-engine consensus" tone="cyan" />
        <MetricCard label="Live PnL" value={formatCurrency(snapshot.pnl)} helper="Realized + unrealized" tone="emerald" />
        <MetricCard label="Delta Velocity" value={snapshot.deltaVelocity} helper="Aggressor pressure" tone="violet" />
        <MetricCard label="Spread Quality" value={`${snapshot.spreadQuality}%`} helper={`${snapshot.executionLatencyMs} ms routing`} tone="amber" />
        <MetricCard label="Current ATM" value={snapshot.atmStrike} helper={snapshot.premiumFocusZone} tone="cyan" />
        <MetricCard label="Exposure" value={formatPct(snapshot.liveExposurePct)} helper={`Max ${snapshot.risk.maxExposurePct}%`} tone="emerald" />
        <MetricCard label="Vol Regime" value={snapshot.volatilityRegime.replaceAll('_', ' ')} helper="IV adaptive sizing" tone="violet" />
        <MetricCard label="Trail State" value={snapshot.trailingStopState} helper="ATR/orderflow managed" tone={snapshot.risk.safeMode ? 'rose' : 'cyan'} />
      </div>
      <Card title="Active Trades" eyebrow="Automated trade management" className="xl:col-span-5">
        <div className="space-y-4">
          {snapshot.activeTrades.map((trade) => (
            <div key={trade.id} className="rounded-2xl border border-slate-700/70 bg-slate-950/50 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-bold text-white">{trade.id}</p>
                  <p className="text-xs text-slate-400">{trade.symbol} {trade.strike} {trade.side} | Qty {trade.qty}</p>
                </div>
                <span className="rounded-full bg-cyan-300/10 px-3 py-1 text-xs font-bold text-cyan-200">{trade.status.replaceAll('_', ' ')}</span>
              </div>
              <div className="mt-4 grid grid-cols-4 gap-3 text-xs">
                <div><p className="text-slate-500">Entry</p><p className="font-mono text-slate-100">{trade.entry}</p></div>
                <div><p className="text-slate-500">LTP</p><p className="font-mono text-slate-100">{trade.ltp}</p></div>
                <div><p className="text-slate-500">Stop</p><p className="font-mono text-rose-200">{trade.stop}</p></div>
                <div><p className="text-slate-500">Target</p><p className="font-mono text-emerald-200">{trade.target}</p></div>
              </div>
              <div className="mt-4 flex items-center justify-between text-sm">
                <span className="text-slate-400">PnL</span>
                <span className={trade.pnl >= 0 ? 'font-bold text-emerald-300' : 'font-bold text-rose-300'}>{formatCurrency(trade.pnl)}</span>
              </div>
              <div className="mt-3"><ScoreBar label="Trade Quality Score" value={trade.tqs} /></div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
