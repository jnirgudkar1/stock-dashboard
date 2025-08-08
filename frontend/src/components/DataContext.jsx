// ✅ New: src/components/DataContext.jsx
import React, { createContext, useContext, useEffect, useState } from 'react';
import { useSymbol } from './SymbolContext';

const DataContext = createContext();

export const DataProvider = ({ children }) => {
  const { symbol } = useSymbol();
  const [cache, setCache] = useState({}); // { AAPL: { news, valuation, lastFetched } }
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchDataIfNeeded = async () => {
      const now = Date.now();
      const cached = cache[symbol];
      const expired = !cached || now - cached.lastFetched > 2 * 60 * 60 * 1000;

      if (!expired) return;

      setLoading(true);
      try {
        // Fetch news
        const newsRes = await fetch(`/api/news/${symbol}`);
        const articles = await newsRes.json();
        const newsUrls = Array.isArray(articles) ? articles.map((a) => a.url) : [];

        // Fetch valuation
        const valRes = await fetch(`/api/stocks/${symbol}/valuation`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ news_urls: newsUrls })
        });
        const valuation = await valRes.json();

        setCache((prev) => ({
          ...prev,
          [symbol]: {
            news: articles,
            valuation,
            lastFetched: now
          }
        }));
      } catch (err) {
        console.error("Failed to prefetch news/valuation:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchDataIfNeeded();
  }, [symbol]);

  return (
    <DataContext.Provider value={{ data: cache[symbol] || {}, loading }}>
      {children}
    </DataContext.Provider>
  );
};

export const useStockData = () => useContext(DataContext);