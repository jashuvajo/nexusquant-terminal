import type { BacktestMetric, EngineScore, HeatmapCell, JournalEntry, MarketSymbol, Regime, TelemetryPoint, TerminalSnapshot, VolatilityRegime } from '../types';

const regimes: Regime[] = ['TREND_EXPANSION', 'RANGE_ABSORPTION', 'VOLATILITY_COMPRESSION', 'REVERSAL_RISK'];
const volRegimes: VolatilityRegime[] = ['NORMAL_IV', 'IV_EXPANSION', 'LOW_IV', 'EVENT_SPIKE'];
const engines = [
  ['Delta Engine', 0.16],
  ['Momentum Engine', 0.14],
  ['Heatmap Engine', 0.12],
  ['Volume Engine', 0.1],
  ['Regime Engine', 0.1],
  ['Spread Analysis', 0.09],
  ['Option Chain Bias', 0.1],
  ['Gamma Positioning', 0.1],
  ['IV Expansion', 0.05],
  ['Market Profile Alignment', 0.04],
] as const;

const clamp = (value: number, min: number, max: number) => Math.max(min, Math.min(max, value));
const wave = (tick: number, speed: number, phase = 0) => Math.sin(tick / speed + phase);
const money = (value: number) => Math.round(value * 100) / 100;

function makeAiMatrix(tick: number): EngineScore[] {
  return engines.map(([engine, weight], index) => {
    const score = clamp(72 + wave(tick + index * 7, 5, index) * 18 + (index % 3) * 3, 28, 99);
    return {
      engine,
      score: Math.round(score),
      weight,
      status: score > 78 ? 'pass' : score > 62 ? 'watch' : 'fail',
    };
  });
}

function makeHeatmap(symbol: MarketSymbol, tick: number, atm: number): HeatmapCell[] {
  const step = symbol === 'NIFTY' ? 50 : 100;
  return Array.from({ length: 18 }, (_, index) => {
    const distance = index - 8;
    const side = index % 3 === 0 ? 'FUTURE' : index % 2 === 0 ? 'CALL' : 'PUT';
    const liquidity = clamp(54 + wave(tick + index, 3.4) * 35 + (8 - Math.abs(distance)) * 3, 12, 99);
    const gammaWall = clamp(40 + Math.abs(distance) * 4 + wave(tick, 7, index) * 26, 4, 98);
    const stopDensity = clamp(35 + wave(tick, 4.5, distance) * 30 + (Math.abs(distance) > 5 ? 18 : 0), 5, 96);
    return {
      id: `${symbol}-${index}`,
      strike: atm + distance * step,
      side,
      liquidity: Math.round(liquidity),
      absorption: Math.round(clamp(44 + wave(tick, 4.1, index * 0.7) * 38, 3, 99)),
      gammaWall: Math.round(gammaWall),
      stopDensity: Math.round(stopDensity),
      sweepRisk: Math.round(clamp(28 + wave(tick, 2.8, index) * 42, 2, 94)),
      label: liquidity > 82 ? 'Liquidity cluster' : gammaWall > 78 ? 'Gamma wall' : stopDensity > 76 ? 'SL density' : 'Acceptance',
    };
  });
}

function makeTelemetry(tick: number, base: number): TelemetryPoint[] {
  return Array.from({ length: 36 }, (_, index) => {
    const local = tick - 35 + index;
    return {
      time: `${String((9 + Math.floor(index / 6)) % 24).padStart(2, '0')}:${String((index * 5) % 60).padStart(2, '0')}`,
      pnl: Math.round(wave(local, 6) * 4200 + index * 120 - 1700),
      tqs: Math.round(clamp(72 + wave(local, 4) * 18, 30, 98)),
      latency: Math.round(clamp(31 + wave(local, 3, 1.2) * 18, 8, 98)),
      volume: Math.round(clamp(4200 + wave(local, 3.8) * 2500 + index * 90, 900, 11000)),
      price: money(base + wave(local, 8) * 34 + index * 1.7),
    };
  });
}

function makeJournal(tick: number): JournalEntry[] {
  const reasons = ['ATR trail lock', 'Gamma wall rejection', 'Partial exit plus runner', 'Safe mode flatten', 'Breakout velocity fade'];
  return Array.from({ length: 6 }, (_, index) => ({
    time: `${String(10 + index).padStart(2, '0')}:${String((tick * 3 + index * 7) % 60).padStart(2, '0')}`,
    instrument: index % 2 === 0 ? 'NIFTY 50 CE' : 'SENSEX PE',
    tqs: Math.round(clamp(68 + wave(tick, 3, index) * 21, 45, 98)),
    pnl: Math.round(2400 + wave(tick, 4, index) * 6200),
    exitReason: reasons[index % reasons.length],
  }));
}

