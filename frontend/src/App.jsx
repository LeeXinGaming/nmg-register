import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import AuthPage from './pages/AuthPage';
import DashboardPage from './pages/DashboardPage';
import AdminPanelModal from './components/AdminPanelModal';
import { api } from './services/api';

export default function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAdminOpen, setIsAdminOpen] = useState(false);
  const [botInfo, setBotInfo] = useState(null);

  useEffect(() => {
    checkAuth();
    checkBotHealth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('nmc_auth_token');
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      const userData = await api.auth.me();
      setUser(userData);
    } catch (err) {
      console.warn('Session expired or invalid token:', err);
      localStorage.removeItem('nmc_auth_token');
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const checkBotHealth = async () => {
    try {
      const data = await api.health();
      setBotInfo(data);
    } catch (err) {
      console.warn('Could not reach health check:', err);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('nmc_auth_token');
    setUser(null);
  };

  if (loading) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'var(--text-muted)'
      }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
          <div style={{
            width: '40px',
            height: '40px',
            border: '3px solid rgba(245, 158, 11, 0.2)',
            borderTopColor: 'var(--gold-500)',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }}></div>
          <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
          <span>Loading NMC Portal...</span>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar
        user={user}
        onLogout={handleLogout}
        onOpenAdmin={() => setIsAdminOpen(true)}
        botInfo={botInfo}
      />

      <main style={{ flex: 1 }}>
        {!user ? (
          <AuthPage onAuthSuccess={(userData) => setUser(userData)} />
        ) : (
          <DashboardPage
            user={user}
            onUserUpdate={(updatedUser) => setUser(updatedUser)}
          />
        )}
      </main>

      <footer style={{
        textAlign: 'center',
        padding: '2rem 1.5rem',
        borderTop: '1px solid var(--border-subtle)',
        fontSize: '0.82rem',
        color: 'var(--text-dim)',
        marginTop: 'auto'
      }}>
        NMC SERVER © 2026. All rights reserved. Automated FiveM & Discord Role Management.
      </footer>

      {user?.is_admin && (
        <AdminPanelModal
          isOpen={isAdminOpen}
          onClose={() => setIsAdminOpen(false)}
        />
      )}
    </div>
  );
}
