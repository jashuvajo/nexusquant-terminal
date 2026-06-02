import { useEffect, useRef, useState } from 'react';
import { createMockSnapshot } from '../data/mockMarket';
import type { StreamStatus, TerminalSnapshot } from '../types';

const defaultWsUrl = import.meta.env.VITE_WS_URL ?? 'ws://localhost:8000/ws/market';

export function useMarketStream() {
  const [snapshot, setSnapshot] = useState<TerminalSnapshot>(() => createMockSnapshot(1));
  const [status, setStatus] = useState<StreamStatus>('connecting');
  const tickRef = useRef(1);

  useEffect(() => {
    let closed = false;
    let fallbackTimer: number | undefined;
    let fallbackStarted = false;
    let socket: WebSocket | undefined;

    const startFallback = () => {
      if (fallbackStarted || closed) return;
      fallbackStarted = true;
      setStatus('fallback');
      fallbackTimer = window.setInterval(() => {
        tickRef.current += 1;
        setSnapshot(createMockSnapshot(tickRef.current));
      }, 1000);
    };

    const fallbackTimeout = window.setTimeout(startFallback, 1800);

    try {
      socket = new WebSocket(defaultWsUrl);
      socket.onopen = () => {
        window.clearTimeout(fallbackTimeout);
        setStatus('live');
      };
      socket.onmessage = (event) => {
        try {
          setSnapshot(JSON.parse(event.data) as TerminalSnapshot);
        } catch (error) {
          console.warn('Invalid market snapshot received', error);
        }
      };
      socket.onerror = startFallback;
      socket.onclose = () => {
        if (!closed) startFallback();
      };
    } catch {
      startFallback();
    }

    return () => {
      closed = true;
      window.clearTimeout(fallbackTimeout);
      if (fallbackTimer) window.clearInterval(fallbackTimer);
      socket?.close();
    };
  }, []);

  return { snapshot, status };
}
