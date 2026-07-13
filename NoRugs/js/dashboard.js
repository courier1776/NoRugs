(() => {
  NoRugsShell.renderShell('dashboard.html');
  const body=document.getElementById('coins-body');
  const loading=document.getElementById('loading-state');
  const empty=document.getElementById('empty-state');
  const wrap=document.getElementById('table-wrap');
  const search=document.getElementById('coin-search');
  const risk=document.getElementById('risk-filter');
  const sort=document.getElementById('sort-filter');
  const resultCount=document.getElementById('result-count');
  let coins=[];

  const params=new URLSearchParams(location.search);
  search.value=params.get('search') || '';

  function renderStats(stats){
    document.getElementById('stat-total').textContent=NoRugsFormat.number(stats.total_coins);
    document.getElementById('stat-low').textContent=NoRugsFormat.number(stats.low_risk);
    document.getElementById('stat-moderate').textContent=NoRugsFormat.number(stats.moderate_risk);
    document.getElementById('stat-high').textContent=NoRugsFormat.number(Number(stats.high_risk||0)+Number(stats.critical_risk||0));
  }

  function sorted(items){
    const list=[...items];
    switch(sort.value){
      case 'risk-desc': return list.sort((a,b)=>Number(b.overall_risk_score??-1)-Number(a.overall_risk_score??-1));
      case 'risk-asc': return list.sort((a,b)=>Number(a.overall_risk_score??999)-Number(b.overall_risk_score??999));
      case 'market-cap': return list.sort((a,b)=>Number(b.market_cap_usd??0)-Number(a.market_cap_usd??0));
      case 'change': return list.sort((a,b)=>Math.abs(Number(b.price_change_24h_pct??0))-Math.abs(Number(a.price_change_24h_pct??0)));
      default:return list.sort((a,b)=>Number(a.market_rank??999999)-Number(b.market_rank??999999));
    }
  }

  function render(){
    const q=search.value.trim().toLowerCase();
    const level=risk.value;
    let filtered=coins.filter(c=>(!q || `${c.name} ${c.symbol} ${c.external_market_id}`.toLowerCase().includes(q)) && (!level || c.risk_level===level));
    filtered=sorted(filtered);
    resultCount.textContent=`${filtered.length} OF ${coins.length} ASSETS · LIVE API`;
    body.innerHTML='';
    if(!filtered.length){wrap.hidden=true;empty.hidden=false;return}
    empty.hidden=true;wrap.hidden=false;
    for(const coin of filtered){
      const score=coin.overall_risk_score==null?null:Number(coin.overall_risk_score);
      const badge=NoRugsFormat.badgeClass(coin.risk_level);
      const change=Number(coin.price_change_24h_pct);
      const row=document.createElement('tr');
      const id=coin.external_market_id || coin.cryptocurrency_id;
      row.innerHTML=`
        <td class="mono">${coin.market_rank ?? '—'}</td>
        <td><a class="table-link" href="coin-analysis.html?id=${encodeURIComponent(id)}"><div class="cell-asset">
          ${coin.logo_url?`<img class="coin-logo" src="${NoRugsFormat.escapeHtml(coin.logo_url)}" alt="" loading="lazy">`:`<div class="cell-asset-icon">${NoRugsFormat.escapeHtml(coin.symbol.slice(0,2))}</div>`}
          <div><div class="cell-asset-name">${NoRugsFormat.escapeHtml(coin.name)}</div><div class="cell-asset-ticker">${NoRugsFormat.escapeHtml(coin.symbol)} · ${NoRugsFormat.escapeHtml(coin.external_market_id||'')}</div></div>
        </div></a></td>
        <td class="mono">${NoRugsFormat.currency(coin.price_usd,false)}</td>
        <td class="mono ${change>=0?'change-up':'change-down'}">${NoRugsFormat.percent(coin.price_change_24h_pct)}</td>
        <td class="mono">${NoRugsFormat.currency(coin.market_cap_usd,true)}</td>
        <td class="mono">${NoRugsFormat.currency(coin.volume_24h_usd,true)}</td>
        <td><div class="risk-cell">${score==null?'':NoRugsGauge.buildGaugeSVG(Math.round(score),{variant:'mini',size:30})}<span class="badge-pill ${badge}"><span class="dot"></span>${NoRugsFormat.escapeHtml(coin.risk_level||'UNKNOWN')}${score==null?'':` · ${score.toFixed(0)}`}</span></div></td>
        <td class="table-meta">${NoRugsFormat.dateTime(coin.market_data_updated_at)}</td>`;
      body.appendChild(row);
    }
  }

  async function init(){
    try{
      const [coinData,stats]=await Promise.all([NoRugsAPI.getCoins({limit:500}),NoRugsAPI.getDashboardStats()]);
      coins=coinData;renderStats(stats);loading.hidden=true;render();
    }catch(error){
      loading.innerHTML='<strong>Unable to load the dashboard</strong>Start FastAPI with <code>fastapi dev api/app.py</code>, then refresh this page.';
      const banner=document.getElementById('connection-banner');banner.textContent=`API error: ${error.message}`;banner.classList.add('show');
    }
  }
  let timer;search.addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(render,120)});risk.addEventListener('change',render);sort.addEventListener('change',render);init();
})();
