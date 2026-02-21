import requests
from bs4 import BeautifulSoup
import feedparser
from datetime import datetime, timedelta
import json
import re
import os

# CONFIGURATION
MAX_ARTICLES = 1000 # On monte à 1000 comme convenu
ARCHIVE_HOUR_JST = 4 # Heure du Japon pour créer l'archive quotidienne (04:00 AM)

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

def clean_mainichi_title(text):
    text = re.split(r'\d{4}/\d{1,2}/\d{1,2}', text)[0]
    text = re.split(r'\d+文字', text)[0]
    text = re.split(r' \d{1,2}日', text)[0]
    return text.strip()

def get_current_news():
    articles = {}
    headers = {"User-Agent": "Mozilla/5.0"}
    # Date formatée pour le stockage (Japon)
    jst_now = datetime.utcnow() + timedelta(hours=9)
    date_str = jst_now.strftime("%d/%m/%Y")
    
    for src in SOURCES:
        try:
            temp = []
            if src["type"] == "rss":
                d = feedparser.parse(src["url"])
                for e in d.entries[:20]:
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
                        if src["name"] == "Mainichi": tit = clean_mainichi_title(tit)
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
    now_full = (datetime.utcnow() + timedelta(hours=9)).strftime("%d/%m %H:%M")
    src_list = sorted(list(set(a['s'] for a in data)))
    date_list = sorted(list(set(a['dt'] for a in data)), reverse=True)
    
    # Récupérer la liste des fichiers dans archives/ pour le menu
    arch_files = []
    if os.path.exists("archives"):
        arch_files = sorted([f for f in os.listdir("archives") if f.endswith(".html")], reverse=True)

    with open(filename, "w", encoding="utf-8") as f:
        f.write("<!DOCTYPE html><html lang='ja'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'>")
        f.write(f"<title>{'Archive' if is_archive else 'Live'} Japan News</title><style>")
        f.write("body{font-family:sans-serif;background:#f0f2f5;margin:0;padding:10px;color:#1c1e21} .header{background:white;padding:15px;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,0.05);position:sticky;top:10px;z-index:100;margin-bottom:20px} .label{font-size:0.75rem;font-weight:bold;color:#65676b;display:block;margin-top:12px;margin-bottom:5px;text-transform:uppercase} .btn{padding:8px 14px;border-radius:8px;border:1px solid #ddd;background:white;cursor:pointer;font-size:0.85rem;margin:2px;font-weight:bold} .btn.active{background:#1a73e8;color:white;border-color:#1a73e8} .btn-scope.active{background:#ffb300;color:black} .article{background:white;padding:20px;margin-bottom:15px;border-radius:10px;border-top:5px solid #1a73e8} .hidden{display:none!important} a{text-decoration:none;color:#000;font-weight:800;display:block;font-size:1.3rem;margin-bottom:10px} .summary{font-size:0.95rem;color:#444;background:#f8f9fa;padding:10px;border-radius:6px}</style></head><body>")
        
        f.write("<div class='header'>")
        f.write(f"<h1>{'📂 ARCHIVE : ' + data[0]['dt'] if is_archive else '🇯🇵 Japan News Raw'}</h1>")
        if not is_archive: f.write(f"<div style='font-size:0.7rem;color:gray'>Mise à jour JST : {now_full}</div>")
        else: f.write("<a href='../index.html' style='font-size:0.9rem;color:#1a73e8'>← Retour au Live</a>")
        
        f.write("<input type='text' id='q' placeholder='Rechercher...' style='width:100%;padding:12px;border-radius:8px;border:1px solid #ddd;box-sizing:border-box;margin-top:10px' onkeyup='f()'>")
        
        f.write("<span class='label'>RECHERCHER DANS :</span><div><button class='btn btn-scope active' onclick='sc(\"all\",this)'>Titre+Texte</button><button class='btn btn-scope' onclick='sc(\"t\",this)'>Titre</button><button class='btn btn-scope' onclick='sc(\"d\",this)'>Texte</button></div>")
        
        f.write("<div style='margin-top:10px'><button class='btn' id='smBtn' onclick='tgSm()' style='background:#34a853;color:white'>Regroupement : ON</button><button class='btn' onclick='mass(true)' style='background:#6c757d;color:white'>TOUT COCHER</button><button class='btn' onclick='mass(false)' style='background:#6c757d;color:white'>TOUT DÉCOCHER</button></div>")
        
        if arch_files and not is_archive:
            f.write("<span class='label'>HISTORIQUE :</span><div style='overflow-x:auto;white-space:nowrap;'>")
            for af in arch_files[:7]: # 7 derniers jours
                f.write(f"<a href='archives/{af}' style='display:inline-block;font-size:0.8rem;margin-right:10px;color:#1a73e8'>{af.replace('.html','')}</a>")
            f.write("</div>")

        f.write("<span class='label'>JOURNAUX :</span><div>")
        for s in src_list: f.write(f"<button class='btn active src-b' data-s='{s}' onclick='t(\"{s}\",this)'>{s.upper()}</button>")
        f.write("</div>")
        
        if not is_archive:
            f.write("<span class='label'>DATES :</span><div><button class='btn active date-b' onclick='sd(\"all\",this)'>TOUTES</button>")
            for d in date_list: f.write(f"<button class='btn date-b' onclick='sd(\"{d}\",this)'>{d}</button>")
            f.write("</div>")
            
        f.write("</div><div id='feed'>")
        for a in data:
            f.write(f"<div class='article' data-s='{a['s']}' data-dt='{a['dt']}' data-orig-t='{a['t'].replace(chr(39),chr(32))}'><div style='font-size:0.7rem;color:#1a73e8;font-weight:bold'>{a['s']} | {a['dt']}</div><a href='{a['l']}' target='_blank'>{a['t']}</a>")
            if a['d']: f.write(f"<div class='summary'>{a['d']}</div>")
            f.write("<div class='ex'></div></div>")
        
        f.write(f"</div><script>let acts=new Set({json.dumps(src_list)});let selD='all';let sm=true;let scope='all';function tgSm(){{sm=!sm;const b=document.getElementById('smBtn');b.innerText='Regroupement : '+(sm?'ON':'OFF');b.style.background=sm?'#34a853':'#6c757d';f()}}function sc(s,b){{scope=s;document.querySelectorAll('.btn-scope').forEach(x=>x.classList.remove('active'));b.classList.add('active');f()}}function sd(d,b){{selD=d;document.querySelectorAll('.date-b').forEach(x=>x.classList.remove('active'));b.classList.add('active');f()}}function t(s,b){{if(acts.has(s))acts.delete(s);else acts.add(s);b.classList.toggle('active');f()}}function mass(v){{const btns=document.querySelectorAll('.src-b');btns.forEach(b=>{{const s=b.getAttribute('data-s');if(v){{acts.add(s);b.classList.add('active')}}else{{acts.clear();b.classList.remove('active')}}}});f()}}function getSim(s1,s2){{let x=new Set(s1.split(' ')),y=new Set(s2.split(' '));let i=new Set([...x].filter(z=>y.has(z)));return i.size/Math.max(x.size,y.size)}}function f(){{let q=document.getElementById('q').value.toLowerCase();let arts=Array.from(document.querySelectorAll('.article'));arts.forEach(a=>{{a.classList.remove('hidden');a.querySelector('.ex').innerHTML=''}});let seen=[];arts.forEach(a=>{{let s=a.getAttribute('data-s'),d=a.getAttribute('data-dt'),titleEl=a.querySelector('a'),descEl=a.querySelector('.summary'),tTxt=titleEl?titleEl.innerText.toLowerCase():'',dTxt=descEl?descEl.innerText.toLowerCase():'',matchQ=false;if(scope==='all')matchQ=tTxt.includes(q)||dTxt.includes(q);else if(scope==='t')matchQ=tTxt.includes(q);else matchQ=dTxt.includes(q);let v=acts.has(s)&&(selD==='all'||d===selD)&&matchQ;if(v&&sm){{let curT=a.getAttribute('data-orig-t');let dupe=seen.find(x=>getSim(x.t,curT)>0.6);if(dupe){{v=false;dupe.e.querySelector('.ex').innerHTML='<span style=\"background:#ffd400;color:black;font-size:0.7rem;padding:3px 8px;border-radius:5px;font-weight:bold;margin-top:10px;display:inline-block\">+ Sujet similaire</span>'}}else{{seen.push({{t:curT,e:a}})}}}}if(!v)a.classList.add('hidden')}})}}window.onload=f</script></body></html>")

