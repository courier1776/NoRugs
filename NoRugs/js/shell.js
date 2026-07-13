window.NoRugsShell = (() => {
  const links = [
    ['dashboard.html','Dashboard','M4 13h6V4H4v9Zm10 7h6V4h-6v16ZM4 20h6v-5H4v5Zm10 0h6v-7h-6v7Z'],
    ['coin-analysis.html','Coin Analysis','M12 3a9 9 0 1 0 9 9 9 9 0 0 0-9-9Zm0 4v5l3 3'],
    ['wallet-analysis.html','Wallet Analysis','M3 7h18v12H3z M16 12h5'],
    ['comparison.html','Compare','M7 7h12M5 12h14M7 17h12'],
    ['watchlist.html','Watchlist','M12 3l3 6 7 1-5 5 1 7-6-3-6 3 1-7-5-5 7-1z'],
    ['alerts.html','Alerts','M12 22a2.5 2.5 0 0 0 2.5-2.5h-5A2.5 2.5 0 0 0 12 22Zm8-6H4c1-2 2-4 2-8a6 6 0 0 1 12 0c0 4 1 6 2 8Z']
  ];
  function icon(path){return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="${path}"/></svg>`}
  function renderShell(active){
    const rail = document.querySelector('[data-rail]');
    const topbar = document.querySelector('[data-topbar]');
    if(rail){
      rail.innerHTML = `<a class="rail-brand" href="index.html"><div class="brand-mark">NR</div><div><div class="rail-brand-name">NoRugs</div><div class="rail-brand-sub">CRYPTO RISK MONITOR</div></div></a><nav class="rail-nav">${links.map(l=>`<a class="rail-link ${active===l[0]?'active':''}" href="${l[0]}">${icon(l[2])}<span>${l[1]}</span></a>`).join('')}</nav><div class="rail-footer"><strong><span class="live-dot"></span> Live Risk Engine</strong><br><span id="api-status-text">Connecting to local API…</span></div>`;
    }
    if(topbar){
      topbar.innerHTML = `<form class="topbar-search" id="global-search-form"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#5c7197" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.8-4.8"/></svg><input id="global-search-input" placeholder="Search token or ticker" autocomplete="off" /></form><div class="topbar-actions"><a class="icon-btn" href="alerts.html" aria-label="Alerts">⌁</a><div class="avatar">NR</div></div>`;
      const form = topbar.querySelector('#global-search-form');
      form?.addEventListener('submit', e => {
        e.preventDefault();
        const q = topbar.querySelector('#global-search-input').value.trim();
        window.location.href = `dashboard.html${q ? `?search=${encodeURIComponent(q)}` : ''}`;
      });
    }
    if(window.NoRugsAPI){
      window.NoRugsAPI.health().then(() => {
        const el=document.getElementById('api-status-text'); if(el) el.textContent='API connected · PostgreSQL live';
      }).catch(() => {
        const el=document.getElementById('api-status-text'); if(el) el.textContent='API unavailable · start FastAPI';
      });
    }
  }
  return { renderShell };
})();
