// START: Global SymbolSelector
import React from 'react';
import { useSymbol } from './SymbolContext';

const assetOptions = ["AAPL", "GOOGL", "NVDA", "RKLB", "RCAT", "BKSY", "AMD", "TSLA", "PLTR", "AMZN", "BBAI"];

const SymbolSelector = () => {
  const { symbol, setSymbol } = useSymbol();

  return (
    <div className="flex justify-center mb-6">
      <div className="w-full max-w-xs">
        <label className="block text-sm font-semibold text-gray-700 mb-1">
          📌 Select Ticker
        </label>
        <div className="relative">
          <select
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            className="block w-full appearance-none rounded-xl border border-gray-300 bg-white py-2 px-4 pr-10 text-lg text-gray-800 shadow-md focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-400 transition-all"
          >
            {assetOptions.map((s) => (
              <option key={s} value={s} className="text-base">
                {s}
              </option>
            ))}
          </select>
          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3 text-gray-500">
            ▼
          </div>
        </div>
      </div>
    </div>
  );
};

export default SymbolSelector;