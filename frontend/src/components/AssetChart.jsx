// frontend/src/components/AssetChart.jsx
import React, { useMemo } from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Scatter,
} from 'recharts';

// Props:
//   series:  [{ date:'YYYY-MM-DD', open, high, low, close, volume }]
//   markers: [{ date:'YYYY-MM-DD', price:number, type:'entry'|'exit' }]
export default function AssetChart({ series = [], markers = [] }) {
  const data = Array.isArray(series) ? series : [];

  // Snap markers to existing x-categories to ensure they render on the categorical X axis.
  const markerData = useMemo(() => {
    if (!Array.isArray(markers) || !markers.length || !data.length) return [];
    const byDate = new Map(data.map((d) => [String(d.date), d]));
    return markers
      .map((m) => {
        const d = String(m.date);
        const row = byDate.get(d);
        if (!row) return null; // if the X value doesn't exist, skip
        const price = Number.isFinite(m.price) ? Number(m.price) : Number(row.close);
        if (!Number.isFinite(price)) return null;
        return { date: row.date, y: price, type: m.type === 'exit' ? 'exit' : 'entry' };
      })
      .filter(Boolean);
  }, [markers, data]);

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    const p = payload.find((x) => x.dataKey === 'close')?.payload;
    if (!p) return null;
    const n = (v, d = 2) => (Number.isFinite(v) ? Number(v).toFixed(d) : '—');
    return (
      <div className="rounded-xl border bg-white/95 shadow p-2 text-xs">
        <div className="font-medium">{label}</div>
        <div>Open: <b className="tabular-nums">{n(p.open)}</b></div>
        <div>High: <b className="tabular-nums">{n(p.high)}</b></div>
        <div>Low: <b className="tabular-nums">{n(p.low)}</b></div>
        <div>Close: <b className="tabular-nums">{n(p.close)}</b></div>
        {Number.isFinite(p.volume) && (
          <div>Vol: <b className="tabular-nums">{Number(p.volume).toLocaleString()}</b></div>
        )}
      </div>
    );
  };

  // inline SVG triangles
  const MarkerShape = (props) => {
    const { cx, cy, payload } = props;
    if (!Number.isFinite(cx) || !Number.isFinite(cy)) return null;
    const type = payload?.type === 'exit' ? 'exit' : 'entry';
    const size = 7;
    const color = type === 'entry' ? '#10B981' : '#EF4444'; // emerald / rose
    const points =
      type === 'entry'
        ? `${cx},${cy - size} ${cx - size},${cy + size} ${cx + size},${cy + size}`
        : `${cx},${cy + size} ${cx - size},${cy - size} ${cx + size},${cy - size}`;
    return <polygon points={points} fill={color} stroke="white" strokeWidth="1" />;
  };

  return (
    <div className="w-full h-[360px]">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ top: 10, right: 16, bottom: 8, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} />
          <YAxis
            yAxisId="price"
            domain={['auto', 'auto']}
            tick={{ fontSize: 11 }}
            tickFormatter={(v) => Number(v).toFixed(0)}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            yAxisId="price"
            type="monotone"
            dataKey="close"
            stroke="#111827"
            fill="#e5e7eb"
            fillOpacity={0.35}
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
          />
          <Line
            yAxisId="price"
            type="monotone"
            dataKey="close"
            stroke="#111827"
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
          />
          {markerData.length > 0 && (
            <Scatter
              yAxisId="price"
              data={markerData}
              dataKey="y"
              shape={<MarkerShape />}
              isAnimationActive={false}
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>

      {markerData.length > 0 && (
        <div className="flex items-center gap-4 px-3 pb-2 text-xs text-gray-600">
          <div className="flex items-center gap-1">
            <svg width="12" height="12" viewBox="0 0 12 12"><polygon points="6,1 1,11 11,11" fill="#10B981" stroke="white" strokeWidth="1"/></svg>
            Entry
          </div>
          <div className="flex items-center gap-1">
            <svg width="12" height="12" viewBox="0 0 12 12"><polygon points="6,11 1,1 11,1" fill="#EF4444" stroke="white" strokeWidth="1"/></svg>
            Exit
          </div>
        </div>
      )}
    </div>
  );
}