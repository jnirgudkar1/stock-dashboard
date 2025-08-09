// frontend/src/components/NewsFeed.jsx
import React from 'react';

const getSentiment = (text = '') => {
  const lower = text.toLowerCase();
  if (lower.includes('surge') || lower.includes('beat') || lower.includes('growth') || lower.includes('record') || lower.includes('rally')) {
    return 'positive';
  }
  if (lower.includes('fall') || lower.includes('loss') || lower.includes('decline') || lower.includes('miss') || lower.includes('downgrade')) {
    return 'negative';
  }
  return 'neutral';
};

const sentimentClasses = (label) => {
  switch (label) {
    case 'positive': return 'bg-green-100 text-green-800';
    case 'negative': return 'bg-red-100 text-red-800';
    case 'neutral':  return 'bg-yellow-100 text-yellow-800';
    default:         return 'bg-gray-100 text-gray-700';
  }
};

const getImpact = (title = '', desc = '') => {
  const text = `${title} ${desc}`;
  const score = (text.match(/ai|earnings|merger|iphone|forecast|inflation|guidance|lawsuit|upgrade|downgrade/gi) || []).length;
  if (score >= 3) return 'High';
  if (score === 2) return 'Medium';
  return 'Low';
};

export default function NewsFeed({ items = [] }) {
  return (
    <div className="grid gap-3">
      {items.map((n, i) => {
        // Prefer backend-provided sentiment if present; fall back to heuristic
        const backend = n?.sentiment && typeof n.sentiment === 'object';
        const label = backend ? (n.sentiment.label || 'neutral') : getSentiment(`${n.title}. ${n.description || ''}`);
        const colorClass = backend
          ? (n.sentiment.color === 'green' ? 'bg-green-100 text-green-800'
            : n.sentiment.color === 'red' ? 'bg-red-100 text-red-800'
            : n.sentiment.color === 'yellow' ? 'bg-yellow-100 text-yellow-800'
            : 'bg-gray-100 text-gray-700')
          : sentimentClasses(label);
        const scoreText = backend && typeof n.sentiment.score === 'number'
          ? ` (${n.sentiment.score.toFixed(2)})`
          : '';

        const impact = n?.impact || getImpact(n.title, n.description);

        return (
          <a
            key={i}
            href={n.url}
            target="_blank"
            rel="noreferrer"
            className="p-3 rounded-xl border hover:shadow-sm flex flex-col gap-1"
          >
            <div className="flex items-center gap-2">
              <div className="font-semibold">{n.title}</div>
              <span className="text-xs opacity-60">•</span>
              <span className="text-xs opacity-60">{n.source || '—'}</span>
            </div>

            {n.description && <div className="text-sm opacity-80">{n.description}</div>}

            <div className="text-xs opacity-60">
              {new Date((n.published_at || 0)).toLocaleString()}
            </div>

            <div className="text-xs mt-2 flex gap-3 items-center">
              <span className={`px-2 py-0.5 rounded ${colorClass}`}>
                {label[0].toUpperCase() + label.slice(1)}{scoreText}
              </span>
              <span className="px-2 py-0.5 rounded bg-gray-100 text-gray-800">
                {impact} impact
              </span>
            </div>
          </a>
        );
      })}
    </div>
  );
}