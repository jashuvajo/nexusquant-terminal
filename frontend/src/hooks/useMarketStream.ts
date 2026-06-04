import { useEffect, useState } from 'react';
import type { MarketSymbol, StreamStatus, TerminalSnapshot } from '../types';

const apiUrl = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
const pollMs = Number(import.meta.env.VITE_POLL_MS ?? 3000);

interface StreamIssue {
  status: string;
  message: string;
}

function isVerifiedSnapshot(item: Partial<TerminalSnapshot> | undefined): item is TerminalSnapshot {
  return Boolean(
    item?.dataSource === 'UPSTOX_REALTIME_REST'
    && item?.upstoxConnection?.connected === true
    && item?.upstoxConnection?.marketDataVerified === true
    && item?.expiryState?.selectedExpiry,
  );
}

export function useMarketStream() {
  const [snapshot, setSnapshot] = useState<TerminalSnapshot | null>(null);
  const [snapshots, setSnapshots] = useState<Partial<Record<MarketSymbol, TerminalSnapshot>>>({});
  const [status, setStatus] = useState<StreamStatus>('connecting');
  const [issue, setIssue] = useState<StreamIssue | null>(null);

  useEffect(() => {
    let disposed = false;
    let timer: number | undefined;
    let inFlight = false;
    let failures = 0;

    const handlePayload = (payload: Record<string, unknown>) => {
      const incoming = (payload.snapshots ?? {}) as Partial<Record<MarketSymbol, TerminalSnapshot>>;
      const verifiedEntries = Object.entries(incoming).filter(([, item]) => isVerifiedSnapshot(item)) as Array<[MarketSymbol, TerminalSnapshot]>;

      if (verifiedEntries.length === 0) {
        setSnapshot(null);
        setSnapshots({});
        setStatus('status');
        const errors = payload.symbolErrors as Record<string, string> | undefined;
        setIssue({
          status: 'WAITING_FOR_UPSTOX_DATA',
          message: errors ? Object.entries(errors).map(([symbol, error]) => `${symbol}: ${error}`).join('; ') : 'No verified NIFTY/SENSEX Upstox market-data snapshots yet.',
        });
        return;
      }

      const nextSnapshots = Object.fromEntries(verifiedEntries) as Partial<Record<MarketSymbol, TerminalSnapshot>>;
      setSnapshots(nextSnapshots);
      const displaySymbol = payload.displaySymbol as MarketSymbol | undefined;
      setSnapshot((displaySymbol && nextSnapshots[displaySymbol]) || nextSnapshots.NIFTY || nextSnapshots.SENSEX || verifiedEntries[0][1]);
      setStatus('live');
      setIssue(null);
    };

    const poll = async () => {
      if (disposed || inFlight) return;
      inFlight = true;
      try {
        const response = await fetch(`${apiUrl}/api/market/snapshots`, {
          method: 'GET',
          headers: { Accept: 'application/json' },
          cache: 'no-store',
        });
        const payload = await response.json();
        if (!response.ok) {
          failures += 1;
          setStatus('status');
          setIssue({
            status: payload.detail ? 'UPSTOX_DATA_ERROR' : 'POLLING_ERROR',
            message: typeof payload.detail === 'string' ? payload.detail : JSON.stringify(payload.detail ?? payload),
          });
          return;
        }
        failures = 0;
        handlePayload(payload as Record<string, unknown>);
      } catch (error) {
        failures += 1;
        setStatus(failures > 3 ? 'error' : 'connecting');
        setIssue({
          status: 'HTTP_POLL_RECONNECTING',
          message: `HTTP polling stream failed (${error instanceof Error ? error.message : String(error)}). Retrying every ${Math.round(pollMs / 1000)}s.`,
        });
      } finally {
        inFlight = false;
        if (!disposed) timer = window.setTimeout(poll, pollMs);
      }
    };

    window.setTimeout(() => {
      if (disposed) return;
      setStatus('connecting');
      setIssue({ status: 'HTTP_POLLING_STREAM', message: 'Using HTTP polling stream for stable Railway/Vercel connectivity. No WebSocket required.' });
      void poll();
    }, 0);

    return () => {
      disposed = true;
      if (timer) window.clearTimeout(timer);
    };
  }, []);

  return { snapshot, snapshots, status, issue };
}
