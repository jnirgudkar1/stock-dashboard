// frontend/src/pages/DashboardPage.jsx
import React, { useEffect, useMemo, useState } from 'react';
import AssetChart from '../components/AssetChart';
import { useSymbol } from '../components/SymbolContext';
import { getPrices, toRechartsSeries, getMetadata } from '../services/api';

// --- tiny indicator helpers (local only) ---
const ema = (arr, p) => {
  const out = Array(arr.length).fill(undefined);
  const k = 2 / (p + 1);
  let e = 0, s = 0;
  for (let i = 0; i < arr.length; i++) {
    const v = Number(arr[i]);
    if (!Number.isFinite(v)) continue;
    if (i < p) { s += v; if (i === p - 1) { e = s / p; out[i] = e; } }
    else { e = k * v + (1 - k) * e; out[i] = e; }
  }
  return out;
};
const macdHist = (closes) => {
  const e12 = ema(closes, 12);
  const e26 = ema(closes, 26);
  const macd = closes.map((_, i) => (e12[i] != null && e26[i] != null) ? e12[i] - e26[i] : undefined);
  const sig = ema(macd.map(v => (v == null ? NaN : v)), 9);
  return macd.map((m, i) => (m != null && sig[i] != null) ? m - sig[i] : undefined);
};
const rsi14 = (closes) => {
  const p = 14, out = Array(closes.length).fill(undefined);
  if (closes.length <= p) return out;
  let g = 0, l = 0;
  for (let i = 1; i <= p; i++) {
    const c = closes[i] - closes[i - 1];
    if (c >= 0) g += c; else l += -c;
  }
  g /= p; l /= p;
  out[p] = 100 - 100 / (1 + (l === 0 ? 100 : g / l));
  for (let i = p + 1; i < closes.length; i++) {
    const c = closes[i] - closes[i - 1];
    const gain = c > 0 ? c : 0, loss = c < 0 ? -c : 0;
    g = (g * (p - 1) + gain) / p;
    l = (l * (p - 1) + loss) / p;
    out[i] = 100 - 100 / (1 + (l === 0 ? 100 : g / l));
  }
  return out;
};

const ranges = [7, 30, 90, 180, 365];
const fmt2 = (n, d = 2) => (typeof n === 'number' && Number.isFinite(n) ? n.toFixed(d) : '—');
const pct = (x, d = 1) => (typeof x === 'number' && Number.isFinite(x) ? `${(x * 100).toFixed(d)}%` : '—');
const compactCap = (n) => {
  if (n == null || Number.isNaN(Number(n))) return '—';
  const num = Number(n);
  if (num >= 1e12) return `${(num / 1e12).toFixed(2)}T`;
  if (num >= 1e9) return `${(num / 1e9).toFixed(2)}B`;
  if (num >= 1e6) return `${(num / 1e6).toFixed(2)}M`;
  return num.toFixed(2);
};

