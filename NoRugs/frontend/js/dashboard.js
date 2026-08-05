(() => {
  NoRugsShell.renderShell('dashboard.html');
  const esc = NoRugsShell.escapeHtml;
  const body = document.getElementById('market-body');
  const search = document.getElementById('market-search');
  const riskFilter = document.getElementById('risk-filter');
  const sort = document.getElementById('market-sort');
  let coins = [];
  let usingLiveData = false;
  const refreshEveryMs = 15000;
  const statusEveryMs = 5000;
  let updateStatus = null;

  const formatTime = iso => {
    if(!iso) return 'not completed yet';
    const date = new Date(iso);
    return Number.isNaN(date.getTime()) ? 'unknown' : date.toLocaleTimeString([], {hour:'numeric', minute:'2-digit', second:'2-digit'});
  };
  function renderUpdateStatus(status){
    updateStatus = status;
    const pulse = document.getElementById('live-pulse');
    const title = document.getElementById('live-status-title');
    const detail = document.getElementById('live-status-detail');
    const button = document.getElementById('refresh-live');
    const enabled = Boolean(status && status.enabled);
    const running = Boolean(status && status.running);
    const error = status && status.last_error;
    pulse.className = `live-pulse${running ? ' running' : ''}${error ? ' error' : ''}`;
    title.textContent = error ? 'Live updater needs attention' : running ? 'Database refresh in progress' : enabled ? 'Real-time database updates verified' : 'Live updates are disabled';
    detail.textContent = error ? error : running ? 'Provider data is being collected and saved to PostgreSQL.' : enabled ? `Background collection runs every ${status.interval_seconds} seconds.` : 'Enable LIVE_UPDATES_ENABLED in the .env file.';
    document.getElementById('live-cycle-count').textContent = `Cycles: ${Number(status.cycles_completed || 0).toLocaleString('en-US')}`;
    document.getElementById('live-last-update').textContent = `Last update: ${formatTime(status.last_success_at)}`;
    button.disabled = running || !enabled;
    button.textContent = running ? 'Refreshing…' : 'Refresh now';
    updateCountdown();
  }
  function updateCountdown(){
    const target = document.getElementById('live-next-update');
    if(!updateStatus || !updateStatus.enabled){target.textContent='Next update: disabled';return;}
    if(updateStatus.running){target.textContent='Next update: running now';return;}
    const completed = updateStatus.last_completed_at ? new Date(updateStatus.last_completed_at).getTime() : Date.now();
    const seconds = Math.max(0, Math.ceil((completed + Number(updateStatus.interval_seconds || 60) * 1000 - Date.now()) / 1000));
    target.textContent = `Next update: ${seconds}s`;
  }
  async function loadUpdateStatus(){
    try{renderUpdateStatus(await NoRugsApi.updateStatus());}
    catch(error){renderUpdateStatus({enabled:false,running:false,last_error:'Unable to contact the live update status endpoint.',cycles_completed:0});}
  }

  const number = value => { if(value === null || value === undefined || value === '') return 0; const parsed = Number(value); return Number.isFinite(parsed) ? parsed : 0; };
  const money = (value) => {
    const n = number(value);
    if (!Number.isFinite(n)) return '—';
    if (Math.abs(n) >= 1e12) return `$${(n / 1e12).toFixed(2)}T`;
    if (Math.abs(n) >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
    if (Math.abs(n) >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
    if (Math.abs(n) >= 1) return `$${n.toLocaleString('en-US', {maximumFractionDigits: 2})}`;
    return `$${n.toLocaleString('en-US', {maximumSignificantDigits: 5})}`;
  };
  const riskBucket = score => score < 25 ? 'low' : score < 50 ? 'moderate' : 'high';
  const riskLabel = score => score < 25 ? 'Low' : score < 50 ? 'Moderate' : score < 75 ? 'High' : 'Critical';
  const badge = score => score < 25 ? 'badge-safe' : score < 50 ? 'badge-caution' : 'badge-danger';

  function fallbackCoins(){
    return (NoRugsData.watchlist || []).map((coin, i) => ({
      cryptocurrency_id: i + 1,
      name: coin.name,
      symbol: coin.ticker,
      chain: coin.chain || 'Ethereum',
      price_usd: coin.price || 0,
      price_change_24h_pct: coin.change || 0,
      market_cap_usd: coin.marketCap || 0,
      volume_24h_usd: coin.volume || 0,
      overall_risk_score: coin.score,
      market_rank: i + 1
    }));
  }

  function updateSummary(data, live){
    const scores = data.map(c => number(c.overall_risk_score));
    document.getElementById('tracked-count').textContent = data.length.toLocaleString('en-US');
    document.getElementById('low-count').textContent = scores.filter(s => s < 25).length.toLocaleString('en-US');
    document.getElementById('moderate-count').textContent = scores.filter(s => s >= 25 && s < 50).length.toLocaleString('en-US');
    document.getElementById('high-count').textContent = scores.filter(s => s >= 50).length.toLocaleString('en-US');
    document.getElementById('database-note').textContent = live ? 'Live database records' : 'Demo records — start server for live data';
  }

  function render(){
    const term = search.value.trim().toLowerCase();
    const filter = riskFilter.value;
    let shown = coins.filter(c => {
      const haystack = `${c.name || ''} ${c.symbol || ''} ${c.coingecko_id || ''}`.toLowerCase();
      return (!term || haystack.includes(term)) && (filter === 'all' || riskBucket(number(c.overall_risk_score)) === filter);
    });
    shown.sort((a,b) => {
      if(sort.value === 'cap') return number(b.market_cap_usd) - number(a.market_cap_usd);
      if(sort.value === 'risk') return number(b.overall_risk_score) - number(a.overall_risk_score);
      if(sort.value === 'change') return number(b.price_change_24h_pct) - number(a.price_change_24h_pct);
      return number(a.market_rank || a.cryptocurrency_id) - number(b.market_rank || b.cryptocurrency_id);
    });
    document.getElementById('market-count').textContent = `${shown.length} of ${coins.length} assets · ${usingLiveData ? 'live API' : 'demo data'}`;
    if(!shown.length){body.innerHTML = '<tr><td colspan="7" class="table-message">No assets match these filters.</td></tr>';return;}
    body.innerHTML = shown.slice(0,500).map((c,index) => {
      const score = Math.round(number(c.overall_risk_score));
      const change = number(c.price_change_24h_pct);
      const symbol = String(c.symbol || '?').toUpperCase();
      return `<tr class="market-row" data-symbol="${esc(symbol)}">
        <td>${esc(c.market_rank || index + 1)}</td>
        <td><div class="cell-asset"><div class="coin-logo ${symbol === 'BTC' ? 'btc' : ''}">${symbol === 'BTC' ? '₿' : esc(symbol.slice(0,2))}</div><div><div class="cell-asset-name">${esc(c.name || symbol)}</div><div class="cell-asset-ticker">${esc(symbol)} · ${esc(c.chain || c.coingecko_id || 'asset')}</div></div></div></td>
        <td class="mono">${money(c.price_usd)}</td>
        <td class="mono ${change >= 0 ? 'change-up' : 'change-down'}">${change >= 0 ? '+' : ''}${change.toFixed(2)}%</td>
        <td class="mono">${money(c.market_cap_usd)}</td>
        <td class="mono">${money(c.volume_24h_usd)}</td>
        <td><span class="badge-pill ${badge(score)}"><span class="dot"></span>${riskLabel(score)} <span class="risk-number">${score}</span></span></td>
      </tr>`;
    }).join('');
    body.querySelectorAll('.market-row').forEach(row => row.addEventListener('click', () => {
      window.location.href = `coin-analysis.html?symbol=${encodeURIComponent(row.dataset.symbol)}`;
    }));
  }

  [search,riskFilter,sort].forEach(el => el.addEventListener(el.tagName === 'INPUT' ? 'input' : 'change', render));

  async function load(){
    try {
      const live = await NoRugsApi.getCoins();
      if(!Array.isArray(live) || live.length === 0) throw new Error('No database records');
      coins = live;
      usingLiveData = true;
      updateSummary(coins, true);
      NoRugsShell.setEngineStatus('API connected · PostgreSQL live', true);
    } catch(error) {
      if (!coins.length || usingLiveData) coins = fallbackCoins();
      usingLiveData = false;
      updateSummary(coins, false);
      NoRugsShell.setEngineStatus('Demo mode · start Flask for live data', false);
    }
    render();
  }
  document.getElementById('refresh-live').addEventListener('click', async () => {
    const button = document.getElementById('refresh-live');
    button.disabled = true;
    button.textContent = 'Starting…';
    try{await NoRugsApi.refreshNow();}
    catch(error){/* A 409 only means a scheduled refresh is already running. */}
    await loadUpdateStatus();
  });
  load();
  loadUpdateStatus();
  window.setInterval(() => {
    if (!document.hidden) load();
  }, refreshEveryMs);
  window.setInterval(() => {if(!document.hidden) loadUpdateStatus();}, statusEveryMs);
  window.setInterval(updateCountdown, 1000);
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) load();
  });
})();
