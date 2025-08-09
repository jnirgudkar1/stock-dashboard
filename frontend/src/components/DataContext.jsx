// frontend/src/components/DataContext.jsx
import React, { createContext, useContext, useEffect, useState } from 'react';
import { useSymbol } from './SymbolContext';
import { getStockNews, getValuation } from '../services/api';

const DataContext = createContext();

export const DataProvider = ({ children }) => {
  const { symbol } = useSymbol();
  const [cache, setCache] = useState({}); // { AAPL: { news, valuation, lastFetched } }
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let alive = true;
    const fetchDataIfNeeded = async () => {
      const now = Date.now();
      const cached = cache[symbol];
      const expired = !cached || now - cached.lastFetched > 2 * 60 * 60 * 1000; // 2h

      if (!expired) return;

      setLoading(true);
      try {
        const [newsRes, valuationRes] = await Promise.all([
          getStockNews(symbol, { max: 20 }),   // GET /api/stocks/{symbol}/news
          getValuation(symbol),                // GET /api/stocks/{symbol}/valuation
        ]);

        if (!alive) return;
        setCache(prev => ({
          ...prev,
          [symbol]: {
            news: newsRes?.items || [],
            valuation: valuationRes || null,
            lastFetched: now,
          }
        }));
      } catch (e) {
        // optional: surface error somewhere
        console.error('DataContext fetch error:', e);
      } finally {
        if (alive) setLoading(false);
      }
    };

    fetchDataIfNeeded();
    return () => { alive = false; };
  }, [symbol]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <DataContext.Provider value={{ data: cache[symbol] || {}, loading }}>
      {children}
    </DataContext.Provider>
  );
};

export const useStockData = () => useContext(DataContext);