// frontend/src/pages/DashboardPage.jsx
import React, { useEffect, useMemo, useState } from 'react';
import AssetChart from '../components/AssetChart';
import { useSymbol } from '../components/SymbolContext';
import { getPrices, toRechartsSeries, getMetadata, getValuation } from '../services/api';

const ranges = [7, 30, 90, 180, 365];

const fmt2 = (n) => (typeof n === 'number' ? n.toFixed(2) : n ?? '—');
const compactCap = (n) => {
  if (n == null || Number.isNaN(Number(n))) return '—';
  const num = Number(n);
  if (num >= 1e12) return `${(num / 1e12).toFixed(2)}T`;
  if (num >= 1e9) return `${(num / 1e9).toFixed(2)}B`;
  if (num >= 1e6) return `${(num / 1e6).toFixed(2)}M`;
  return num.toFixed(2);
};

const DashboardPage = () => {
  const { symbol } = useSymbol();
  const [range, setRange] = useState(30);
  const [series, setSeries] = useState([]);
  const [meta, setMeta] = useState(null);
  const [val, setVal] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => {
    let alive = true;
    const run = async () => {
      setLoading(true);
      setErr(null);
      try {
        const [prices, metadata] = await Promise.all([
          getPrices(symbol, range),
          getMetadata(symbol),
        ]);
        if (!alive) return;
        setSeries(toRechartsSeries(prices));
        setMeta(metadata);
        getValuation(symbol).then((v) => { if (alive) setVal(v); }).catch(() => {});
      } catch (e) {
        if (!alive) return;
        setErr(e?.message || 'Failed to load');
      } finally {
        if (alive) setLoading(false);
      }
    };
    run();
    return () => { alive = false; };
  }, [symbol, range]);

  const verdictLabel = val?.verdict?.label || val?.verdict || null;
  const verdictColor = val?.verdict?.color || null;
  const verdictPill = (() => {
    if (!verdictLabel) return 'bg-gray-100 text-gray-700';
    if (verdictColor === 'green' || verdictLabel === 'Buy') return 'bg-green-100 text-green-800';
    if (verdictColor === 'yellow' || verdictLabel === 'Hold') return 'bg-yellow-100 text-yellow-800';
    if (verdictColor === 'red' || verdictLabel === 'Sell') return 'bg-red-100 text-red-800';
    return 'bg-gray-100 text-gray-700';
  })();

  const chartData = useMemo(() => series, [series]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold flex items-center gap-3">
          Dashboard — {symbol}
          {verdictLabel && (
            <span className={`px-2 py-0.5 rounded text-sm ${verdictPill}`}>
              {verdictLabel}
            </span>
          )}
        </h2>

        <div className="flex items-center gap-2">
          {ranges.map((r) => (
            <button
              key={r}
              className={`px-2 py-1 rounded border ${range === r ? 'bg-gray-900 text-white' : ''}`}
              onClick={() => setRange(r)}
            >
              {r}D
            </button>
          ))}
        </div>
      </div>

      {err && <div className="text-red-600">{err}</div>}

      {/* Chart container with border & padding */}
      <div className="p-4 border rounded-xl bg-white overflow-x-auto">
        <AssetChart series={chartData} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-3 rounded-xl border">
          <div className="font-semibold mb-2">Asset Metadata</div>
          {meta ? (
            <>
              <div><span className="font-medium">Name:</span> {meta.name ?? '—'}</div>
              <div><span className="font-medium">Sector:</span> {meta.sector ?? '—'}</div>
              <div><span className="font-medium">Industry:</span> {meta.industry ?? '—'}</div>
              <div className="mt-2 grid grid-cols-2 gap-2">
                <div><span className="font-medium">Market Cap:</span> {compactCap(meta.marketCap)}</div>
                <div><span className="font-medium">P/E:</span> {fmt2(meta.peRatio)}</div>
                <div><span className="font-medium">Dividend Yield:</span> {fmt2(meta.dividendYield)}</div>
                <div><span className="font-medium">52w High/Low:</span> {fmt2(meta.weekHigh)} / {fmt2(meta.weekLow)}</div>
              </div>
            </>
          ) : (
            <div className="text-sm text-gray-500">Loading metadata…</div>
          )}
        </div>

        <div className="p-3 rounded-xl border">
          <div className="font-semibold mb-2">Notes</div>
          <div className="text-sm text-gray-700">
            Use the verdict badge as a quick “at a glance” read. Dive into the Valuation tab for explanations of
            sentiment, financial, and growth scores in plain English.
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;