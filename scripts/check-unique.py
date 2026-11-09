"""Contrôle d'unicité du contenu — RECETTE-SITE.md §6 et §7.

Usage : python3 check-unique.py <dossier-site> [--verbose] [--seuil 30]

Deux règles, toutes deux bloquantes avant publication :
  1. Deux pages indexables ne dépassent pas 30 % de similarité textuelle.
  2. Une question de FAQ (schema FAQPage) ne paraît que sur une seule page.

Le texte comparé est celui de <main>, sans les scripts ni les balises. Les nombres
sont neutralisés avant comparaison : deux pages « par montant » qui ne diffèrent que
par leurs chiffres sont du contenu dupliqué, pas du contenu unique.
"""
import re, sys, glob, os, html, json, difflib, itertools, collections

site = sys.argv[1].rstrip('/')

# Astro sort dans `dist/`, Next en export statique dans `out/`. Sans ce choix, les
# cinq sites Next du portefeuille rendaient « 0 page, 0 a corriger » : un echec
# deguise en succes.
# Les dossiers d'archive ne sont pas servis : les compter reviendrait a auditer
# un site fantome, et fausserait l'unicite autant que le compte de pages.
ARCHIVES = ('_archives/', '/archive/', '/old/', '/backup/')
# Le dossier servi n'est pas toujours `dist` : salaryafter.com publie depuis
# `docs/` et calorierule.com depuis `output/`. Ne chercher que dist et out
# faisait contrôler un build obsolète, ou rien du tout (2026-09-26).
# Quand deux candidats coexistent, c'est celui qui porte le plus de pages.
SORTIES = ('dist', 'out', 'build', 'docs', 'output', '_site', 'www')


def _compte_pages(chemin):
    n = 0
    for racine, _, fichiers in os.walk(chemin):
        n += sum(1 for f in fichiers if f.endswith('.html'))
    return n


_candidats = [d for d in SORTIES
              if os.path.isdir(f'{site}/{d}') and os.path.isfile(f'{site}/{d}/index.html')]
if _candidats:
    sortie = max(_candidats, key=lambda d: _compte_pages(f'{site}/{d}'))
else:
    sortie = '' if os.path.isfile(f'{site}/index.html') else 'dist'
verbose = '--verbose' in sys.argv
seuil = 30.0
if '--seuil' in sys.argv:
    seuil = float(sys.argv[sys.argv.index('--seuil') + 1])

NUM = re.compile(r'[\d][\d\s.,\'’%€$£-]*')


OPEN = re.compile(r'<(section|div|aside|nav|form|p)\b[^>]*>', re.I)


def strip_chrome(t: str) -> str:
    """Retire les blocs `data-chrome` en respectant l'imbrication.

    Un `.*?</div>` s'arrêterait au premier `</div>` intérieur et laisserait la fin
    du bloc dans le texte comparé : l'encart auteur et le calculateur, qui ont des
    div imbriquées, revenaient ainsi dans la mesure.
    """
    while True:
        # `ul` et `ol` s'ajoutent a la liste : une bibliographie ou une liste de
        # liens generee a partir d'un fichier partage est identique par
        # construction d'une langue a l'autre. Mesure du 2026-09-25 sur
        # fdeinsider.com : /en/sources/ et /fr/sources/ ressortaient a 34 % de
        # similarite alors que toute leur prose differe, parce que les deux
        # listent les memes titres, editeurs et URL.
        m = re.search(r'<(section|div|aside|nav|form|p|ul|ol)\b[^>]*\sdata-chrome[^>]*>', t, re.I)
        if not m:
            return t
        tag = m.group(1).lower()
        depth, i = 1, m.end()
        pat = re.compile(rf'<(/?){tag}\b[^>]*>', re.I)
        while depth and (n := pat.search(t, i)):
            depth += -1 if n.group(1) else 1
            i = n.end()
        t = t[:m.start()] + ' ' + t[i:]


def body(doc: str) -> str:
    m = re.search(r'<main[^>]*>(.*?)</main>', doc, re.S)
    t = m.group(1) if m else doc
    # Blocs de chrome (navigation, calculateur, calculateurs associés, sources,
    # encart auteur) : identiques par construction, marqués `data-chrome`.
    t = strip_chrome(t)
    t = re.sub(r'<(script|style|table)[^>]*>.*?</\1>', ' ', t, flags=re.S | re.I)
    t = re.sub(r'<[^>]+>', ' ', t)
    t = html.unescape(t)
    t = NUM.sub('#', t)                       # les chiffres ne font pas l'unicité
    return re.sub(r'\s+', ' ', t).strip().lower()


