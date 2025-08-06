// src/pages/DashboardPage.jsx
import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer, BarChart, Bar } from 'recharts';
import AssetSummary from '../components/AssetSummary';
import { useSymbol } from '../components/SymbolContext';

const DashboardPage = () => {
  const { symbol: selectedSymbol } = useSymbol();
  const [selectedRange, setSelectedRange] = useState(30);
  const [chartData, setChartData] = useState([]);
  const [latestPrice, setLatestPrice] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [error, setError] = useState(null);

  const fetchData = () => {
    fetch(`/api/stocks/${selectedSymbol}`, {
      headers: {
        'Cache-Control': 'no-cache',
      },
    })
      .then(async (res) => {
        if (!res.ok) {
          const text = await res.text();
          throw new Error(`HTTP ${res.status}: ${text}`);
        }
        return res.json();
      })
      .then((data) => {
        if (data.prices) {
          const formatted = Object.entries(data.prices)
            .slice(0, selectedRange)
            .reverse()
            .map(([date, values], index, array) => {
              const price = parseFloat(values['4. close']);
              const volume = parseInt(values['5. volume']);

              let sma = null;
              if (index >= 6) {
                const slice = array.slice(index - 6, index + 1);
                const avg = slice.reduce(
                  (sum, [d]) => sum + parseFloat(data.prices[d]['4. close']),
                  0
                ) / 7;
                sma = parseFloat(avg.toFixed(2));
              }

              return { date, price, volume, sma };
            });

          setChartData(formatted);
          setLatestPrice(formatted[formatted.length - 1]?.price || null);
          setError(null);

        } else if (data.symbol && data.price && data.date) {
          const fallbackData = [{ date: data.date, price: data.price, volume: 0, sma: null }];
          setChartData(fallbackData);
          setLatestPrice(data.price);
          setError(null);

        } else {
          throw new Error('Unsupported or missing price data');
        }
      })
      .catch((err) => {
        console.error('Fetch error:', err.message);
        setError('Failed to load price data. Please try again.');
      });
  };

  const fetchMetadata = () => {
    fetch(`/api/stocks/${selectedSymbol}/metadata`, {
      headers: {
        'Cache-Control': 'no-cache',
      },
    })
      .then(async (res) => {
        if (!res.ok) {
          const text = await res.text();
          throw new Error(`HTTP ${res.status}: ${text}`);
        }
        return res.json();
      })
      .then((data) => {
        setMetadata(data);
      })
      .catch((err) => {
        console.error('Metadata fetch error:', err.message);
        setMetadata(null);
      });
  };

  useEffect(() => {
    fetchData();
    fetchMetadata();
  }, [selectedSymbol, selectedRange]);

  const handleRangeChange = (days) => setSelectedRange(days);

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-2xl font-semibold">Dashboard</h1>

      {/* Range Filter */}
      <div className="flex gap-2">
        {[7, 30, 90].map((d) => (
          <button
            key={d}
            onClick={() => handleRangeChange(d)}
            className={`px-3 py-1 rounded ${selectedRange === d ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          >
            {d}D
          </button>
        ))}
      </div>

      {/* Error Message */}
      {error && <p className="text-red-500">{error}</p>}

      {/* Price Display */}
      {latestPrice !== null && (
        <p className="text-lg text-gray-800 font-medium">
          Current Price: <span className="text-green-600">${latestPrice.toFixed(2)}</span>
        </p>
      )}

      {/* Chart */}
      <div className="bg-white rounded-2xl shadow-md p-6 space-y-4 border border-gray-200">
        <div className="bg-white p-4 rounded shadow">
          <h2 className="text-lg font-semibold mb-2">Price & Volume</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis yAxisId="left" domain={['auto', 'auto']} />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Line yAxisId="left" type="monotone" dataKey="price" stroke="#007bff" dot={false} />
              <Line yAxisId="left" type="monotone" dataKey="sma" stroke="#82ca9d" dot={false} strokeDasharray="5 5" />
              <BarChart yAxisId="right" data={chartData}>
                <Bar dataKey="volume" fill="#8884d8" />
              </BarChart>
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Metadata */}
      <div className="bg-white rounded-2xl shadow-md p-6 space-y-4 border border-gray-200">
        <div className="bg-white p-4 rounded shadow">
          <h3 className="text-lg font-semibold text-gray-800 mb-3">📊 Asset Metadata</h3>
          {metadata ? (
            <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm text-gray-700">
              <div><span className="font-medium">Market Cap:</span> ${parseFloat(metadata.marketCap || 0).toLocaleString()}</div>
              <div><span className="font-medium">P/E Ratio:</span> {metadata.peRatio || 'N/A'}</div>
              <div><span className="font-medium">Dividend Yield:</span> {metadata.dividendYield || 'N/A'}%</div>
              <div><span className="font-medium">Sector:</span> {metadata.sector || 'N/A'}</div>
            </div>
          ) : (
            <p className="text-sm text-gray-500">Loading metadata...</p>
          )}
        </div>
      </div>

      {/* Summary */}
      <div className="bg-white rounded-2xl shadow-md p-6 space-y-4 border border-gray-200">
        <AssetSummary symbol={selectedSymbol} />
      </div>
    </div>
  );
};

export default DashboardPage;