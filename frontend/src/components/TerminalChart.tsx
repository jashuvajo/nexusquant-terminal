import { useEffect, useRef } from 'react';
import { ColorType, LineSeries, createChart, type IChartApi, type ISeriesApi, type Time } from 'lightweight-charts';
import { Card } from './Card';
import type { TerminalSnapshot } from '../types';

interface TerminalChartProps {
  snapshot: TerminalSnapshot;
}

export function TerminalChart({ snapshot }: TerminalChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Line'> | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const chart = createChart(containerRef.current, {
      height: 320,
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#94a3b8',
      },
      grid: {
        vertLines: { color: 'rgba(148, 163, 184, 0.08)' },
        horzLines: { color: 'rgba(148, 163, 184, 0.08)' },
      },
      rightPriceScale: { borderColor: 'rgba(148, 163, 184, 0.16)' },
      timeScale: { borderColor: 'rgba(148, 163, 184, 0.16)', timeVisible: true },
    });

    const series = chart.addSeries(LineSeries, {
      color: '#22d3ee',
      lineWidth: 2,
      crosshairMarkerVisible: true,
      lastValueVisible: true,
      priceLineVisible: true,
    });

    chartRef.current = chart;
    seriesRef.current = series;

    const resize = () => {
      if (containerRef.current) chart.applyOptions({ width: containerRef.current.clientWidth });
    };
    resize();
    window.addEventListener('resize', resize);
    return () => {
      window.removeEventListener('resize', resize);
      chart.remove();
    };
  }, []);

  useEffect(() => {
    if (!seriesRef.current) return;
    const baseTs = Math.floor(Date.now() / 1000) - snapshot.telemetry.length * 60;
    seriesRef.current.setData(
      snapshot.telemetry.map((point, index) => ({
        time: (baseTs + index * 60) as Time,
        value: point.price,
      })),
    );
    chartRef.current?.timeScale().fitContent();
  }, [snapshot]);

  return (
    <Card title="Market Microstructure Chart" eyebrow="Realtime price telemetry" className="min-h-[396px]">
      <div ref={containerRef} className="h-80 w-full" />
    </Card>
  );
}
