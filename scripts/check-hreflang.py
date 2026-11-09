"""Contrôle hreflang d'un site construit — RECETTE-SITE.md §18.

Usage : python3 _template/scripts/check-hreflang.py <dossier-site> [--verbose]

Un site multilingue signale à Google quelles pages sont les traductions les unes
des autres. Une seule erreur dans ce maillage et Google ignore **tout** le jeu
d'annotations de la page : les versions se concurrencent alors au lieu de se
compléter, et la traduction ne sert plus à rien.

Cinq contrôles, dans l'ordre où une erreur invalide le reste :

  1. Auto-référence — chaque page doit se citer elle-même. Sans cela Google
     écarte l'ensemble du jeu.
  2. Réciprocité — si A cite B, B doit citer A. Un lien qui ne revient pas
     annule le signal pour les deux pages.
  3. Accord avec le canonical — l'URL d'auto-référence doit être exactement
     celle du canonical, sinon les deux balises se contredisent.
  4. Codes de langue — ISO 639-1 sur deux lettres. `jp` pour le japonais et
     `eng` pour l'anglais sont les deux erreurs courantes ; le code correct est
     `ja` et `en`.
  5. URL absolues — Google exige une URL complète, protocole compris. Une URL
     relative est ignorée, ce qui vide le jeu d'annotations de son sens.
  6. Codes de région — ISO 3166-1 alpha-2, en majuscules, toujours précédés
     d'une langue. `en-uk` est invalide (le code du Royaume-Uni est `GB`), et
     une région seule ne veut rien dire.

Une seule balise `x-default` est admise par page.
"""
import re, glob, html, sys, os
from collections import defaultdict

site = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "."
verbose = "--verbose" in sys.argv

ALT = re.compile(
    r'<link[^>]+rel=["\']alternate["\'][^>]*>', re.I)
ATTR_HREFLANG = re.compile(r'hreflang=["\']([^"\']+)["\']', re.I)
ATTR_HREF = re.compile(r'href=["\']([^"\']+)["\']', re.I)
CANONICAL = re.compile(
    r'<link[^>]+rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']', re.I)
NOINDEX = re.compile(
    r'name=["\']robots["\'][^>]*noindex|noindex[^>]*name=["\']robots', re.I)

# ISO 639-1 : deux lettres. La liste complète compte 184 codes ; on valide la
# forme et on refuse les confusions les plus fréquentes plutôt que d'embarquer
# la table entière, qui vieillirait sans être maintenue.
FAUX_CODES = {
    "jp": "ja (japonais)",
    "eng": "en (anglais)",
    "fre": "fr (français)",
    "ger": "de (allemand)",
    "spa": "es (espagnol)",
    "por": "pt (portugais)",
    "chi": "zh (chinois)",
    "gre": "el (grec)",
    "dut": "nl (néerlandais)",
}
FAUSSES_REGIONS = {
    "UK": "GB (Royaume-Uni)",
    "EU": "aucun — l'Union européenne n'est pas un pays",
    "UN": "aucun — ce n'est pas un pays",
    "LA": "aucun — l'Amérique latine n'est pas un pays",
}
FORME = re.compile(r"^([a-z]{2,3})(?:-([A-Za-z]{4}))?(?:-([A-Za-z]{2}))?$")


def normalise(u: str) -> str:
    """Compare les URL sans se soucier du protocole ni du slash final."""
    u = u.strip().split("#")[0]
    u = re.sub(r"^https?://", "", u)
    return u.rstrip("/")


def lire(chemin: str):
    doc = open(chemin, encoding="utf-8", errors="ignore").read()
    if NOINDEX.search(doc):
        return None
    alternates = []
    for balise in ALT.finditer(doc):
        t = balise.group(0)
        lang, href = ATTR_HREFLANG.search(t), ATTR_HREF.search(t)
        if lang and href:
            alternates.append((lang.group(1).strip(), html.unescape(href.group(1).strip())))
    can = CANONICAL.search(doc)
    return {
        "alternates": alternates,
        "canonical": html.unescape(can.group(1).strip()) if can else None,
    }


