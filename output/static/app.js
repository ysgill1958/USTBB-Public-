(function(){
  const grid = document.getElementById('grid');
  const empty = document.getElementById('empty');
  const q = document.getElementById('q');
  const count = document.getElementById('count');
  const dateStartEl = document.getElementById('dateStart');
  const dateEndEl   = document.getElementById('dateEnd');
  const clearDates  = document.getElementById('clearDates');

  // keyword UI
  const kwInput = document.getElementById('kwInput');
  const kwAdd   = document.getElementById('kwAdd');
  const kwChips = document.getElementById('kwChips');
  const kwPresets = document.querySelectorAll('.chip--preset');

  let all = [];
  let keywords = []; // each item is {raw:string, terms:string[]} where terms is OR list

  // --- utils ---
  const toISODateOnly = s => (s||'').slice(0,10);
  const esc = s => (s||'').replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

  // split a raw keyword into OR terms by "|", keep quotes together
  function parseRawKeyword(raw){
    // allow phrases in quotes “like this” or "like this"
    const terms = [];
    const re = /"([^"]+)"|“([^”]+)”|([^|]+)/g;
    let m;
    while ((m = re.exec(raw)) !== null){
      const t = (m[1]||m[2]||m[3]||"").trim();
      if (t) terms.push(t.toLowerCase());
    }
    return terms;
  }

  function addKeyword(raw){
    raw = (raw || '').trim();
    if(!raw) return;
    // de-dupe by raw string lowercased
    if (keywords.some(k => k.raw.toLowerCase() === raw.toLowerCase())) return;
    keywords.push({ raw, terms: raw.split('|').map(s=>s.trim()).filter(Boolean).map(s=>s.toLowerCase()) });
    renderKwChips();
    refresh();
  }
  function removeKeyword(raw){
    keywords = keywords.filter(k => k.raw.toLowerCase() !== raw.toLowerCase());
    renderKwChips();
    refresh();
  }
  function renderKwChips(){
    kwChips.innerHTML = keywords.map(k =>
      `<span class="chip">${k.raw} <button aria-label="Remove ${k.raw}" data-del="${k.raw}">×</button></span>`
    ).join('');
    kwChips.querySelectorAll('button[data-del]').forEach(btn=>{
      btn.addEventListener('click', ()=> removeKeyword(btn.dataset.del));
    });
  }

  function highlight(text, terms){
    if(!text || !terms.length) return text || '';
    // flatten all OR terms from all keywords
    const flat = [];
    terms.forEach(orList => orList.forEach(t => flat.push(t)));
    const uniq = [...new Set(flat)].filter(Boolean);
    if(!uniq.length) return text;
    const rx = new RegExp('(' + uniq.map(esc).join('|') + ')','gi');
    return (text||'').replace(rx, '<mark>$1</mark>');
  }

  // keyword match: AND across keywords, OR within a keyword list
  function matchesKeywords(item){
    if(!keywords.length) return true;
    const hay = ((item.title||'') + ' ' + (item.summary||'')).toLowerCase();
    return keywords.every(k => k.terms.some(t => hay.includes(t)));
  }

  function withinDate(i){
    const d = toISODateOnly(i.date);
    const ds = dateStartEl?.value || null;
    const de = dateEndEl?.value || null;
    if (ds && d < ds) return false;
    if (de && d > de) return false;
    return true;
  }

  function anyFiltersActive(){
    const term = (q?.value||'').trim();
    return !!term || !!(dateStartEl?.value) || !!(dateEndEl?.value) || keywords.length>0;
  }

  function filterAll(){
    const term=(q?.value||'').toLowerCase();
    return all.filter(i=>{
      const tOk = !term || ((i.title||'').toLowerCase().includes(term) || (i.summary||'').toLowerCase().includes(term));
      return tOk && withinDate(i) && matchesKeywords(i);
    });
  }

 function cardHTML(i){
  const img = i.image
    ? `<div class="mediaBox"><img class="thumb" loading="lazy" src="${i.image}" alt=""></div>`
    : `<div class="mediaBox mediaBox--placeholder">
         <div class="media__inner">
           <div class="media__title">${(i.title||'').slice(0,120)}</div>
           <div class="media__summary">${(i.summary||'No summary available.').slice(0,180)}</div>
         </div>
       </div>`;

  // (If you also added keyword highlighting earlier, keep that. If not, just use i.title / i.summary.)
  const title = i.title || '';
  const summary = i.summary || '';

  return `<div class="card">
    <div class="inner">
      <div class="txt">
        <h3 class="title"><a target="_blank" href="${i.link}">${title}</a></h3>
        <div class="muted">${i.date||''} • ${i.source||''}</div>
        <p class="summary">${summary}</p>
      </div>
      ${img}
    </div>
  </div>`;
}


  function render(list){
    const limit = anyFiltersActive() ? list.length : 25;
    const limited = list.slice(0, limit);
    grid.innerHTML = limited.map(cardHTML).join('');
    count.textContent = anyFiltersActive()
      ? `${limited.length} results (all matches shown)`
      : `${limited.length}/${list.length} shown • ${all.length} total`;
    empty.style.display = limited.length ? 'none' : '';
  }

  function refresh(){ render(filterAll()); }

  // --- bootstrap ---
  fetch('./data/items.json?cb=' + Date.now(), {cache:'no-store'})
    .then(r=>{ if(!r.ok) throw new Error('HTTP '+r.status); return r.json(); })
    .then(items=>{
      if(!Array.isArray(items)){ throw new Error('items.json invalid'); }
      all = items;
      refresh();
    })
    .catch(_=>{
      empty.style.display=''; count.textContent='0 results';
    });

  // events
  let t=null;
  if (q) q.addEventListener('input', ()=>{ clearTimeout(t); t=setTimeout(refresh, 160); });
  [dateStartEl, dateEndEl].forEach(el => el?.addEventListener('change', refresh));
  clearDates?.addEventListener('click', ()=>{ if(dateStartEl) dateStartEl.value=''; if(dateEndEl) dateEndEl.value=''; refresh(); });

  kwAdd?.addEventListener('click', ()=>{
    addKeyword(kwInput.value);
    kwInput.value='';
    kwInput.focus();
  });
  kwInput?.addEventListener('keydown', (e)=>{
    if(e.key === 'Enter'){ e.preventDefault(); kwAdd.click(); }
    if(e.key === 'Escape'){ kwInput.blur(); }
  });
  kwPresets.forEach(btn=>{
    btn.addEventListener('click', ()=> addKeyword(btn.dataset.kw));
  });
})();
