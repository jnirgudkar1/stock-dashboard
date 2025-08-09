import React from 'react';

const getSentiment = (text = '') => {
  const lower = text.toLowerCase();
  if (lower.includes('surge') || lower.includes('beat') || lower.includes('growth')) return 'positive';
  if (lower.includes('fall') || lower.includes('loss') || lower.includes('decline')) return 'negative';
  return 'neutral';
};

const getImpact = (title = '', desc = '') => {
  const text = `${title} ${desc}`;
  const score = (text.match(/ai|earnings|merger|iphone|forecast|inflation/gi) || []).length;
  if (score >= 3) return '🔥 High Impact';
  if (score === 2) return '⚠️ Medium Impact';
  return 'Low Impact';
};

// Expects items: [{ title, source, published_at, url, description }]
const NewsFeed = ({ items = [] }) => {
  return (
    <div className="space-y-3">
      {items.map((n, i) => (
        <a
          key={i}
          href={n.url}
          target="_blank"
          rel="noreferrer"
          className="block bg-white rounded-xl p-4 shadow border hover:shadow-md transition"
        >
          <div className="text-sm text-gray-500 flex gap-2">
            <span>{n.source || 'Unknown'}</span>
            <span>•</span>
            <span>{new Date((n.published_at || 0) * 1000).toLocaleString()}</span>
          </div>
          <div className="font-semibold">{n.title}</div>
          {n.description && <div className="text-sm text-gray-600 mt-1">{n.description}</div>}
          <div className="text-xs mt-2 flex gap-3">
            <span className="px-2 py-0.5 rounded bg-gray-100">
              {getSentiment(`${n.title}. ${n.description || ''}`)}
            </span>
            <span className="px-2 py-0.5 rounded bg-gray-100">
              {getImpact(n.title, n.description)}
            </span>
          </div>
        </a>
      ))}
    </div>
  );
};

export default NewsFeed;