fichiers = sorted(glob.glob(f"{site}/dist/**/index.html", recursive=True))
if not fichiers:
    fichiers = sorted(glob.glob(f"{site}/**/index.html", recursive=True))

pages = {}
for f in fichiers:
    if any(p in f for p in ("/node_modules/", "/_archives/")):
        continue
    d = lire(f)
    if d:
        pages[f] = d

# Index des URL déclarées, pour vérifier la réciprocité sans refaire de lecture.
# Plusieurs fichiers peuvent revendiquer le même canonical — une page de
# redirection à la racine pointe souvent vers la version par défaut. Seules les
# pages qui portent elles-mêmes des alternates comptent : une page sans
# alternate ne participe à aucun maillage et l'écraserait à tort.
par_url = {}
for f, d in pages.items():
    if not d["canonical"] or not d["alternates"]:
        continue
    cle = normalise(d["canonical"])
    if cle not in par_url:
        par_url[cle] = f

signale = 0
for f, d in sorted(pages.items()):
    chemin = os.path.relpath(f, site)
    alternates = d["alternates"]
    if not alternates:
        continue  # page monolingue : rien à vérifier

    defauts = []
    codes = [c for c, _ in alternates]

    # 1. Auto-référence, et 3. accord avec le canonical
    if d["canonical"]:
        cible = normalise(d["canonical"])
        if not any(normalise(h) == cible for _, h in alternates):
            defauts.append("pas d'auto-référence vers son propre canonical")
    else:
        defauts.append("pas de canonical : l'auto-référence est invérifiable")

    # 2. Réciprocité
    for code, href in alternates:
        if code == "x-default":
            continue
        autre = par_url.get(normalise(href))
        if autre is None:
            continue  # page hors du site construit : hors de portée du contrôle
        retours = {normalise(h) for _, h in pages[autre]["alternates"]}
        if d["canonical"] and normalise(d["canonical"]) not in retours:
            defauts.append(f"{code} ne renvoie pas vers cette page")

    # 5. URL absolues
    relatives = [c for c, h in alternates if not re.match(r"^https?://", h.strip())]
    if relatives:
        defauts.append(
            f"URL relative sur {len(relatives)} alternate(s) — hreflang exige l'URL complète")

    # 4 et 6. Forme des codes
    for code in codes:
        if code == "x-default":
            continue
        m = FORME.match(code)
        if not m:
            defauts.append(f"code « {code} » malformé")
            continue
        langue, _, region = m.groups()
        if langue in FAUX_CODES:
            defauts.append(f"« {langue} » n'existe pas, écrire {FAUX_CODES[langue]}")
        elif len(langue) == 3:
            defauts.append(f"« {langue} » est un code à trois lettres, hreflang en veut deux")
        if region:
            if region.upper() in FAUSSES_REGIONS:
                defauts.append(f"région « {region} » : écrire {FAUSSES_REGIONS[region.upper()]}")
            elif region != region.upper():
                defauts.append(f"région « {region} » doit être en majuscules")

    if codes.count("x-default") > 1:
        defauts.append("plusieurs x-default")

    doublons = {c for c in codes if codes.count(c) > 1 and c != "x-default"}
    for c in doublons:
        defauts.append(f"code « {c} » déclaré plusieurs fois")

    if defauts or verbose:
        signale += bool(defauts)
        marque = "!! " if defauts else "   "
        print(f"{marque}{chemin:58s} {len(alternates):2d} alt  {' · '.join(dict.fromkeys(defauts))}")

multilingues = sum(1 for d in pages.values() if d["alternates"])
print(f"{site} : {len(pages)} pages, {multilingues} avec hreflang, {signale} à corriger")
