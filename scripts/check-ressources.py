# -*- coding: utf-8 -*-
"""Chaque ressource appelee par une page en ligne repond-elle ?

Ecrit apres avoir annonce « quatre sites en ligne » sur la foi du seul code HTTP
de la page d'accueil. Les quatre repondaient bien 200, et les quatre etaient
pourtant servis en HTML nu : Jekyll, actif par defaut sur une branche publiee,
masquait le dossier `_astro` ou Astro place le CSS et le JavaScript. Un 200 sur
le document ne dit rien des fichiers qu'il appelle.

On collecte donc les feuilles de style, les scripts, les images, les polices et
les preloads de chaque page controlee, et on verifie chacun.
"""
import re, sys, urllib.request, urllib.error, concurrent.futures
from urllib.parse import urljoin

AGENT = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36'}
MOTIF = re.compile(
    r'<link[^>]+href="([^"]+)"[^>]*rel="(?:stylesheet|preload|icon|manifest)"'
    r'|<link[^>]+rel="(?:stylesheet|preload|icon|manifest)"[^>]+href="([^"]+)"'
    r'|<script[^>]+src="([^"]+)"'
    r'|<img[^>]+src="([^"]+)"', re.I)


def lire(u, delai=25):
    r = urllib.request.Request(u, headers=AGENT)
    with urllib.request.urlopen(r, timeout=delai) as f:
        return f.status, f.read().decode('utf8', 'replace')


def code(u, delai=25):
    try:
        r = urllib.request.Request(u, headers=AGENT, method='GET')
        with urllib.request.urlopen(r, timeout=delai) as f:
            return f.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:
        return type(e).__name__


for base in sys.argv[1:]:
    try:
        st, html = lire(base)
    except Exception as e:
        print(f'{base} : page inaccessible ({type(e).__name__})')
        continue
    urls = set()
    for m in MOTIF.finditer(html):
        u = next(g for g in m.groups() if g)
        if u.startswith(('data:', 'mailto:', '#')):
            continue
        urls.add(urljoin(base, u))
    with concurrent.futures.ThreadPoolExecutor(8) as ex:
        res = list(ex.map(code, sorted(urls)))
    mauvais = [(u, c) for u, c in zip(sorted(urls), res) if c != 200]
    print(f'{base} : {len(urls)} ressource(s), {len(mauvais)} en échec')
    for u, c in mauvais:
        print(f'    {c}  {u}')