const backtest: BacktestMetric[] = [
  { name: 'Win Rate', value: 68.4, unit: '%' },
  { name: 'Profit Factor', value: 2.18, unit: 'x' },
  { name: 'Avg Hold', value: 4.6, unit: 'min' },
  { name: 'Max DD', value: 1.9, unit: '%' },
  { name: 'Sharpe', value: 3.4, unit: '' },
  { name: 'Expectancy', value: 1280, unit: 'INR' },
];

export function createMockSnapshot(tick = 1): TerminalSnapshot {
  const symbol: MarketSymbol = tick % 7 < 4 ? 'NIFTY' : 'SENSEX';
  const spotBase = symbol === 'NIFTY' ? 23650 : 78120;
  const step = symbol === 'NIFTY' ? 50 : 100;
  const spot = money(spotBase + wave(tick, 9) * 86 + wave(tick, 2.7) * 18);
  const atmStrike = Math.round(spot / step) * step;
  const aiMatrix = makeAiMatrix(tick);
  const tradeQualityScore = Math.round(aiMatrix.reduce((sum, item) => sum + item.score * item.weight, 0));
  const safeMode = tradeQualityScore < 70 || wave(tick, 11) < -0.82;

  return {
    timestamp: new Date().toISOString(),
    symbol,
    spot,
    atmStrike,
    premiumFocusZone: `${atmStrike - step}-${atmStrike + step} ${symbol} weekly options`,
    aiConfidence: Math.round(clamp(tradeQualityScore + wave(tick, 4.2) * 7, 10, 99)),
    tradeQualityScore,
    pnl: Math.round(12800 + wave(tick, 6) * 9400),
    liveExposurePct: Math.round(clamp(21 + wave(tick, 5) * 14, 5, 48)),
    spreadQuality: Math.round(clamp(84 + wave(tick, 3.7) * 13, 22, 99)),
    executionLatencyMs: Math.round(clamp(38 + wave(tick, 4.9) * 24, 8, 130)),
    deltaVelocity: Math.round(clamp(62 + wave(tick, 2.8) * 36, -100, 100)),
    trailingStopState: safeMode ? 'SAFE MODE - reduced size' : tradeQualityScore > 82 ? 'Adaptive target extension' : 'ATR trail armed',
    regime: regimes[Math.abs(Math.floor(tick / 6)) % regimes.length],
    volatilityRegime: volRegimes[Math.abs(Math.floor(tick / 8)) % volRegimes.length],
    activeTrades: [
      {
        id: 'NQ-ALPHA-01',
        symbol,
        side: wave(tick, 5) > 0 ? 'CALL' : 'PUT',
        strike: atmStrike,
        qty: safeMode ? 75 : 150,
        entry: money(142 + wave(tick, 9) * 12),
        ltp: money(154 + wave(tick, 3.4) * 18),
        pnl: Math.round(6200 + wave(tick, 4) * 4800),
        tqs: tradeQualityScore,
        stop: money(126 + wave(tick, 5) * 4),
        target: money(188 + wave(tick, 6) * 12),
        status: safeMode ? 'SAFE_MODE' : tradeQualityScore > 85 ? 'TRAILING' : 'SCALPING',
      },
      {
        id: 'NQ-HEDGE-02',
        symbol,
        side: wave(tick, 4.4) > 0 ? 'PUT' : 'CALL',
        strike: atmStrike + step,
        qty: 75,
        entry: 88.4,
        ltp: money(93 + wave(tick, 3.9) * 8),
        pnl: Math.round(2100 + wave(tick, 7) * 1600),
        tqs: Math.max(60, tradeQualityScore - 9),
        stop: 78.2,
        target: 112.5,
        status: 'PARTIAL_EXIT',
      },
    ],
    heatmap: makeHeatmap(symbol, tick, atmStrike),
    orderflow: {
      cumulativeDelta: Math.round(42000 + wave(tick, 5) * 36000),
      deltaVelocity: Math.round(clamp(58 + wave(tick, 2.2) * 44, -100, 100)),
      aggressiveBuyers: Math.round(clamp(71 + wave(tick, 3.1) * 25, 5, 99)),
      aggressiveSellers: Math.round(clamp(37 + wave(tick, 4.3) * 24, 3, 99)),
      domImbalance: Math.round(clamp(56 + wave(tick, 2.9) * 37, -100, 100)),
      liquidityShift: Math.round(clamp(64 + wave(tick, 5.2) * 22, 0, 99)),
      sweepDetection: Math.round(clamp(48 + wave(tick, 3.6) * 39, 0, 99)),
      volumeAcceleration: Math.round(clamp(68 + wave(tick, 4.5) * 28, 0, 99)),
      breakoutVelocity: Math.round(clamp(61 + wave(tick, 3.8) * 33, 0, 99)),
    },
    greeks: {
      delta: Number((0.54 + wave(tick, 6) * 0.18).toFixed(2)),
      gamma: Number((0.018 + Math.abs(wave(tick, 4)) * 0.022).toFixed(3)),
      theta: Number((-4.2 - Math.abs(wave(tick, 7)) * 2.4).toFixed(2)),
      vega: Number((9.6 + wave(tick, 5) * 2.2).toFixed(2)),
      ivRank: Math.round(clamp(54 + wave(tick, 8) * 31, 1, 99)),
      ivPercentile: Math.round(clamp(62 + wave(tick, 9) * 24, 1, 99)),
      ivExpansion: Math.round(clamp(39 + wave(tick, 2.7) * 42, 0, 99)),
    },
    marketProfile: {
      poc: atmStrike - step,
      vah: atmStrike + step * 2,
      val: atmStrike - step * 3,
      acceptanceZone: tradeQualityScore > 78 ? 'Breakout accepted above VAH' : 'Auction inside value area',
      volumeProfile: Array.from({ length: 12 }, (_, index) => ({
        level: atmStrike + (index - 6) * step,
        volume: Math.round(clamp(1200 + wave(tick, 3.3, index) * 900 + (6 - Math.abs(index - 6)) * 260, 120, 4200)),
      })),
    },
    aiMatrix,
    risk: {
      safeMode,
      dailyDrawdownPct: Number(clamp(0.7 + Math.abs(wave(tick, 10)) * 1.2, 0, 4.5).toFixed(2)),
      maxDrawdownPct: 3,
      slippageBps: Number(clamp(3.2 + Math.abs(wave(tick, 4)) * 4.5, 1, 18).toFixed(1)),
      staleDataMs: Math.round(clamp(120 + Math.abs(wave(tick, 5)) * 420, 40, 1800)),
      apiDisconnects: safeMode ? 1 : 0,
      latencyMs: Math.round(clamp(41 + Math.abs(wave(tick, 4.4)) * 36, 10, 180)),
      spreadWideningPct: Number(clamp(3 + Math.abs(wave(tick, 3.1)) * 9, 0, 22).toFixed(1)),
      maxExposurePct: safeMode ? 18 : 42,
      cooldownSeconds: safeMode ? 180 : 25,
    },
    infra: {
      brokerHealth: safeMode ? 82 : 98,
      websocketLatencyMs: Math.round(clamp(18 + Math.abs(wave(tick, 3.6)) * 23, 5, 120)),
      orderRouterLatencyMs: Math.round(clamp(24 + Math.abs(wave(tick, 3.9)) * 34, 8, 150)),
      redisHealth: 99,
      postgresHealth: 98,
      prometheusHealth: 99,
    },
    portfolio: {
      capital: 1250000,
      margin: 348000,
      realizedPnl: 84200,
      unrealizedPnl: Math.round(9200 + wave(tick, 4) * 6200),
      executionQuality: Math.round(clamp(88 + wave(tick, 5.4) * 8, 55, 99)),
      positions: 2,
      orders: 14,
    },
    strategy: {
      selected: safeMode ? 'Capital preservation scalp' : tradeQualityScore > 84 ? 'Momentum expansion scalp' : 'Liquidity acceptance scalp',
      aggression: safeMode ? 26 : Math.round(clamp(58 + wave(tick, 4.2) * 28, 10, 92)),
      sizeMultiplier: safeMode ? 0.35 : Number(clamp(0.75 + wave(tick, 6) * 0.22, 0.25, 1.25).toFixed(2)),
      threshold: safeMode ? 86 : 76,
      router: safeMode ? 'SAFE_MODE' : tradeQualityScore > 87 ? 'AGGRESSIVE_SWEEP' : tradeQualityScore > 76 ? 'SMART_LIMIT' : 'PASSIVE_JOIN',
    },
    telemetry: makeTelemetry(tick, spot),
    journal: makeJournal(tick),
    backtest,
  };
}
