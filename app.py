import json, requests, feedparser
from pathlib import Path

OUTPUT = Path("output/data/items.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

FEEDS = [
    "https://www.nature.com/nature.rss",
    "https://www.thelancet.com/rssfeed/lancet_current.xml"
]

items = []
for url in FEEDS:
    fp = feedparser.parse(requests.get(url).content)
    for e in fp.entries[:20]:
        items.append({
            "title": e.get("title", ""),
            "link": e.get("link", ""),
            "date": e.get("published", ""),
            "summary": e.get("summary", "")[:200]
        })

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(items, f, indent=2)
