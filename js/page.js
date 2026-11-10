/* Where the lifeboats go. RNLI lifeboat launches 2021 to 2025 on a plain MapLibre base map (OpenFreeMap Positron).
 * Launches are shown as counts on 1 km squares (heat layer and circles), stations as rings sized by launches, and an
 * optional coast layer shaded by each station's launches per 10 km of coast. Filters: year, boat type, casualty group.
 * Dr Tristan Hotham, Independent researcher, 2026. MIT licence. */
(function () {
  'use strict';
  const qs = new URLSearchParams(location.search);
  const STYLE = 'https://tiles.openfreemap.org/styles/positron';
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const norm = s => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const small = matchMedia('(max-width:800px)').matches;
  const fmt = n => n == null ? 'n/a' : Number(n).toLocaleString('en-GB');
  const GN = ['Commercial', 'Powered and sail craft', 'Paddle and board craft', 'People in the water', 'People on the shore', 'Other or unknown'];
  const GC = ['#55606B', '#2F6A9E', '#2E9C9C', '#B4442E', '#D08A1E', '#A79F92'];
  const BN = ['All-weather', 'Inshore', 'Hovercraft or water craft'];
  const YR = [2021, 2022, 2023, 2024, 2025];
  const CTRY = { ENG: 'England', SCT: 'Scotland', WAL: 'Wales', NIR: 'Northern Ireland', IRL: 'Ireland', IOM: 'Isle of Man', CHI: 'Channel Islands' };
  let map = null, D = null, F = { y: -1, b: -1, g: -1 };
  document.getElementById('theme').addEventListener('click', () => { const r = document.documentElement, d = r.dataset.theme ? r.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; r.dataset.theme = d ? 'light' : 'dark'; });
  const ct = document.getElementById('cartouche'); const fold = f => ct.classList.toggle('folded', f);
  if (small) fold(true);
  document.getElementById('ctToggle').addEventListener('click', () => fold(!ct.classList.contains('folded')));
  document.getElementById('ctFold').addEventListener('click', () => fold(true));

  const keep = (y, b, g) => (F.y < 0 || F.y === y) && (F.b < 0 || F.b === b) && (F.g < 0 || F.g === g);
  function cellFeatures() {
    const out = []; let tot = 0;
    D.cells.forEach((c, i) => { let n = 0; for (const [y, b, g, k] of c[2]) if (keep(y, b, g)) n += k;
      if (n) { tot += n; out.push({ type: 'Feature', properties: { i, n }, geometry: { type: 'Point', coordinates: [c[0], c[1]] } }); } });
    return { fc: { type: 'FeatureCollection', features: out }, tot };
  }
  function stationN(s) {
    let n = 0; for (const [y, b, g, k] of s.x) if (keep(y, b, g)) n += k; return n;
  }
  function stationFeatures() {
    return { type: 'FeatureCollection', features: D.stations.map((s, i) => ({ type: 'Feature', properties: { i, n: s.n, N: stationN(s), t: s.t }, geometry: { type: 'Point', coordinates: [s.lo, s.la] } })) };
  }
  function refresh() {
    const { fc, tot } = cellFeatures();
    map.getSource('cells').setData(fc); map.getSource('st').setData(stationFeatures());
    document.getElementById('nshow').textContent = `${fmt(tot)} located launches shown.`;
    const parts = []; if (F.y >= 0) parts.push(YR[F.y]); if (F.b >= 0) parts.push(BN[F.b].toLowerCase()); if (F.g >= 0) parts.push(GN[F.g].toLowerCase());
    document.getElementById('keyTitle').textContent = 'Lifeboat launches' + (parts.length ? ': ' + parts.join(', ') : ', 2021 to 2025');
  }
  function bars(v, labels, col) {
    const mx = Math.max(1, ...v);
    return '<div class="bars">' + v.map((x, i) => `<i style="height:${Math.max(x ? 2 : 0, 40 * x / mx)}px;background:${col}" title="${labels[i]}: ${x}"><span>${String(labels[i]).slice(-2)}</span></i>`).join('') + '</div><div style="height:12px"></div>';
  }
  function gbar(g, N) { return '<div class="gbar">' + g.map((x, i) => x ? `<i style="width:${100 * x / N}%;background:${GC[i]}" title="${GN[i]}: ${x}"></i>` : '').join('') + '</div>'; }
  function stPopup(s, ll) {
    let h = `<b class="t">${esc(s.n)}</b><div class="nt">${s.t === 'ALB' ? 'All-weather and inshore station' : 'Inshore station'}, ${esc(CTRY[s.c] || s.c)}${s.inl ? ' (river or lake)' : ''}</div>`;
    h += `<table><tr><td>Launches</td><td><b>${fmt(s.N)}</b> in 2021 to 2025 (${(s.N / 5).toFixed(0)} a year)</td></tr>`;
    h += `<tr><td>Boats</td><td>${esc(s.a)}</td></tr>`;
    h += `<tr><td>By boat</td><td>${fmt(s.b[0])} all-weather, ${fmt(s.b[1])} inshore${s.b[2] ? ', ' + fmt(s.b[2]) + ' other' : ''}</td></tr>`;
    if (s.md != null) h += `<tr><td>Median trip</td><td>${s.md} km from the station</td></tr>`;
    if (s.p10 != null) h += `<tr><td>Coast</td><td>${fmt(s.ck)} km nearest to this station; ${s.p10} launches per 10 km</td></tr>`;
    if (s.dk != null) h += `<tr><td>In the dark</td><td>${s.dk}% of launches</td></tr>`;
    h += `<tr><td>Most often</td><td>${s.tp.map(esc).join(', ')}</td></tr></table>`;
    h += bars(s.y, YR, '#2F6A9E') + gbar(s.g, s.N);
    h += '<div class="nt">' + s.g.map((x, i) => x ? `<span style="color:${GC[i]}">■</span> ${GN[i]} ${x}` : '').filter(Boolean).join(' · ') + '</div>';
    h += `<p class="nt">Source: RNLI Returns of Service open data.${s.u ? ` <a href="${esc(s.u)}" target="_blank" rel="noopener">Station page</a>` : ''}</p>`;
    new maplibregl.Popup({ maxWidth: '330px', anchor: small ? 'bottom' : undefined }).setLngLat(ll).setHTML(h).addTo(map);
  }
  function cellPopup(i, ll) {
    const c = D.cells[i]; const y = [0, 0, 0, 0, 0], g = [0, 0, 0, 0, 0, 0], b = [0, 0, 0]; let N = 0, n = 0;
    for (const [yy, bb, gg, k] of c[2]) { N += k; y[yy] += k; g[gg] += k; b[bb] += k; if (keep(yy, bb, gg)) n += k; }
    let h = `<b class="t">${fmt(N)} launch${N > 1 ? 'es' : ''} to this 1 km square</b><div class="nt">2021 to 2025${n !== N ? `; ${fmt(n)} match the filters` : ''}</div>`;
    h += `<table><tr><td>Boats</td><td>${fmt(b[0])} all-weather, ${fmt(b[1])} inshore${b[2] ? ', ' + fmt(b[2]) + ' other' : ''}</td></tr></table>`;
    h += bars(y, YR, '#B4442E') + gbar(g, N);
    h += '<div class="nt">' + g.map((x, j) => x ? `<span style="color:${GC[j]}">■</span> ${GN[j]} ${x}` : '').filter(Boolean).join(' · ') + '</div>';
    h += '<p class="nt">Incident positions as recorded by crews, counted on 1 km squares. Source: RNLI Returns of Service open data.</p>';
    new maplibregl.Popup({ maxWidth: '320px', anchor: small ? 'bottom' : undefined }).setLngLat(ll).setHTML(h).addTo(map);
  }
  function setup() {
    map.addSource('cells', { type: 'geojson', data: { type: 'FeatureCollection', features: [] }, attribution: 'Launches: RNLI open data' });
    map.addSource('st', { type: 'geojson', data: stationFeatures() });
    const p10 = D.coast.map(c => D.stations[c[2]] ? D.stations[c[2]].p10 : null);
    map.addSource('coast', { type: 'geojson', data: { type: 'FeatureCollection', features: D.coast.map((c, j) => ({ type: 'Feature', properties: { v: p10[j] == null ? 0 : p10[j] }, geometry: { type: 'Point', coordinates: [c[0], c[1]] } })) } });
    map.addLayer({ id: 'coastl', type: 'circle', source: 'coast', layout: { visibility: 'none' }, paint: {
      'circle-radius': ['interpolate', ['linear'], ['zoom'], 4, 1.6, 8, 3.5, 12, 6],
      'circle-color': ['interpolate', ['linear'], ['ln', ['+', 1, ['get', 'v']]], 0, '#E3EEF6', 2, '#A9C8E2', 3.5, '#5E93C2', 5, '#2F6A9E', 6, '#14365C'], 'circle-opacity': 0.95 } });
    map.addLayer({ id: 'heat', type: 'heatmap', source: 'cells', maxzoom: 13, paint: {
      'heatmap-weight': ['interpolate', ['linear'], ['ln', ['+', 1, ['get', 'n']]], 0, 0, 6, 1],
      'heatmap-intensity': ['interpolate', ['linear'], ['zoom'], 4, 1.8, 7, 1.4, 10, 1.6],
      'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 4, 7, 6, 10, 8, 16, 11, 24],
      'heatmap-color': ['interpolate', ['linear'], ['heatmap-density'], 0, 'rgba(242,197,139,0)', 0.15, 'rgba(242,197,139,0.55)', 0.4, '#E07A1F', 0.7, '#B4442E', 1, '#6B1F2A'],
      'heatmap-opacity': ['interpolate', ['linear'], ['zoom'], 6, 0.95, 10, 0.4, 12.5, 0.15] } });
    map.addLayer({ id: 'cellc', type: 'circle', source: 'cells', paint: {
      'circle-radius': ['interpolate', ['linear'], ['zoom'], 4, ['+', 1.2, ['*', 0.25, ['sqrt', ['get', 'n']]]], 8, ['+', 2.5, ['*', 0.6, ['sqrt', ['get', 'n']]]], 12, ['+', 5, ['*', 1.4, ['sqrt', ['get', 'n']]]]],
      'circle-color': ['interpolate', ['linear'], ['ln', ['get', 'n']], 0, '#F2B26B', 2, '#E07A1F', 4, '#B4442E', 6, '#6B1F2A'],
      'circle-opacity': ['interpolate', ['linear'], ['zoom'], 4, 0.45, 8, 0.8], 'circle-stroke-color': '#fff', 'circle-stroke-width': ['interpolate', ['linear'], ['zoom'], 4, 0, 8, 0.6] } });
    map.addLayer({ id: 'stc', type: 'circle', source: 'st', paint: {
      'circle-radius': ['interpolate', ['linear'], ['zoom'], 4, ['+', 2, ['*', 0.1, ['sqrt', ['get', 'N']]]], 6, ['+', 3, ['*', 0.2, ['sqrt', ['get', 'N']]]], 9, ['+', 6, ['*', 0.45, ['sqrt', ['get', 'N']]]], 13, ['+', 9, ['*', 0.7, ['sqrt', ['get', 'N']]]]],
      'circle-color': 'rgba(255,255,255,0.35)', 'circle-stroke-color': ['match', ['get', 't'], 'ALB', '#1D3F6E', '#E07A1F'], 'circle-stroke-width': ['interpolate', ['linear'], ['zoom'], 4, 1, 7, 1.6, 9, 2.4], 'circle-stroke-opacity': ['interpolate', ['linear'], ['zoom'], 4, 0.75, 7, 1] } });
    map.addLayer({ id: 'stl', type: 'symbol', source: 'st', minzoom: 7.5, layout: { 'text-field': ['get', 'n'], 'text-size': 11.5, 'text-font': ['Noto Sans Regular'], 'text-offset': [0, 1.3], 'text-anchor': 'top', 'text-optional': true }, paint: { 'text-color': '#1D3F6E', 'text-halo-color': '#fff', 'text-halo-width': 1.6 } });
    map.on('click', e => {
      const st = map.queryRenderedFeatures(e.point, { layers: ['stc'] }); if (st.length) { const s = D.stations[st[0].properties.i]; stPopup(s, [s.lo, s.la]); return; }
      const ce = map.queryRenderedFeatures(e.point, { layers: ['cellc'] }); if (ce.length) cellPopup(ce[0].properties.i, ce[0].geometry.coordinates);
    });
    ['stc', 'cellc'].forEach(l => { map.on('mouseenter', l, () => map.getCanvas().style.cursor = 'pointer'); map.on('mouseleave', l, () => map.getCanvas().style.cursor = ''); });
    const lp = document.getElementById('lp'), btn = document.getElementById('lyrBtn');
    btn.addEventListener('click', e => { e.stopPropagation(); const o = lp.classList.toggle('open'); btn.setAttribute('aria-expanded', o); });
    document.addEventListener('click', e => { if (!lp.contains(e.target) && e.target !== btn) { lp.classList.remove('open'); btn.setAttribute('aria-expanded', false); } });
    const vis = (ids, v) => ids.forEach(id => map.setLayoutProperty(id, 'visibility', v ? 'visible' : 'none'));
    document.getElementById('lyH').addEventListener('change', e => vis(['heat'], e.target.checked));
    document.getElementById('lyC').addEventListener('change', e => vis(['cellc'], e.target.checked));
    document.getElementById('lyS').addEventListener('change', e => vis(['stc'], e.target.checked));
    document.getElementById('lyK').addEventListener('change', e => { vis(['coastl'], e.target.checked); document.getElementById('keyK').style.display = e.target.checked ? '' : 'none'; });
    document.getElementById('lyL').addEventListener('change', e => vis(['stl'], e.target.checked));
    const baseSym = map.getStyle().layers.filter(l => l.type === 'symbol' && l.id !== 'stl').map(l => l.id);
    document.getElementById('lyB').addEventListener('change', e => vis(baseSym, e.target.checked));
    [['fy', 'y'], ['fb', 'b'], ['fg', 'g']].forEach(([id, k]) => { const el = document.getElementById(id); el.addEventListener('change', () => { F[k] = +el.value; refresh(); }); });
    refresh();
  }
  function go(i) {
    const s = D.stations[i]; fold(true);
    map.flyTo({ center: [s.lo, s.la], zoom: small ? 10 : 10.5, duration: 1200, offset: [0, Math.round(map.getContainer().clientHeight * (small ? 0.28 : 0.2))] });
    map.once('moveend', () => stPopup(s, [s.lo, s.la]));
  }
  function setupSearch() {
    const q = document.getElementById('q'), sug = document.getElementById('sug'); let items = [], k = -1;
    const idx = D.stations.map((s, i) => ({ t: s.n, nn: norm(s.n), i, s: fmt(s.N) }));
    const show = () => { const v = norm(q.value.trim()); sug.innerHTML = ''; k = -1; if (v.length < 2) { sug.style.display = 'none'; return; }
      items = idx.filter(x => x.nn.startsWith(v)).concat(idx.filter(x => !x.nn.startsWith(v) && v.length > 2 && x.nn.includes(v))).slice(0, 12);
      items.forEach((it, j) => { const li = document.createElement('li'); li.setAttribute('role', 'option'); li.innerHTML = `${esc(it.t)} <span>${it.s}</span>`; li.addEventListener('mousedown', e => { e.preventDefault(); pick(j); }); sug.appendChild(li); });
      sug.style.display = items.length ? 'block' : 'none'; };
    const pick = j => { const it = items[j]; if (!it) return; q.value = it.t; sug.style.display = 'none'; go(it.i); };
    q.addEventListener('input', show);
    q.addEventListener('keydown', e => { const lis = [...sug.children];
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); k = Math.max(0, Math.min(lis.length - 1, k + (e.key === 'ArrowDown' ? 1 : -1))); lis.forEach((l, i) => l.setAttribute('aria-selected', i === k)); }
      else if (e.key === 'Enter') { e.preventDefault(); if (!items.length) show(); pick(k < 0 ? 0 : k); } else if (e.key === 'Escape') sug.style.display = 'none'; });
    q.addEventListener('blur', () => setTimeout(() => sug.style.display = 'none', 150));
  }
  fetch('data/site.json').then(r => r.json()).then(d => {
    D = d;
    const at = (qs.get('at') || '').split(',').map(Number);
    const mo = at.length === 3 && at.every(isFinite) ? { center: [at[1], at[0]], zoom: at[2] } : { bounds: [[-10.8, 49.1], [2.0, 60.9]], fitBoundsOptions: { padding: small ? { top: 110, bottom: 20, left: 10, right: 10 } : { top: 60, bottom: 30, left: 360, right: 60 } } };
    const m0 = new maplibregl.Map(Object.assign({ container: 'map', style: STYLE, attributionControl: { compact: true }, maxZoom: 15 }, mo));
    return new Promise((res, rej) => { m0.once('load', () => res(m0)); m0.once('error', e => { if (!m0.loaded()) rej(e.error || e); }); });
  }).then(mm => {
    map = mm; window.__map = mm;
    mm.on('error', e => { const er = e && e.error; if (er && (er.name === 'AbortError' || /abort/i.test(er.message || ''))) return; console.error(er || e); });
    const n = document.getElementById('nojs'); if (n) n.remove();
    mm.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
    const foldAt = () => document.querySelectorAll('.maplibregl-ctrl-attrib.maplibregl-compact').forEach(at => { at.classList.remove('maplibregl-compact-show'); at.removeAttribute('open'); });
    mm.once('idle', foldAt); setTimeout(foldAt, 1500);
    setup(); setupSearch();
    if (qs.get('station')) { const i = D.stations.findIndex(s => norm(s.n) === norm(qs.get('station'))); if (i >= 0) go(i); }
    document.getElementById('mapWrap').addEventListener('pointerdown', e => { if (e.target.closest && e.target.closest('.cartouche,.ov-top,.lp,.keys,.mfs-btn,.maplibregl-ctrl,.maplibregl-popup')) return; fold(true); }, { capture: true, passive: true, once: true });
  }).catch(e => { console.error(e); const n = document.getElementById('nojs'); if (n) n.textContent = 'The map could not load: ' + e.message; });
})();
