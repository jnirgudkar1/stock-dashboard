// frontend/src/pages/ValuationPage.jsx
import React, { useEffect, useMemo, useState } from 'react';
import { useSymbol } from '../components/SymbolContext';
import { getValuation, getPrediction } from '../services/api';
import ValuationResult from '../components/ValuationResult';

function pct(x, digits = 1) { if (typeof x !== 'number' || Number.isNaN(x)) return '—'; return `${(x * 100).toFixed(digits)}%`; }
function fmt(x, digits = 4) { if (x === null || x === undefined || Number.isNaN(Number(x))) return '—'; return Number(x).toFixed(digits); }
function tsToLocal(ts) { if (!ts) return ''; const d = new Date(ts * 1000); return d.toLocaleString(); }

const ConfidenceBar = ({ value }) => {
  const v = Math.max(0, Math.min(1, Number(value) || 0));
  return <div className="w-full h-2 bg-gray-200 rounded"><div className="h-2 rounded bg-emerald-500" style={{ width: `${(v * 100).toFixed(0)}%` }} /></div>;
};

const TopFeatures = ({ items }) => {
  const list = Array.isArray(items) ? items : [];
  const maxAbs = useMemo(() => list.reduce((m, it) => Math.max(m, Math.abs(Number(it?.contribution) || 0)), 0) || 1, [list]);
  if (!list.length) return null;
  return (
    <div className="space-y-2">
      {list.map((f) => {
        const name = String(f?.name ?? '');
        const contrib = Number(f?.contribution) || 0;
        const weight = Number(f?.weight) || 0;
        const widthPct = Math.min(100, Math.round((Math.abs(contrib) / maxAbs) * 100));
        const pos = contrib >= 0;
        return (
          <div key={name}>
            <div className="flex items-center justify-between text-sm text-gray-700">
              <div className="truncate mr-2">{name}</div>
              <div className="tabular-nums text-gray-500">contrib {fmt(contrib, 4)} · w {fmt(weight, 4)}</div>
            </div>
            <div className="w-full h-2 bg-gray-200 rounded overflow-hidden">
              <div className={`h-2 ${pos ? 'bg-blue-500' : 'bg-rose-500'}`} style={{ width: `${widthPct}%` }} title={`${name}: ${fmt(contrib, 4)}`} />
            </div>
          </div>
        );
      })}
    </div>
  );
};

