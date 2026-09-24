import React, { useState } from 'react';
import { Gamepad2, X, AlertCircle, CheckCircle2, Link2 } from 'lucide-react';
import { api } from '../services/api';

export default function FiveMLinkModal({ isOpen, onClose, onLinked, currentIdentifier }) {
  const [identifier, setIdentifier] = useState(currentIdentifier || '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!identifier.trim()) {
      setError('Please provide your FiveM player identifier.');
      return;
    }

    setLoading(true);
    setError('');
    setSuccessMsg('');

    try {
      const res = await api.fivem.link(identifier.trim());
      setSuccessMsg(res.message || 'FiveM account linked! 𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑 role assigned.');
      setTimeout(() => {
        onLinked(identifier.trim());
        onClose();
      }, 1500);
    } catch (err) {
      setError(err.message || 'Failed to link FiveM identifier.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.8)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 100,
      padding: '1rem'
    }}>
      <div className="glass-panel" style={{
        maxWidth: '480px',
        width: '100%',
        padding: '2rem',
        position: 'relative',
        boxShadow: '0 20px 40px rgba(0, 0, 0, 0.7)'
      }}>
        {/* Close Button */}
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '1.25rem',
            right: '1.25rem',
            background: 'transparent',
            border: 'none',
            color: 'var(--text-muted)',
            cursor: 'pointer'
          }}
        >
          <X size={20} />
        </button>

        {/* Modal Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem', marginBottom: '1.25rem' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '10px',
            background: 'rgba(6, 182, 212, 0.15)',
            border: '1px solid rgba(6, 182, 212, 0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Gamepad2 size={24} color="var(--cyan-400)" />
          </div>
          <div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#fff' }}>
              Link FiveM Player Account
            </h3>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
              Automatically grants the <strong>𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑</strong> role on Discord
            </p>
          </div>
        </div>

        {error && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.12)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            color: 'var(--danger-400)',
            padding: '0.75rem 1rem',
            borderRadius: 'var(--radius-md)',
            marginBottom: '1.25rem',
            fontSize: '0.85rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            <AlertCircle size={16} />
            {error}
          </div>
        )}

        {successMsg && (
          <div style={{
            background: 'rgba(16, 185, 129, 0.12)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            color: 'var(--emerald-400)',
            padding: '0.75rem 1rem',
            borderRadius: 'var(--radius-md)',
            marginBottom: '1.25rem',
            fontSize: '0.85rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            <CheckCircle2 size={16} />
            {successMsg}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
              FiveM Identifier / CFX ID / License:
            </label>
            <input
              type="text"
              className="form-input"
              placeholder="e.g. license:4a88f7..., steam:110000..., or CFX username"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              disabled={loading}
              autoFocus
            />
            <div style={{ fontSize: '0.74rem', color: 'var(--text-dim)', marginTop: '0.45rem' }}>
              You can find your Rockstar License or Steam ID inside your FiveM settings or in-game player ID.
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
            <button
              type="button"
              className="btn btn-outline"
              onClick={onClose}
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
            >
              <Link2 size={16} />
              {loading ? 'Linking & Assigning...' : 'Link FiveM Account'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
