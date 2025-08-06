// src/components/Navigation.jsx
import React from 'react';
import { NavLink } from 'react-router-dom';

const tabs = [
  { name: 'Dashboard', to: '/' },
  { name: 'Insights', to: '/insights' },
  { name: 'Portfolio', to: '/portfolio' },
  { name: 'Valuation', to: '/valuation' },
];

const Navigation = () => {
  return (
    <nav className="flex justify-center space-x-4 mb-6">
      {tabs.map(tab => (
        <NavLink
          key={tab.name}
          to={tab.to}
          className={({ isActive }) =>
            `px-4 py-2 rounded-lg font-medium ${
              isActive
                ? 'bg-purple-600 text-white shadow'
                : 'text-purple-600 hover:bg-purple-100'
            }`
          }
        >
          {tab.name}
        </NavLink>
      ))}
    </nav>
  );
};

export default Navigation;