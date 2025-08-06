import React, { useEffect, useState } from 'react';

const AssetSummary = ({ symbol }) => {
  const [summary, setSummary] = useState('');

  useEffect(() => {
    fetch(`/api/summaries/${symbol}`)
      .then(res => res.json())
      .then(data => setSummary(data.summary))
      .catch(() => setSummary('Unable to fetch summary.'));
  }, [symbol]);

  return (
    <div className="bg-gray-100 p-4 rounded text-sm">
      <p>🤖 <strong>AI Summary</strong>: {summary}</p>
    </div>
  );
};

export default AssetSummary;