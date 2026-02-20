import requests
from bs4 import BeautifulSoup
import feedparser
from datetime import datetime
import json

# LISTE DE VOS SOURCES
SOURCES = [
    {"name": "Mainichi", "url": "https://mainichi.jp/shakai/", "type": "html", "sel": "section.articlelist"},
    {"name": "Mainichi", "url": "https://mainichi.jp/incident/", "type": "html", "sel": "section.articlelist"},
    {"name": "News On Japan", "url": "https://newsonjapan.com/html/newsdesk/Society_News/rss/index.xml", "type": "rss"},
    {"name": "Asahi AJW", "url": "https://www.asahi.com/ajw/travel/", "type": "html", "sel": ".list-style-01"},
    {"name": "Ouest France", "url": "https://altselection.ouest-france.fr/asie/japon/", "type": "html", "sel": "main"},
    {"name": "Japan Daily", "url": "https://japandaily.jp/category/culture/", "type": "html", "sel": "#main"},
    {"name": "Japan Forward", "url": "https://japan-forward.com/category/culture/", "type": "html", "sel": ".archive-content"},
    {"name": "Japan Today", "url": "https://japantoday.com/category/national", "type": "html", "sel": ".media-body"},
    {"name": "Sora News", "url": "https://soranews24.com/category/japan/", "type": "html", "sel": "#content"},
]

def get_articles():
    articles = {}
    headers = {"User-Agent": "Mozilla/5.0"}
    date_now = datetime.now().strftime("%d/%m")
    for src in SOURCES:
        try:
            temp = []
            if src["type"] == "rss":
                d = feedparser.parse(src["url"])
                for e in d.entries[:15]:
                    summ = BeautifulSoup(e.summary, "html.parser").get_text()[:200] if 'summary' in e else ""
                    temp.append({"t": e.title, "l": e.link, "d": summ})
            else:
                r = requests.get(src["url"], headers=headers, timeout=15)
                soup = BeautifulSoup(r.text, "html.parser")
                area = soup.select_one(src["sel"]) if "sel" in src else soup
                if not area: area = soup
                for a in area.find_all("a", href=True):
                    url = a['href']
                    if not url.startswith("http"):
                        url = "/".join(src["url"].split("/")[:3]) + ("" if url.startswith("/") else "/") + url
                    tit = a.get_text().strip()
                    if len(tit) > 30:
                        par = a.find_parent(['div', 'li', 'article'])
                        desc = par.find('p').get_text().strip()[:200] if par and par.find('p') else ""
                        temp.append({"t": tit, "l": url, "d": desc})
            for i in temp[:15]:
                if i["l"] not in articles:
                    articles[i["l"]] = {"t": i['t'], "d": i['d'], "l": i["l"], "s": src["name"], "dt": date_now}
        except: print(f"Erreur {src['name']}")
    return list(articles.values())

def main():
    data = get_articles()
    src_list = sorted(list(set(a['s'] for a in data)))
    with open("index.html", "w", encoding="utf-8") as f:
        # TRES IMPORTANT : lang='ja' pour que Chrome propose la traduction
        f.write("<!DOCTYPE html><html lang='ja'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'>")
        f.write("<style>body{font-family:sans-serif;background:#f0f2f5;margin:0;padding:10px} .header{background:white;padding:15px;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,0.05);position:sticky;top:10px;z-index:100;margin-bottom:20px} .btn{padding:6px 12px;border-radius:8px;border:1px solid #ddd;background:white;cursor:pointer;font-size:0.8rem;margin:2px} .btn.active{background:#1a73e8;color:white} .article{background:white;padding:20px;margin-bottom:15px;border-radius:10px;border-top:5px solid #1a73e8} .hidden{display:none!important} a{text-decoration:none;color:000;font-weight:800;display:block;font-size:1.2rem;margin-bottom:8px} .summary{font-size:0.95rem;color:#444;background:#f8f9fa;padding:10px;border-radius:6px}</style></head><body>")
        f.write("<div class='header'><h1>🇯🇵 Japan News Raw</h1><input type='text' id='q' placeholder='Rechercher...' style='width:100%;padding:10px' onkeyup='f()'><div style='margin-top:10px'>")
        for s in src_list: f.write(f"<button class='btn active src-b' data-s='{s}' onclick='t(\"{s}\",this)'>{s.upper()}</button>")
        f.write("</div></div><div id='feed'>")
        for a in data:
            f.write(f"<div class='article' data-s='{a['s']}' data-t='{a['t']}'><div style='font-size:0.7rem;color:#1a73e8;font-weight:bold'>{a['s']} | {a['dt']}</div>")
            f.write(f"<a href='{a['l']}' target='_blank'>{a['t']}</a><div class='summary'>{a['d']}</div></div>")
        f.write("</div><script>let acts=new Set("+json.dumps(src_list)+"); function t(s,b){if(acts.has(s)){acts.delete(s);b.classList.remove('active')}else{acts.add(s);b.classList.add('active')}f()} function f(){let q=document.getElementById('q').value.toLowerCase();document.querySelectorAll('.article').forEach(a=>{let v=acts.has(a.getAttribute('data-s'))&&a.getAttribute('data-t').toLowerCase().includes(q);a.classList.toggle('hidden',!v)})}</script></body></html>")

if __name__ == "__main__":
    main()
