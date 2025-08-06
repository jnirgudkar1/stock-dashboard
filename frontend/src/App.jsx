// src/App.jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navigation from './components/Navigation';
import DashboardPage from './pages/DashboardPage';
import InsightsPage from './pages/InsightsPage';
import PortfolioPage from './pages/PortfolioPage';
import ValuationPage from './pages/ValuationPage';
import SymbolSelector from './components/SymbolSelector';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-100 p-6">
        <h1 className="text-3xl font-bold text-center text-purple-600 mb-4">
          📈 Innovative Investment Dashboard
        </h1>
        <SymbolSelector />
        <Navigation />
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/insights" element={<InsightsPage />} />
          <Route path="/portfolio" element={<PortfolioPage />} />
          <Route path="/valuation" element={<ValuationPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;