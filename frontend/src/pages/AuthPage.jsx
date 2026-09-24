import React, { useState } from 'react';
import { Shield, ArrowRight, UserPlus, LogIn, CheckCircle2, Lock, ShieldCheck, Gamepad2 } from 'lucide-react';
import { api } from '../services/api';

export default function AuthPage({ onAuthSuccess }) {
  const [isLogin, setIsLogin] = useState(false);
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      let res;
      if (isLogin) {
        res = await api.auth.login(username || email, password);
      } else {
        if (!email.trim() || !username.trim() || !password.trim()) {
          throw new Error('Please fill in all required fields.');
        }
        res = await api.auth.register(email.trim(), username.trim(), password);
      }

      localStorage.setItem('nmc_auth_token', res.access_token);
      onAuthSuccess(res.user);
    } catch (err) {
      setError(err.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleDirectDiscordAuth = async () => {
    try {
      setLoading(true);
      const res = await api.discord.getLoginUrl();
      if (res && res.url) {
        window.location.href = res.url;
      }
    } catch (err) {
      setError('Failed to initiate Discord OAuth: ' + err.message);
      setLoading(false);
    }
  };

  return (
    <div style={{
      maxWidth: '1100px',
      margin: '3rem auto',
      padding: '0 1.5rem',
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
      gap: '2.5rem',
      alignItems: 'center'
    }}>
      {/* Left Info Column */}
      <div>
        <div className="badge badge-gold" style={{ marginBottom: '1rem' }}>
          ⭐ OFFICIAL SERVER PORTAL
        </div>
        <h1 style={{
          fontSize: '2.75rem',
          fontWeight: 900,
          lineHeight: 1.15,
          color: '#fff',
          marginBottom: '1rem'
        }}>
          Automated FiveM & Discord Role System
        </h1>
        <p style={{ fontSize: '1.05rem', color: 'var(--text-muted)', marginBottom: '2rem' }}>
          Connect your Discord account and FiveM identifier to automatically receive verified server roles without waiting for administrators.
        </p>

        {/* Feature Progression Flow */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.85rem' }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: 'rgba(245, 158, 11, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0
            }}>
              <CheckCircle2 size={18} color="var(--gold-400)" />
            </div>
            <div>
              <div style={{ fontWeight: 700, color: '#fff', fontSize: '0.95rem' }}>
                1. Register Website Account
              </div>
              <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                Create your player account or log in with one click.
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.85rem' }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: 'rgba(16, 185, 129, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0
            }}>
              <ShieldCheck size={18} color="var(--emerald-400)" />
            </div>
            <div>
              <div style={{ fontWeight: 700, color: '#fff', fontSize: '0.95rem' }}>
                2. Connect Discord &rarr; Auto 𝐍𝐌𝐂 𝐂𝐈𝐓𝐈𝐙𝐄𝐍
              </div>
              <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                Bot verifies NMC SERVER membership and grants Citizen role immediately.
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.85rem' }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: 'rgba(6, 182, 212, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0
            }}>
              <Gamepad2 size={18} color="var(--cyan-400)" />
            </div>
            <div>
              <div style={{ fontWeight: 700, color: '#fff', fontSize: '0.95rem' }}>
                3. Link FiveM &rarr; Auto 𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑
              </div>
              <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                Link your player license or CFX ID to instantly receive Player privileges.
              </div>
            </div>
          </div>
        </div>

        {/* Security disclaimer */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: '0.85rem 1rem',
          fontSize: '0.8rem',
          color: 'var(--text-dim)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.65rem'
        }}>
          <Lock size={16} color="var(--gold-400)" />
          <span>
            <strong>Security Notice:</strong> 𝐍𝐌𝐂 𝐒𝐄𝐑𝐕𝐄𝐑 𝐓𝐄𝐀𝐌 is never assigned automatically and is strictly controlled by server staff.
          </span>
        </div>
      </div>

      {/* Right Form Card */}
      <div className="glass-panel panel-glow-gold" style={{ padding: '2.5rem' }}>
        {/* Tab switch */}
        <div style={{
          display: 'flex',
          background: 'rgba(0, 0, 0, 0.4)',
          padding: '0.3rem',
          borderRadius: 'var(--radius-md)',
          marginBottom: '1.75rem',
          border: '1px solid var(--border-subtle)'
        }}>
          <button
            type="button"
            onClick={() => { setIsLogin(false); setError(''); }}
            style={{
              flex: 1,
              padding: '0.65rem',
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              background: !isLogin ? 'var(--gold-500)' : 'transparent',
              color: !isLogin ? '#000' : 'var(--text-muted)',
              fontWeight: 700,
              fontSize: '0.9rem',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            Create Account
          </button>
          <button
            type="button"
            onClick={() => { setIsLogin(true); setError(''); }}
            style={{
              flex: 1,
              padding: '0.65rem',
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              background: isLogin ? 'var(--gold-500)' : 'transparent',
              color: isLogin ? '#000' : 'var(--text-muted)',
              fontWeight: 700,
              fontSize: '0.9rem',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            Sign In
          </button>
        </div>

        {error && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            color: 'var(--danger-400)',
            padding: '0.75rem 1rem',
            borderRadius: 'var(--radius-md)',
            marginBottom: '1.25rem',
            fontSize: '0.85rem'
          }}>
            {error}
          </div>
        )}

        {/* 1-Click Discord OAuth Register/Login */}
        <button
          type="button"
          onClick={handleDirectDiscordAuth}
          className="btn btn-discord"
          style={{ width: '100%', marginBottom: '1.5rem', padding: '0.85rem' }}
          disabled={loading}
        >
          <svg width="20" height="20" viewBox="0 0 127.14 96.36" fill="currentColor">
            <path d="M107.7,8.07A105.15,105.15,0,0,0,81.47,0a72.06,72.06,0,0,0-3.36,6.83A97.68,97.68,0,0,0,49,6.83,72.37,72.37,0,0,0,45.64,0,105.89,105.89,0,0,0,19.39,8.09C2.79,32.65-1.71,56.6.54,80.21h0A105.73,105.73,0,0,0,32.71,96.36,77.7,77.7,0,0,0,39.6,85.25a68.42,68.42,0,0,1-10.85-5.18c.91-.66,1.8-1.34,2.66-2a75.57,75.57,0,0,0,64.32,0c.87.71,1.76,1.39,2.66,2a68.68,68.68,0,0,1-10.87,5.19,77,77,0,0,0,6.89,11.1A105.25,105.25,0,0,0,126.6,80.22h0C129.24,52.84,122.09,29.11,107.7,8.07ZM42.45,65.69C36.18,65.69,31,60,31,53s5-12.74,11.43-12.74S54,45.91,53.89,53,48.84,65.69,42.45,65.69Zm42.24,0C78.41,65.69,73.25,60,73.25,53s5-12.74,11.44-12.74S96.23,45.91,96.12,53,91.08,65.69,84.69,65.69Z"/>
          </svg>
          Continue with Discord
        </button>

        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '1rem',
          margin: '1.25rem 0',
          color: 'var(--text-dim)',
          fontSize: '0.78rem'
        }}>
          <div style={{ flex: 1, height: '1px', background: 'var(--border-subtle)' }}></div>
          <span>OR CONTINUE WITH EMAIL</span>
          <div style={{ flex: 1, height: '1px', background: 'var(--border-subtle)' }}></div>
        </div>

        <form onSubmit={handleSubmit}>
          {!isLogin && (
            <div style={{ marginBottom: '1.15rem' }}>
              <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.4rem' }}>
                Email Address
              </label>
              <input
                type="email"
                className="form-input"
                placeholder="name@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required={!isLogin}
                disabled={loading}
              />
            </div>
          )}

          <div style={{ marginBottom: '1.15rem' }}>
            <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.4rem' }}>
              {isLogin ? 'Username or Email' : 'Username'}
            </label>
            <input
              type="text"
              className="form-input"
              placeholder={isLogin ? 'Enter your username or email' : 'Choose a unique username'}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              disabled={loading}
            />
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.4rem' }}>
              Password
            </label>
            <input
              type="password"
              className="form-input"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={loading}
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', padding: '0.85rem' }}
            disabled={loading}
          >
            {loading ? 'Processing...' : isLogin ? 'Sign In to Dashboard' : 'Complete Registration'}
            <ArrowRight size={16} />
          </button>
        </form>
      </div>
    </div>
  );
}
