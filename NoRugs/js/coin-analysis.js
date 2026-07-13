(() => {
  NoRugsShell.renderShell('coin-analysis.html');
  const form=document.getElementById('analysis-search');
  const input=document.getElementById('analysis-id');
  form.addEventListener('submit',e=>{e.preventDefault();const id=input.value.trim();if(id) location.href=`coin-analysis.html?id=${encodeURIComponent(id)}`});
  const params=new URLSearchParams(location.search);const id=params.get('id')||'bitcoin';input.value=id;
  const set=(name,value)=>document.getElementById(name).textContent=value;
  function colorFor(score){return score>=75?'var(--risk-danger-700)':score>=50?'var(--risk-caution-700)':'var(--blue-700)'}
  async function load(){
    try{
      const coin=await NoRugsAPI.getCoin(id);
      document.title=`${coin.name} — Coin Analysis — NoRugs`;
      document.getElementById('coin-logo').src=coin.logo_url||'';document.getElementById('coin-logo').style.display=coin.logo_url?'block':'none';
      set('coin-name',`${coin.name} (${coin.symbol})`);set('coin-meta',`${coin.external_market_id || id} · Rank ${coin.market_rank ?? '—'}`);
      const website=document.getElementById('coin-website');if(coin.website_url){website.href=coin.website_url}else{website.style.display='none'}
      const score=coin.overall_risk_score==null?0:Number(coin.overall_risk_score);NoRugsGauge.mountGauge(document.getElementById('main-gauge'),Math.round(score),{size:250});
      const badge=document.getElementById('risk-badge');badge.className=`badge-pill ${NoRugsFormat.badgeClass(coin.risk_level)}`;badge.innerHTML=`<span class="dot"></span>${NoRugsFormat.escapeHtml(coin.risk_level)} RISK`;
      set('confidence',`Confidence ${coin.confidence_score ?? '—'}%`);
      const factors=document.getElementById('factor-list');factors.innerHTML='';
      (coin.risk_factors||[]).forEach(f=>{const score=Number(f.factor_score);const row=document.createElement('div');row.className='factor-row';row.innerHTML=`<div><strong>${NoRugsFormat.escapeHtml(f.factor_name)}</strong><div class="table-meta">Weight ${(Number(f.weight)*100).toFixed(0)}%</div></div><div><div class="factor-track"><div class="factor-fill" style="width:${Math.max(0,Math.min(100,score))}%;background:${colorFor(score)}"></div></div><div class="table-meta" style="margin-top:5px">${NoRugsFormat.escapeHtml(f.explanation||'')}</div></div><div class="factor-value">${score.toFixed(0)}/100</div>`;factors.appendChild(row)});
      if(!(coin.risk_factors||[]).length) factors.innerHTML='<div class="state-card">No factor-level data is available yet.</div>';
      set('m-price',NoRugsFormat.currency(coin.price_usd,false));set('m-change',NoRugsFormat.percent(coin.price_change_24h_pct));document.getElementById('m-change').className=`stat-value ${Number(coin.price_change_24h_pct)>=0?'change-up':'change-down'}`;set('m-cap',NoRugsFormat.currency(coin.market_cap_usd,true));set('m-volume',NoRugsFormat.currency(coin.volume_24h_usd,true));set('m-rank',coin.market_rank??'—');set('m-updated',NoRugsFormat.dateTime(coin.market_data_updated_at));
      set('s-circulating',NoRugsFormat.number(coin.circulating_supply,{notation:'compact',maximumFractionDigits:2}));set('s-total',NoRugsFormat.number(coin.total_supply,{notation:'compact',maximumFractionDigits:2}));set('s-max',NoRugsFormat.number(coin.max_supply,{notation:'compact',maximumFractionDigits:2}));set('s-assessed',NoRugsFormat.dateTime(coin.risk_assessed_at));set('risk-summary',coin.risk_summary||'No assessment summary is available.');
      document.getElementById('analysis-loading').hidden=true;document.getElementById('analysis-content').hidden=false;
    }catch(error){document.getElementById('analysis-loading').hidden=true;document.getElementById('analysis-error').hidden=false;console.error(error)}
  }
  load();
})();
