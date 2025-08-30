def write_home_shell():
    (OUTPUT/"index.html").write_text("""<!doctype html>
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

    <div class="keywords">
      <div class="kw-input">
        <input id="kwInput" type="text" placeholder="Add keyword (Enter). Use OR with | and phrases in “quotes”">
        <button id="kwAdd" class="btn btn-primary">Add</button>
      </div>
      <div id="kwChips" class="kw-chips" aria-live="polite"></div>
      <div class="kw-presets">
        <button class="chip chip--preset" data-kw="longevity">longevity</button>
        <button class="chip chip--preset" data-kw="aging">aging</button>
        <button class="chip chip--preset" data-kw="randomized trial">randomized trial</button>
        <button class="chip chip--preset" data-kw="Ayurveda|Yoga">Ayurveda | Yoga (OR)</button>
      </div>
    </div>
  </details>

  <div id="count" class="muted"></div>
  <div id="grid" class="grid"></div>
  <div id="empty" class="empty" style="display:none">No results.</div>

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
          <li><a href="https://twitter.com/" target="_blank" rel="noopener">Twitter</a></li>
          <li><a href="https://facebook.com/" target="_blank" rel="noopener">Facebook</a></li>
          <li><a href="https://linkedin.com/" target="_blank" rel="noopener">LinkedIn</a></li>
        </ul>
      </div>
    </div>
  </footer>
</div>

<script src="./static/app.js"></script>
""", encoding="utf-8")
