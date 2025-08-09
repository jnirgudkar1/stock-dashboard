// frontend/src/components/ValuationResult.jsx
import React from 'react';

const pill = (color) => {
  switch (color) {
    case 'green': return 'bg-green-100 text-green-800';
    case 'yellow': return 'bg-yellow-100 text-yellow-800';
    case 'red': return 'bg-red-100 text-red-800';
    default: return 'bg-gray-100 text-gray-700';
  }
};

const verdictTextColor = (color, verdict) => {
  if (color === 'green') return 'text-green-600';
  if (color === 'yellow') return 'text-yellow-600';
  if (color === 'red') return 'text-red-600';
  if (verdict === 'Buy') return 'text-green-600';
  if (verdict === 'Hold') return 'text-yellow-600';
  if (verdict === 'Sell') return 'text-red-600';
  return 'text-gray-700';
};

const ValuationResult = ({ data }) => {
  if (!data) return null;

  // Prefer new structured fields if present
  const hasV2 = !!data.scores;
  const verdictLabel = hasV2 ? (data.verdict_detail?.label || data.verdict?.label || data.verdict) : data.verdict;
  const verdictColor = hasV2 ? (data.verdict_detail?.color || data.verdict?.color) : null;

  // Pull score blocks with fallback to legacy fields
  const s = hasV2 ? data.scores.sentiment : { value: data.sentiment_score };
  const f = hasV2 ? data.scores.financial : { value: data.financial_score };
  const g = hasV2 ? data.scores.growth    : { value: data.growth_score };
  const t = hasV2 ? data.scores.total      : { value: data.total_score };

  const explain = data.explain || {};

  // Helper to render a metric card
  const Metric = ({ title, block }) => {
    const label = block?.label || '—';
    const color = block?.color || 'gray';
    const val = typeof block?.value === 'number' ? block.value.toFixed(2) : (block?.value ?? '—');
    const why = block?.why;

    return (
      <div className="p-3 rounded-lg border">
        <div className="text-gray-600 text-sm">{title}</div>
        <div className="mt-1">
          <span className={`px-2 py-0.5 rounded ${pill(color)}`}>
            {label}{typeof block?.value === 'number' ? ` (${val})` : ''}
          </span>
        </div>
        {why && <div className="text-xs text-gray-600 mt-2">{why}</div>}
      </div>
    );
  };

  return (
    <div className="bg-white rounded-2xl shadow p-4">
      <div className="text-lg">
        Verdict:{' '}
        <b className={verdictTextColor(verdictColor, verdictLabel)}>
          {verdictLabel}
        </b>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-3">
        <Metric title="Sentiment" block={s} />
        <Metric title="Financial" block={f} />
        <Metric title="Growth" block={g} />
      </div>

      {/* Show total as a separate chip (optional, but useful) */}
      <div className="mt-3">
        <div className="text-gray-600 text-sm mb-1">Overall</div>
        <span className={`px-2 py-0.5 rounded ${pill(t?.color || 'gray')}`}>
          {(t?.label || '—')}{typeof t?.value === 'number' ? ` (${t.value.toFixed(2)})` : ''}
        </span>
      </div>

      {explain?.metadata_used && (
        <div className="mt-4 text-xs text-gray-600">
          <div className="font-medium mb-1">Inputs:</div>
          <pre className="bg-gray-50 p-2 rounded overflow-auto">
            {JSON.stringify(explain.metadata_used, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

export default ValuationResult;