window.NoRugsShell = (() => {
  const links = [
    ['dashboard.html','Dashboard','M4 13h6V4H4v9Zm10 7h6V4h-6v16ZM4 20h6v-5H4v5Zm10 0h6v-7h-6v7Z'],
    ['coin-analysis.html','Coin Analysis','M12 3a9 9 0 1 0 9 9 9 9 0 0 0-9-9Zm0 4v5l3 3'],
    ['wallet-analysis.html','Portfolio Analysis','M3 7h18v12H3z M16 12h5'],
    ['comparison.html','Compare','M7 7h12M5 12h14M7 17h12'],
    ['watchlist.html','Watchlist','M12 3l3 6 7 1-5 5 1 7-6-3-6 3 1-7-5-5 7-1z'],
    ['alerts.html','Alerts','M12 22a2.5 2.5 0 0 0 2.5-2.5h-5A2.5 2.5 0 0 0 12 22Zm8-6H4c1-2 2-4 2-8a6 6 0 0 1 12 0c0 4 1 6 2 8Z']
  ];
  function icon(path){return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="${path}"/></svg>`}
  function escapeHtml(value){
    return String(value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function setupGlobalSearch(topbar){
    const form = topbar.querySelector('[data-global-search]');
    const input = topbar.querySelector('[data-global-search-input]');
    const results = topbar.querySelector('[data-global-search-results]');
    let coins = [];
    let loaded = false;
    let selectedIndex = -1;

    async function loadCoins(){
      if(loaded) return coins;
      const response = await fetch('/api/coins', {cache:'no-store', headers:{Accept:'application/json'}});
      if(!response.ok) throw new Error('Search API unavailable');
      const payload = await response.json();
      coins = Array.isArray(payload) ? payload : [];
      loaded = true;
      return coins;
    }
    function matches(){
      const term = input.value.trim().toLowerCase();
      if(!term) return [];
      return coins.filter(c => `${c.name || ''} ${c.symbol || ''} ${c.coingecko_id || ''}`.toLowerCase().includes(term)).slice(0,8);
    }
    function close(){results.hidden=true;results.innerHTML='';selectedIndex=-1;}
    function open(items){
      if(!items.length){
        results.innerHTML='<div class="search-empty">No matching assets found.</div>';
      } else {
        results.innerHTML=items.map((c,i)=>`<button type="button" class="search-result" data-index="${i}" data-symbol="${escapeHtml(String(c.symbol || ''))}"><span><strong>${escapeHtml(c.name || c.symbol || 'Unknown asset')}</strong><small>${escapeHtml(String(c.symbol || '').toUpperCase())}</small></span><span class="search-score">Risk ${Math.round(Number(c.overall_risk_score) || 0)}</span></button>`).join('');
      }
      results.hidden=false;
      results.querySelectorAll('.search-result').forEach(button => button.addEventListener('click',()=>navigate(button.dataset.symbol)));
    }
    function highlight(items){
      results.querySelectorAll('.search-result').forEach((el,i)=>el.classList.toggle('selected',i===selectedIndex));
      if(items[selectedIndex]) results.querySelectorAll('.search-result')[selectedIndex]?.scrollIntoView({block:'nearest'});
    }
    function navigate(symbol){
      if(!symbol) return;
      window.location.href=`coin-analysis.html?symbol=${encodeURIComponent(symbol)}`;
    }
    async function refreshResults(){
      try{
        await loadCoins();
        const items=matches();
        selectedIndex=-1;
        open(items);
      }catch(error){
        results.hidden=false;
        results.innerHTML='<div class="search-empty">Live search is unavailable. Confirm the NoRugs server is running.</div>';
      }
    }
    input.addEventListener('focus',()=>{if(input.value.trim()) refreshResults();});
    input.addEventListener('input',refreshResults);
    input.addEventListener('keydown',event=>{
      const items=matches();
      if(event.key==='ArrowDown' && items.length){event.preventDefault();selectedIndex=(selectedIndex+1)%items.length;highlight(items);}
      if(event.key==='ArrowUp' && items.length){event.preventDefault();selectedIndex=(selectedIndex-1+items.length)%items.length;highlight(items);}
      if(event.key==='Escape') close();
      if(event.key==='Enter'){
        event.preventDefault();
        const target=items[selectedIndex] || items[0];
        if(target) navigate(target.symbol);
        else refreshResults();
      }
    });
    form.addEventListener('submit',event=>{event.preventDefault();const item=matches()[0];if(item) navigate(item.symbol);else refreshResults();});
    document.addEventListener('click',event=>{if(!form.contains(event.target)) close();});
  }

  function renderShell(active){
    const rail = document.querySelector('[data-rail]');
    const topbar = document.querySelector('[data-topbar]');
    if(rail){
      rail.innerHTML = `<a class="rail-brand" href="index.html"><div class="brand-mark">NR</div><div><div class="rail-brand-name">NoRugs</div><div class="rail-brand-sub">CRYPTO RISK MONITOR</div></div></a><nav class="rail-nav">${links.map(l=>`<a class="rail-link ${active===l[0]?'active':''}" href="${l[0]}">${icon(l[2])}<span>${l[1]}</span></a>`).join('')}</nav><div class="rail-footer"><strong><span class="engine-dot"></span>Live Risk Engine</strong><br><span data-engine-status>Checking API connection…</span></div>`;
    }
    if(topbar){
      topbar.innerHTML = `<form class="topbar-search" data-global-search role="search" autocomplete="off"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#5c7197" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.8-4.8"/></svg><input data-global-search-input aria-label="Search cryptocurrencies" placeholder="Search token name or ticker" /><div class="global-search-results" data-global-search-results hidden></div></form><div class="topbar-actions"><a class="icon-btn" href="alerts.html" aria-label="Notifications">↝</a><div class="avatar">NR</div></div>`;
      setupGlobalSearch(topbar);
    }
  }
  function setEngineStatus(message, connected){const status=document.querySelector('[data-engine-status]');const dot=document.querySelector('.engine-dot');if(status) status.textContent=message;if(dot) dot.classList.toggle('offline', !connected);}
  return { renderShell, escapeHtml, setEngineStatus };
})();
