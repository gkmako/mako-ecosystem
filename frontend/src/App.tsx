import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import Chat from './components/Chat';
import Admin from './components/Admin';

const App: React.FC = () => {
  useEffect(() => {
    const theme = localStorage.getItem('mako_theme') || 'root';
    if (theme !== 'root') {
      document.documentElement.setAttribute('data-theme', theme);
    }
  }, []);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/admin" element={<Admin />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;