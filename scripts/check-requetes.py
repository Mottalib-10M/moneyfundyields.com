#!/usr/bin/env python3
"""Couverture des requêtes réelles (RECETTE §23.2).

Interroge les suggestions Google du pays et de la langue pour chaque requête-graine,
puis cherche, pour chaque suggestion, la page du site dont le titre, le H1 ou l'URL
en reprend le mieux les mots, dans toute écriture (latin, grec, cyrillique, arabe, hébreu…).
Une suggestion sans page qui couvre au moins 60 % de ses mots est un trou possible, à lire
à la main (marque, navigation, intention hors sujet). Une suggestion dont aucun mot n'a pu
être lu est signalée « ?? », jamais comptée comme couverte.

Usage : check-requetes.py <site> --hl nb --gl no "lønn etter skatt" "skattekalkulator" …
"""
import argparse, glob, html, json, re, sys, time, unicodedata, urllib.parse, urllib.request

# Écritures dont les signes diacritiques sont décoratifs (accents, tonos, harakat, niqqud) : on
# les retire. Ailleurs (devanagari, thaï…) ils font partie du mot et restent.
SANS_DIACRITIQUES = ('LATIN', 'GREEK', 'CYRILLIC', 'ARABIC', 'HEBREW')
# Arabe : variantes d'écriture qui se confondent dans les recherches (le hamza de أ إ آ ؤ ئ
# tombe déjà avec les diacritiques).
ARABE = str.maketrans({'ة': 'ه', 'ى': 'ي', 'ـ': None, 'ٱ': 'ا'})
# Hébreu : lettres finales ramenées à leur forme courante.
HEBREU = str.maketrans('ךםןףץ', 'כמנפצ')
ARTICLE_ARABE = re.compile(r'^(?:[وفبك]?ال|لل)(?=...)')
# Écritures sans espace entre les mots : on compare des paires de caractères.
SANS_ESPACE = re.compile(r'[฀-໿က-႟ក-៿぀-ヿ㐀-䶿一-鿿가-힯豈-﫿]')

def lettre(c):
    return c.isalnum() or unicodedata.category(c) in ('Mn', 'Mc')

def norm(t):
    t = unicodedata.normalize('NFKD', t.casefold())
    s, base = [], ''
    for c in t:
        if unicodedata.combining(c):
            if base.startswith(SANS_DIACRITIQUES): continue
        else:
            base = unicodedata.name(c, '')
            d = unicodedata.decimal(c, None)
            if d is not None: c = str(d)  # chiffres arabes-indiens, persans, devanagari… → 0-9
        s.append(c)
    t = unicodedata.normalize('NFC', ''.join(s)).translate(ARABE).translate(HEBREU)
    ws = []
    for w in ''.join(c if lettre(c) else ' ' for c in t).split():
        if SANS_ESPACE.search(w): ws += [w[i:i + 2] for i in range(max(1, len(w) - 1))]; continue
        w = ARTICLE_ARABE.sub('', w)
        if len(w) > 2 or w.isdigit(): ws.append(w)
    # Une année vaut une autre année (la page 2026 répond à « … 2025 », 1447 à « … 1448 » en
    # calendrier hégirien) ; singulier et pluriel se confondent par la racine.
    return ['<annee>' if re.fullmatch(r'20\d\d|14[4-5]\d', w) else w[:6] for w in ws]

ap = argparse.ArgumentParser(); ap.add_argument('site'); ap.add_argument('--hl', required=True); ap.add_argument('--gl', required=True); ap.add_argument('seeds', nargs='+')
a = ap.parse_args()
out = 'dist' if glob.glob(f'{a.site}/dist/**/index.html', recursive=True) else 'out'
pages = []
for p in glob.glob(f'{a.site}/{out}/**/index.html', recursive=True):
    t = open(p, encoding='utf-8').read()
    if 'noindex' in t[:4000] or '/embed/' in p: continue
    ti = re.search(r'<title>(.*?)</title>', t, re.S); h1 = re.search(r'<h1[^>]*>(.*?)</h1>', t, re.S)
    url = p[len(a.site) + len(out) + 1:-10] or '/'
    txt = ' '.join([html.unescape(ti.group(1)) if ti else '', html.unescape(re.sub('<[^>]+>', '', h1.group(1))) if h1 else '', url.replace('-', ' ')])
    pages.append((url, set(norm(txt))))
    if not pages[-1][1]: print(f'?? page {url} : aucun mot lu dans le titre, le H1 ou l\'URL')
if not pages: sys.exit('0 page trouvée : le contrôle a échoué (RECETTE §0).')
holes = total = vides = 0
for seed in a.seeds:
    u = 'https://suggestqueries.google.com/complete/search?' + urllib.parse.urlencode({'client': 'firefox', 'hl': a.hl, 'gl': a.gl, 'q': seed})
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=15)
        sugg = json.loads(r.read().decode(r.headers.get_content_charset() or 'utf-8', 'replace'))[1][:8]
    except Exception as e: print(f'?? {seed}: {e}'); continue
    for q in sugg:
        words = set(norm(q)); total += 1
        if not words:  # jamais en silence : un « aucun trou » ne vaut que si chaque suggestion a été lue
            vides += 1; print(f'?? {q:55} → aucun mot exploitable, suggestion non comparée'); continue
        best = max(pages, key=lambda pg: (len(words & pg[1]), -len(pg[1])))  # à égalité, la page la plus ciblée
        cov = len(words & best[1]) / len(words)
        flag = 'ok' if cov >= 0.6 else '!!'
        holes += flag == '!!'
        print(f'{flag} {q:55} → {best[0]} ({cov:.0%})')
    time.sleep(0.4)
print(f'{a.site} : {total} suggestion(s), {holes} sans page qui les couvre (à lire à la main)'
      + (f', {vides} illisible(s) (« ?? » : à lire à la main)' if vides else ''))
if total and vides == total: sys.exit('Aucune suggestion lue : le contrôle a échoué (RECETTE §0), pas de conclusion possible.')
