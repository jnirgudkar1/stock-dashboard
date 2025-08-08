import React, { useEffect, useState } from 'react';
import ValuationResult from '../components/ValuationResult';
import { useSymbol } from '../components/SymbolContext';
import { useStockData } from '../components/DataContext';
import PredictionCard from '../components/PredictionCard'; // ✅ new import

const ValuationPage = () => {
  const { symbol } = useSymbol();
  const { data, loading } = useStockData();
  const [prediction, setPrediction] = useState(null);

  useEffect(() => {
    if (!symbol) return;

    fetch(`/api/predict/${symbol}`)
      .then(res => res.json())
      .then(setPrediction)
      .catch(err => {
        console.error("Prediction fetch failed:", err);
        setPrediction(null);
      });
  }, [symbol]);

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-2xl font-semibold">Valuation</h1>

      {loading && <p className="text-sm text-gray-500">Calculating valuation...</p>}

      {!loading && data.valuation && (
        <>
          <ValuationResult result={data.valuation} />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* 🧠 Prediction Card */}
            <PredictionCard prediction={prediction} />

            {/* 📈 Growth Metrics */}
            <div className="text-sm text-gray-700 bg-white rounded-xl shadow p-4 border border-gray-200">
              <h4 className="font-semibold mb-2">📈 Growth Metrics</h4>
              <ul className="list-disc pl-5">
                <li><strong>EPS Estimate Growth:</strong> {data.valuation.eps_growth?.toFixed(2)}%</li>
                <li><strong>Revenue Growth:</strong> {data.valuation.revenue_growth?.toFixed(2)}%</li>
                <li><strong>Growth Score:</strong> {data.valuation.growth_score}</li>
              </ul>
            </div>
          </div>
        </>
      )}

      {!loading && !data.valuation && (
        <p className="text-sm text-gray-500">No valuation data available.</p>
      )}

      {!loading && data.lastFetched && (
        <p className="text-xs text-gray-400 text-right italic">
          Last updated {Math.round((Date.now() - data.lastFetched) / 60000)} min ago
        </p>
      )}
    </div>
  );
};

export default ValuationPage;