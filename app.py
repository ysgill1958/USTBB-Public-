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

def feed(url, name, limit=50):
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

BASE_FEEDS = [
    ("NIH", "https://www.nih.gov/news-events/news-releases/rss.xml"),
    ("WHO", "https://www.who.int/feeds/entity/mediacentre/news/en/rss.xml"),
    ("Nature", "https://www.nature.com/nature.rss"),
    ("BMJ", "https://www.bmj.com/latest.xml"),
    ("Lancet", "https://www.thelancet.com/rssfeed/lancet_current.xml"),
    ("ScienceDaily Health", "https://www.sciencedaily.com/rss/health_medicine.xml"),
]

def aggregate(query, max_total=300, thumb_budget=120):
    feeds = [("Google News", google_news(query))] + BASE_FEEDS
    raw=[]
    for name, url in feeds:
        raw.extend(feed(url, name))

    # dedupe
    seen=set(); items=[]
    for it in raw:
        if not it.get("title") or not it.get("link"): continue
        key = normalize_key(it["title"], it["link"])
        if key in seen: continue
        seen.add(key); items.append(it)
        if len(items) >= max_total: break

    # thumbnails
    for it in items:
        if thumb_budget <= 0: break
        img = get_og_image(it["link"])
        if img:
            it["image"] = img
            thumb_budget -= 1

    items.sort(key=lambda x: x.get("date") or "", reverse=True)
    return items

# --- HTML generators ---

def footer_html():
    return """
  <footer class="footer">
    <div class="footer-grid">
      <div>
        <h3>Essential Legal & Info</h3>
        <ul>
          <li>© 2025 USTBB</li>
          <li><a href="./privacy.html">Privacy Policy</a></li>
          <li><a href="./terms.html">Terms of Use</a></li>
          <li><a href="./sitemap.xml">Sitemap</a></li>
          <li><a href="mailto:contact@ustbb.org">Contact</a></li>
        </ul>
      </div>
      <div>
        <h3>Navigation & Content</h3>
        <ul>
          <li><a href="./newsletter.html">Newsletter</a></li>
          <li><a href="./about.html">About Us</a></li>
          <li><a href="./faq.html">FAQ / Support</a></li>
          <li><a href="./category/ai.html">AI</a></li>
          <li><a href="./category/space.html">Space</a></li>
          <li><a href="./category/health.html">Health</a></li>
        </ul>
      </div>
      <div>
        <h3>Community & Social</h3>
        <ul class="social">
          <li><a href="https://twitter.com/" target="_blank">Twitter</a></li>
          <li><a href="https://facebook.com/" target="_blank">Facebook</a></li>
          <li><a href="https://linkedin.com/" target="_blank">LinkedIn</a></li>
        </ul>
      </div>
    </div>
  </footer>
"""

def write_home_shell():
    (OUTPUT/"index.html").write_text(f"""<!doctype html>
<meta charset="utf-8">
<title>Universal Sci & Tech Breakthrough Beat — Global S&T Info Hub</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="./static/styles.css">

<div class="wrap">
  <header class="mast mast--colorful">
    <div class="brand">
      <h1>Universal Sci & Tech Breakthrough Beat</h1>
      <div class="tag">Global S&T Info Hub</div>
    </div>
    <nav class="nav">
      <a class="link" href="./archive/index.html">Archive →</a>
      <a class="link" href="./data/items.json" target="_blank" rel="noopener">JSON</a>
    </nav>
  </header>

  <details class="filters" open>
    <summary>Show Search Filter</summary>
    <div class="filter-grid">
      <input id="q" type="search" placeholder="Free text: title or summary…">
      <label>Date start <input id="dateStart" type="date"></label>
      <label>Date end <input id="dateEnd" type="date"></label>
      <button id="clearDates" class="btn">Clear dates</button>
    </div>
  </details>

  <div id="count" class="muted"></div>
  <div id="grid" class="grid"></div>
  <div id="empty" class="empty" style="display:none">No results.</div>
  {footer_html()}
</div>

<script src="./static/app.js"></script>
""", encoding="utf-8")

def write_archive_index():
    (ARCHIVE/"index.html").write_text(f"""<!doctype html>
<meta charset="utf-8">
<title>Archive — USTBB</title>
<link rel="stylesheet" href="../static/styles.css">
<div class="wrap">
  <header class="mast mast--colorful">
    <div class="brand">
      <h1>Archive</h1>
      <div class="tag">Global S&T Info Hub</div>
    </div>
    <nav class="nav">
      <a class="link" href="../index.html">← Home</a>
    </nav>
  </header>

  <p>Monthly archive pages appear after first scraper run.</p>
  {footer_html()}
</div>
""", encoding="utf-8")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--query",
        required=True,
        help="Search query for feeds (e.g., 'longevity OR aging OR randomized trial')"
    )
    args = parser.parse_args()

    # 1) Write homepage (includes colourful header + footer)
    write_home_shell()

    # 2) Scrape and aggregate items
    items = aggregate(args.query)

    # 3) Save items JSON for the frontend
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "items.json").write_text(json.dumps(items, indent=2), encoding="utf-8")

    # 4) Generate monthly archives + archive index (with header/footer)
    write_archives(items)

    print(f"✅ Wrote {len(items)} items")


if __name__ == "__main__":
    items = scrape_sources()
    write_index(items)
    write_archive_index(items) 
