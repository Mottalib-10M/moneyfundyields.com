"""Liens internes morts, et annotations hreflang vers des pages absentes — §18.

Usage : python3 check-liens.py <dossier-site> [--verbose]

Astro construit sans se plaindre un lien vers une page qui n'existe pas. Aucun
des autres controleurs ne le voit : check-seo lit les pages une par une,
check-trame regarde la structure, check-sources ne sort que sur les URL
externes. Un lien de navigation casse donc silencieusement sur toutes les pages
du site a la fois, et ne se decouvre qu'en cliquant.

Mesure du 2026-09-24 sur forwarddeployedguide.com, 47 pages construites :
18 cibles internes manquantes, dont trois presentes dans la navigation et donc
mortes sur chacune des 47 pages. Aucun controleur ne les signalait.

Le controle est volontairement strict sur un point : une ancre du menu qui
pointe vers une page pas encore ecrite est un lien mort pour le visiteur, pas
une note de travail. On la compte.
"""
import re, glob, sys, os
from collections import defaultdict

site = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "."
verbose = "--verbose" in sys.argv
dist = os.path.join(site, "dist")
racine = dist if os.path.isdir(dist) else site

HREF = re.compile(r'href="(/[^"#?]*)"')
# Les annotations hreflang portent une URL absolue : un `alternate` vers une
# page qui repond 404 invalide tout le jeu d'annotations de la page, donc une
# traduction partielle mal declaree coute plus cher que pas de traduction
# (RECETTE §18). Mesure du 2026-09-25 sur fdeinsider.com : 20 cibles mortes
# apres l'ouverture d'une seconde langue dont une seule page etait ecrite.
# Aucun controleur ne les voyait : check-hreflang verifie la reciprocite et la
# forme des codes, pas l'existence des pages.
ALT = re.compile(r'rel="alternate"[^>]*href="(?:https?://[^/"]+)?(/[^"#?]*)"')
# Un chemin dont le dernier segment porte une extension designe un fichier
# (feuille de style, image, flux) : il est servi tel quel, pas comme une page.
FICHIER = re.compile(r"\.[a-z0-9]{2,5}$", re.I)


def normalise(h: str) -> str:
    return h if h.endswith("/") else h + "/"


pages = set()
for f in glob.glob(f"{racine}/**/*.html", recursive=True):
    rel = "/" + os.path.relpath(f, racine)
    if rel.endswith("/index.html"):
        pages.add(rel[: -len("index.html")])
    else:
        pages.add(rel)
        pages.add(normalise(rel[: -len(".html")]))
pages.add("/")

# Les fichiers servis tels quels : on les releve pour ne pas les confondre avec
# des pages absentes.
fichiers = {
    "/" + os.path.relpath(f, racine)
    for f in glob.glob(f"{racine}/**/*", recursive=True)
    if os.path.isfile(f)
}

morts = defaultdict(set)
for f in sorted(glob.glob(f"{racine}/**/*.html", recursive=True)):
    doc = open(f, encoding="utf-8", errors="ignore").read()
    source = "/" + os.path.relpath(f, racine).replace("index.html", "")
    for m in HREF.finditer(doc):
        h = m.group(1)
        if h in fichiers or FICHIER.search(h.rsplit("/", 1)[-1]):
            continue
        if normalise(h) not in pages:
            morts[normalise(h)].add(source)
    for m in ALT.finditer(doc):
        h = m.group(1)
        if normalise(h) not in pages:
            morts[normalise(h)].add(source + ' (hreflang)')

for cible, sources in sorted(morts.items(), key=lambda kv: -len(kv[1])):
    exemple = sorted(sources)[0]
    print(f"!! {cible:56s} {len(sources):3d} page(s)  ex. {exemple}")
    if verbose:
        for s in sorted(sources):
            print(f"       {s}")

# --- Routes declarees mais jamais construites -------------------------------
#
# Une route peut porter un chemin dans routes.ts sans qu'aucune page ne
# l'occupe. Rien ne le signale tant qu'aucun lien ne pointe dessus : la boucle
# ci-dessus ne verifie que les cibles effectivement citees. Le jour ou une page
# d'une autre langue declare son hreflang, elle pointe vers une URL qui n'existe
# pas, et le jeu d'annotations entier est ignore par Google.
# Constate sur fdeinsider.com le 2026-09-25 : implementation-roadmap declarait
# un chemin anglais depuis la creation du site, sans page.
CHEMIN = re.compile(r"""\b(?:en|fr|es|it|de|nl|pt|sv)\s*:\s*['"](/[^'"]*)['"]""")
routes_src = os.path.join(site, "src", "i18n", "routes.ts")
vides = []
if os.path.exists(routes_src):
    for m in CHEMIN.finditer(open(routes_src, encoding="utf-8").read()):
        chemin = normalise(m.group(1))
        if chemin not in pages:
            vides.append(m.group(1))
for v in sorted(set(vides)):
    print(f"!! {v:56s} route declaree, aucune page construite")

total = sum(len(s) for s in morts.values())
print(f"{site} : {len(pages)} pages, {len(morts)} cible(s) morte(s), "
      f"{total} lien(s) a corriger, {len(set(vides))} route(s) vide(s)")
sys.exit(1 if morts or vides else 0)
