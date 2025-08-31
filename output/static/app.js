(function(){
  const grid = document.getElementById('grid');
  const empty = document.getElementById('empty');
  const q = document.getElementById('q');
  const count = document.getElementById('count');
  const dateStart = document.getElementById('dateStart');
  const dateEnd = document.getElementById('dateEnd');
  const clearDates = document.getElementById('clearDates');

  let all = [];

  const toISODateOnly = s => (s || '').slice(0,10);

  function withinDate(i){
    const d = toISODateOnly(i.date);
    const ds = dateStart && dateStart.value ? dateStart.value : null;
    const de = dateEnd && dateEnd.value ? dateEnd.value : null;
    if (ds && d < ds) return false;
    if (de && d > de) return false;
    return true;
  }

  function anyFiltersActive(){
    const term = q && q.value ? q.value.trim() : '';
    return !!term || (dateStart && dateStart.value) || (dateEnd && dateEnd.value);
  }

  function filterAll(){
    const term = q && q.value ? q.value.toLowerCase() : '';
    return all.filter(i=>{
      const tOk = !term ||
        (String(i.title||'').toLowerCase().includes(term)) ||
        (String(i.summary||'').toLowerCase().includes(term));
      return tOk && withinDate(i);
    });
  }

  function cardHTML(i){
    const imgBox = i.image
      ? '<div class="mediaBox"><img class="thumb" loading="lazy" src="'+i.image+'" alt=""></div>'
      : '<div class="mediaBox mediaBox--placeholder"><div class="media__inner"><div class="media__title">'
        + (i.title||'').slice(0,120) + '</div><div class="media__summary">'
        + (i.summary||'No summary available.').slice(0,180) + '</div></div></div>';

    return '<div class="card"><div class="inner">'
      + '<div class="txt">'
      + '<h3 class="title"><a target="_blank" href="'+i.link+'">'+(i.title||'')+'</a></h3>'
      + '<div class="muted">'+(i.date||'')+' • '+(i.source||'')+'</div>'
      + '<p class="summary">'+(i.summary||'')+'</p>'
      + '</div>'
      + imgBox
      + '</div></div>';
  }

  function render(list){
    const limit = anyFiltersActive() ? list.length : 25;
    const limited = list.slice(0, limit);
    grid.innerHTML = limited.map(cardHTML).join('');
    count.textContent = anyFiltersActive()
      ? (limited.length + ' result(s)')
      : (limited.length + '/' + list.length + ' shown • ' + all.length + ' total');
    empty.style.display = limited.length ? 'none' : '';
  }

  function refresh(){ render(filterAll()); }

  // load data
  fetch('./data/items.json?cb=' + Date.now(), {cache:'no-store'})
    .then(r=>{ if(!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
    .then(items=>{
      if(!Array.isArray(items)) throw new Error('items.json invalid');
      all = items;
      refresh();
    })
    .catch(err=>{
      if (empty) empty.style.display = '';
      if (count) count.textContent = '0 results';
      console.error('Failed to fetch items.json', err);
    });

  // events
  let t=null;
  if (q) q.addEventListener('input', ()=>{ clearTimeout(t); t=setTimeout(refresh, 160); });
  if (dateStart) dateStart.addEventListener('change', refresh);
  if (dateEnd) dateEnd.addEventListener('change', refresh);
  if (clearDates) clearDates.addEventListener('click', ()=>{
    if (dateStart) dateStart.value = '';
    if (dateEnd) dateEnd.value = '';
    refresh();
  });
})();
