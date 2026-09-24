const API_BASE = '/api';

function getAuthHeader() {
  const token = localStorage.getItem('nmc_auth_token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

async function request(endpoint, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...getAuthHeader(),
    ...options.headers
  };

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers
  });

  const contentType = response.headers.get('content-type');
  let data = null;
  if (contentType && contentType.includes('application/json')) {
    data = await response.json();
  } else {
    data = await response.text();
  }

  if (!response.ok) {
    const errorMsg = data && data.detail ? data.detail : (typeof data === 'string' ? data : 'API Request Failed');
    throw new Error(errorMsg);
  }

  return data;
}

export const api = {
  auth: {
    register: (email, username, password) =>
      request('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ email, username, password })
      }),
    login: (username_or_email, password) =>
      request('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username_or_email, password })
      }),
    me: () => request('/auth/me')
  },
  discord: {
    getLoginUrl: (userId) =>
      request(`/discord/login${userId ? `?user_id=${encodeURIComponent(userId)}` : ''}`),
    getStatus: () => request('/discord/status'),
    sync: () => request('/discord/sync', { method: 'POST' }),
    unlink: () => request('/discord/unlink', { method: 'POST' }),
    getRoles: () => request('/discord/roles')
  },
  fivem: {
    link: (identifier) =>
      request('/fivem/link', {
        method: 'POST',
        body: JSON.stringify({ identifier })
      }),
    unlink: () => request('/fivem/unlink', { method: 'POST' })
  },
  admin: {
    assignRole: (discord_user_id, role_id, reason) =>
      request('/admin/discord/assign-role', {
        method: 'POST',
        body: JSON.stringify({ discord_user_id, role_id, reason })
      }),
    removeRole: (discord_user_id, role_id, reason) =>
      request('/admin/discord/remove-role', {
        method: 'POST',
        body: JSON.stringify({ discord_user_id, role_id, reason })
      }),
    getLogs: () => request('/admin/discord/logs')
  },
  health: () => request('/health')
};
