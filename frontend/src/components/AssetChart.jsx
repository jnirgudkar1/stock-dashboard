import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar
} from 'recharts';

const AssetChart = ({ prices }) => {
  if (!prices || typeof prices !== 'object') return null;

  const dates = Object.keys(prices).sort();
  const formatted = dates.map((date, index, arr) => {
    const close = parseFloat(prices[date]['4. close']);
    const volume = parseInt(prices[date]['5. volume']);

    let sma = null;
    if (index >= 6) {
      const avg = arr
        .slice(index - 6, index + 1)
        .reduce((sum, d) => sum + parseFloat(prices[d]['4. close']), 0) / 7;
      sma = parseFloat(avg.toFixed(2));
    }

    return { date, price: close, volume, sma };
  });

  return (
    <>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={formatted}>
          <XAxis dataKey="date" hide />
          <YAxis domain={['auto', 'auto']} />
          <Tooltip />
          <Line type="monotone" dataKey="price" stroke="#4f46e5" name="Close Price" strokeWidth={2} />
          <Line type="monotone" dataKey="sma" stroke="#10b981" name="7-Day SMA" strokeDasharray="3 3" />
        </LineChart>
      </ResponsiveContainer>

      <ResponsiveContainer width="100%" height={100}>
        <BarChart data={formatted}>
          <XAxis dataKey="date" hide />
          <YAxis hide />
          <Tooltip />
          <Bar dataKey="volume" fill="#9ca3af" name="Volume" />
        </BarChart>
      </ResponsiveContainer>
    </>
  );
};

export default AssetChart;