window.NoRugsApi = {
  async request(path, options = {}) {
    const response = await fetch(path, {
      cache: 'no-store',
      headers: { Accept: 'application/json', ...(options.headers || {}) },
      ...options
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.detail || payload.message || 'API unavailable');
    return payload;
  },
  getCoins() {
    return this.request('/api/coins');
  },
  getCoin(symbol) {
    return this.request(`/api/coins/${encodeURIComponent(symbol)}`);
  },
  health() {
    return this.request('/api/health');
  },
  updateStatus() {
    return this.request('/api/updates/status');
  },
  refreshNow() {
    return this.request('/api/updates/refresh', { method: 'POST' });
  }
};
