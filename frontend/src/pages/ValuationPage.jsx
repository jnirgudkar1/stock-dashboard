// frontend/src/pages/ValuationPage.jsx
import React, { useEffect, useState } from 'react';
import { useSymbol } from '../components/SymbolContext';
import { getValuation, getPrediction } from '../services/api';
import ValuationResult from '../components/ValuationResult';

const ValuationPage = () => {
  const { symbol } = useSymbol();
  const [val, setVal] = useState(null);
  const [pred, setPred] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => {
    let alive = true;
    const run = async () => {
      setLoading(true); setErr(null);
      try {
        const [v, p] = await Promise.all([
          getValuation(symbol),
          getPrediction(symbol).catch(() => null), // model may be missing
        ]);
        if (!alive) return;
        setVal(v);
        setPred(p);
      } catch (e) {
        if (!alive) return;
        setErr(String(e));
      } finally {
        if (alive) setLoading(false);
      }
    };
    run();
    return () => { alive = false; };
  }, [symbol]);

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Valuation & Prediction — {symbol}</h2>
      {loading ? (
        <div>Loading…</div>
      ) : err ? (
        <div className="text-red-600">{err}</div>
      ) : (
        <>
          {val && <ValuationResult data={val} />}
          {pred && (
            <div className="bg-white rounded-2xl shadow p-4">
              <div className="text-sm text-gray-700">
                Model prediction: <b>{pred.label}</b> (↑ {pred.prob_up}, ↓ {pred.prob_down})
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default ValuationPage;