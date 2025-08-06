// src/api.js

export async function fetchStockPrice(symbol) {
  const res = await fetch(`/api/stocks/${symbol}`, {
    headers: {
      'Cache-Control': 'no-cache',
    },
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Failed to fetch stock data: ${res.status} - ${errText}`);
  }

  return await res.json();
}

export async function fetchNews(symbol) {
  const res = await fetch(`/api/news/${symbol}`, {
    headers: { 'Cache-Control': 'no-cache' },
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Failed to fetch news: ${res.status} - ${errText}`);
  }

  return await res.json();
}