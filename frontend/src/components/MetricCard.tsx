import type { ReactNode } from 'react';

interface MetricCardProps {
  label: string;
  value: ReactNode;
  helper?: string;
  tone?: 'cyan' | 'emerald' | 'amber' | 'rose' | 'violet';
}

const toneMap = {
  cyan: 'from-cyan-400/25 to-blue-500/5 text-cyan-200 border-cyan-300/20',
  emerald: 'from-emerald-400/25 to-teal-500/5 text-emerald-200 border-emerald-300/20',
  amber: 'from-amber-400/25 to-orange-500/5 text-amber-200 border-amber-300/20',
  rose: 'from-rose-400/25 to-red-500/5 text-rose-200 border-rose-300/20',
  violet: 'from-violet-400/25 to-indigo-500/5 text-violet-200 border-violet-300/20',
};

export function MetricCard({ label, value, helper, tone = 'cyan' }: MetricCardProps) {
  return (
    <div className={`rounded-2xl border bg-gradient-to-br p-3 ${toneMap[tone]}`}>
      <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-slate-400">{label}</p>
      <div className="mt-2 text-2xl font-bold text-slate-50">{value}</div>
      {helper && <p className="mt-1 text-xs text-slate-400">{helper}</p>}
    </div>
  );
}
