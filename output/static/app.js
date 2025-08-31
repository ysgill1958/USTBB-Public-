// USTBB front-end script: filtering, keywords, rendering
(function(){
  // --- DOM handles (some may be absent; code is defensive) ---
  const grid       = document.getElementById('grid');
  const empty      = document.getElementById('empty');
  const q          = document.getElementById('q');
  const count      = document.getElementById('count');
  const dateStart  = document.getElementById('dateStart');
  const dateEnd    = document.getElementById('dateEnd');
  const clearDates = document.getElementById('clearDates');

  // Keyword UI (present on home; might be absent on archive pages)
  const kwInput   = document.getElementById('kwInput');
  const kwAdd     = document.getElementById('kwAdd');
  const kwChips   = document.getElementById('kwChips');
  const kwPresets = document.querySelectorAll('.chip--preset');

  // --- State ---
  let all = [];       // full list from items.json
  let keywords = [];  // array of { raw: "Ayurveda|Yoga", terms: ["ayurveda","yoga"] }

  // --- Utils ---
  const toISODateOnly = s => (s || '').slice(0, 10);
  const esc = s => (s || '').replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

  function clamp(str, lines){
    // CSS handles clamping, but keep shorter summaries to reduce overdraw in DOM
    if (!str) return '';
    const s = String(str);
    if (s.length <= 1000) return s;
    return s.slice(0, 1000) + '…';
  }

  function addKeyword(raw){
    raw = (raw || '').trim();
    if (!raw) return;
    // de-dupe by lowercase raw
    const low = raw.toLowerCase();
    if (keywords.some(k => k.raw.toLowerCase() === low)) return;
    const terms = raw.split('|').map(s => s.trim()).filter(Boolean).map(s => s.toLowerCase());
    keywords.push({ raw, terms });
    renderKwChips();
    refresh();
  }

  function removeKeyword(raw){
    const low = (raw || '').toLowerCase();
    keywords = keywords.filter(k => k.raw.toLowerCase() !== low);
    renderKwChips();
    refresh();
  }

  function renderKwChips(){
    if (!kwChips) return;
    kwChips.innerHTML = keywords.map(k =>
      `<span class="chip">${k.raw} <button aria-label="Remove ${k.raw}" data-del="${k.raw}">×</button></span>`
    ).join('');
    kwChips.querySelectorAll('button[data-del]').forEach(btn=>{
      btn.addEventListener('click', ()=> removeKeyword(btn.dataset.del));
    });
  }

  // Highlight occurrences of any OR-term across all chips
  function highlight(text){
    if (!text || !keywords.length) return text || '';
    const flat = [];
    keywords.forEach(k => k.terms.forEach(t => flat.push(t)));
    const uniq = [...new Set(flat)].filter(Boolean);
    if (!uniq.length) return text || '';
    const rx = new RegExp('(' + uniq.map(esc).join('|') + ')', 'gi');
    return (text || '').replace(rx, '<mark>$1</mark>');
  }

  function matchesKeywords(item){
    if (!keywords.length) return true; // no keyword filter active
    const hay = ((item.title || '') + ' ' + (item.summary || '')).toLowerCase();
    // AND across chips, OR within a chip
    return keywords.every(k => k.terms.some(t => hay.includes(t)));
  }

  function withinDate(i){
    const d  = toISODateOnly(i.date);
    const ds = dateStart?.value || null;
    const de = dateEnd?.value   || null;
    if (ds && d < ds) return false;
    if (de && d > de) return false;
    return true;
  }

  function anyFiltersActive(){
    const term = (q?.value || '').trim();
    return !!term || !!(dateStart?.value) || !!(dateEnd?.value) || keywords.length > 0;
  }

  function filterAll(){
    const term = (q?.value || '').toLowerCase();
    return all.filter(i => {
      const tOk = !term ||
        (String(i.title || '').toLowerCase().includes(term)) ||
        (String(i.summary || '').toLowerCase().includes(term));
      return tOk && withinDate(i) && matchesKeywords(i);
    });
  }

  // --- Card rendering ---
  function cardHTML(i){
    const imgBox = i.image
      ? `<div class="mediaBox"><img class="thumb" loading="lazy" src="${i.image}" alt=""></div>`
      : `<div class="mediaBox mediaBox--placeholder">
           <div class="media__inner">
             <div class="media__title">${(i.title || '').slice(0,120)}</div>
             <div class="media__summary">${(i.summary || 'No summary available.').slice(0,180)}</div>
           </div>
         </div>`;

    const title   = highlight(i.title || '');
    const summary = highlight(clamp(i.summary || '', 4));

    return `<div class="card">
      <div class="inner">
        <div class="txt">
          <h3 class="title"><a target="_blank" href="${i.link}">${title}</a></h3>
          <div class="muted">${i.date || ''} • ${i.source || ''}</div>
          <p class="summary">${summary}</p>
        </div>
        ${imgBox}
      </div>
    </div>`;
  }

  function render(list){
    // show only 25 when no filters active (homepage style)
    const limit   = anyFiltersActive() ? list.length : 25;
    const limited = list.slice(0, limit);
    grid.innerHTML = limited.map(cardHTML).join('');
    count.textContent = anyFiltersActive()
      ? `${limited.length} result(s)`
      : `${limited.length}/${list.length} shown • ${all.length} total`;
    empty.style.display = limited.length ? 'none' : '';
  }

  function refresh(){ render(filterAll()); }

  // --- Bootstrap: fetch items.json ---
  fetch('./data/items.json?cb=' + Date.now(), { cache: 'no-store' })
    .then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
    .then(items => {
      if (!Array.isArray(items)) throw new Error('items.json invalid');
      all = items;
      refresh();
    })
    .catch(err => {
      if (empty) empty.style.display = '';
      if (count) count.textContent = '0 results';
      console.error('Failed to fetch items.json', err);
    });

  // --- Events ---
  let t = null;
  if (q) q.addEventListener('input', () => { clearTimeout(t); t = setTimeout(refresh, 160); });
  [dateStart, dateEnd].forEach(el => el?.addEventListener('change', refresh));
  clearDates?.addEventListener('click', () => {
    if (dateStart) dateStart.value = '';
    if (dateEnd)   dateEnd.value   = '';
    refresh();
  });

  // Keyword UI
  kwAdd?.addEventListener('click', () => {
    addKeyword(kwInput?.value || '');
    if (kwInput) kwInput.value = '';
    kwInput?.focus();
  });
  kwInput?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter'){ e.preventDefault(); kwAdd?.click(); }
    if (e.key === 'Escape'){ kwInput.blur(); }
  });
  kwPresets.forEach(btn => {
    btn.addEventListener('click', () => addKeyword(btn.dataset.kw || ''));
  });
})();
