import type { ReactNode } from 'react';

interface CardProps {
  title?: string;
  eyebrow?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function Card({ title, eyebrow, action, children, className = '' }: CardProps) {
  return (
    <section className={`glass-panel signal-line rounded-2xl p-4 ${className}`}>
      {(title || eyebrow || action) && (
        <div className="relative z-10 mb-4 flex items-start justify-between gap-4">
          <div>
            {eyebrow && <p className="text-[10px] font-semibold uppercase tracking-[0.32em] text-cyan-300/70">{eyebrow}</p>}
            {title && <h2 className="mt-1 text-sm font-semibold uppercase tracking-[0.18em] text-slate-100">{title}</h2>}
          </div>
          {action}
        </div>
      )}
      <div className="relative z-10">{children}</div>
    </section>
  );
}
