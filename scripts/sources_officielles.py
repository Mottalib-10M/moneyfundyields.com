"""Reconnaissance des sources officielles — partagée par check-seo.py et check-regles.py.

RECETTE §7 et §26 (2026-10-16). Avant, chaque contrôleur portait sa propre expression
régulière, et toutes deux ignoraient des organismes publics légitimes (cre.fr, rte-france.com,
bundesnetzagentur.de, ree.es, cnmc.es, energiavirasto.fi, revenuquebec.ca…). Trois sources :
  1. les libellés publics du nom d'hôte : gov, gouv, gob, govt, gv (et go.xx), .int, .mil,
     et les suffixes gc.ca, admin.ch, bund.de, europa.eu, public.lu, overheid.nl ;
  2. la liste partagée sources-officielles.txt (à côté de ce fichier) ;
  3. scripts/sources-primaires.txt du site (une ligne de commentaire avant chaque domaine).
"""
import os
import re

ICI = os.path.dirname(os.path.abspath(__file__))
LIBELLES_PUBLICS = {'gov', 'gouv', 'gob', 'govt', 'gv'}
SUFFIXES_PUBLICS = ('gc.ca', 'admin.ch', 'bund.de', 'europa.eu', 'public.lu', 'overheid.nl')
RE_URL = re.compile(r'https?://[a-z0-9.-]+\.[a-z]{2,}(?::\d+)?(?:/[^\s"\'<>()\\]*)?', re.I)


def _normaliser(ligne):
    ligne = re.sub(r'^https?://', '', ligne.strip().lower())
    return re.sub(r'^www\.', '', ligne).rstrip('/')


def lire_liste(chemin, strict=False):
    """Domaines d'un fichier. strict : chaque domaine doit suivre une ligne de commentaire."""
    if not os.path.isfile(chemin):
        return []
    motifs, justifie = [], False
    for ligne in open(chemin, encoding='utf-8'):
        ligne = ligne.strip()
        if not ligne:
            justifie = False
            continue
        if ligne.startswith('#'):
            justifie = True
            continue
        if strict and not justifie:
            raise SystemExit(
                f"{chemin} : « {ligne} » n'est précédé d'aucun commentaire. "
                "Chaque domaine déclaré doit dire pourquoi il fait autorité sur ce sujet.")
        motifs.append(_normaliser(ligne))
        if strict:
            justifie = False
    return motifs


PARTAGEE = lire_liste(os.path.join(ICI, 'sources-officielles.txt'))


def primaires_du_site(site, strict=True):
    return lire_liste(os.path.join(site, 'scripts', 'sources-primaires.txt'), strict=strict)


def _hote_chemin(url):
    m = re.match(r'https?://([^/?#:]+)(?::\d+)?([^?#]*)', url.strip(), re.I)
    if not m:
        return '', ''
    return re.sub(r'^www\.', '', m.group(1).lower()).rstrip('.'), m.group(2) or '/'


def _vise(hote, chemin, motif):
    dom, _, voie = motif.partition('/')
    if not (hote == dom or hote.endswith('.' + dom)):
        return False
    return not voie or chemin.lstrip('/').lower().startswith(voie)


def public_par_nom(hote):
    """Nom d'hôte d'une administration, d'après ses libellés (nhtsa.gov, ato.gov.au…)."""
    lab = hote.split('.')
    if len(lab) < 2:
        return False
    if lab[-1] in ('gov', 'mil', 'int'):
        return True
    if any(l in LIBELLES_PUBLICS for l in lab[-3:-1]):
        return True
    if len(lab) >= 3 and lab[-2] == 'go' and len(lab[-1]) == 2:   # go.jp, go.kr, go.th
        return True
    if len(lab) >= 4 and lab[-1] == 'us' and lab[-3] == 'state':   # leg.state.nv.us
        return True
    return any(hote == s or hote.endswith('.' + s) for s in SUFFIXES_PUBLICS)


def est_officielle(url, extra=()):
    # Copie d'archive d'une page officielle (web.archive.org/web/<date>/<url>) : on juge l'URL archivée.
    m = re.match(r'https?://web\.archive\.org/web/[^/]+/(https?://.+)$', url.strip(), re.I)
    if m:
        return est_officielle(m.group(1), extra)
    hote, chemin = _hote_chemin(url)
    if not hote:
        return False
    if public_par_nom(hote):
        return True
    return any(_vise(hote, chemin, m) for m in PARTAGEE) or any(_vise(hote, chemin, m) for m in extra)


def urls_officielles(doc, extra=()):
    """URL distinctes d'un document HTML qui pointent vers une source officielle."""
    return {u.rstrip('.,;') for u in RE_URL.findall(doc) if est_officielle(u, extra)}


if __name__ == '__main__':   # auto-test : python3 sources_officielles.py
    bons = ['https://www.cre.fr/x', 'https://services-rte.com/fr', 'https://www.rte-france.com/',
            'https://www.enedis.fr/', 'https://www.bundesnetzagentur.de/', 'https://www.bundesgesundheitsministerium.de/',
            'https://www.gkv-spitzenverband.de/', 'https://www.bundesanzeiger.de/', 'https://www.gesetze-im-internet.de/sgb_5/',
            'https://www.destatis.de/', 'https://www.bmas.de/', 'https://www.recht.bund.de/bgbl/', 'https://www.ree.es/',
            'https://api.esios.ree.es/', 'https://www.cnmc.es/', 'https://www.boe.es/', 'https://www.dgt.es/',
            'https://sede.dgt.gob.es/', 'https://energiavirasto.fi/', 'https://www.vero.fi/', 'https://stat.fi/',
            'https://www.fingrid.fi/', 'https://www.nhtsa.gov/', 'https://www.epa.gov/', 'https://www.fueleconomy.gov/',
            'https://www.cms.gov/', 'https://www.medicaid.gov/', 'https://travel.state.gov/', 'https://www.ecfr.gov/',
            'https://gov.uk/x', 'https://www.gov.uk/', 'https://www.legislation.gov.uk/', 'https://www.canada.ca/',
            'https://www.revenuquebec.ca/', 'https://www.ato.gov.au/', 'https://abr.gov.au/', 'https://www.bmf.gv.at/',
            'https://www.estv.admin.ch/', 'https://www.retraitequebec.gouv.qc.ca/', 'https://www.nenkin.go.jp/',
            'https://ec.europa.eu/eurostat', 'https://www.who.int/', 'https://www.ird.govt.nz/', 'https://www.vd.ch/', 'https://www.leg.state.nv.us/',
            'https://web.archive.org/web/2024/https://www.gov.uk/x']
    mauvais = ['https://www.cre.frog.com/', 'https://notcre.fr/', 'https://govtech.com/', 'https://www.gov-news.com/',
               'https://example.com/gov.uk', 'https://monsite.fr/?u=https:', 'https://www.calculeo.fr/', 'https://web.archive.org/web/2024/https://exemple.com/', 'https://www.du.ae/',
               'https://costoflivingcanada.ca/']
    rate = [u for u in bons if not est_officielle(u)] + [u for u in mauvais if est_officielle(u)]
    assert est_officielle('https://openai.com/careers/x', ['openai.com/careers'])
    assert not est_officielle('https://openai.com/blog', ['openai.com/careers'])
    print('sources_officielles :', 'OK' if not rate else f'ÉCHEC {rate}', f'({len(bons)} bons, {len(mauvais)} mauvais)')
    raise SystemExit(1 if rate else 0)
