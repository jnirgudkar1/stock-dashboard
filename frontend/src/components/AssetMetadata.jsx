const AssetMetadata = ({ metadata }) => {
  if (!metadata) return null;

  return (
    <div className="p-4 bg-gray-50 rounded border text-sm space-y-1">
      <h3 className="font-medium text-gray-700">📋 Asset Metadata</h3>
      <p>Market Cap: <span className="font-semibold">{metadata.marketCap}</span></p>
      <p>P/E Ratio: <span className="font-semibold">{metadata.peRatio}</span></p>
      <p>EPS: <span className="font-semibold">{metadata.eps}</span></p>
      <p>Dividend Yield: <span className="font-semibold">{metadata.dividendYield}</span></p>
    </div>
  );
};

export default AssetMetadata;