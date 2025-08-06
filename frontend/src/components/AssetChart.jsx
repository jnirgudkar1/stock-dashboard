import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts';

const AssetChart = ({ data }) => {
  if (!data?.length) return null;

  return (
    <>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <XAxis dataKey="date" hide />
          <YAxis domain={['auto', 'auto']} />
          <Tooltip />
          <Line type="monotone" dataKey="price" stroke="#4f46e5" name="Close Price" strokeWidth={2} />
          <Line type="monotone" dataKey="sma" stroke="#10b981" name="7-Day SMA" strokeDasharray="3 3" />
        </LineChart>
      </ResponsiveContainer>

      <ResponsiveContainer width="100%" height={100}>
        <BarChart data={data}>
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