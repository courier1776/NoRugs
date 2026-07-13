window.NoRugsFormat = (() => {
  function number(value, options = {}) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return '—';
    return new Intl.NumberFormat('en-US', options).format(numeric);
  }

  function currency(value, compact = true) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return '—';
    const abs = Math.abs(numeric);
    let max = 2;
    if (abs > 0 && abs < 0.01) max = 8;
    else if (abs < 1) max = 4;
    return new Intl.NumberFormat('en-US', {
      style: 'currency', currency: 'USD', notation: compact && abs >= 1000000 ? 'compact' : 'standard',
      maximumFractionDigits: max
    }).format(numeric);
  }

  function percent(value) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return '—';
    return `${numeric >= 0 ? '+' : ''}${numeric.toFixed(2)}%`;
  }

  function dateTime(value) {
    if (!value) return '—';
    const date = new Date(value);
    if (Number.isNaN(date.valueOf())) return '—';
    return new Intl.DateTimeFormat('en-US', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
  }

  function badgeClass(level) {
    switch ((level || '').toUpperCase()) {
      case 'LOW': return 'badge-safe';
      case 'MODERATE': return 'badge-caution';
      case 'HIGH': case 'CRITICAL': return 'badge-danger';
      default: return 'badge-neutral';
    }
  }

  function escapeHtml(value = '') {
    return String(value).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#039;','"':'&quot;'}[c]));
  }

  return { number, currency, percent, dateTime, badgeClass, escapeHtml };
})();
