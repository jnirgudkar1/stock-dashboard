// src/components/AssetTabs.jsx
import React, { useEffect, useState } from 'react';

const AssetTabs = ({ symbol, type }) => {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch(`/api/${type}/${symbol}`)
      .then(res => res.json())
      .then(setData)
      .catch(console.error);
  }, [symbol, type]);

  return (
    <div className="p-4 bg-white rounded-lg shadow-md">
      <h2 className="text-xl font-semibold mb-2">{symbol} ({type.toUpperCase()})</h2>
      {data ? (
        <pre className="text-sm text-gray-700">{JSON.stringify(data, null, 2)}</pre>
      ) : (
        <p className="text-gray-500">Loading data...</p>
      )}
    </div>
  );
};

export default AssetTabs;