(async function(){
  const grid = document.getElementById('grid');
  const empty = document.getElementById('empty');
  const q = document.getElementById('q');
  const count = document.getElementById('count');
  const dateStartEl = document.getElementById('dateStart');
  const dateEndEl   = document.getElementById('dateEnd');
  const clearDates  = document.getElementById('clearDates');

  let all = [];
  try{
    const res = await fetch('./data/items.json?cb=' + Date.now(), {cache:'no-store'});
    if(!res.ok) throw new Error('HTTP ' + res.status);
    all = await res.json();
  }catch(e){
    empty.style.display = '';
    count.textContent = '0 results';
    console.error('Failed to fetch items.json', e);
    return;
  }
  if(!Array.isArray(all) || all.length===0){
    empty.style.display='';
    count.textContent = '0 results';
    return;
  }

  function toISODateOnly(s){ return (s||'').slice(0,10); }
  function decorate(item){ return { ...item, _dateOnly: toISODateOnly(item.date) }; }
  all = all.map(decorate);

  function withinDate(i){
    const d = i._dateOnly;
    const ds = dateStartEl?.value || null;
    const de = dateEndEl?.value || null;
    if (ds && d < ds) return false;
    if (de && d > de) return false;
    return true;
  }
  function anyFiltersActive(){
    const term = (q?.value||'').trim();
    return !!term || !!(dateStartEl?.value) || !!(dateEndEl?.value);
  }
  function filterAll(){
    const term=(q?.value||'').toLowerCase();
    return all.filter(i=>{
      const termOk = !term || ((i.title||'').toLowerCase().includes(term) || (i.summary||'').toLowerCase().includes(term));
      const dateOk = withinDate(i);
      return termOk && dateOk;
    });
  }
  function cardHTML(i){
    const img = i.image ? `<img class="thumb" loading="lazy" src="${i.image}" alt="">`
                         : `<div class="media"><div class="media__inner">
                              <div class="media__title">${(i.title||'').slice(0,120)}</div>
                              <div class="media__summary">${(i.summary||'No summary available.').slice(0,180)}</div>
                            </div></div>`;
    return `<div class="card">
      <div class="inner">
        <div class="txt">
          <h3 style="margin:.4rem 0"><a target="_blank" href="${i.link}">${i.title}</a></h3>
          <div class="muted">${i.date||''} • ${i.source||''}</div>
          <p>${i.summary||''}</p>
        </div>
        <div>${img}</div>
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

  let t=null;
  if (q) q.addEventListener('input', ()=>{ clearTimeout(t); t=setTimeout(refresh, 160); });
  [dateStartEl, dateEndEl].forEach(el => el?.addEventListener('change', refresh));
  clearDates?.addEventListener('click', ()=>{ if(dateStartEl) dateStartEl.value=''; if(dateEndEl) dateEndEl.value=''; refresh(); });

  refresh();
})();
