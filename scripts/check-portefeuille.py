"""Contrôle entre sites du portefeuille — RECETTE-SITE.md §16.

Usage : python3 check-portefeuille.py <dossier-site> [--verbose]

Deux règles de l'utilisateur, toutes deux bloquantes avant publication :
  1. Pas de copie entre sites : aucun paragraphe repris ou simplement reformulé
     d'un autre site du portefeuille. Un paragraphe (p, li, td, dd de 12 mots et
     plus, hors nav/header/footer) est signalé quand 40 % de ses suites de 8 mots
     existent déjà sur un autre site en ligne. C'est la règle du contrôle
     quotidien de seo-platform (onglet Environnement Google).
  2. Pas de réseau : aucun lien vers un autre site du portefeuille.

Les blocs auteur, éditeur, sources, méthode et mentions se rédigent pour chaque
site : les reprendre d'un _cfg voisin est précisément ce que ce contrôle bloque.
Les pages légales (CGU, confidentialité, mentions) sont exclues.
Les sites comparés sont les dossiers de GitHub/en-ligne/ (sortie servie de chacun).
"""
import os, re, sys
from pathlib import Path

SORTIES = ('dist', 'out', 'build', 'docs', 'output', '_site', 'www')
SEUIL = 0.4
# Pages légales : adresse de l'hébergeur, clauses de CGU et mentions sont identiques
# par nature et ne comptent pas pour Google ; les inclure noierait les vraies copies.
# Turc et indonésien (tr-bayram, 2026-10-28) : le bloc hébergeur de /tr/yasal-bilgiler/ était compté comme copie.
LEGAL = re.compile(r'/(terms|terms-of-service|terms-of-use|privacy|privacy-policy|cookies?|legal|legal-notice|disclaimer|mentions-legales|confidentialite|cgu|impressum|datenschutz|agb|aviso-legal|privacidad|termini|note-legali|voorwaarden|vilkar|villkor|personvern|integritet|termos|privacidade|kayttoehdot|tietosuoja|evasteet|yasal-bilgiler|gizlilik|cerezler|kullanim-kosullari|privasi|kebijakan-privasi|ketentuan|syarat-ketentuan)(/|\.html|$)', re.I)


def sortie_de(site: Path):
    cands = [site / d for d in SORTIES if (site / d / 'index.html').is_file()]
    if not cands:
        return site if (site / 'index.html').is_file() else None
    return max(cands, key=lambda d: sum(1 for _ in d.rglob('*.html')))


def paragraphes(texte):
    corps = re.sub(r'<(script|style|nav|footer|header|noscript)\b[\s\S]*?</\1>', ' ', texte, flags=re.I)
    for m in re.finditer(r'<(p|li|td|dd)\b[^>]*>([\s\S]*?)</\1>', corps, flags=re.I):
        t = re.sub(r'&[a-z#0-9]+;', ' ', re.sub(r'<[^>]+>', ' ', m.group(2)), flags=re.I)
        t = re.sub(r'\s+', ' ', t).strip()
        if len(t.split(' ')) >= 12:
            yield t


def shingles(t, n=8):
    mots = re.sub(r'[^\w ]', ' ', t.lower()).split()
    return {' '.join(mots[i:i + n]) for i in range(len(mots) - n + 1)}


def pages(sortie: Path):
    return [f for f in sortie.rglob('*.html')
            if not any(a in f.as_posix() for a in ('/_archives/', '/archive/', '/old/', '/backup/'))
            and not LEGAL.search('/' + f.relative_to(sortie).as_posix())]


def _test():
    """Non-régression (RECETTE §26, 2026-10-15) : `<path>`, `<pre>`, `<link>` ne sont pas des paragraphes."""
    dix = ' '.join(['mot'] * 14)
    doc = (f'<svg><path d="M0 0"/></svg><select>{dix} Ain Aisne Allier</select><p>vrai paragraphe {dix}</p>'
           f'<pre>{dix}</pre><link rel="x"><li>élément de liste {dix}</li>')
    trouves = list(paragraphes(doc))
    ok = trouves == [f'vrai paragraphe {dix}', f'élément de liste {dix}']
    print('check-portefeuille --test :', 'OK' if ok else f'ÉCHEC {trouves}')
    sys.exit(0 if ok else 1)


def main():
    if sys.argv[1:] == ['--test']:
        _test()
    site = Path(sys.argv[1]).resolve()
    verbose = '--verbose' in sys.argv
    sortie = sortie_de(site)
    if not sortie:
        print(f'check-portefeuille : pas de build dans {site} — lancer le build avant.')
        sys.exit(1)
    en_ligne = next((p / 'en-ligne' for p in site.parents if (p / 'en-ligne').is_dir()), None)
    if not en_ligne:
        print('check-portefeuille : dossier en-ligne/ introuvable, contrôle impossible.')
        sys.exit(1)
    soi = site.name.lower().removeprefix('www.')
    autres = [d for d in sorted(en_ligne.iterdir()) if d.is_dir() and '.' in d.name and d.name.lower() != soi]
    domaines = {d.name.lower().removeprefix('www.') for d in autres}

    # Index des suites de 8 mots des autres sites
    index = {}
    for d in autres:
        s = sortie_de(d)
        if not s:
            continue
        for f in pages(s):
            for t in paragraphes(f.read_text(errors='ignore')):
                for sh in shingles(t):
                    index.setdefault(sh, d.name)

    copies, liens = [], {}
    vus = set()
    for f in pages(sortie):
        texte = f.read_text(errors='ignore')
        rel = f.relative_to(sortie).as_posix()
        for t in paragraphes(texte):
            if t in vus:
                continue
            vus.add(t)
            s = shingles(t)
            if len(s) < 3:
                continue
            par_site = {}
            for sh in s:
                if sh in index:
                    par_site[index[sh]] = par_site.get(index[sh], 0) + 1
            if par_site:
                autre, n = max(par_site.items(), key=lambda x: x[1])
                if n / len(s) >= SEUIL:
                    copies.append((rel, autre, round(100 * n / len(s)), t))
        for m in re.finditer(r'href=["\']https?://(?:www\.)?([a-z0-9.-]+)', texte, flags=re.I):
            h = m.group(1).lower()
            if h in domaines:
                liens.setdefault(h, set()).add(rel)

    for rel, autre, pct, t in copies[: (None if verbose else 15)]:
        print(f'COPIE  {rel} — {pct} % déjà sur {autre} : {t[:120]}')
    for h, ps in liens.items():
        print(f'RESEAU lien vers {h} sur {len(ps)} page(s), ex. {sorted(ps)[0]}')
    print(f'check-portefeuille : {len(copies)} paragraphe(s) copiés, {len(liens)} site(s) du portefeuille liés, {len(autres)} sites comparés.')
    sys.exit(1 if copies or liens else 0)


if __name__ == '__main__':
    main()
