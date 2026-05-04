import React, { useState, useEffect } from 'react';
import { getTrades, evaluateTrades } from '../services/api';

async function fetchLastClose(symbol) {
  const res = await fetch(`/api/stocks/${encodeURIComponent(symbol)}/prices?interval=1day&limit=1`, {
    headers: { 'Cache-Control': 'no-cache' },
  });
  const data = await res.json();
  const arr = (data && data.prices) || [];
  if (!arr.length) throw new Error('No price data');
  const last = arr[arr.length - 1];
  return Number(last.close);
}

const PortfolioPage = () => {
  const [portfolio, setPortfolio] = useState([]);
  const [useBackend, setUseBackend] = useState(false);
  const [form, setForm] = useState({
    ticker: '',
    price: '',
    quantity: '',
    date: '',
  });
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const loadPortfolio = async () => {
      try {
        const backend = await getTrades();
        if (backend && backend.items && backend.items.length > 0) {
          setPortfolio(backend.items);
          setUseBackend(true);
          return;
        }
      } catch (e) {
        // Fall back to localStorage
      }
      const saved = localStorage.getItem('portfolio');
      if (saved) setPortfolio(JSON.parse(saved));
    };
    loadPortfolio();
  }, []);

  useEffect(() => {
    if (!useBackend) {
      localStorage.setItem('portfolio', JSON.stringify(portfolio));
    }
  }, [portfolio, useBackend]);

  // ...existing code...

  const handleChange = e => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const addEntry = () => {
    if (!form.ticker || !form.price || !form.quantity) return;
    const row = { ...form, id: Date.now() };
    setPortfolio([row, ...portfolio]);
    setForm({ ticker: '', price: '', quantity: '', date: '' });
  };

  const removeEntry = id => {
    setPortfolio(portfolio.filter(p => p.id !== id));
  };

  const evaluateTrades = async () => {
    if (!portfolio.length) return;
    setBusy(true);
    try {
      if (useBackend) {
        // Use backend evaluation
        const result = await evaluateTrades();
        alert(`Backend evaluated ${result?.evaluated || 0} trades`);
        // Reload portfolio from backend
        const updated = await getTrades();
        if (updated && updated.items) setPortfolio(updated.items);
      } else {
        // Local evaluation (existing logic)
        const now = Date.now();
        const next = [];
        for (const row of portfolio) {
          const meta = row._papertrade;
          if (!meta || row._eval) { next.push(row); continue; }

          const openedAtMs = row.date ? new Date(row.date).getTime() : row.id;
          const dueAtMs = openedAtMs + (meta.horizon_days || 7) * 24 * 3600 * 1000;

          if (now >= dueAtMs) {
            try {
              const last = await fetchLastClose(row.ticker);
              const entry = Number(row.price);
              const ret = (last - entry) / (entry || 1);
              const correct = ret >= 0; // long-only evaluation
              next.push({ ...row, _eval: { asOf: new Date().toISOString(), last, ret, correct } });
            } catch (e) {
              next.push({ ...row, _eval: { error: String(e) } });
            }
          } else {
            next.push(row);
          }
        }
        setPortfolio(next);

        // quick summary
        const closed = next.filter(r => r._eval && typeof r._eval.ret === 'number');
        const hit = closed.filter(r => r._eval.correct).length;
        const avg = closed.reduce((s, r) => s + (Number(r._eval.ret) || 0), 0) / (closed.length || 1);
        alert(`Evaluated ${closed.length} trades\nHit-rate: ${closed.length ? Math.round((hit/closed.length)*100) : 0}%\nAvg return: ${(avg*100).toFixed(2)}%`);
      }
    } catch (e) {
      alert(`Evaluation failed: ${e?.message || e}`);
    } finally {
      setBusy(false);
    }
  };

  const fmtPct = (x) => (typeof x === 'number' ? `${(x * 100).toFixed(2)}%` : '—');

  return (
    <div className="p-4 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">📊 Paper Portfolio</h2>
        <div className="flex items-center gap-2">
          <button
            onClick={evaluateTrades}
            disabled={busy}
            className={`px-3 py-2 rounded ${busy ? 'bg-gray-300' : 'bg-emerald-600 hover:bg-emerald-700'} text-white`}
            title="Check trades whose horizon has passed and mark outcome"
          >
            {busy ? 'Evaluating…' : 'Evaluate trades'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 bg-gray-50 p-4 rounded">
        <input
          name="ticker"
          value={form.ticker}
          onChange={handleChange}
          placeholder="Ticker (e.g., AAPL)"
          className="border p-2 rounded"
        />
        <input
          name="price"
          value={form.price}
          onChange={handleChange}
          type="number"
          placeholder="Buy Price"
          className="border p-2 rounded"
        />
        <input
          name="quantity"
          value={form.quantity}
          onChange={handleChange}
          type="number"
          placeholder="Quantity"
          className="border p-2 rounded"
        />
        <input
          name="date"
          value={form.date}
          onChange={handleChange}
          type="date"
          className="border p-2 rounded"
        />
        <button
          onClick={addEntry}
          className="col-span-full md:col-span-1 bg-blue-600 text-white py-2 rounded hover:bg-blue-700"
        >
          ➕ Add Trade
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full text-sm border rounded">
          <thead>
            <tr className="bg-gray-100 text-left">
              <th className="p-2">Ticker</th>
              <th className="p-2">Buy Price</th>
              <th className="p-2">Quantity</th>
              <th className="p-2">Date</th>
              <th className="p-2">Eval</th>
              <th className="p-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {portfolio.map((entry) => {
              const evald = entry._eval;
              let evalCell = '—';
              if (evald && typeof evald.ret === 'number') {
                evalCell = `${evald.correct ? '✅' : '❌'} ${fmtPct(evald.ret)} (last ${evald.last?.toFixed?.(2) ?? '—'})`;
              } else if (evald && evald.error) {
                evalCell = `⚠️ ${evald.error}`;
              }
              return (
                <tr key={entry.id} className="border-t">
                  <td className="p-2 font-semibold">{entry.ticker}</td>
                  <td className="p-2">${entry.price}</td>
                  <td className="p-2">{entry.quantity}</td>
                  <td className="p-2">{entry.date || '—'}</td>
                  <td className="p-2">{evalCell}</td>
                  <td className="p-2">
                    <button
                      onClick={() => removeEntry(entry.id)}
                      className="text-red-500 hover:underline"
                    >
                      ❌ Remove
                    </button>
                  </td>
                </tr>
              );
            })}
            {portfolio.length === 0 && (
              <tr>
                <td colSpan="6" className="p-2 text-center text-gray-500">
                  No entries yet
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default PortfolioPage;