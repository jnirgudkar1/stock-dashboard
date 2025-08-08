import React from "react";

const PredictionCard = ({ prediction }) => {
  if (!prediction) return null;

  const { verdict, confidence, inputs } = prediction;

  return (
    <div className="text-sm text-gray-700 bg-white rounded-xl shadow p-4 border border-gray-200">
      <h4 className="font-semibold mb-2">🧠 ML Prediction</h4>
      <ul className="list-disc pl-5">
        <li><strong>Verdict:</strong> {verdict}</li>
        <li><strong>Confidence:</strong> {confidence}%</li>
      </ul>
      <div className="mt-2 text-xs text-gray-500">
        <strong>Inputs:</strong>
        <ul className="pl-4">
          <li>Price: {inputs.close_price}</li>
          <li>PE Ratio: {inputs.pe_ratio}</li>
          <li>EPS: {inputs.eps}</li>
          <li>Revenue Growth: {inputs.revenue_growth}</li>
        </ul>
      </div>
    </div>
  );
};

export default PredictionCard;