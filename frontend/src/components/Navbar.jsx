import React from 'react';
import { Shield, User, LogOut, CheckCircle, Radio, Terminal } from 'lucide-react';

export default function Navbar({ user, onLogout, onOpenAdmin, botInfo }) {
  return (
    <nav style={{
      borderBottom: '1px solid var(--border-subtle)',
      background: 'rgba(8, 10, 15, 0.8)',
      backdropFilter: 'blur(12px)',
      position: 'sticky',
      top: 0,
      zIndex: 50,
      padding: '0.9rem 2rem'
    }}>
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, var(--gold-500) 0%, var(--gold-600) 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 15px rgba(245, 158, 11, 0.4)'
          }}>
            <Shield size={22} color="#000" strokeWidth={2.5} />
          </div>
          <div>
            <div style={{
              fontSize: '1.25rem',
              fontWeight: 800,
              letterSpacing: '0.04em',
              background: 'linear-gradient(90deg, #fff 0%, #cbd5e1 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              fontFamily: 'Outfit, sans-serif'
            }}>
              NMC SERVER
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontWeight: 500, letterSpacing: '0.05em' }}>
              DISCORD & FIVEM VERIFICATION PORTAL
            </div>
          </div>
        </div>

        {/* Status & User Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          {/* Bot Live Pulse Indicator */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.45rem',
            background: 'rgba(255, 255, 255, 0.04)',
            padding: '0.4rem 0.8rem',
            borderRadius: 'var(--radius-full)',
            border: '1px solid var(--border-subtle)',
            fontSize: '0.78rem'
          }}>
            <span style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: botInfo?.bot_ready ? 'var(--emerald-500)' : 'var(--gold-500)',
              boxShadow: botInfo?.bot_ready ? '0 0 10px var(--emerald-500)' : '0 0 10px var(--gold-500)',
              display: 'inline-block'
            }}></span>
            <span style={{ color: 'var(--text-muted)' }}>
              Bot: <strong style={{ color: '#fff' }}>{botInfo?.bot_ready ? 'Online' : 'Active'}</strong>
            </span>
          </div>

          {user && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
              {/* Admin Button */}
              {user.is_admin && (
                <button
                  onClick={onOpenAdmin}
                  className="btn btn-outline"
                  style={{
                    padding: '0.45rem 0.9rem',
                    fontSize: '0.85rem',
                    borderColor: 'rgba(245, 158, 11, 0.4)',
                    color: 'var(--gold-400)'
                  }}
                >
                  <Terminal size={14} />
                  Staff Console
                </button>
              )}

              {/* User Profile Capsule */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.6rem',
                background: 'rgba(255, 255, 255, 0.05)',
                padding: '0.35rem 0.85rem 0.35rem 0.45rem',
                borderRadius: 'var(--radius-full)',
                border: '1px solid var(--border-subtle)'
              }}>
                <div style={{
                  width: '30px',
                  height: '30px',
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  overflow: 'hidden'
                }}>
                  {user.discord_avatar ? (
                    <img
                      src={`https://cdn.discordapp.com/avatars/${user.discord_id}/${user.discord_avatar}.png`}
                      alt={user.username}
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    />
                  ) : (
                    <User size={16} color="#fff" />
                  )}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <span style={{ fontSize: '0.86rem', fontWeight: 600, color: '#fff', lineHeight: 1.2 }}>
                    {user.username}
                  </span>
                  {user.is_admin && (
                    <span style={{ fontSize: '0.65rem', color: 'var(--gold-400)', fontWeight: 700 }}>
                      ADMIN
                    </span>
                  )}
                </div>
              </div>

              {/* Logout Button */}
              <button
                onClick={onLogout}
                className="btn btn-outline"
                style={{
                  padding: '0.45rem 0.75rem',
                  fontSize: '0.85rem',
                  color: 'var(--text-muted)'
                }}
                title="Log Out"
              >
                <LogOut size={16} />
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
