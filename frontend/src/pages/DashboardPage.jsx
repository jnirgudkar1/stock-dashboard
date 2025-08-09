// frontend/src/pages/DashboardPage.jsx
import React, { useEffect, useMemo, useState } from 'react';
import AssetChart from '../components/AssetChart';
import { useSymbol } from '../components/SymbolContext';
import { getPrices, toRechartsSeries, getMetadata } from '../services/api';

const ranges = [7, 30, 90, 180, 365];

const DashboardPage = () => {
  const { symbol } = useSymbol();
  const [range, setRange] = useState(30);
  const [series, setSeries] = useState([]);
  const [meta, setMeta] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => {
    let alive = true;
    const run = async () => {
      setLoading(true); setErr(null);
      try {
        const [p, m] = await Promise.all([
          getPrices(symbol, { interval: '1day', limit: 400 }),
          getMetadata(symbol),
        ]);
        if (!alive) return;
        const full = toRechartsSeries(p);
        const cut = full.slice(-range);
        setSeries(cut);
        setMeta(m);
      } catch (e) {
        if (!alive) return;
        setErr(String(e));
      } finally {
        if (alive) setLoading(false);
      }
    };
    run();
    return () => { alive = false; };
  }, [symbol, range]);

  const latest = useMemo(
    () => (series.length ? series[series.length - 1] : null),
    [series]
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">{symbol} Dashboard</h2>
        <div className="flex gap-2">
          {ranges.map(r => (
            <button
              key={r}
              onClick={() => setRange(r)}
              className={`px-3 py-1 rounded border ${range === r ? 'bg-black text-white' : 'bg-white'}`}
            >
              {r}D
            </button>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-2xl shadow p-4">
        {loading ? (
          <div>Loading chart…</div>
        ) : err ? (
          <div className="text-red-600">{err}</div>
        ) : (
          <AssetChart series={series} />
        )}
        {latest && (
          <div className="mt-2 text-sm text-gray-600">
            Latest close: <span className="font-semibold">{latest.close}</span>
          </div>
        )}
      </div>

      <div className="bg-white rounded-2xl shadow p-4 grid grid-cols-2 gap-4">
        {meta ? (
          <>
            <div><span className="font-medium">Market Cap:</span> {meta.marketCap ?? '—'}</div>
            <div><span className="font-medium">P/E:</span> {meta.peRatio ?? '—'}</div>
            <div><span className="font-medium">Dividend Yield:</span> {meta.dividendYield ?? '—'}</div>
            <div><span className="font-medium">52w High/Low:</span> {meta.weekHigh ?? '—'} / {meta.weekLow ?? '—'}</div>
          </>
        ) : (
          <div className="text-sm text-gray-500">Loading metadata…</div>
        )}
      </div>
    </div>
  );
};

export default DashboardPage;