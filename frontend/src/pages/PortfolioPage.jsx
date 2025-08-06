import React, { useState, useEffect } from 'react';

const PortfolioPage = () => {
  const [portfolio, setPortfolio] = useState([]);
  const [form, setForm] = useState({
    ticker: '',
    price: '',
    quantity: '',
    date: '',
  });

  useEffect(() => {
    const saved = localStorage.getItem('portfolio');
    if (saved) setPortfolio(JSON.parse(saved));
  }, []);

  useEffect(() => {
    localStorage.setItem('portfolio', JSON.stringify(portfolio));
  }, [portfolio]);

  const handleChange = e => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const addEntry = () => {
    if (!form.ticker || !form.price || !form.quantity) return;
    setPortfolio([...portfolio, { ...form, id: Date.now() }]);
    setForm({ ticker: '', price: '', quantity: '', date: '' });
  };

  const removeEntry = id => {
    setPortfolio(portfolio.filter(p => p.id !== id));
  };

  return (
    <div className="p-4 space-y-6">
      <h2 className="text-xl font-semibold">📊 Paper Portfolio</h2>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-gray-50 p-4 rounded">
        <input
          name="ticker"
          value={form.ticker}
          onChange={handleChange}
          placeholder="Ticker (e.g., AAPL)"
          className="border p-2 rounded"
        />
        <input
          name="price"
          value={form.price}
          onChange={handleChange}
          type="number"
          placeholder="Buy Price"
          className="border p-2 rounded"
        />
        <input
          name="quantity"
          value={form.quantity}
          onChange={handleChange}
          type="number"
          placeholder="Quantity"
          className="border p-2 rounded"
        />
        <input
          name="date"
          value={form.date}
          onChange={handleChange}
          type="date"
          className="border p-2 rounded"
        />
        <button
          onClick={addEntry}
          className="col-span-full md:col-span-1 bg-blue-600 text-white py-2 rounded hover:bg-blue-700"
        >
          ➕ Add Trade
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full text-sm border rounded">
          <thead>
            <tr className="bg-gray-100 text-left">
              <th className="p-2">Ticker</th>
              <th className="p-2">Buy Price</th>
              <th className="p-2">Quantity</th>
              <th className="p-2">Date</th>
              <th className="p-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {portfolio.map((entry) => (
              <tr key={entry.id} className="border-t">
                <td className="p-2 font-semibold">{entry.ticker}</td>
                <td className="p-2">${entry.price}</td>
                <td className="p-2">{entry.quantity}</td>
                <td className="p-2">{entry.date || '—'}</td>
                <td className="p-2">
                  <button
                    onClick={() => removeEntry(entry.id)}
                    className="text-red-500 hover:underline"
                  >
                    ❌ Remove
                  </button>
                </td>
              </tr>
            ))}
            {portfolio.length === 0 && (
              <tr>
                <td colSpan="5" className="p-2 text-center text-gray-500">
                  No entries yet
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default PortfolioPage;