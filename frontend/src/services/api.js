// frontend/src/services/api.js
// Robust API client that avoids fetching the frontend's index.html by mistake.
// Tries absolute API URLs first (with and without /api), supports dev fallbacks,
// and accepts both number and object forms for certain options.
// Set VITE_API_BASE=http://localhost:8000 in frontend/.env(.local) to pin the base.

const JSON_HDRS = { 'Cache-Control': 'no-cache' };

// Resolve API base from env or sensible defaults
const ENV_BASE =
  (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE) || '';

const isDev = typeof import.meta !== 'undefined' && !!import.meta.env && import.meta.env.DEV;
const here = (typeof window !== 'undefined' && window.location) ? window.location : { protocol: 'http:', hostname: 'localhost', port: '' };

// Build candidate absolute bases
const defaultPortBase =
  (here.port && here.port !== '8000')
    ? `${here.protocol}//${here.hostname}:8000`
    : `${here.protocol}//${here.hostname}${here.port ? ':' + here.port : ''}`;

// Primary base list (unique, in order)
const BASES = Array.from(new Set([
  ENV_BASE,
  isDev ? 'http://localhost:8000' : '',
  isDev ? 'http://127.0.0.1:8000' : '',
  defaultPortBase,
  '', // same-origin
].filter(Boolean)));

function qs(params = {}) {
  const usp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null) usp.set(k, String(v));
  });
  const s = usp.toString();
  return s ? `?${s}` : '';
}

function join(base, path) {
  if (!base) return path;
  if (path.startsWith('/')) return base + path;
  return base.replace(/\/+$/, '') + '/' + path.replace(/^\/+/, '');
}

function withApiPrefix(path) {
  return path.startsWith('/api') ? path : '/api' + path;
}

async function getJSONInternal(path) {
  const candidates = [];
  for (const b of BASES) {
    candidates.push(join(b, path));
    candidates.push(join(b, withApiPrefix(path)));
  }

  let lastErr;
  for (const url of candidates) {
    try {
      const res = await fetch(url, { headers: JSON_HDRS });
      const ct = (res.headers.get('content-type') || '').toLowerCase();

      if (res.ok && ct.includes('application/json')) {
        return await res.json();
      }
      if (ct.includes('text/html')) {
        lastErr = new Error(`Got HTML from ${url}`);
        continue;
      }
      const txt = await res.text();
      lastErr = new Error(`${res.status} ${res.statusText} at ${url}: ${txt}`);
    } catch (e) {
      lastErr = e;
    }
  }
  throw lastErr || new Error('Network error');
}

async function getJSON(path) {
  return getJSONInternal(path);
}

// ---- Stocks ----

export async function getPrices(symbol, opts = {}) {
  const { interval = '1day', limit = 200 } = opts;
  return getJSON(`/stocks/${encodeURIComponent(symbol)}/prices${qs({ interval, limit })}`);
}

export async function getMetadata(symbol) {
  return getJSON(`/stocks/${encodeURIComponent(symbol)}/metadata`);
}

export async function getValuation(symbol) {
  return getJSON(`/stocks/${encodeURIComponent(symbol)}/valuation`);
}

export async function getPrediction(symbol, opts = {}) {
  const { temp } = opts || {};
  return getJSON(`/stocks/${encodeURIComponent(symbol)}/predict${qs({ temp })}`);
}

export async function getFeatures(symbol, opts = {}) {
  const { interval = '1day', limit = 240, max_news = 50 } = opts;
  return getJSON(`/stocks/${encodeURIComponent(symbol)}/features${qs({ interval, limit, max_news })}`);
}

// ---- News ----
// Accepts either getStockNews(symbol, 20) OR getStockNews(symbol, { max: 20 }) / { max_items, limit }
export async function getStockNews(symbol, maxOrOpts = 20) {
  let maxItems = 20;
  if (typeof maxOrOpts === 'number') {
    maxItems = maxOrOpts;
  } else if (maxOrOpts && typeof maxOrOpts === 'object') {
    maxItems = Number(maxOrOpts.max ?? maxOrOpts.max_items ?? maxOrOpts.limit ?? 20);
  }
  return getJSON(`/stocks/${encodeURIComponent(symbol)}/news${qs({ max_items: maxItems })}`);
}

export async function getArticle(urlStr) {
  return getJSON(`/news/article${qs({ url: urlStr })}`);
}

// ---- Helpers ----

export function toRechartsSeries(normalized) {
  if (!normalized || !Array.isArray(normalized.prices)) return [];
  return normalized.prices.map((bar) => {
    const d = new Date(Number(bar.timestamp) * 1000);
    const pad = (n) => String(n).padStart(2, '0');
    const date = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
    return {
      date,
      open: Number(bar.open),
      high: Number(bar.high),
      low: Number(bar.low),
      close: Number(bar.close),
      volume: Number(bar.volume),
    };
  });
}