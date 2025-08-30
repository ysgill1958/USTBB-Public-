(async function(){
  const res = await fetch('./data/items.json');
  const items = await res.json();
  const root = document.getElementById('root');
  root.innerHTML = items.map(i =>
    `<div><h3><a href="${i.link}" target="_blank">${i.title}</a></h3>
     <small>${i.date}</small><p>${i.summary}</p></div>`
  ).join('');
})();
