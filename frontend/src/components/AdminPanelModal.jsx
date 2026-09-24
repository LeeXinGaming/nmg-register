import React, { useState, useEffect } from 'react';
import { X, Shield, Terminal, Crown, Trash2, RefreshCw, AlertTriangle, CheckCircle } from 'lucide-react';
import { api } from '../services/api';

export default function AdminPanelModal({ isOpen, onClose }) {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [targetDiscordId, setTargetDiscordId] = useState('');
  const [roleToAssign, setRoleToAssign] = useState('1550320871128957020'); // Server Team default
  const [actionReason, setActionReason] = useState('Administrative promotion');
  const [actionStatus, setActionStatus] = useState({ error: '', success: '', loading: false });

  useEffect(() => {
    if (isOpen) {
      loadLogs();
    }
  }, [isOpen]);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const data = await api.admin.getLogs();
      setLogs(data);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRoleAction = async (isAssign) => {
    if (!targetDiscordId.trim()) {
      setActionStatus({ error: 'Please enter a target Discord User ID.', success: '', loading: false });
      return;
    }

    setActionStatus({ error: '', success: '', loading: true });
    try {
      if (isAssign) {
        await api.admin.assignRole(targetDiscordId.trim(), roleToAssign, actionReason);
        setActionStatus({ error: '', success: `Role successfully assigned to ${targetDiscordId}.`, loading: false });
      } else {
        await api.admin.removeRole(targetDiscordId.trim(), roleToAssign, actionReason);
        setActionStatus({ error: '', success: `Role successfully removed from ${targetDiscordId}.`, loading: false });
      }
      loadLogs();
    } catch (err) {
      setActionStatus({ error: err.message || 'Operation failed.', success: '', loading: false });
    }
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.85)',
      backdropFilter: 'blur(10px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 100,
      padding: '1rem'
    }}>
      <div className="glass-panel" style={{
        maxWidth: '850px',
        width: '100%',
        maxHeight: '90vh',
        overflowY: 'auto',
        padding: '2rem',
        position: 'relative',
        boxShadow: '0 25px 50px rgba(0, 0, 0, 0.8)'
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
          <X size={22} />
        </button>

        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem', marginBottom: '1.5rem' }}>
          <div style={{
            width: '44px',
            height: '44px',
            borderRadius: '12px',
            background: 'rgba(245, 158, 11, 0.15)',
            border: '1px solid rgba(245, 158, 11, 0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Terminal size={22} color="var(--gold-400)" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#fff' }}>
              NMC SERVER — Staff Command Console
            </h2>
            <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)' }}>
              Secure administrative role assignment & real-time audit log stream
            </p>
          </div>
        </div>

        {/* Manual Role Control Box */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: '1.25rem',
          marginBottom: '2rem'
        }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--gold-400)', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Crown size={16} /> Manage Roles (Including 𝐍𝐌𝐂 𝐒𝐄𝐑𝐕𝐄𝐑 𝐓𝐄𝐀𝐌)
          </h3>

          {actionStatus.error && (
            <div style={{
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: 'var(--danger-400)',
              padding: '0.65rem 0.9rem',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.84rem',
              marginBottom: '1rem'
            }}>
              {actionStatus.error}
            </div>
          )}

          {actionStatus.success && (
            <div style={{
              background: 'rgba(16, 185, 129, 0.15)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              color: 'var(--emerald-400)',
              padding: '0.65rem 0.9rem',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.84rem',
              marginBottom: '1rem'
            }}>
              {actionStatus.success}
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                Target Discord User ID:
              </label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. 1549509737060638751"
                value={targetDiscordId}
                onChange={(e) => setTargetDiscordId(e.target.value)}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                Select Role:
              </label>
              <select
                className="form-input"
                value={roleToAssign}
                onChange={(e) => setRoleToAssign(e.target.value)}
                style={{ background: 'var(--bg-input)' }}
              >
                <option value="1550320871128957020">👑 𝐍𝐌𝐂 𝐒𝐄𝐑𝐕𝐄𝐑 𝐓𝐄𝐀𝐌 (Staff Only)</option>
                <option value="1550320871128957018">🏛️ 𝐍𝐌𝐂 𝐂𝐈𝐓𝐈𝐙𝐄𝐍</option>
                <option value="1550320871128957019">🎮 𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                Reason for Action:
              </label>
              <input
                type="text"
                className="form-input"
                placeholder="Reason recorded in audit log"
                value={actionReason}
                onChange={(e) => setActionReason(e.target.value)}
              />
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
            <button
              className="btn btn-danger"
              style={{ padding: '0.55rem 1.1rem', fontSize: '0.88rem' }}
              onClick={() => handleRoleAction(false)}
              disabled={actionStatus.loading}
            >
              <Trash2 size={15} /> Remove Role
            </button>
            <button
              className="btn btn-primary"
              style={{ padding: '0.55rem 1.1rem', fontSize: '0.88rem' }}
              onClick={() => handleRoleAction(true)}
              disabled={actionStatus.loading}
            >
              <Crown size={15} /> Assign Role
            </button>
          </div>
        </div>

        {/* Audit Log Stream */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.85rem' }}>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fff' }}>
              System Audit Logs
            </h3>
            <button
              onClick={loadLogs}
              className="btn btn-outline"
              style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem' }}
              disabled={loading}
            >
              <RefreshCw size={13} className={loading ? 'animate-spin' : ''} /> Refresh
            </button>
          </div>

          {logs.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-dim)', fontSize: '0.88rem' }}>
              No audit logs recorded yet.
            </div>
          ) : (
            <div style={{
              background: 'rgba(0, 0, 0, 0.4)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              maxHeight: '320px',
              overflowY: 'auto'
            }}>
              {logs.map((log) => (
                <div
                  key={log.id}
                  style={{
                    padding: '0.75rem 1rem',
                    borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: '0.84rem'
                  }}
                >
                  <div>
                    <span style={{
                      fontWeight: 700,
                      color: log.action.includes('ROLE_ASSIGNED') ? 'var(--emerald-400)' :
                             log.action.includes('REMOVED') ? 'var(--danger-400)' : 'var(--cyan-400)',
                      marginRight: '0.6rem'
                    }}>
                      [{log.action}]
                    </span>
                    <span style={{ color: 'var(--text-muted)' }}>
                      Target: <strong style={{ color: '#fff' }}>{log.target_discord_id || 'System'}</strong> |
                      Reason: <em>{log.reason || 'None'}</em>
                    </span>
                  </div>
                  <div style={{ color: 'var(--text-dim)', fontSize: '0.74rem' }}>
                    {log.created_at ? new Date(log.created_at).toLocaleString() : ''}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