def questions(doc: str) -> list[str]:
    out = []
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', doc, re.S):
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        for node in (data if isinstance(data, list) else [data]):
            if isinstance(node, dict) and node.get('@type') == 'FAQPage':
                for q in node.get('mainEntity', []):
                    if isinstance(q, dict) and q.get('name'):
                        out.append(' '.join(q['name'].split()))
    return out


pages: dict[str, str] = {}
faq: dict[str, list[str]] = {}
for f in sorted(x for x in glob.glob(f'{site}/{sortie}/**/index.html', recursive=True)
                if not any(a in x for a in ARCHIVES)):
    doc = open(f, encoding='utf-8', errors='ignore').read()
    if 'content="noindex' in doc:
        continue
    path = '/' + os.path.relpath(os.path.dirname(f), f'{site}/{sortie}').replace(os.sep, '/').strip('/') + '/'
    if path == '//':
        continue
    txt = body(doc)
    if len(txt.split()) < 120:                # pages de service trop courtes : hors contrôle
        continue
    pages[path] = txt
    faq[path] = questions(doc)

# Au-delà de 300 pages, la comparaison deux à deux dépasse 200 000 diffs et ne
# finit pas en un temps utile : on échantillonne alors une page sur n, réparties
# dans l'ordre alphabétique des URL, et le rapport le signale (2026-09-20).
ECHANTILLON = 250
echantillonne = len(pages) > ECHANTILLON
if echantillonne:
    pas = len(pages) / ECHANTILLON
    gardees = {p: t for i, (p, t) in enumerate(sorted(pages.items())) if int(i % pas) == 0}
    pages = gardees

# ── 1. Similarité deux à deux ────────────────────────────────────────────────
paires = []
for (pa, ta), (pb, tb) in itertools.combinations(pages.items(), 2):
    # pré-filtre peu coûteux sur le vocabulaire avant le diff, plus lent
    sa, sb = set(ta.split()), set(tb.split())
    if len(sa & sb) / max(len(sa | sb), 1) < 0.25:
        continue
    # difflib coûte O(n²) : sur un site de 600 pages longues, la comparaison
    # deux à deux ne finissait pas. Deux garde-fous (breeds101.com, 2026-09-20) :
    # on ne compare que les 12 000 premiers caractères, et on écarte d'abord les
    # paires que les bornes supérieures de difflib donnent déjà sous le seuil.
    sm = difflib.SequenceMatcher(None, ta[:12000], tb[:12000])
    if sm.real_quick_ratio() * 100 < seuil or sm.quick_ratio() * 100 < seuil:
        continue
    r = sm.ratio() * 100
    if r > seuil or verbose:
        paires.append((r, pa, pb))
paires.sort(reverse=True)

# ── 2. Questions de FAQ répétées ─────────────────────────────────────────────
compte = collections.Counter(q for qs in faq.values() for q in qs)
repetees = {q: n for q, n in compte.items() if n > 1}

echecs = 0
if paires:
    trop = [p for p in paires if p[0] > seuil]
    if trop:
        print(f'\n  Pages trop proches (seuil {seuil:.0f} %) :')
        for r, pa, pb in trop[:20]:
            print(f'    {r:5.1f} %  {pa}  ≈  {pb}')
        echecs += len(trop)
    if verbose:
        for r, pa, pb in paires[:10]:
            print(f'    {r:5.1f} %  {pa}  ·  {pb}')

if repetees:
    print(f'\n  Questions de FAQ présentes sur plusieurs pages :')
    for q, n in sorted(repetees.items(), key=lambda x: -x[1])[:20]:
        ou = [p for p, qs in faq.items() if q in qs]
        print(f'    ×{n}  « {q[:70]} »')
        print(f'         {", ".join(ou[:4])}{" …" if len(ou) > 4 else ""}')
    echecs += len(repetees)

print(f'\n{site} : {len(pages)} pages comparées{" (échantillon)" if echantillonne else ""}, '
      f'{len([p for p in paires if p[0] > seuil])} paire(s) trop proches, '
      f'{len(repetees)} question(s) recyclée(s)')
sys.exit(1 if echecs else 0)
