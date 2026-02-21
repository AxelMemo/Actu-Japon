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
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
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
                    if url.startswith('//'): url = 'https:' + url
                    elif url.startswith('/'): url = 'https://mainichi.jp' + url
                    tit = a.get_text().strip()
                    if len(tit) > 30 and ("/articles/" in url or "rss" not in url):
                        if "mainichi.jp" in url: tit = clean_mainichi_title(tit)
                        par = a.find_parent(['div', 'li', 'article', 'section'])
                        desc = ""
                        if par:
                            p_tag = par.find(['p', 'div', 'span'], class_=re.compile(r'txt|summary|content|body|lead'))
                            if not p_tag: p_tag = par.find('p')
                            if p_tag: desc = p_tag.get_text().strip()[:200]
                        temp.append({"t": tit, "l": url, "d": desc})
            for i in temp[:15]:
                if i["l"] not in articles:
                    articles[i["l"]] = {"t": i['t'], "d": i['d'], "l": i["l"], "s": src["name"], "dt": date_str}
        except: print(f"Erreur {src['name']}")
    return articles

def write_html(filename, data, is_archive=False):
    jst_now = datetime.utcnow() + timedelta(hours=9)
    now_full = jst_now.strftime("%H:%M")
    src_list = sorted(list(set(a['s'] for a in data)))
    date_list = sorted(list(set(a['dt'] for a in data)), reverse=True)
    arch_files = sorted([f for f in os.listdir("archives") if f.endswith(".html")], reverse=True) if os.path.exists("archives") else []

    with open(filename, "w", encoding="utf-8") as f:
        f.write("<!DOCTYPE html><html lang='ja'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'>")
        f.write("<title>Japan News</title><style>")
        # STYLE NON-STICKY
        f.write("body{font-family:sans-serif;background:#f0f2f5;margin:0;padding:10px;color:#1c1e21}")
        f.write(".header{background:white;padding:15px;border-radius:12px;box-shadow:0 2px 10px rgba(0,0,0,0.05);margin-bottom:20px}")
        f.write("h1{font-size:1.3rem;margin:0 0 10px 0;display:inline-block}.update-time{font-size:0.75rem;color:gray;float:right}")
        f.write(".label{font-size:0.7rem;font-weight:bold;color:#65676b;margin:10px 0 5px 0;text-transform:uppercase}")
        f.write(".scroll-x{display:flex;overflow-x:auto;white-space:nowrap;gap:5px;padding-bottom:5px;scrollbar-width:none} .scroll-x::-webkit-scrollbar{display:none}")
        f.write(".btn{padding:8px 14px;border-radius:8px;border:1px solid #ddd;background:white;cursor:pointer;font-size:0.85rem;font-weight:bold;flex-shrink:0}")
        f.write(".btn.active{background:#1a73e8;color:white;border-color:#1a73e8} .btn-scope.active{background:#ffb300;color:black} .btn-util{background:#6c757d;color:white;border:none}")
        f.write(".article{background:white;padding:20px;margin-bottom:15px;border-radius:10px;border-top:5px solid #1a73e8;box-shadow:0 1px 3px rgba(0,0,0,0.1)}")
        f.write(".hidden{display:none!important} a{text-decoration:none;color:#000;font-weight:800;display:block;font-size:1.25rem;margin-bottom:10px;line-height:1.3}")
        f.write(".summary{font-size:0.95rem;color:#444;background:#f8f9fa;padding:12px;border-radius:8px;line-height:1.5}</style></head><body>")
        
        f.write("<div class='header'>")
        f.write(f"<h1>🇯🇵 News</h1> <span class='update-time'>Actualisé à {now_full} (JST)</span>")
        f.write("<input type='text' id='q' placeholder='Rechercher...' style='width:100%;padding:12px;border-radius:8px;border:1px solid #ddd;box-sizing:border-box' onkeyup='f()'>")
        
        f.write("<div class='label'>Rechercher dans :</div><div class='scroll-x'>")
        f.write("<button class='btn btn-scope active' onclick='sc(\"all\",this)'>Titre+Texte</button>")
        f.write("<button class='btn btn-scope' onclick='sc(\"t\",this)'>Titre</button>")
        f.write("<button class='btn btn-scope' onclick='sc(\"d\",this)'>Texte</button></div>")

        f.write("<div class='scroll-x' style='margin-top:10px'>")
        f.write("<button class='btn' id='smBtn' onclick='tgSm()' style='background:#34a853;color:white'>Regroupement : ON</button>")
        f.write("<button class='btn btn-util' onclick='mass(true)'>TOUT COCHER</button>")
        f.write("<button class='btn btn-util' onclick='mass(false)'>TOUT DÉCOCHER</button></div>")
        
        f.write("<div class='label'>Journaux :</div><div class='scroll-x'>")
        for s in src_list: f.write(f"<button class='btn active src-b' data-s='{s}' onclick='t(\"{s}\",this)'>{s.upper()}</button>")
        f.write("</div>")
        
        f.write("<div class='label'>Dates :</div><div class='scroll-x'>")
        if not is_archive:
            f.write("<button class='btn active date-b' onclick='sd(\"all\",this)'>TOUTES</button>")
            for d in date_list: f.write(f"<button class='btn date-b' onclick='sd(\"{d}\",this)'>{d.split('/')[0]+'/'+d.split('/')[1]}</button>")
        if arch_files and not is_archive:
            for af in arch_files[:5]: f.write(f"<a href='archives/{af}' class='btn' style='text-decoration:none;color:#1a73e8'>{af.replace('.html','')[:5]}</a>")
        f.write("</div>")
        
        if is_archive: f.write(f"<div style='margin-top:10px'><a href='../index.html' class='btn' style='display:inline-block;text-decoration:none'>← Retour au Live</a></div>")
        f.write("</div>")

        f.write("<div id='feed'>")
        for a in data:
            f.write(f"<div class='article' data-s='{a['s']}' data-dt='{a['dt']}' data-orig-t='{a['t'].replace(chr(39),chr(32))}'><div style='font-size:0.7rem;color:#1a73e8;font-weight:bold;margin-bottom:5px'>{a['s']} | {a['dt']}</div>")
            f.write(f"<a class='art-title' href='{a['l']}' target='_blank'>{a['t']}</a>")
            if a['d']: f.write(f"<div class='art-desc summary'>{a['d']}</div>")
            f.write("<div class='ex'></div></div>")
            
        f.write(f"</div><script>var acts=new Set({json.dumps(src_list)}); var selD='all'; var sm=true; var scope='all';")
        f.write("function tgSm(){{sm=!sm; const b=document.getElementById('smBtn'); b.innerText='Regroupement : '+(sm?'ON':'OFF'); b.style.background=sm?'#34a853':'#6c757d'; f()}}")
        f.write("function sc(s,b){{scope=s;document.querySelectorAll('.btn-scope').forEach(x=>x.classList.remove('active'));b.classList.add('active');f()}}")
        f.write("function sd(d,b){{selD=d;document.querySelectorAll('.date-b').forEach(x=>x.classList.remove('active'));b.classList.add('active');f()}}")
        f.write("function t(s,b){{if(acts.has(s))acts.delete(s);else acts.add(s);b.classList.toggle('active');f()}}")
        f.write("function mass(v){{var btns=document.querySelectorAll('.src-b');btns.forEach(b=>{{var s=b.getAttribute('data-s');if(v){{acts.add(s);b.classList.add('active')}}else{{acts.clear();b.classList.remove('active')}}}});f()}}")
        f.write("function getSim(s1,s2){{let x=new Set(s1.split(' ')), y=new Set(s2.split(' ')); let i=new Set([...x].filter(z=>y.has(z))); return i.size/Math.max(x.size,y.size);}}")
        f.write("function f(){{var q=document.getElementById('q').value.toLowerCase();document.querySelectorAll('.article').forEach(a=>{{")
        f.write("var s=a.getAttribute('data-s'), d=a.getAttribute('data-dt'), tTxt=a.querySelector('.art-title').innerText.toLowerCase(), dTxt=a.querySelector('.art-desc')?a.querySelector('.art-desc').innerText.toLowerCase():'';")
        f.write("var matchQ=false; if(scope==='all')matchQ=tTxt.includes(q)||dTxt.includes(q); else if(scope==='t')matchQ=tTxt.includes(q); else matchQ=dTxt.includes(q);")
        f.write("var v=acts.has(s)&&(selD==='all'||d===selD)&&matchQ; a.classList.toggle('hidden',!v);}})}} window.onload=f;</script></body></html>")

def main():
    os.makedirs("archives", exist_ok=True)
    all_articles = json.load(open("data.json", "r", encoding="utf-8")) if os.path.exists("data.json") else {}
    new_news = get_current_news()
    all_articles.update(new_news)
    json.dump(all_articles, open("data.json", "w", encoding="utf-8"), ensure_ascii=False)
    sorted_keys = sorted(all_articles.keys(), reverse=True)[:MAX_ARTICLES]
    live_data = [all_articles[k] for k in sorted_keys]
    write_html("index.html", live_data, is_archive=False)
    jst_now = datetime.utcnow() + timedelta(hours=9)
    if jst_now.hour == ARCHIVE_HOUR_JST:
        yesterday = (jst_now - timedelta(days=1)).strftime("%d/%m/%Y")
        archive_filename = f"archives/{yesterday.replace('/','-')}.html"
        if not os.path.exists(archive_filename):
            day_data = [a for a in all_articles.values() if a['dt'] == yesterday]
            if day_data: write_html(archive_filename, day_data, is_archive=True)

if __name__ == "__main__":
    main()
