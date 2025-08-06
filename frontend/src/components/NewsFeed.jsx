import React from 'react';

const getSentiment = (text = '') => {
  const lower = text.toLowerCase();
  if (lower.includes('surge') || lower.includes('beat') || lower.includes('growth')) return 'positive';
  if (lower.includes('fall') || lower.includes('loss') || lower.includes('decline')) return 'negative';
  return 'neutral';
};

const getImpactScore = (text = '') => {
  const score = (text.match(/ai|earnings|merger|iphone|forecast|inflation/gi) || []).length;
  if (score >= 3) return '🔥 High Impact';
  if (score === 2) return '⚠️ Medium Impact';
  if (score === 1) return '🟡 Low Impact';
  return null;
};

const NewsFeed = ({ articles = [] }) => {
  if (!articles.length) return <p className="text-gray-500">No news available.</p>;

  return (
    <div className="space-y-4">
      {articles.map((a, i) => {
        const sentiment = getSentiment(a.title + ' ' + a.description);
        const impact = getImpactScore(a.title + ' ' + a.description);

        return (
          <div key={i} className="border rounded-lg p-4 shadow flex gap-4 bg-white">
            <img src={a.image} alt={a.title} className="w-28 h-20 object-cover rounded" />
            <div className="flex-1">
              <a href={a.url} target="_blank" rel="noopener noreferrer" className="text-blue-700 font-semibold hover:underline">
                {a.title}
              </a>
              <p className="text-sm text-gray-600 mb-1">
                {a.source?.name} • {new Date(a.publishedAt).toLocaleDateString()}
              </p>
              <p className="text-sm text-gray-800">{a.description}</p>
              <div className="text-xs mt-1 text-gray-600 flex gap-2">
                {impact && <span>{impact}</span>}
                {sentiment === 'positive' && <span className="text-green-600">🟢 Positive</span>}
                {sentiment === 'negative' && <span className="text-red-600">🔴 Negative</span>}
                {sentiment === 'neutral' && <span className="text-gray-500">⚪ Neutral</span>}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default NewsFeed;