const PredictionCard = ({ pred }) => {
  if (!pred) return null;
  const up = Number(pred.prob_up);
  const down = Number(pred.prob_down);
  const confidence = Number(pred.confidence || 0);
  const mode = pred.mode || 'legacy';
  const temp = pred?.calibration?.temperature;
  const calibrated = pred?.calibration?.applied ? ` (T=${temp})` : '';
  const when = tsToLocal(pred.timestamp || Math.floor(Date.now() / 1000));
  return (
    <div className="bg-white rounded-2xl shadow p-5 space-y-4">
      <div className="flex items-baseline justify-between">
        <div className="text-lg font-semibold">Prediction</div>
        <div className="text-xs text-gray-500">as of {when}</div>
      </div>
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-700">
          Model: <span className="font-medium uppercase">{mode}</span>
          <span className="text-gray-400">{calibrated}</span>
        </div>
        <div className={`text-sm px-2 py-1 rounded-full ${pred.label === 'UP' ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'}`}>{pred.label}</div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="p-3 rounded-xl bg-gray-50">
          <div className="text-xs text-gray-500">Prob ↑</div>
          <div className="text-xl font-semibold tabular-nums">{pct(up, 1)}</div>
        </div>
        <div className="p-3 rounded-xl bg-gray-50">
          <div className="text-xs text-gray-500">Prob ↓</div>
          <div className="text-xl font-semibold tabular-nums">{pct(down, 1)}</div>
        </div>
      </div>
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <div className="text-gray-700">Confidence</div>
          <div className="tabular-nums text-gray-600">{pct(confidence, 0)}</div>
        </div>
        <ConfidenceBar value={confidence} />
      </div>
      {Array.isArray(pred.top_features) && pred.top_features.length > 0 && (
        <div className="space-y-2">
          <div className="text-sm font-medium text-gray-700">Top drivers</div>
          <TopFeatures items={pred.top_features} />
        </div>
      )}
      <div className="pt-2 border-t border-gray-100">
        <div className="text-xs text-gray-500">Feature vector (ordered)</div>
        <div className="mt-1 grid grid-cols-1 md:grid-cols-2 gap-1">
          {(pred.feature_order || []).map((k) => (
            <div key={k} className="text-xs text-gray-700 flex justify-between">
              <span className="truncate mr-2">{k}</span>
              <span className="tabular-nums">{fmt(pred.features?.[k] ?? '—', 6)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const DEV = typeof import.meta !== 'undefined' && import.meta.env && !!import.meta.env.DEV;

// NEW: one-line decision banner
const DecisionStrip = ({ pred, val }) => {
  if (!pred) return null;
  const p = Number(pred.prob_up);
  const conf = Math.abs(p - 0.5) * 2; // 0..1
  const base = p >= 0.6 ? 'Buy' : p <= 0.4 ? 'Sell' : 'Hold';
  const valVerdict = (val?.verdict || '').trim();

  // If valuation conflicts and confidence isn't strong, neutralize to Hold
  let suggestion = base;
  const conflict = (base === 'Buy' && valVerdict === 'Sell') || (base === 'Sell' && valVerdict === 'Buy');
  if (conflict && conf < 0.4) suggestion = 'Hold';

  const cls =
    suggestion === 'Buy' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
    suggestion === 'Sell' ? 'bg-rose-50 text-rose-700 border-rose-200' :
    'bg-amber-50 text-amber-700 border-amber-200';

  const reason = `Model: Prob↑ ${pct(p)}${pred?.calibration?.applied ? ` (T=${fmt(pred?.calibration?.temperature, 2)})` : ''}` +
    (valVerdict ? ` · Valuation: ${valVerdict}` : '');

  return (
    <div className={`p-3 rounded-2xl border ${cls} flex flex-wrap items-center gap-3`}>
      <div className="font-semibold">Suggestion: {suggestion}</div>
      <div className="text-sm opacity-90">{reason}</div>
    </div>
  );
};

const DevTempControl = ({ value, onChange }) => {
  if (!DEV) return null;
  return (
    <div className="p-3 rounded-xl border bg-white">
      <div className="flex items-center justify-between mb-2">
        <div className="font-medium">Calibration Temperature</div>
        <div className="text-sm text-gray-600">T = {fmt(value, 2)}</div>
      </div>
      <input
        type="range"
        min="0.50"
        max="2.00"
        step="0.05"
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full"
      />
      <div className="text-xs text-gray-500 mt-1">
        Lower T (&lt;1) → sharper (more confident). Higher T (&gt;1) → flatter (less confident).
      </div>
    </div>
  );
};

const ValuationPage = () => {
  const { symbol } = useSymbol();
  const [val, setVal] = useState(null);
  const [pred, setPred] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  // Dev-only temp slider state
  const [temp, setTemp] = useState(1.0);

  useEffect(() => {
    let alive = true;
    const run = async () => {
      setLoading(true);
      setErr(null);
      try {
        const vPromise = getValuation(symbol);
        // pass temp only in dev; in prod the backend default env PREDICT_TEMP is used
        const pPromise = DEV ? getPrediction(symbol, { temp }) : getPrediction(symbol);
        const [v, p] = await Promise.allSettled([vPromise, pPromise]);
        if (!alive) return;
        if (v.status === 'fulfilled') setVal(v.value);
        if (p.status === 'fulfilled') setPred(p.value);
        if (v.status === 'rejected' && p.status === 'rejected') {
          throw new Error(`${v.reason?.message || v.reason} | ${p.reason?.message || p.reason}`);
        }
      } catch (e) {
        setErr(e?.message || String(e));
      } finally {
        if (alive) setLoading(false);
      }
    };
    run();
    return () => { alive = false; };
  }, [symbol, temp]); // re-run when temperature changes

  return (
    <div className="max-w-5xl mx-auto p-4 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Valuation & Prediction</h1>
        <div className="text-sm text-gray-500">Symbol: <b>{symbol}</b></div>
      </div>

      {DEV && <DevTempControl value={temp} onChange={setTemp} />}

      {loading && (
        <div className="p-4 bg-gray-50 rounded-xl text-sm text-gray-600">Loading valuation & prediction…</div>
      )}
      {err && (
        <div className="p-4 bg-rose-50 text-rose-700 rounded-xl text-sm">{err}</div>
      )}
      {!loading && !err && (
        <>
          {/* NEW: one-line decision banner */}
          {pred && <DecisionStrip pred={pred} val={val} />}

          {val && <ValuationResult data={val} />}
          {pred && <PredictionCard pred={pred} />}
        </>
      )}
    </div>
  );
};

export default ValuationPage;