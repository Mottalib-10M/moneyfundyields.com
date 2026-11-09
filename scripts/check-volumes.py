"""Seuil de volume avant tout site — RECETTE-SITE.md §2.0 (règle du 2026-10-03).

Usage : python3 check-volumes.py <fichier-volumes> [--seuil 100000]

Aucun site ne se construit si les requêtes qu'il vise totalisent moins de
100 000 recherches par mois dans son pays, relevées dans le Keyword Planner de
Google Ads (compte objetech@gmail.com, jamais amradif). Le fichier est soit l'export CSV
du Keyword Planner, soit le copier-coller de l'écran (une requête, puis sa
fourchette « 10 k – 100 k » sur la ligne suivante).

Sans dépense publicitaire, Google ne donne qu'une fourchette. On retient la
moyenne géométrique des deux bornes (10 k – 100 k → 31 623), qui suit l'échelle
logarithmique des fourchettes : la borne basse sous-estimerait tout, la borne
haute promettrait dix fois trop. La décision affiche aussi le total des bornes
basses, pour voir la marge.

Une requête de marque, de jeu ou hors sujet se retire du fichier avant le
calcul : seules comptent les requêtes que le site servira vraiment.

Code de sortie 1 si l'estimation est sous le seuil.
"""
import csv, io, math, re, sys

args = [a for a in sys.argv[1:] if not a.startswith("--")]
if not args:
    print(__doc__); sys.exit(2)
SEUIL = 100_000
if "--seuil" in sys.argv:
    SEUIL = int(sys.argv[sys.argv.index("--seuil") + 1])
    args = [a for a in args if a != str(SEUIL)]

raw = open(args[0], "rb").read()
# L'export du Keyword Planner est en UTF-16 avec BOM ; un copier-coller est en UTF-8.
if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
    txt = raw.decode("utf-16")
else:
    try:
        txt = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        txt = raw.decode("latin-1")


def nombre(s: str) -> float:
    """« 10 k » → 10 000 ; « 1 M » → 1 000 000 ; « 1 900 » → 1 900."""
    s = s.strip().replace(" ", "").replace("\xa0", "").replace(" ", "").replace(",", ".").upper()
    mult = 1
    if s.endswith("K"): mult, s = 1_000, s[:-1]
    elif s.endswith("M"): mult, s = 1_000_000, s[:-1]
    return float(s) * mult


FOURCHETTE = re.compile(r"^\s*([\d\s., \xa0]+[kKmM]?)\s*[–-]\s*([\d\s., \xa0]+[kKmM]?)\s*$")
EXACT = re.compile(r"^\s*([\d\s \xa0]+)\s*$")


def lire_valeur(cellule: str):
    m = FOURCHETTE.match(cellule)
    if m:
        lo, hi = nombre(m.group(1)), nombre(m.group(2))
        return lo, hi, math.sqrt(max(lo, 1) * hi)
    m = EXACT.match(cellule)
    if m:
        v = nombre(m.group(1))
        return v, v, v
    return None


rows = []
# Les lignes « # … » sont des notes (pays, compte, date) et ne se lisent pas.
lignes = [l for l in txt.splitlines() if not l.lstrip().startswith("#")]
txt = "\n".join(lignes)
tabulaire = any(re.search(r"mot.?cl|keyword", l, re.I) and ("\t" in l or "," in l) for l in lignes[:20])
if tabulaire:
    delim = "\t" if any("\t" in l for l in lignes[:20]) else ","
    data = list(csv.reader(io.StringIO(txt), delimiter=delim))
    entete = next((i for i, r in enumerate(data) if any(re.search(r"mot.?cl|keyword", c, re.I) for c in r)), None)
    if entete is None:
        sys.exit("Export CSV sans colonne « Mot clé » / « Keyword ».")
    h = data[entete]
    ck = next(i for i, c in enumerate(h) if re.search(r"mot.?cl|keyword", c, re.I))
    cv = next((i for i, c in enumerate(h) if re.search(r"recherches mensuelles|monthly searches", c, re.I)), None)
    if cv is None:
        sys.exit("Export CSV sans colonne « Nombre moyen de recherches mensuelles ».")
    for r in data[entete + 1:]:
        if len(r) > max(ck, cv) and r[ck].strip():
            v = lire_valeur(r[cv])
            if v: rows.append((r[ck].strip(), *v))
else:
    prec = None
    for l in lignes:
        v = lire_valeur(l)
        if v and prec:
            rows.append((prec, *v)); prec = None
        elif l.strip() and not v and not re.match(r"^[\s+\-–—%0-9,.€]*$|^(Faible|Moyen|Moy|Élevé|Elevé|Low|Medium|High)\b|^(Idées de mots clés|Mots clés que vous avez fournis)", l.strip()):
            prec = l.strip()

if not rows:
    sys.exit("Aucune requête lue : le fichier n'a ni colonne de volume ni fourchettes.")

rows.sort(key=lambda r: -r[3])
tot_est = sum(r[3] for r in rows); tot_bas = sum(r[1] for r in rows)
for k, lo, hi, est in rows:
    print(f"  {est:>10,.0f}  ({lo:,.0f} – {hi:,.0f})  {k}".replace(",", " "))
print(f"\n{len(rows)} requête(s) · estimation {tot_est:,.0f} recherches/mois · bornes basses {tot_bas:,.0f} · seuil {SEUIL:,}".replace(",", " "))
if tot_est < SEUIL:
    print("NO-GO : sous le seuil de volume (RECETTE §2.0). On ne construit pas.")
    sys.exit(1)
print("GO volume : le seuil est atteint. Passer au SERP (§2.1), à l'actif (§2.2) et aux leads (§2.3).")
