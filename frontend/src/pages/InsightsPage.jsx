// frontend/src/pages/InsightsPage.jsx
import React, { useEffect, useState } from 'react';
import NewsFeed from '../components/NewsFeed';
import { useSymbol } from '../components/SymbolContext';
import { getStockNews } from '../services/api';

const InsightsPage = () => {
  const { symbol } = useSymbol();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => {
    let alive = true;
    const run = async () => {
      setLoading(true); setErr(null);
      try {
        const res = await getStockNews(symbol, { max: 30 });
        if (!alive) return;
        setItems(res.items || []);
      } catch (e) {
        if (!alive) return;
        setErr(String(e));
      } finally {
        if (alive) setLoading(false);
      }
    };
    run();
    return () => { alive = false; };
  }, [symbol]);

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">News for {symbol}</h2>
      {loading ? (
        <div>Loading…</div>
      ) : err ? (
        <div className="text-red-600">{err}</div>
      ) : (
        <NewsFeed items={items} />
      )}
    </div>
  );
};

export default InsightsPage;