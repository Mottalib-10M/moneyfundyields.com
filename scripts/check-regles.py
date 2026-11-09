"""check-regles.py — les règles automatiques de l'éditeur (RECETTE §6.6), avant publication.

Même calcul et mêmes seuils que l'onglet « Environnement Google » de seo-platform
(src/lib/audit-regles.ts), mais sur le build local, pour qu'un site soit conforme AVANT
d'être en ligne :
  - trame       : structure de l'accueil (suites de 4 blocs h1/h2/h3/section/form/table…)
                  comparée aux accueils en ligne du portefeuille. ≥ 80 % = KO, ≥ 60 % = à revoir.
  - chiffres    : date de mise à jour visible + au moins un lien vers une source officielle
                  (motif de la plateforme, ou domaines de scripts/sources-primaires.txt).
  - credibilite : l'accueil lie une page À propos ET une page de méthode.
  - reseau      : aucun lien de l'accueil ou de l'À propos vers un autre domaine du portefeuille.
  - publicite   : au plus 3 emplacements publicitaires sur l'accueil.
La copie entre sites est contrôlée par check-portefeuille.py.

Usage : python3 check-regles.py <dossier-site>        (code 1 si une règle est KO)
"""
import concurrent.futures as cf, glob, html, os, re, sys, time, urllib.request, json

site = sys.argv[1] if len(sys.argv) > 1 else '.'
ROOT = os.path.expanduser('~/Documents/GitHub')
DOMAINES = [l.strip() for l in open(os.path.join(ROOT, '_trame/domaines-ovh.txt')) if l.strip() and not l.startswith('#')]
# Sources officielles : liste partagée avec check-seo.py (sources_officielles.py, RECETTE §26 du 2026-10-16).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sources_officielles
RE_A_PROPOS = re.compile(r"/(about|about-us|a-propos|qui-sommes-nous|ueber-uns|uber-uns|sobre|sobre-nosotros|sobre-nos|chi-siamo|over-ons|om-oss|om-os|om|quem-somos|tietoa|meista|o-nas|sxetika|chi-siamo|despre|hakkimizda|tentang-kami)\b", re.I)
RE_METHODE = re.compile(r"(method|methodo|méthodo|methodik|metodolog|metode|berekening|calcul-|how-we-calculate|comment-calcul|sources|laskentatapa|menetelma|metod|yontem)", re.I)
RE_MAJ = re.compile(r"(mis à jour|mise à jour|updated|last updated|aktualisiert|stand:|actualizado|aggiornat|bijgewerkt|oppdatert|uppdaterad|atualizad|opdateret|päivitetty|zaktualizowano|aktualizacja|ενημερώθηκε|ενημέρωση|aggiornato|güncellendi|güncelleme|diperbarui|pembaruan)", re.I)
SLOTS = re.compile(r"<ins\b[^>]*adsbygoogle|data-ad-slot|class=[\"'][^\"']*\bad-slot", re.I)

def lire(p):
    try: return open(p, encoding='utf-8').read()
    except Exception: return ''

def accueil_local(d):
    out = os.path.join(d, 'dist') if os.path.isdir(os.path.join(d, 'dist')) else d
    h = lire(os.path.join(out, 'index.html'))
    m = re.search(r'http-equiv=["\']refresh["\'][^>]*url=([^"\'>]+)', h, re.I)
    if m:  # racine qui redirige vers /fr/ ou /en/ : on lit la vraie page
        h = lire(os.path.join(out, m.group(1).strip('/').split('?')[0], 'index.html')) or h
    return out, h

def structure(h):
    h = re.sub(r"<(script|style|svg|noscript)[\s\S]*?</\1>", "", h, flags=re.I)
    blocs = [m.group(1).lower() for m in re.finditer(r"<(h1|h2|h3|section|article|form|table|ul|ol|details|figure|input|select|button|aside)\b", h, re.I)]
    return {'>'.join(blocs[i:i + 4]) for i in range(len(blocs) - 3)}

def jaccard(a, b):
    return len(a & b) / len(a | b) if a and b else 0

def liens(h):
    return re.findall(r'href=["\']([^"\']+)', h)

