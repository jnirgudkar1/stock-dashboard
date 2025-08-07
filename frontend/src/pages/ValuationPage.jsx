// src/pages/ValuationPage.jsx
import React, { useEffect, useState } from 'react';
import ValuationResult from '../components/ValuationResult';
import { useSymbol } from '../components/SymbolContext';

const ValuationPage = () => {
  const { symbol: selectedSymbol } = useSymbol();
  const [valuationResult, setValuationResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 🧠 Simulate shared news URLs from Insights tab
  const newsUrls = [
    `https://finance.yahoo.com/news/apple-reports-third-quarter-results-200500763.html`,
    `https://www.reuters.com/technology/apple-posts-better-than-expected-results-boosted-iphone-sales-2024-08-01/`
  ];

  useEffect(() => {
    const fetchValuation = async () => {
      setLoading(true);
      try {
        const res = await fetch(`/api/stocks/${selectedSymbol}/valuation`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ news_urls: newsUrls })
        });

        if (!res.ok) {
          const text = await res.text();
          throw new Error(`HTTP ${res.status}: ${text}`);
        }

        const data = await res.json();
        setValuationResult(data);
        setError(null);
      } catch (err) {
        console.error("Valuation fetch error:", err.message);
        setError("Failed to load valuation data.");
        setValuationResult(null);
      } finally {
        setLoading(false);
      }
    };

    fetchValuation();
  }, [selectedSymbol]);

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-2xl font-semibold">Valuation</h1>

      {loading && <p className="text-sm text-gray-500">Calculating valuation...</p>}
      {error && <p className="text-sm text-red-500">{error}</p>}
      {!loading && !error && <ValuationResult result={valuationResult} />}
    </div>
  );
};

export default ValuationPage;