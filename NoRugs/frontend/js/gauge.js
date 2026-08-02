window.NoRugsGauge = (() => {
  const zones = [
    { max: 39, name: 'Low risk', color: '#2563eb' },
    { max: 69, name: 'Elevated risk', color: '#0284c7' },
    { max: 100, name: 'High risk', color: '#dc2626' }
  ];
  function zoneFor(score){ return zones.find(z => score <= z.max) || zones[2]; }
  function buildGaugeSVG(score, opts={}){
    const size = opts.size || 180, stroke = opts.variant === 'mini' ? 6 : 14;
    const r = (size - stroke) / 2, c = size / 2, circ = 2 * Math.PI * r;
    const z = zoneFor(score), dash = circ * Math.max(0, Math.min(100, score)) / 100;
    const fontSize = opts.variant === 'mini' ? size * .28 : size * .22;
    return `<svg class="risk-gauge" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" aria-label="Risk score ${score}">
      <circle class="gauge-face" cx="${c}" cy="${c}" r="${r}" fill="#fff" stroke="#dbeafe" stroke-width="${stroke}"/>
      <circle class="gauge-inner-ring" cx="${c}" cy="${c}" r="${r}" fill="none" stroke="#eaf2ff" stroke-width="${stroke}"/>
      <circle cx="${c}" cy="${c}" r="${r}" fill="none" stroke="${z.color}" stroke-width="${stroke}" stroke-linecap="round" stroke-dasharray="${dash} ${circ-dash}" transform="rotate(-90 ${c} ${c})"/>
      <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="Space Grotesk, sans-serif" font-weight="800" font-size="${fontSize}" fill="#0b1f3f">${score}</text>
      ${opts.variant === 'mini' ? '' : `<text x="50%" y="63%" dominant-baseline="middle" text-anchor="middle" font-family="IBM Plex Mono, monospace" font-size="${size*.045}" font-weight="700" fill="#5c7197">RISK SCORE</text>`}
    </svg>`;
  }
  function mountGauge(el, score, opts){ if(el) el.innerHTML = buildGaugeSVG(score, opts); }
  return { zoneFor, buildGaugeSVG, mountGauge };
})();
