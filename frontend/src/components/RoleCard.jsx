import React from 'react';
import { Check, Lock, ShieldCheck, ShieldAlert, Award, Gamepad2, Crown } from 'lucide-react';

export default function RoleCard({ role, isGuildMember }) {
  const isCitizen = role.type === 'CITIZEN';
  const isPlayer = role.type === 'PLAYER';
  const isServerTeam = role.type === 'SERVER_TEAM';

  let icon = <Award size={24} color="var(--gold-400)" />;
  let badgeColorClass = "badge-gold";
  let roleBorderColor = "var(--border-subtle)";

  if (isCitizen) {
    icon = <ShieldCheck size={24} color="var(--emerald-400)" />;
    badgeColorClass = "badge-connected";
    if (role.assigned) roleBorderColor = "rgba(16, 185, 129, 0.4)";
  } else if (isPlayer) {
    icon = <Gamepad2 size={24} color="var(--cyan-400)" />;
    badgeColorClass = "badge-cyan";
    if (role.assigned) roleBorderColor = "rgba(6, 182, 212, 0.4)";
  } else if (isServerTeam) {
    icon = <Crown size={24} color="#c084fc" />;
    badgeColorClass = "badge-purple";
    if (role.assigned) roleBorderColor = "rgba(139, 92, 246, 0.5)";
  }

  return (
    <div
      className="glass-panel"
      style={{
        padding: '1.5rem',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        position: 'relative',
        overflow: 'hidden',
        borderColor: roleBorderColor,
        boxShadow: role.assigned ? '0 10px 30px -10px rgba(0, 0, 0, 0.6), 0 0 20px rgba(255, 255, 255, 0.05)' : 'none'
      }}
    >
      {/* Top Header */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
          <div style={{
            width: '46px',
            height: '46px',
            borderRadius: '12px',
            background: 'rgba(255, 255, 255, 0.04)',
            border: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            {icon}
          </div>

          {/* Assigned Badge */}
          {role.assigned ? (
            <span className="badge badge-connected" style={{ fontSize: '0.85rem', padding: '0.35rem 0.8rem' }}>
              <Check size={14} strokeWidth={3} /> Assigned
            </span>
          ) : isServerTeam ? (
            <span className="badge badge-purple" style={{ fontSize: '0.82rem' }}>
              <Lock size={12} /> Staff Only
            </span>
          ) : (
            <span className="badge badge-disconnected" style={{ fontSize: '0.82rem' }}>
              Not Assigned
            </span>
          )}
        </div>

        {/* Role Name */}
        <h3 style={{
          fontSize: '1.2rem',
          fontWeight: 700,
          color: '#fff',
          marginBottom: '0.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem'
        }}>
          {role.assigned ? '✅' : isServerTeam ? '🔒' : '⚪'} {role.name}
        </h3>

        {/* Description */}
        <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
          {role.description}
        </p>
      </div>

      {/* Footer Condition */}
      <div style={{
        paddingTop: '0.85rem',
        borderTop: '1px solid var(--border-subtle)',
        fontSize: '0.78rem',
        color: 'var(--text-dim)'
      }}>
        {isCitizen && (
          <span>
            Requirement: <strong>Website Account + Discord Connected</strong>
          </span>
        )}
        {isPlayer && (
          <span>
            Requirement: <strong>FiveM Identifier Linked</strong>
          </span>
        )}
        {isServerTeam && (
          <span style={{ color: '#c084fc' }}>
            Protected: <strong>Manual admin assignment only via /staffrole</strong>
          </span>
        )}
      </div>
    </div>
  );
}
