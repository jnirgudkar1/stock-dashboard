// frontend/src/components/ValuationResult.jsx
import React from 'react';

const ValuationResult = ({ data }) => {
  if (!data) return null;
  const {
    sentiment_score,
    financial_score,
    growth_score,
    total_score,
    verdict,
    explain = {},
  } = data;

  const getColor = () => {
    if (verdict === 'Buy') return 'text-green-600';
    if (verdict === 'Sell') return 'text-red-600';
    return 'text-gray-700';
    };

  return (
    <div className="bg-white rounded-2xl shadow p-4 border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-800 mb-2">📈 Valuation & Prediction</h3>
      <div className="grid grid-cols-2 gap-4 text-sm text-gray-700">
        <div><span className="font-medium">Sentiment Score:</span> {sentiment_score}</div>
        <div><span className="font-medium">Financial Score:</span> {financial_score}</div>
        <div><span className="font-medium">Growth Score:</span> {growth_score}</div>
        <div><span className="font-medium">Total Score:</span> {total_score}</div>
        <div>
          <span className="font-medium">Verdict:</span>{' '}
          <span className={`${getColor()} font-semibold`}>{verdict}</span>
        </div>
      </div>

      {explain?.metadata_used && (
        <div className="mt-4 text-xs text-gray-600">
          <div className="font-medium mb-1">Inputs:</div>
          <pre className="bg-gray-50 p-2 rounded overflow-auto">
            {JSON.stringify(explain.metadata_used, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

export default ValuationResult;