export default function DashboardPage() {
  const { symbol } = useSymbol();

  const [rangeDays, setRangeDays] = useState(90);
  const [series, setSeries] = useState([]);
  const [meta, setMeta] = useState(null);

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      setLoading(true);
      setErr(null);
      try {
        const [p, m] = await Promise.allSettled([
          getPrices(symbol, { interval: '1day', limit: 500 }),
          getMetadata(symbol),
        ]);
        if (!alive) return;
        if (p.status === 'fulfilled') setSeries(toRechartsSeries(p.value));
        else throw p.reason;
        if (m.status === 'fulfilled') setMeta(m.value);
      } catch (e) {
        setErr(e?.message || String(e));
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, [symbol]);

  // chart range
  const chartData = useMemo(() => {
    if (!Array.isArray(series)) return [];
    return series.slice(Math.max(0, series.length - rangeDays));
  }, [series, rangeDays]);

  // plain-English signal summary (no markers)
  const signal = useMemo(() => {
    const N = chartData.length;
    if (N < 60) return { have: false, status: 'Not enough data', explain: '', last: null, rsiNow: null, macdNow: null };
    const closes = chartData.map(d => Number(d.close));
    const dates = chartData.map(d => String(d.date));
    const hist = macdHist(closes);
    const rsi = rsi14(closes);

    let inPos = false;
    let last = null;
    for (let i = 1; i < N; i++) {
      const hPrev = hist[i - 1], hNow = hist[i];
      const r = rsi[i];
      if (!inPos) {
        if (hPrev != null && hNow != null && hPrev <= 0 && hNow > 0 && r != null && r < 70) {
          inPos = true;
          last = { type: 'Buy', date: dates[i], reason: `Momentum turned up (MACD hist crossed above 0) and RSI ${fmt2(r,1)} was below 70.` };
        }
      } else {
        if ((hPrev != null && hNow != null && hPrev >= 0 && hNow < 0) || (r != null && r > 70)) {
          inPos = false;
          last = { type: 'Sell', date: dates[i], reason: (r != null && r > 70)
            ? `RSI ${fmt2(r,1)} went above 70 (overbought).`
            : `Momentum turned down (MACD hist crossed below 0).` };
        }
      }
    }

    const rNow = rsi[N - 1];
    const hNow = hist[N - 1];
    const status = inPos ? 'In trade (would be long)' : 'Waiting (no position)';
    const next = inPos
      ? 'Exit when MACD hist flips below 0 or RSI rises above 70.'
      : 'Enter when MACD hist flips above 0 while RSI is below 70.';

    return {
      have: true,
      status,
      next,
      explain: 'Buy = momentum turns up and not overbought. Sell = momentum turns down or becomes overbought.',
      last,
      rsiNow: rNow, macdNow: hNow,
    };
  }, [chartData]);

  return (
    <div className="max-w-6xl mx-auto p-4 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <div className="text-sm text-gray-500">Symbol: <b>{symbol}</b></div>
      </div>

      {loading && <div className="p-3 rounded-xl bg-gray-50 text-sm text-gray-600">Loading…</div>}
      {err && <div className="p-3 rounded-xl bg-rose-50 text-rose-700 text-sm">{err}</div>}

      {/* Range selector */}
      <div className="flex gap-2 flex-wrap">
        {ranges.map((r) => (
          <button
            key={r}
            onClick={() => setRangeDays(r)}
            className={`px-3 py-1 rounded-full border text-sm ${
              rangeDays === r ? 'bg-gray-900 text-white border-gray-900' : 'bg-white text-gray-800 border-gray-300'
            }`}
          >
            {r}D
          </button>
        ))}
      </div>

      {/* Price Chart (no markers) */}
      <div className="rounded-2xl border">
        <AssetChart series={chartData} />
      </div>

      {/* Signals (plain-English) */}
      <div className="rounded-2xl border p-4">
        <div className="font-semibold mb-2">Signals — simple MACD + RSI</div>
        {!signal.have ? (
          <div className="text-sm text-gray-600">Not enough data to compute signals yet.</div>
        ) : (
          <div className="space-y-2 text-sm text-gray-800">
            <div>
              <span className="font-medium">What it means:</span>{' '}
              <span className="text-gray-700">{signal.explain}</span>
            </div>
            <div className="flex flex-wrap gap-3">
              <div className="px-3 py-1 rounded-full bg-gray-50 border">Status: <b>{signal.status}</b></div>
              <div className="px-3 py-1 rounded-full bg-gray-50 border">RSI now: <b className="tabular-nums">{fmt2(signal.rsiNow,1)}</b></div>
              <div className="px-3 py-1 rounded-full bg-gray-50 border">MACD hist now: <b className="tabular-nums">{fmt2(signal.macdNow,3)}</b></div>
            </div>
            {signal.last ? (
              <div>
                <div className="text-gray-600">Last signal:</div>
                <div className="mt-1 p-2 rounded-xl bg-gray-50 border">
                  <div><b>{signal.last.type}</b> on <b>{signal.last.date}</b></div>
                  <div className="text-gray-700">{signal.last.reason}</div>
                </div>
              </div>
            ) : (
              <div className="text-gray-600">No prior signals in this window.</div>
            )}
            <div className="text-gray-600">Next: {signal.next}</div>
            <div className="text-xs text-gray-500">Educational only — not investment advice.</div>
          </div>
        )}
      </div>

      {/* Metadata (kept minimal) */}
      <div className="p-3 rounded-2xl border">
        <div className="font-semibold mb-2">Asset Metadata</div>
        {meta ? (
          <>
            <div><span className="font-medium">Name:</span> {meta.name ?? '—'}</div>
            <div><span className="font-medium">Sector:</span> {meta.sector ?? '—'}</div>
            <div><span className="font-medium">Industry:</span> {meta.industry ?? '—'}</div>
            <div className="mt-2 grid grid-cols-2 gap-2">
              <div><span className="font-medium">Market Cap:</span> {compactCap(meta.marketCap)}</div>
              <div><span className="font-medium">P/E:</span> {fmt2(meta.peRatio)}</div>
              <div><span className="font-medium">Dividend Yld:</span> {fmt2(meta.dividendYield)}</div>
              <div><a className="text-blue-600 hover:underline" href={meta.website} target="_blank" rel="noreferrer">Website</a></div>
            </div>
          </>
        ) : (
          <div className="text-sm text-gray-600">—</div>
        )}
      </div>
    </div>
  );
}