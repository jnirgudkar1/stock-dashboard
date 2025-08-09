// frontend/src/components/AssetChart.jsx
import React from 'react';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, CartesianGrid,
} from 'recharts';

// Accepts `series` as array of { date, open, high, low, close, volume }
const AssetChart = ({ series = [] }) => {
  if (!Array.isArray(series) || series.length === 0) return null;

  // Keep price/volume plot areas aligned
  const yAxisWidth = 20;

  const formatTick = (value) => (typeof value === 'number' ? value.toFixed(2) : value);

  const formatDate = (d) => {
    // Handle ISO strings or timestamps
    const dt = typeof d === 'number' ? new Date(d) : new Date(String(d));
    if (Number.isNaN(dt.getTime())) return d;
    return dt.toLocaleDateString(undefined, { month: 'short', day: '2-digit' });
  };

  return (
    <>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart
          data={series}
          margin={{ top: 10, right: 16, left: yAxisWidth, bottom: 0 }}
          syncId="asset"
        >
          <CartesianGrid vertical={false} strokeOpacity={0.15} />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
            tickFormatter={formatDate}
            interval="preserveStartEnd"
            minTickGap={28}
          />
          <YAxis
            width={yAxisWidth}
            tick={{ fontSize: 12 }}
            tickFormatter={formatTick}
            domain={[
              (dataMin) => Math.min(dataMin * 0.98, dataMin),
              (dataMax) => Math.max(dataMax * 1.02, dataMax),
            ]}
          />
          <Tooltip
            formatter={(value) => (typeof value === 'number' ? value.toFixed(2) : value)}
            labelFormatter={formatDate}
            cursor={{ strokeOpacity: 0.15 }}
          />
          <Line
            type="monotone"
            dataKey="close"
            name="Close"
            dot={false}
            strokeWidth={2}
            activeDot={{ r: 3 }}
          />
        </LineChart>
      </ResponsiveContainer>

      <ResponsiveContainer width="100%" height={100}>
        <BarChart
          data={series}
          margin={{ top: 0, right: 16, left: 40, bottom: 0 }}
          syncId="asset"
        >
          <XAxis dataKey="date" hide />
          <YAxis hide />
          <Tooltip
            formatter={(value) => (typeof value === 'number' ? value.toFixed(2) : value)}
            labelFormatter={formatDate}
            cursor={{ fillOpacity: 0.08 }}
          />
          <Bar dataKey="volume" name="Volume" />
        </BarChart>
      </ResponsiveContainer>
    </>
  );
};

export default AssetChart;