def main():
    # 1. Charger l'historique complet
    if os.path.exists("data.json"):
        with open("data.json", "r", encoding="utf-8") as f:
            all_articles = json.load(f)
    else:
        all_articles = {}

    # 2. Chercher les nouvelles news
    new_news = get_current_news()
    all_articles.update(new_news)
    
    # 3. Sauvegarder data.json
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(all_articles, f, ensure_ascii=False)

    # 4. Préparer le Live (index.html) - les 1000 derniers
    sorted_keys = sorted(all_articles.keys(), reverse=True)[:MAX_ARTICLES]
    live_data = [all_articles[k] for k in sorted_keys]
    write_html("index.html", live_data, is_archive=False)

    # 5. Logique d'archivage quotidien (JST)
    jst_now = datetime.utcnow() + timedelta(hours=9)
    if jst_now.hour == ARCHIVE_HOUR_JST:
        yesterday = (jst_now - timedelta(days=1)).strftime("%d/%m/%Y")
        archive_filename = f"archives/{yesterday.replace('/','-')}.html"
        
        if not os.path.exists(archive_filename):
            day_data = [a for a in all_articles.values() if a['dt'] == yesterday]
            if day_data:
                write_html(archive_filename, day_data, is_archive=True)
                print(f"Archive créée : {archive_filename}")

if __name__ == "__main__":
    main()
