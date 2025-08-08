// ✅ Updated: src/pages/InsightsPage.jsx
import React from 'react';
import NewsFeed from '../components/NewsFeed';
import { useSymbol } from '../components/SymbolContext';
import { useStockData } from '../components/DataContext';

const InsightsPage = () => {
  const { symbol } = useSymbol();
  const { data, loading } = useStockData();

  return (
    <div className="bg-white p-4 rounded shadow space-y-4">
      <h2 className="text-2xl font-bold text-purple-700 mb-4 border-b pb-2">📰 News for {symbol}</h2>
      <div className="rounded-xl border bg-white p-4 shadow-md hover:shadow-lg transition-all">
        {loading ? (
          <p className="text-sm text-gray-500">Loading news...</p>
        ) : (
          <NewsFeed articles={data.news || []} />
        )}
      </div>
      {!loading && data.lastFetched && (
        <p className="text-xs text-gray-400 text-right italic">
          Last updated {Math.round((Date.now() - data.lastFetched) / 60000)} min ago
        </p>
      )}
    </div>
  );
};

export default InsightsPage;