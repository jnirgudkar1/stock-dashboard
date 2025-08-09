// frontend/src/pages/InsightsPage.jsx
import React, { useEffect, useMemo, useState } from 'react';
import NewsFeed from '../components/NewsFeed';
import { useSymbol } from '../components/SymbolContext';
import { getStockNews } from '../services/api';

const IMP_RANK = { high: 0, medium: 1, low: 2, unknown: 3 };
const rankImpact = (impact) => {
  const v = (impact || 'unknown').toString().toLowerCase();
  return IMP_RANK[v] ?? 3;
};

export default function InsightsPage() {
  const { symbol } = useSymbol();
  const [rawItems, setRawItems] = useState([]);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  const [sortMode, setSortMode] = useState('impact'); // 'impact' | 'latest'
  const [source, setSource] = useState('All');

  useEffect(() => {
    let alive = true;
    const run = async () => {
      setLoading(true);
      setErr(null);
      try {
        const res = await getStockNews(symbol);
        if (!alive) return;

        // Accept either an array or an object like { symbol, items: [...] }
        const raw = Array.isArray(res) ? res : Array.isArray(res?.items) ? res.items : [];
        setRawItems(raw);
      } catch (e) {
        if (!alive) return;
        setErr(e?.message || 'Failed to load news');
      } finally {
        if (alive) setLoading(false);
      }
    };
    run();
    return () => { alive = false; };
  }, [symbol]);

  // Derive list of sources for the filter
  const sources = useMemo(() => {
    const uniq = Array.from(new Set(rawItems.map(it => it?.source).filter(Boolean))).sort();
    return ['All', ...uniq];
  }, [rawItems]);

  // Apply filter + sort
  useEffect(() => {
    const filtered = (source === 'All')
      ? rawItems
      : rawItems.filter(it => (it?.source || '') === source);

    const sorted = filtered.slice().sort((a, b) => {
      if (sortMode === 'impact') {
        const ai = rankImpact(a?.impact);
        const bi = rankImpact(b?.impact);
        if (ai !== bi) return ai - bi;
      }
      // tie-break or default for 'latest': newest first
      const at = typeof a?.published_at === 'number' ? a.published_at : (Number(a?.published_at) || 0);
      const bt = typeof b?.published_at === 'number' ? b.published_at : (Number(b?.published_at) || 0);
      return bt - at;
    });

    setItems(sorted);
  }, [rawItems, sortMode, source]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <h2 className="text-2xl font-bold">News for {symbol}</h2>
        <div className="flex items-center gap-2">
          {/* Source filter */}
          <select
            value={source}
            onChange={(e) => setSource(e.target.value)}
            className="border rounded px-2 py-1 text-sm"
            aria-label="Filter by source"
          >
            {sources.map(s => <option key={s} value={s}>{s}</option>)}
          </select>

          {/* Sort toggle */}
          <div className="flex items-center gap-1 text-sm">
            <button
              className={`px-2 py-1 rounded border ${sortMode === 'impact' ? 'bg-gray-900 text-white' : ''}`}
              onClick={() => setSortMode('impact')}
              aria-pressed={sortMode === 'impact'}
            >
              Sort: Impact
            </button>
            <button
              className={`px-2 py-1 rounded border ${sortMode === 'latest' ? 'bg-gray-900 text-white' : ''}`}
              onClick={() => setSortMode('latest')}
              aria-pressed={sortMode === 'latest'}
            >
              Latest
            </button>
          </div>
        </div>
      </div>

      {loading ? (
        <div>Loading…</div>
      ) : err ? (
        <div className="text-red-600">{err}</div>
      ) : items.length === 0 ? (
        <div className="text-sm text-gray-600">No news found for the current filters.</div>
      ) : (
        <NewsFeed items={items} />
      )}
    </div>
  );
}