import { Cell, PolarAngleAxis, RadialBar, RadialBarChart, ResponsiveContainer } from 'recharts';
import { Card } from './Card';
import { MetricCard } from './MetricCard';
import type { TerminalSnapshot } from '../types';

interface GreeksIvProps {
  snapshot: TerminalSnapshot;
}

export function GreeksIv({ snapshot }: GreeksIvProps) {
  const radial = [
    { name: 'IV Rank', value: snapshot.greeks.ivRank, fill: '#22d3ee' },
    { name: 'IV Percentile', value: snapshot.greeks.ivPercentile, fill: '#a78bfa' },
    { name: 'IV Expansion', value: snapshot.greeks.ivExpansion, fill: '#34d399' },
  ];

  return (
    <div className="grid gap-4 xl:grid-cols-2">
      <Card title="Options Greeks Engine" eyebrow="Delta, gamma, theta, vega intelligence">
        <div className="grid gap-3 sm:grid-cols-2">
          <MetricCard label="Delta" value={snapshot.greeks.delta} helper="Directional sensitivity" tone="cyan" />
          <MetricCard label="Gamma" value={snapshot.greeks.gamma} helper="Scalp convexity" tone="emerald" />
          <MetricCard label="Theta" value={snapshot.greeks.theta} helper="Decay pressure" tone="rose" />
          <MetricCard label="Vega" value={snapshot.greeks.vega} helper="IV sensitivity" tone="violet" />
        </div>
      </Card>
      <Card title="IV Intelligence" eyebrow="Rank, percentile, expansion">
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <RadialBarChart data={radial} innerRadius="22%" outerRadius="92%" startAngle={90} endAngle={-270}>
              <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
              <RadialBar background dataKey="value">
                {radial.map((entry) => <Cell key={entry.name} fill={entry.fill} />)}
              </RadialBar>
            </RadialBarChart>
          </ResponsiveContainer>
        </div>
        <div className="grid gap-2 text-sm text-slate-300">
          {radial.map((item) => (
            <div key={item.name} className="flex items-center justify-between rounded-xl bg-slate-950/60 px-3 py-2">
              <span>{item.name}</span><span className="font-mono text-white">{item.value}%</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
