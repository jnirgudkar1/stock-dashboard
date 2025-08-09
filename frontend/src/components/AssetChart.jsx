// frontend/src/components/AssetChart.jsx
import React from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

// Accepts `series` as array of { date, open, high, low, close, volume }
const AssetChart = ({ series = [] }) => {
  if (!Array.isArray(series) || series.length === 0) return null;

  return (
    <>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={series} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <XAxis dataKey="date" hide />
          <YAxis domain={[
            dataMin => Math.min(dataMin * 0.98, dataMin),
            dataMax => Math.max(dataMax * 1.02, dataMax)
          ]} />
          <Tooltip />
          <Line type="monotone" dataKey="close" dot={false} name="Close" />
        </LineChart>
      </ResponsiveContainer>

      <ResponsiveContainer width="100%" height={100}>
        <BarChart data={series}>
          <XAxis dataKey="date" hide />
          <YAxis hide />
          <Tooltip />
          <Bar dataKey="volume" name="Volume" />
        </BarChart>
      </ResponsiveContainer>
    </>
  );
};

export default AssetChart;