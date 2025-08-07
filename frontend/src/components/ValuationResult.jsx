import React from 'react';

const ValuationResult = ({ result }) => {
  if (!result) return <p className="text-sm text-gray-500">Valuation data not available.</p>;

  const { sentiment_score, financial_score, total_score, verdict } = result;

  const getColor = () => {
    if (verdict === "Buy") return "text-green-600";
    if (verdict === "Sell") return "text-red-600";
    return "text-yellow-600";
  };

  return (
    <div className="bg-white rounded-2xl shadow-md p-6 space-y-3 border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-800 mb-2">📈 Valuation & Prediction</h3>
      <div className="grid grid-cols-2 gap-4 text-sm text-gray-700">
        <div><span className="font-medium">Sentiment Score:</span> {sentiment_score}</div>
        <div><span className="font-medium">Financial Score:</span> {financial_score}</div>
        <div><span className="font-medium">Total Score:</span> {total_score}</div>
        <div>
          <span className="font-medium">Verdict:</span>{' '}
          <span className={`${getColor()} font-semibold`}>{verdict}</span>
        </div>
      </div>
    </div>
  );
};

export default ValuationResult;