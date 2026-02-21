import requests
from bs4 import BeautifulSoup
import feedparser
from datetime import datetime, timedelta
import json
import re
import os

# CONFIGURATION
MAX_ARTICLES = 1000 
ARCHIVE_HOUR_JST = 4 

SOURCES = [
    {"name": "Msociété", "url": "https://mainichi.jp/shakai/", "type": "html", "sel": "section.articlelist"},
    {"name": "MIncident", "url": "https://mainichi.jp/incident/", "type": "html", "sel": "section.articlelist"},
    {"name": "News On Japan", "url": "https://newsonjapan.com/html/newsdesk/Society_News/rss/index.xml", "type": "rss"},
    {"name": "Asahi AJW", "url": "https://www.asahi.com/ajw/travel/", "type": "html", "sel": ".list-style-01"},
    {"name": "Ouest France", "url": "https://altselection.ouest-france.fr/asie/japon/", "type": "html", "sel": "main"},
    {"name": "Japan Daily", "url": "https://japandaily.jp/category/culture/", "type": "html", "sel": "#main"},
    {"name": "Japan Forward", "url": "https://japan-forward.com/category/culture/", "type": "html", "sel": ".archive-content"},
    {"name": "Japan Today", "url": "https://japantoday.com/category/national", "type": "html", "sel": ".media-body"},
    {"name": "Sora News", "url": "https://soranews24.com/category/japan/", "type": "html", "sel": "#content"},
]

def clean_mainichi_title(text):
    text = re.split(r'\d{4}/\d{1,2}/\d{1,2}', text)[0]
    text = re.split(r'\d+文字', text)[0]
    text = re.split(r' \d{1,2}日', text)[0]
    return text.strip()

def get_current_news():
    articles = {}
    headers = {"User-Agent": "Mozilla/5.0"}
    jst_now = datetime.utcnow() + timedelta(hours=9)
    date_str = jst_now.strftime("%d/%m/%Y")
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
                        if "mainichi.jp" in url: tit = clean_mainichi_title(tit)
                        par = a.find_parent(['div', 'li', 'article', 'section'])
                        desc = ""
                        if par:
                            p_tag = par.find(['p', 'div', 'span'], class_=re.compile(r'txt|summary|content|body|lead'))
                            if not p_tag: p_tag = par.find('p')
                            if p_tag: desc = p_tag.get_text().strip()[:200]
                        temp.append({"t": tit, "l": url, "d": desc})
            for i in temp:
                if i["l"] not in articles:
                    articles[i["l"]] = {"t": i['t'], "d": i['d'], "l": i["l"], "s": src["name"], "dt": date_str}
        except: pass
    return articles

