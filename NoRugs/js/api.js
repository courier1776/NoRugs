window.NoRugsAPI = (() => {
  const API_BASE = localStorage.getItem('norugs_api_base') || 'http://127.0.0.1:8000';

  async function request(path) {
    const response = await fetch(`${API_BASE}${path}`, {
      headers: { 'Accept': 'application/json' }
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || `Request failed with status ${response.status}`);
    }
    return response.json();
  }

  const getCoins = ({ search = '', riskLevel = '', limit = 500 } = {}) => {
    const params = new URLSearchParams({ limit: String(limit) });
    if (search) params.set('search', search);
    if (riskLevel) params.set('risk_level', riskLevel);
    return request(`/api/coins?${params.toString()}`);
  };

  const getCoin = (id) => request(`/api/coins/${encodeURIComponent(id)}`);
  const getDashboardStats = () => request('/api/stats/dashboard');
  const health = () => request('/api/health');

  return { API_BASE, getCoins, getCoin, getDashboardStats, health };
})();
