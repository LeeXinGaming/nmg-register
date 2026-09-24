import React, { useState, useEffect } from 'react';
import {
  Shield,
  RefreshCw,
  Link2,
  Unlink,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Gamepad2,
  Server,
  User,
  Sparkles
} from 'lucide-react';
import { api } from '../services/api';
import RoleCard from '../components/RoleCard';
import FiveMLinkModal from '../components/FiveMLinkModal';

export default function DashboardPage({ user, onUserUpdate }) {
  const [discordStatus, setDiscordStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [statusMessage, setStatusMessage] = useState(null);
  const [showFiveMModal, setShowFiveMModal] = useState(false);

  // Check URL query parameters for redirects from Discord OAuth
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('discord_linked') === 'true') {
      const isMember = params.get('is_member') === 'true';
      const citizenAssigned = params.get('citizen_assigned') === 'true';

      setStatusMessage({
        type: 'success',
        title: 'Registration & Verification Successful!',
        lines: [
          'Registration successful!',
          'Your Discord account has been connected.',
          citizenAssigned
            ? '𝐍𝐌𝐂 𝐂𝐈𝐓𝐈𝐙𝐄𝐍 role has been assigned automatically.'
            : isMember
            ? 'You are a verified member of NMC SERVER.'
            : 'Please join the NMC SERVER Discord to receive your 𝐍𝐌𝐂 𝐂𝐈𝐓𝐈𝐙𝐄𝐍 role!'
        ]
      });
      // Clean query params from URL
      window.history.replaceState({}, document.title, window.location.pathname);
    } else if (params.get('discord_error')) {
      setStatusMessage({
        type: 'error',
        title: 'Discord Connection Notice',
        lines: ['Failed to link Discord account or authentication was cancelled.']
      });
      window.history.replaceState({}, document.title, window.location.pathname);
    }

    loadStatus();
  }, []);

  const loadStatus = async () => {
    setLoading(true);
    try {
      const data = await api.discord.getStatus();
      setDiscordStatus(data);
      // Refresh current user data as well
      const updatedUser = await api.auth.me();
      onUserUpdate(updatedUser);
    } catch (err) {
      console.error('Failed to load status:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleConnectDiscord = async () => {
    setConnecting(true);
    try {
      const res = await api.discord.getLoginUrl(user.id);
      if (res && res.url) {
        window.location.href = res.url;
      }
    } catch (err) {
      setStatusMessage({
        type: 'error',
        title: 'OAuth Error',
        lines: [err.message || 'Could not initiate Discord OAuth.']
      });
      setConnecting(false);
    }
  };

  const handleSyncRoles = async () => {
    setSyncing(true);
    setStatusMessage(null);
    try {
      const res = await api.discord.sync();
      await loadStatus();

      if (res.assigned_roles && res.assigned_roles.length > 0) {
        setStatusMessage({
          type: 'success',
          title: 'Roles Synchronized!',
          lines: res.assigned_roles.map((r) => `${r} role has been assigned automatically.`)
        });
      } else {
        setStatusMessage({
          type: 'info',
          title: 'Synchronization Complete',
          lines: [res.message || 'All eligible Discord roles are already up to date.']
        });
      }
    } catch (err) {
      setStatusMessage({
        type: 'error',
        title: 'Role Sync Notice',
        lines: [err.message || 'Discord role synchronization failed. Please try again.']
      });
    } finally {
      setSyncing(false);
    }
  };

  const handleUnlinkDiscord = async () => {
    if (!window.confirm('Are you sure you want to unlink your Discord account? Your NMC server roles may be revoked.')) {
      return;
    }
    setLoading(true);
    try {
      await api.discord.unlink();
      await loadStatus();
      setStatusMessage({
        type: 'info',
        title: 'Discord Unlinked',
        lines: ['Your Discord account has been disconnected.']
      });
    } catch (err) {
      setStatusMessage({
        type: 'error',
        title: 'Error Unlinking',
        lines: [err.message || 'Failed to unlink Discord account.']
      });
    } finally {
      setLoading(false);
    }
  };

  const handleFiveMLinked = async (ident) => {
    await loadStatus();
    setStatusMessage({
      type: 'success',
      title: 'FiveM Player Linked!',
      lines: [
        'FiveM player account successfully verified.',
        '𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑 role has been assigned automatically.'
      ]
    });
  };

  const isConnected = discordStatus?.connected;
  const isMember = discordStatus?.is_guild_member;
  const roles = discordStatus?.roles || [];

  return (
    <div style={{ maxWidth: '1200px', margin: '2rem auto', padding: '0 1.5rem' }}>
      {/* Dynamic Celebration / Feedback Banner */}
      {statusMessage && (
        <div style={{
          background: statusMessage.type === 'success' ? 'rgba(16, 185, 129, 0.12)' :
                      statusMessage.type === 'error' ? 'rgba(239, 68, 68, 0.12)' : 'rgba(6, 182, 212, 0.12)',
          border: `1px solid ${statusMessage.type === 'success' ? 'rgba(16, 185, 129, 0.35)' :
                                statusMessage.type === 'error' ? 'rgba(239, 68, 68, 0.35)' : 'rgba(6, 182, 212, 0.35)'}`,
          borderRadius: 'var(--radius-lg)',
          padding: '1.25rem 1.5rem',
          marginBottom: '2rem',
          boxShadow: '0 10px 25px rgba(0, 0, 0, 0.4)',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '1rem'
        }}>
          {statusMessage.type === 'success' ? (
            <Sparkles size={24} color="var(--emerald-400)" style={{ flexShrink: 0, marginTop: '2px' }} />
          ) : statusMessage.type === 'error' ? (
            <AlertCircle size={24} color="var(--danger-400)" style={{ flexShrink: 0, marginTop: '2px' }} />
          ) : (
            <CheckCircle2 size={24} color="var(--cyan-400)" style={{ flexShrink: 0, marginTop: '2px' }} />
          )}

          <div style={{ flex: 1 }}>
            <h4 style={{
              fontSize: '1.05rem',
              fontWeight: 700,
              color: statusMessage.type === 'success' ? 'var(--emerald-400)' :
                     statusMessage.type === 'error' ? 'var(--danger-400)' : 'var(--cyan-400)',
              marginBottom: '0.35rem'
            }}>
              {statusMessage.title}
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
              {statusMessage.lines.map((line, idx) => (
                <div key={idx} style={{ fontSize: '0.92rem', color: '#fff', fontWeight: 500 }}>
                  {line}
                </div>
              ))}
            </div>
          </div>

          <button
            onClick={() => setStatusMessage(null)}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              fontSize: '0.85rem'
            }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Main Grid: Status & Controls */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
        gap: '1.5rem',
        marginBottom: '2rem'
      }}>
        {/* Discord Connection & Guild Status Card */}
        <div className="glass-panel" style={{ padding: '1.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#fff', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <svg width="22" height="22" viewBox="0 0 127.14 96.36" fill="var(--discord-blue)">
                <path d="M107.7,8.07A105.15,105.15,0,0,0,81.47,0a72.06,72.06,0,0,0-3.36,6.83A97.68,97.68,0,0,0,49,6.83,72.37,72.37,0,0,0,45.64,0,105.89,105.89,0,0,0,19.39,8.09C2.79,32.65-1.71,56.6.54,80.21h0A105.73,105.73,0,0,0,32.71,96.36,77.7,77.7,0,0,0,39.6,85.25a68.42,68.42,0,0,1-10.85-5.18c.91-.66,1.8-1.34,2.66-2a75.57,75.57,0,0,0,64.32,0c.87.71,1.76,1.39,2.66,2a68.68,68.68,0,0,1-10.87,5.19,77,77,0,0,0,6.89,11.1A105.25,105.25,0,0,0,126.6,80.22h0C129.24,52.84,122.09,29.11,107.7,8.07ZM42.45,65.69C36.18,65.69,31,60,31,53s5-12.74,11.43-12.74S54,45.91,53.89,53,48.84,65.69,42.45,65.69Zm42.24,0C78.41,65.69,73.25,60,73.25,53s5-12.74,11.44-12.74S96.23,45.91,96.12,53,91.08,65.69,84.69,65.69Z"/>
              </svg>
              Discord Status
            </h3>
            {isConnected ? (
              <span className="badge badge-connected">🟢 Connected</span>
            ) : (
              <span className="badge badge-disconnected">🔴 Not Connected</span>
            )}
          </div>

          {/* User Discord Details */}
          {isConnected ? (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '1rem',
              background: 'rgba(0, 0, 0, 0.3)',
              padding: '1rem',
              borderRadius: 'var(--radius-md)',
              marginBottom: '1.25rem'
            }}>
              <div style={{
                width: '48px',
                height: '48px',
                borderRadius: '50%',
                background: 'var(--discord-blue)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                overflow: 'hidden'
              }}>
                {discordStatus.avatar_url ? (
                  <img
                    src={discordStatus.avatar_url}
                    alt="Discord Avatar"
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  />
                ) : (
                  <User size={24} color="#fff" />
                )}
              </div>
              <div>
                <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fff' }}>
                  @{discordStatus.discord_username || 'Discord User'}
                </div>
                {discordStatus.discord_global_name && (
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {discordStatus.discord_global_name}
                  </div>
                )}
                <div style={{ fontSize: '0.74rem', color: 'var(--text-dim)', marginTop: '2px' }}>
                  ID: {discordStatus.discord_user_id}
                </div>
              </div>
            </div>
          ) : (
            <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
              Connect your Discord account to automatically synchronize roles and link your in-game identity.
            </p>
          )}

          {/* Guild Membership Item */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0.75rem 1rem',
            background: 'rgba(255, 255, 255, 0.03)',
            borderRadius: 'var(--radius-md)',
            marginBottom: '1.5rem',
            border: '1px solid var(--border-subtle)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <Server size={18} color="var(--gold-400)" />
              <span style={{ fontSize: '0.92rem', fontWeight: 600, color: '#fff' }}>
                NMC SERVER
              </span>
            </div>
            {isMember ? (
              <span className="badge badge-connected">🟢 Member</span>
            ) : (
              <span className="badge badge-disconnected">🔴 Not Member</span>
            )}
          </div>

          {/* Buttons Group */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem' }}>
            {!isConnected ? (
              <button
                onClick={handleConnectDiscord}
                className="btn btn-discord"
                style={{ flex: 1 }}
                disabled={connecting}
              >
                <Link2 size={16} />
                {connecting ? 'Redirecting...' : 'Connect Discord'}
              </button>
            ) : (
              <>
                <button
                  onClick={handleSyncRoles}
                  className="btn btn-primary"
                  style={{ flex: 1 }}
                  disabled={syncing}
                >
                  <RefreshCw size={16} className={syncing ? 'animate-spin' : ''} />
                  {syncing ? 'Syncing...' : 'Sync Roles'}
                </button>

                <button
                  onClick={handleConnectDiscord}
                  className="btn btn-outline"
                  style={{ fontSize: '0.88rem' }}
                  title="Re-authorize Discord"
                >
                  Verify Discord
                </button>

                <button
                  onClick={handleUnlinkDiscord}
                  className="btn btn-danger"
                  style={{ padding: '0.7rem' }}
                  title="Unlink Discord"
                >
                  <Unlink size={16} />
                </button>
              </>
            )}
          </div>
        </div>

        {/* FiveM Player Connection Card */}
        <div className="glass-panel" style={{ padding: '1.75rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#fff', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <Gamepad2 size={22} color="var(--cyan-400)" />
                FiveM Player Status
              </h3>
              {user.fivem_linked ? (
                <span className="badge badge-cyan">🟢 Linked</span>
              ) : (
                <span className="badge badge-disconnected">🔴 Not Linked</span>
              )}
            </div>

            <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
              Linking your FiveM player account verifies your in-game identity and unlocks the <strong>𝐍𝐌𝐂 𝐏𝐋𝐀𝐘𝐄𝐑</strong> Discord role automatically.
            </p>

            {user.fivem_linked && (
              <div style={{
                background: 'rgba(6, 182, 212, 0.08)',
                border: '1px solid rgba(6, 182, 212, 0.25)',
                padding: '0.85rem 1rem',
                borderRadius: 'var(--radius-md)',
                marginBottom: '1.5rem'
              }}>
                <div style={{ fontSize: '0.74rem', color: 'var(--cyan-400)', fontWeight: 600 }}>
                  Active Identifier:
                </div>
                <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff', wordBreak: 'break-all' }}>
                  {user.fivem_identifier}
                </div>
              </div>
            )}
          </div>

          <div>
            <button
              onClick={() => setShowFiveMModal(true)}
              className="btn btn-outline"
              style={{ width: '100%', borderColor: 'rgba(6, 182, 212, 0.4)', color: 'var(--cyan-400)' }}
            >
              <Gamepad2 size={16} />
              {user.fivem_linked ? 'Update FiveM Identifier' : 'Link FiveM Account'}
            </button>
          </div>
        </div>
      </div>

      {/* Roles Status Section */}
      <div style={{ marginBottom: '2.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
          <div>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#fff' }}>
              Your Discord Roles in NMC SERVER
            </h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Idempotent role verification. Bot automatically detects membership and applies roles.
            </p>
          </div>

          <button
            onClick={loadStatus}
            className="btn btn-outline"
            style={{ padding: '0.45rem 0.85rem', fontSize: '0.85rem' }}
            disabled={loading}
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
          </button>
        </div>

        {/* 3 Role Cards Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '1.25rem'
        }}>
          {roles.map((r) => (
            <RoleCard key={r.id} role={r} isGuildMember={isMember} />
          ))}
        </div>
      </div>

      {/* FiveM Link Modal */}
      <FiveMLinkModal
        isOpen={showFiveMModal}
        onClose={() => setShowFiveMModal(false)}
        onLinked={handleFiveMLinked}
        currentIdentifier={user.fivem_identifier}
      />
    </div>
  );
}