def write_html(filename, data, is_archive=False):
    jst_now = datetime.utcnow() + timedelta(hours=9)
    now_full = jst_now.strftime("%d/%m %H:%M")
    src_list = sorted(list(set(a['s'] for a in data)))
    date_list = sorted(list(set(a['dt'] for a in data)), reverse=True)
    arch_files = sorted([f for f in os.listdir("archives") if f.endswith(".html")], reverse=True) if os.path.exists("archives") else []

    with open(filename, "w", encoding="utf-8") as f:
        f.write("<!DOCTYPE html><html lang='ja'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'>")
        f.write("<title>Japan News Pro</title><style>")
        f.write("body{font-family:sans-serif;background:#f0f2f5;margin:0;padding:10px;color:#1c1e21} .header{background:white;padding:20px;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,0.05);position:sticky;top:10px;z-index:100;margin-bottom:20px} .label{font-size:0.75rem;font-weight:bold;color:#65676b;display:block;margin-top:12px;margin-bottom:5px;text-transform:uppercase} .btn{padding:8px 14px;border-radius:8px;border:1px solid #ddd;background:white;cursor:pointer;font-size:0.85rem;margin:2px;font-weight:bold} .btn.active{background:#1a73e8;color:white;border-color:#1a73e8} .btn-scope.active{background:#ffb300;color:black;border-color:#ffb300} .btn-smart{background:#34a853;color:white;border:none} .btn-util{background:#6c757d;color:white;border:none} .article{background:white;padding:20px;margin-bottom:15px;border-radius:10px;border-top:5px solid #1a73e8} .hidden{display:none!important} .art-title{text-decoration:none;color:#000;font-weight:800;display:block;font-size:1.3rem;margin-bottom:10px;line-height:1.3} .art-desc{font-size:0.95rem;color:#444;background:#f8f9fa;padding:12px;border-radius:6px;line-height:1.5} .badge{background:#ffd400;color:black;font-size:0.7rem;padding:3px 8px;border-radius:5px;font-weight:bold;margin-top:10px;display:inline-block}</style></head><body>")
        
        f.write("<div class='header'><h1>🇯🇵 Japan News Raw</h1>")
        f.write("<input type='text' id='q' placeholder='Rechercher...' style='width:100%;padding:12px;border-radius:8px;border:1px solid #ddd;box-sizing:border-box' onkeyup='f()'>")
        
        f.write("<span class='label'>RECHERCHER DANS :</span><div>")
        f.write("<button class='btn btn-scope active' onclick='sc(\"all\",this)'>Titre+Texte</button>")
        f.write("<button class='btn btn-scope' onclick='sc(\"t\",this)'>Titre</button>")
        f.write("<button class='btn btn-scope' onclick='sc(\"d\",this)'>Texte</button></div>")

        f.write("<div style='margin-top:10px'>")
        f.write("<button class='btn btn-util' onclick='mass(true)'>TOUT COCHER</button>")
        f.write("<button class='btn btn-util' onclick='mass(false)'>TOUT DÉCOCHER</button></div>")
        
        if arch_files and not is_archive:
            f.write("<span class='label'>HISTORIQUE :</span><div style='overflow-x:auto;white-space:nowrap;'>")
            for af in arch_files[:7]: f.write(f"<a href='archives/{af}' style='display:inline-block;font-size:0.8rem;margin-right:10px;color:#1a73e8;text-decoration:none;background:#eef6ff;padding:4px 8px;border-radius:5px'>{af.replace('.html','')}</a>")
            f.write("</div>")

        f.write("<span class='label'>JOURNAUX :</span><div>")
        for s in src_list: f.write(f"<button class='btn active src-b' data-s='{s}' onclick='t(\"{s}\",this)'>{s.upper()}</button>")
        f.write("</div>")
        
        f.write("<span class='label'>DATES :</span><div>")
        f.write("<button class='btn active date-b' onclick='sd(\"all\",this)'>TOUTES</button>")
        for d in date_list: f.write(f"<button class='btn date-b' onclick='sd(\"{d}\",this)'>{d}</button>")
        f.write("</div></div>")

        f.write("<div id='feed'>")
        for a in data:
            f.write(f"<div class='article' data-s='{a['s']}' data-dt='{a['dt']}'><div style='font-size:0.7rem;color:#1a73e8;font-weight:bold;margin-bottom:5px'>{a['s']} | {a['dt']}</div>")
            f.write(f"<a class='art-title' href='{a['l']}' target='_blank'>{a['t']}</a>")
            if a['d']: f.write(f"<div class='art-desc'>{a['d']}</div>")
            f.write("</div>")
            
        f.write("</div><script>")
        # On utilise une syntaxe JavaScript très simple pour éviter les bugs d'injection
        f.write(f"var acts=new Set({json.dumps(src_list)}); var selD='all'; var scope='all';")
        f.write("function sc(s,b){scope=s;document.querySelectorAll('.btn-scope').forEach(x=>x.classList.remove('active'));b.classList.add('active');f()}")
        f.write("function sd(d,b){selD=d;document.querySelectorAll('.date-b').forEach(x=>x.classList.remove('active'));b.classList.add('active');f()}")
        f.write("function t(s,b){if(acts.has(s))acts.delete(s);else acts.add(s);b.classList.toggle('active');f()}")
        f.write("function mass(v){var btns=document.querySelectorAll('.src-b');btns.forEach(b=>{var s=b.getAttribute('data-s');if(v){acts.add(s);b
