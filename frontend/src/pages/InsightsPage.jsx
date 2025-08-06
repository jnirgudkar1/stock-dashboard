// src/pages/InsightsPage.jsx
import React, { useEffect, useState } from 'react';
import { fetchNews } from '../services/API';
import NewsFeed from '../components/NewsFeed';
import { useSymbol } from '../components/SymbolContext';

const InsightsPage = () => {
  const { symbol } = useSymbol();
  const [articles, setArticles] = useState([]);

  useEffect(() => {
    fetchNews(symbol)
      .then(data => {
        if (Array.isArray(data)) setArticles(data);
      })
      .catch(console.error);
  }, [symbol]);

  return (
    <div className="bg-white p-4 rounded shadow space-y-4">
      <h2 className="text-2xl font-bold text-purple-700 mb-4 border-b pb-2">📰 News for {symbol}</h2>
      <div className="rounded-xl border bg-white p-4 shadow-md hover:shadow-lg transition-all">
        <NewsFeed articles={articles} />
      </div>
    </div>
  );
};

export default InsightsPage;