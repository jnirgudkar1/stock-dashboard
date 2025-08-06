// src/pages/ValuationPage.jsx
import React from 'react';

const ValuationPage = () => {
  return (
    <div className="bg-white p-6 rounded shadow">
      <h2 className="text-2xl font-semibold mb-4">📉 Valuation & Prediction</h2>
      <div className="space-y-4">
        <section className="bg-gray-50 border border-purple-200 rounded-lg p-4 shadow-sm">
          <h3 className="text-lg font-medium text-purple-700">🔎 DCF Fair Value</h3>
          <p>Estimated value: <span className="font-bold text-green-600">$165.00</span></p>
          <p className="text-gray-500 text-sm">Assuming 8% growth, 10% discount rate, 5-year horizon.</p>
        </section>

        <section className="bg-gray-50 border border-purple-200 rounded-lg p-4 shadow-sm">
          <h3 className="text-lg font-medium text-purple-700">📐 Graham Formula</h3>
          <p>Intrinsic value: <span className="font-bold text-blue-600">$152.80</span></p>
          <p className="text-gray-500 text-sm">Assumes EPS: $5.8, Growth: 6.5%</p>
        </section>

        <section className="bg-gray-50 border border-purple-200 rounded-lg p-4 shadow-sm">
          <h3 className="text-lg font-medium text-purple-700">🤖 ML-Based Prediction</h3>
          <p>Next 30-day price range: <span className="font-bold text-orange-600">$148 - $163</span></p>
          <p className="text-gray-500 text-sm">Confidence: 70%, based on technical indicators.</p>
        </section>

        <section className="bg-gray-50 border border-purple-200 rounded-lg p-4 shadow-sm">
          <p className="text-sm">
            🧠 Summary: <strong>AAPL appears moderately undervalued</strong> based on DCF and Graham models.
            ML model suggests a neutral to bullish outlook for the short term.
          </p>
        </section>
      </div>
    </div>
  );
};

export default ValuationPage;