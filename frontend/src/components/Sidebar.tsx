import type { LucideIcon } from 'lucide-react';
import { Activity, BarChart3, Bot, BrainCircuit, DatabaseZap, Gauge, History, LineChart, Network, Radar, Route, Settings, ShieldCheck, WalletCards } from 'lucide-react';

export type ModuleId =
  | 'execution'
  | 'heatmap'
  | 'orderflow'
  | 'ai'
  | 'greeks'
  | 'strategy'
  | 'portfolio'
  | 'risk'
  | 'infra'
  | 'analytics'
  | 'journal'
  | 'session'
  | 'backtesting'
  | 'settings';

interface NavItem {
  id: ModuleId;
  label: string;
  icon: LucideIcon;
}

export const navItems: NavItem[] = [
  { id: 'execution', label: 'Execution HUD', icon: Gauge },
  { id: 'heatmap', label: 'Heatmap Terminal', icon: Radar },
  { id: 'orderflow', label: 'Orderflow Analytics', icon: Activity },
  { id: 'ai', label: 'AI Matrix', icon: BrainCircuit },
  { id: 'greeks', label: 'Greeks & IV', icon: LineChart },
  { id: 'strategy', label: 'Strategy Router', icon: Route },
  { id: 'portfolio', label: 'Upstox Portfolio', icon: WalletCards },
  { id: 'risk', label: 'Risk Engine', icon: ShieldCheck },
  { id: 'infra', label: 'Infrastructure Telemetry', icon: Network },
  { id: 'analytics', label: 'AI Analytics', icon: Bot },
  { id: 'journal', label: 'Trade Journal', icon: DatabaseZap },
  { id: 'session', label: 'Session Intelligence', icon: BarChart3 },
  { id: 'backtesting', label: 'Backtesting', icon: History },
  { id: 'settings', label: 'Settings', icon: Settings },
];

interface SidebarProps {
  active: ModuleId;
  onChange: (module: ModuleId) => void;
}

export function Sidebar({ active, onChange }: SidebarProps) {
  return (
    <aside className="glass-panel sticky top-4 hidden h-[calc(100vh-2rem)] w-72 shrink-0 rounded-3xl p-4 lg:block">
      <div className="mb-7 border-b border-slate-700/60 pb-5">
        <p className="text-[10px] font-semibold uppercase tracking-[0.42em] text-cyan-300">NexusQuant</p>
        <h1 className="mt-2 text-xl font-black uppercase tracking-[0.18em] text-white">Institutional Terminal</h1>
        <p className="mt-2 text-xs leading-5 text-slate-400">AI orderflow execution stack for NIFTY and SENSEX index options.</p>
      </div>
      <nav className="custom-scrollbar flex max-h-[calc(100vh-13rem)] flex-col gap-1 overflow-y-auto pr-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const selected = active === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onChange(item.id)}
              className={`group flex items-center gap-3 rounded-2xl px-3 py-2.5 text-left text-sm transition ${
                selected
                  ? 'bg-cyan-400/15 text-cyan-100 shadow-[inset_0_0_0_1px_rgba(103,232,249,0.28)]'
                  : 'text-slate-400 hover:bg-slate-800/70 hover:text-slate-100'
              }`}
            >
              <Icon className={`h-4 w-4 ${selected ? 'text-cyan-300' : 'text-slate-500 group-hover:text-cyan-300'}`} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
