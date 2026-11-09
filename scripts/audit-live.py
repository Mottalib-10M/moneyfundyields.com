#!/usr/bin/env python3
"""audit-live.py — audit d'un site EN LIGNE à partir de son sitemap (RECETTE-SITE.md §23.1).

Pour chaque domaine : pages en erreur, titres hors 50–60, descriptions hors 150–160, titres
ouverts par un mot générique, titres en double, pages minces (< 400 mots dans le HTML servi :
signale une application React vide pour Google), noindex, canonique ailleurs, h1 absent ou multiple.
Écrit pages-<domaine>.json dans le dossier courant.

Usage : python3 audit-live.py domaine1 [domaine2 ...]
"""
import re, sys, json, html, concurrent.futures as cf, urllib.request, collections
import os
src=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'check-seo.py')).read()
G=re.search(r'GENERIC_START = re.compile\(r"(.*)"\)',src).group(1)
G=re.compile(G.replace('^(','^(free\\b|gratuit\\b|simulador\\b|calcular\\b|calcule\\b|optimisez\\b|compare\\b|comparateur\\b|comparatif\\b|guide\\b|',1),re.I)
SITES=sys.argv[1:]
def get(u):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 audit'}),timeout=25); return r.status,r.read().decode('utf8','ignore')
    except Exception as e: return getattr(e,'code',0),''
def locs(x): return re.findall(r'<loc>\s*([^<\s]+)\s*</loc>',x)
res={}
for d in SITES:
    _,sm=get(f'https://{d}/sitemap-index.xml')
    if not locs(sm): _,sm=get(f'https://{d}/sitemap.xml')
    urls=[]
    for l in locs(sm):
        if l.endswith('.xml'): urls+=locs(get(l)[1])
        else: urls.append(l)
    urls=list(dict.fromkeys(urls))
    def one(u):
        st,h=get(u)
        t=html.unescape((re.search(r'<title[^>]*>(.*?)</title>',h,re.S) or [None,''])[1].strip())
        m=re.search(r'<meta[^>]+name="description"[^>]+content="([^"]*)"',h) or re.search(r'<meta[^>]+content="([^"]*)"[^>]+name="description"',h)
        ds=html.unescape(m.group(1)) if m else ''
        noidx=bool(re.search(r'<meta[^>]+robots[^>]+noindex',h))
        can=(re.search(r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"',h) or [None,''])[1]
        body=re.sub(r'<(script|style|nav|header|footer)[\s\S]*?</\1>',' ',h); body=re.sub(r'<[^>]+>',' ',body)
        w=len(re.findall(r'\w+',html.unescape(body)))
        h1=len(re.findall(r'<h1',h))
        return dict(u=u,st=st,t=t,d=ds,noidx=noidx,can=can,w=w,h1=h1)
    with cf.ThreadPoolExecutor(16) as ex: pages=list(ex.map(one,urls))
    ok=[p for p in pages if p['st']==200]
    tl=collections.Counter(p['t'] for p in ok)
    r=dict(n=len(urls),err=sum(p['st']!=200 for p in pages),
      t_len=sum(not 50<=len(p['t'])<=60 for p in ok), d_len=sum(not 150<=len(p['d'])<=160 for p in ok),
      d_missing=sum(not p['d'] for p in ok),
      generic=sum(bool(G.match(p['t'].strip())) for p in ok), dup_t=sum(c for t,c in tl.items() if c>1),
      thin=sum(p['w']<400 for p in ok), noidx=sum(p['noidx'] for p in ok),
      can_other=sum(bool(p['can']) and p['can'].rstrip('/')!=p['u'].rstrip('/') for p in ok),
      h1bad=sum(p['h1']!=1 for p in ok), medw=sorted(p['w'] for p in ok)[len(ok)//2] if ok else 0,
      ex_generic=[p['t'] for p in ok if G.match(p['t'].strip())][:4])
    res[d]=r; print(d, json.dumps(r,ensure_ascii=False)); sys.stdout.flush()
    json.dump(pages,open(f'pages-{d}.json','w'),ensure_ascii=False)