CACHE = '/tmp/check-regles-accueils.json'
def accueils_portefeuille(moi):
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) and time.time() - os.path.getmtime(CACHE) < 86400 else {}
    def get(dom):
        if dom in cache: return dom, cache[dom]
        try:
            req = urllib.request.Request(f'https://{dom}/', headers={'User-Agent': 'Mozilla/5.0 (check-regles)'})
            h = urllib.request.urlopen(req, timeout=15).read().decode('utf-8', 'ignore')
            m = re.search(r'http-equiv=["\']refresh["\'][^>]*url=([^"\'>]+)', h, re.I)
            if m:
                u = m.group(1) if m.group(1).startswith('http') else f'https://{dom}/' + m.group(1).lstrip('/')
                h = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=15).read().decode('utf-8', 'ignore')
            return dom, h
        except Exception:
            return dom, ''
    with cf.ThreadPoolExecutor(12) as ex:
        res = dict(ex.map(get, [d for d in DOMAINES if d != moi]))
    cache.update(res); json.dump(cache, open(CACHE, 'w'))
    return {d: h for d, h in res.items() if h}

out, h = accueil_local(site)
if not h:
    sys.exit(f'{site} : accueil introuvable (build absent ?)')
moi = ''
for f in ('src/data/site-config.ts', 'src/lib/site-config.ts'):
    m = re.search(r"SITE_URL\s*=\s*['\"]https?://([^'\"/]+)", lire(os.path.join(site, f)))
    if m: moi = m.group(1); break
# Repli (sites hors trame Astro, config ailleurs) : sinon le site se compare à sa propre version en ligne.
if not moi:
    for f in ('public/CNAME', 'static/CNAME', 'CNAME', os.path.join(out, 'CNAME')):
        c = lire(os.path.join(site, f)).strip()
        if c: moi = c.splitlines()[0].strip(); break
if not moi:
    m = re.search(r"site\s*:\s*['\"]https?://([^'\"/]+)", lire(os.path.join(site, 'astro.config.mjs')))
    if m: moi = m.group(1)
moi = re.sub(r'^www\.', '', moi)

res = {}
# Trame
s = structure(h)
autres = accueils_portefeuille(moi)
proche = max(((d, jaccard(s, structure(x))) for d, x in autres.items()), key=lambda t: t[1], default=('', 0))
pct = round(proche[1] * 100)
res['trame'] = ('inconnu' if len(s) < 5 else 'ko' if pct >= 80 else 'a-verifier' if pct >= 60 else 'ok', f'site le plus proche : {proche[0]} ({pct} % de blocs en commun)')
# Chiffres
visible = re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)[\s\S]*?</\1>", " ", h, flags=re.I))
prim = sources_officielles.primaires_du_site(site, strict=False)
offi = {re.sub(r'^https?://([^/]+).*', r'\1', u) for u in liens(h) if sources_officielles.est_officielle(u, prim)}
maj = bool(RE_MAJ.search(html.unescape(visible)))
res['chiffres'] = ('ok' if maj and offi else 'a-verifier' if maj or offi else 'ko', f"{'date de mise à jour visible' if maj else 'PAS de date de mise à jour visible'} · {len(offi)} source(s) officielle(s) liée(s)")
# Crédibilité
internes = [u for u in liens(h) if u.startswith('/') and not u.startswith('//')]
ap = any(RE_A_PROPOS.search(u) for u in internes); me = any(RE_METHODE.search(u) for u in internes)
res['credibilite'] = ('ok' if ap and me else 'a-verifier' if ap or me else 'ko', f"À propos {'lié' if ap else 'NON lié'} · méthode {'liée' if me else 'NON liée'}")
# Réseau
apropos = next((lire(p) for p in glob.glob(os.path.join(out, '**', 'index.html'), recursive=True) if RE_A_PROPOS.search('/' + os.path.relpath(os.path.dirname(p), out).replace(os.sep, '/'))), '')
hotes = {re.sub(r'^https?://(www\.)?([^/]+).*', r'\2', u) for u in liens(h) + liens(apropos) if u.startswith('http')}
reseau = sorted(x for x in hotes if x in DOMAINES and x != moi)
res['reseau'] = ('ko' if len(reseau) >= 2 else 'a-verifier' if reseau else 'ok', f"liens vers : {', '.join(reseau) or 'aucun site du portefeuille'}")
# Publicité
n = len(SLOTS.findall(h))
res['publicite'] = ('ko' if n > 6 else 'a-verifier' if n > 3 else 'ok', f'{n} emplacement(s) publicitaire(s) sur l’accueil')

ko = 0
for r, (st, msg) in res.items():
    mark = {'ok': '  ', 'a-verifier': '? ', 'ko': '✗ ', 'inconnu': '~ '}[st]
    print(f'{mark}{r:12s} {st:10s} {msg}')
    ko += st in ('ko', 'a-verifier')
print(f'check-regles : {len(autres)} accueils comparés, {ko} règle(s) KO ou à revoir')
sys.exit(1 if ko else 0)
