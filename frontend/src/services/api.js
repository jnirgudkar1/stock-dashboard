// frontend/src/services/api.js
// Unified API client matching backend routes
// All functions throw on non-2xx responses.

const JSON_HDRS = { 'Cache-Control': 'no-cache' };

async function getJSON(path) {
  const res = await fetch(path, { headers: JSON_HDRS });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${txt}`);
  }
  return res.json();
}

// ---- Stocks ----
export function getPrices(symbol, { interval = '1day', limit = 200 } = {}) {
  return getJSON(
    `/api/stocks/${encodeURIComponent(symbol)}/prices?interval=${interval}&limit=${limit}`
  );
}

export function getMetadata(symbol) {
  return getJSON(`/api/stocks/${encodeURIComponent(symbol)}/metadata`);
}

export function getStockNews(symbol, { max = 20 } = {}) {
  return getJSON(`/api/stocks/${encodeURIComponent(symbol)}/news?max_items=${max}`);
}

export function getValuation(symbol) {
  return getJSON(`/api/stocks/${encodeURIComponent(symbol)}/valuation`);
}

export function getPrediction(symbol) {
  return getJSON(`/api/stocks/${encodeURIComponent(symbol)}/predict`);
}

// ---- Generic news ----
export function searchNews(query, { max = 20 } = {}) {
  return getJSON(`/api/news/search?query=${encodeURIComponent(query)}&max_items=${max}`);
}

export function fetchArticle(url) {
  return getJSON(`/api/news/article?url=${encodeURIComponent(url)}`);
}

// ---- Helpers to adapt to UI expectations ----
// Convert backend normalized list of bars into {date: 'YYYY-MM-DD', close, open, high, low, volume}
export function toRechartsSeries(normalized) {
  if (!normalized || !Array.isArray(normalized.prices)) return [];
  return normalized.prices.map(bar => {
    const d = new Date(bar.timestamp * 1000);
    const pad = n => String(n).padStart(2, '0');
    const date = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
    return {
      date,
      open: bar.open,
      high: bar.high,
      low: bar.low,
      close: bar.close,
      volume: bar.volume,
    };
  });
}