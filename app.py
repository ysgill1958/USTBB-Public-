# app.py — USTBB (Universal Sci & Tech Breakthrough Beat)
# Scrapes science/health feeds → builds output/data/items.json + monthly archives
# Homepage shows latest 25; search is client-side via app.js

import json, re, hashlib, argparse, email.utils as eut
from datetime import datetime, timezone
from time import mktime, sleep
from pathlib import Path
from urllib.parse import urlparse, urljoin
import requests, feedparser
from bs4 import BeautifulSoup

OUTPUT = Path("output")
DATA = OUTPUT / "data"
STATIC = OUTPUT / "static"
ARCHIVE = OUTPUT / "archive"
for p in (OUTPUT, DATA, STATIC, ARCHIVE): p.mkdir(parents=True, exist_ok=True)
(OUTPUT / ".nojekyll").write_text("")

HEADERS = {"User-Agent": "Mozilla/5.0 (USTBB/3.0; +GitHubPages Agent)"}

def clean_html(s: str) -> str:
    if not s: return ""
    s = re.sub(r"<.*?>", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def trunc(s, n=280):
    s = clean_html(s or "")
    return s if len(s) <= n else s[:n].rsplit(" ",1)[0] + "…"

def normalize_key(title, link):
    return hashlib.sha1(f"{urlparse(link or '').netloc}|{(title or '').lower().strip()}".encode()).hexdigest()

def parse_date(entry):
    for k in ("published_parsed","updated_parsed"):
        if entry.get(k):
            try: return datetime.utcfromtimestamp(mktime(entry[k])).strftime("%Y-%m-%d %H:%M:%S")
            except Exception: pass
    for k in ("published","updated","dc_date","date"):
        if entry.get(k):
            try:
                dt = eut.parsedate_to_datetime(entry[k])
                if dt and dt.tzinfo: dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception: pass
    return ""

def get_og_image(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=12); r.raise_for_status()
        soup = BeautifulSoup(r.content, "lxml")
        for sel in ['meta[property="og:image"]','meta[name="twitter:image"]','meta[property="og:image:url"]']:
            m = soup.select_one(sel)
            if m and m.get("content"): return urljoin(url, m["content"])
        img = soup.find("img", src=True)
        if img: return urljoin(url, img["src"])
    except Exception:
        return None

def feed(url, name, limit=60):
    items=[]
    try:
        r = requests.get(url, headers=HEADERS, timeout=25); r.raise_for_status()
        fp = feedparser.parse(r.content)
        for e in fp.entries[:limit]:
            items.append({
                "source": name,
                "title": (e.get("title") or "").strip(),
                "link": (e.get("link") or "").strip(),
                "summary": trunc(e.get("summary") or e.get("description") or ""),
                "date": parse_date(e),
                "image": None
            })
    except Exception:
        pass
    sleep(0.25)
    return items

def google_news(query):
    from requests.utils import quote
    return f"https://news.google.com/rss/search?q={quote(query)}&hl=en-IN&gl=IN&ceid=IN:en"

def pubmed(query):
    from requests.utils import quote
    return f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/erss.cgi?db=pubmed&term={quote(query)}&sort=date"

BASE_FEEDS = [
    ("NIH", "https://www.nih.gov/news-events/news-releases/rss.xml"),
    ("WHO", "https://www.who.int/feeds/entity/mediacentre/news/en/rss.xml"),
    ("Nature", "https://www.nature.com/nature.rss"),
    ("BMJ", "https://www.bmj.com/latest.xml"),
    ("Lancet", "https://www.thelancet.com/rssfeed/lancet_current.xml"),
    ("PLOS Medicine", "https://journals.plos.org/plosmedicine/feed/atom"),
    ("ScienceDaily Health", "https://www.sciencedaily.com/rss/health_medicine.xml"),
    ("bioRxiv Latest", "https://www.biorxiv.org/rss/latest.xml"),
    ("medRxiv Latest", "https://www.medrxiv.org/rss/latest.xml"),
]

def aggregate(query, max_total=600, thumb_budget=220):
    feeds = [("Google News", google_news(query)), ("PubMed", pubmed(query))] + BASE_FEEDS
    raw=[]
    for name, url in feeds:
        raw.extend(feed(url, name))

    # de-duplicate
    seen=set(); items=[]
    for it in raw:
        if not it.get("title") or not it.get("link"): continue
        key = normalize_key(it["title"], it["link"])
        if key in seen: continue
        seen.add(key); items.append(it)
        if len(items) >= max_total: break

    # thumbnails (budgeted)
    for it in items:
        if thumb_budget <= 0: break
        img = get_og_image(it["link"])
        if img:
            it["image"] = img
            thumb_budget -= 1

    # sort newest first
    items.sort(key=lambda x: x.get("date") or "", reverse=True)
    return items

def write_home_shell():
    (OUTPUT/"index.html").write_text("""<!doctype html>
<meta charset="utf-8">
<title>Universal Sci & Tech Breakthrough Beat — Global S&T Info Hub</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="./static/styles.css">
<div class="wrap">
  <header class="mast">
    <div class="brand">
      <h1>Universal Sci & Tech Breakthrough Beat</h1>
      <div class="tag">Global S&T Info Hub</div>
    </div>
    <nav class="nav">
      <a class="link" href="./archive/index.html">Archive →</a>
      <a class="link" href="./data/items.json" target="_blank" rel="noopener">JSON</a>
    </nav>
  </header>

  <details class="filters">
    <summary>Show Search Filter</summary>
    <div class="filter-grid">
      <input id="q" type="search" placeholder="Search title or summary…">
      <label>Date start <input id="dateStart" type="date"></label>
      <label>Date end <input id="dateEnd" type="date"></label>
      <button id="clearDates" class="btn">Clear dates</button>
    </div>
  </details>

  <div id="count" class="muted"></div>
  <div id="grid" class="grid"></div>
  <div id="empty" class="empty" style="display:none">No results.</div>
</div>
<script src="./static/app.js"></script>
""", encoding="utf-8")

def write_archive_index():
    (ARCHIVE/"index.html").write_text("""<!doctype html>
<meta charset="utf-8">
<title>Archive</title>
<link rel="stylesheet" href="../static/styles.css">
<div class="wrap">
  <h1>Archive</h1>
  <p>Monthly archive pages appear after first scraper run.</p>
</div>
""", encoding="utf-8")

def write_archives(items):
    by_month = {}
    for it in items:
        ym = (it.get("date") or "")[:7] or "unknown"
        by_month.setdefault(ym, []).append(it)

    for ym, arr in by_month.items():
        arr.sort(key=lambda x: x.get("date") or "", reverse=True)
        cards=[]
        for it in arr:
            title=it.get("title",""); link=it.get("link","#")
            date=it.get("date",""); summary=it.get("summary",""); image=it.get("image")
            if image:
                media=f"<img class='thumb' loading='lazy' src='{image}' alt=''>"
            else:
                media=f"<div class='media'><div class='media__inner'><div class='media__title'>{title[:120]}</div><div class='media__summary'>{(summary or 'No summary available.')[:180]}</div></div></div>"
            cards.append(f"<div class='card'><div class='inner'><div class='txt'><h3 style='margin:.4rem 0'><a target='_blank' href='{link}'>{title}</a></h3><div class='muted'>{date}</div><p>{summary}</p></div><div>{media}</div></div></div>")

        (ARCHIVE/f"{ym}.html").write_text(
            "<!doctype html><meta charset='utf-8'><title>Archive — "+ym+"</title>"
            "<link rel='stylesheet' href='../static/styles.css'>"
            "<div class='wrap'><h1>Archive — "+ym+"</h1><a class='link' href='../index.html'>← Home</a>"
            "<div class='grid'>"+ "".join(cards) +"</div></div>",
            encoding="utf-8"
        )

def ensure_static_css_js():
    (STATIC/"styles.css").write_text("""*{box-sizing:border-box}
body{font-family:system-ui,Arial,Segoe UI,Roboto,sans-serif;margin:0;background:#f8f9fa;color:#212529}
.wrap{max-width:1140px;margin:0 auto;padding:18px}
.mast{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:10px}
.brand h1{font-size:1.3rem;margin:0}
.tag{color:#6c757d;font-size:.95rem}
.link{color:#0d6efd;text-decoration:none}.link:hover{text-decoration:underline}
.filters{background:#fff;border:1px solid #dee2e6;border-radius:12px;padding:12px;margin-bottom:10px}
.filter-grid{display:grid;gap:8px;grid-template-columns:1fr 200px 200px 120px}
@media(max-width:760px){.filter-grid{grid-template-columns:1fr}}
input[type=search],input[type=date]{width:100%;padding:10px;border-radius:10px;border:1px solid #dee2e6;background:#fff;color:#212529}
.btn{padding:10px 12px;border-radius:10px;border:1px solid #dee2e6;background:#e9ecef;cursor:pointer}
.btn:hover{background:#dee2e6}
.grid{display:grid;gap:14px}
@media(min-width:720px){.grid{grid-template-columns:1fr 1fr}}
.card{background:#fff;border:1px solid #dee2e6;border-radius:12px;overflow:hidden}
.inner{display:grid;gap:12px;grid-template-columns:1fr 220px}
@media(max-width:719px){.inner{grid-template-columns:1fr}}
.txt{padding:14px}
.thumb{width:100%;height:100%;object-fit:cover;background:#f1f3f5}
.muted{color:#6c757d;font-size:.9em}
.badge{display:inline-block;padding:4px 10px;border-radius:999px;font-size:.78em;margin:0 6px 6px 0;border:1px solid #dee2e6;background:#e9ecef;color:#495057}
.empty{padding:18px;text-align:center;color:#6c757d}
.favicon{width:16px;height:16px;border-radius:4px;background:#e9ecef;flex:0 0 auto}
.media{width:100%;height:100%;background:#f1f3f5;border-left:1px solid #dee2e6;display:flex;align-items:center;justify-content:center;padding:12px}
.media__inner{max-height:100%;overflow:hidden;text-align:left}
.media__title{font-weight:600;line-height:1.25;margin:0 0 6px 0;font-size:14px;color:#212529}
.media__summary{color:#6c757d;font-size:13px;line-height:1.35}
.media__row{display:flex;align-items:center;gap:8px;margin-bottom:6px}
""", encoding="utf-8")

    (STATIC/"app.js").write_text("""(async function(){
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
  function decorate(item){
    return { ...item, _dateOnly: toISODateOnly(item.date) };
  }
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
""", encoding="utf-8")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True,
                        help="Search query for Google News / PubMed (e.g., 'longevity OR aging OR randomized trial')")
    args = parser.parse_args()

    ensure_static_css_js()
    write_home_shell()
    write_archive_index()

    items = aggregate(args.query)
    (DATA/"items.json").write_text(json.dumps(items, indent=2), encoding="utf-8")
    write_archives(items)

    print(f"✅ Wrote {len(items)} items")

if __name__ == "__main__":
    main()
