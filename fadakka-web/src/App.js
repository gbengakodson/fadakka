import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/layout/Navbar';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import CoinList from './CoinList';
import Trade from './pages/Trade';
import Portfolio from './pages/portfolio/Portfolio';
import Transactions from './pages/transactions/Transactions';
import './App.css';
import YieldDashboard from './pages/yield/YieldDashboard';
import Profile from './pages/Profile';
import Settings from './pages/Settings';

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <div className="loading-container">Loading...</div>;
  }

  return isAuthenticated ? children : <Navigate to="/login" />;
};

function AppContent() {
  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/yield" element={
          <ProtectedRoute>
             <YieldDashboard />
          </ProtectedRoute>
        } />
        <Route path="/" element={<CoinList />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/dashboard" element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        } />
        <Route path="/portfolio" element={
          <ProtectedRoute>
            <Portfolio />
          </ProtectedRoute>
        } />
        <Route path="/transactions" element={
          <ProtectedRoute>
            <Transactions />
          </ProtectedRoute>
        } />
        <Route path="/trade/:coinId" element={
          <ProtectedRoute>
            <Trade />
          </ProtectedRoute>
        } />

        <Route path="/profile" element={
           <ProtectedRoute>
             <Profile />
           </ProtectedRoute>} />
        <Route path="/settings" element={
            <ProtectedRoute>
                <Settings />
            </ProtectedRoute>} />

      </Routes>
    </>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </Router>
  );
}

export default App;