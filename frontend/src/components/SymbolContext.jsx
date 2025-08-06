// src/components/SymbolContext.jsx
import React, { createContext, useContext, useState } from 'react';

const SymbolContext = createContext();

export const SymbolProvider = ({ children }) => {
  const [symbol, setSymbol] = useState('AAPL');
  return (
    <SymbolContext.Provider value={{ symbol, setSymbol }}>
      {children}
    </SymbolContext.Provider>
  );
};

export const useSymbol = () => useContext(SymbolContext);