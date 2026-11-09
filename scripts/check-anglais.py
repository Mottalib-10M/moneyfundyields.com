"""Chaque page en langue locale a sa version anglaise — RECETTE-SITE.md §3 (règle du 2026-10-03).

Usage : python3 check-anglais.py <dossier-site>

Un site se fait dans la langue du pays et en anglais : les expatriés, les
frontaliers et les anglophones cherchent le même calcul en anglais, et c'est du
trafic en plus pour les mêmes pages. Le contrôle lit le build et vérifie que
toute page indexable dans une autre langue que l'anglais déclare une version
anglaise (`hreflang="en"` ou `en-XX`). La cohérence du maillage lui-même
(auto-référence, réciprocité) reste le travail de `check-hreflang.py`.

Exemptée : un site entièrement anglophone (Royaume-Uni, Irlande, États-Unis…).
Code de sortie 1 s'il manque au moins une version anglaise.
"""
import glob, re, sys

site = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "."
out = next((d for d in ("dist", "out") if glob.glob(f"{site}/{d}/**/index.html", recursive=True)), None)
if not out:
    sys.exit(f"{site} : aucun build (dist/ ou out/). Lancer le build d'abord.")

LANG = re.compile(r'<html[^>]*\blang=["\']([a-zA-Z-]+)', re.I)
ALT_EN = re.compile(r'<link[^>]+hreflang=["\']en(?:-[A-Za-z]{2})?["\']', re.I)
NOINDEX = re.compile(r'name=["\']robots["\'][^>]*noindex|noindex[^>]*name=["\']robots', re.I)
REDIR = re.compile(r'http-equiv=["\']refresh', re.I)

pages, manquantes, langues = 0, [], set()
for f in sorted(glob.glob(f"{site}/{out}/**/index.html", recursive=True)):
    doc = open(f, encoding="utf-8", errors="ignore").read()
    if NOINDEX.search(doc) or REDIR.search(doc) or "/404" in f:
        continue
    m = LANG.search(doc)
    lang = (m.group(1) if m else "").lower().split("-")[0]
    langues.add(lang)
    if lang == "en":
        continue
    pages += 1
    if not ALT_EN.search(doc):
        manquantes.append(f.replace(f"{site}/{out}", "").replace("index.html", "") or "/")

if langues <= {"en"}:
    print(f"{site} : site anglophone, contrôle sans objet.")
    sys.exit(0)
for p in manquantes:
    print(f"!! {p} : pas de version anglaise déclarée (hreflang en)")
print(f"{site} : {pages} page(s) en langue locale, {len(manquantes)} sans version anglaise")
sys.exit(1 if manquantes else 0)
