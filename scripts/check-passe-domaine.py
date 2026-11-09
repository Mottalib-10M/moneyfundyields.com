#!/usr/bin/env python3
"""Un domaine qui a déjà vécu ne se prend jamais — RECETTE-SITE.md §16, règle absolue du 2026-10-16.

Usage :
  check-passe-domaine.py <domaine> [<domaine> …]            avant l'achat : toute capture refuse
  check-passe-domaine.py --achete <domaine> [<domaine> …]   domaine déjà à nous : seules comptent
                                                            les captures antérieures à sa création

Interroge l'index de la Wayback Machine (API CDX, sous-domaines compris). Un domaine
qui a hébergé quoi que ce soit avant nous — vrai site, parking, page « à vendre »,
spam — est refusé : sur les 22 sites en ligne avant juin 2026, les 7 domaines déjà
vécus ont fait 1 clic Google médian sur 28 jours, contre 294 pour les domaines neufs
(reports/analyse-cohorte-2026-10-16), et Google sanctionne l'abus de domaine expiré
depuis mars 2024.

Sortie : 0 si le passé est vierge, 1 si le domaine a déjà vécu, 2 si la vérification
n'a pas pu se faire. Un 2 vaut refus : un domaine non vérifié ne s'achète pas.
"""
import json, re, subprocess, sys, time, urllib.request, urllib.error

CDX = 'https://web.archive.org/cdx/search/cdx?url={d}&matchType=domain&output=json&fl=timestamp,original,statuscode&collapse=timestamp:6&limit=200{to}'
CREATION = re.compile(r'^\s*(?:Creation Date|created|Created On|Registered on|Registration Time|registered|Domain Name Commencement Date|Domain record activated)\s*:\s*(\d{4})-?(\d{2})-?(\d{2})', re.I | re.M)


def captures(dom, avant=None):
    to = f'&to={avant}' if avant else ''
    for essai in range(3):
        try:
            with urllib.request.urlopen(CDX.format(d=dom, to=to), timeout=60) as r:
                rows = json.loads(r.read().decode() or '[]')
            return rows[1:] if rows else []
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            err = e
            time.sleep(5 * (essai + 1))
    raise RuntimeError(f'Wayback injoignable ({err})')


# Serveurs des registres, comme check-domaines.sh. Le `whois` système sans -h rend d'abord le bloc
# IANA de l'extension, dont la date « created » est celle du .com (1985) : lue telle quelle, elle
# laissait passer bmi-imc.com (test du 2026-10-16, cas connu mauvais).
REGISTRES = {'com': 'whois.verisign-grs.com', 'net': 'whois.verisign-grs.com', 'fr': 'whois.nic.fr',
             'de': 'whois.denic.de', 'ch': 'whois.nic.ch', 'nl': 'whois.domain-registry.nl',
             'it': 'whois.nic.it', 'es': 'whois.nic.es', 'pt': 'whois.dns.pt', 'be': 'whois.dns.be',
             'dk': 'whois.punktum.dk', 'se': 'whois.iis.se', 'pl': 'whois.dns.pl', 'at': 'whois.nic.at',
             'fi': 'whois.fi', 'uk': 'whois.nic.uk', 'ma': 'whois.registre.ma', 'mx': 'whois.mx',
             'nz': 'whois.irs.net.nz', 'sg': 'whois.sgnic.sg', 'no': 'whois.norid.no', 'io': 'whois.nic.io',
             'ae': 'whois.aeda.net.ae', 'eu': 'whois.eu', 'lu': 'whois.dns.lu', 'gr': 'whois.ics.forth.gr'}


def creation(dom):
    """Date de création au registre, AAAAMMJJ, ou None quand le registre ne la publie pas (.de, .nl…)."""
    serveur = REGISTRES.get(dom.rsplit('.', 1)[-1])
    if not serveur:
        return None
    out = subprocess.run(['whois', '-h', serveur, dom], capture_output=True, text=True, timeout=60).stdout
    m = CREATION.search(out)
    if not m:
        return None
    # La borne `to` de l'API est incluse : une capture du jour même de notre enregistrement (parking
    # OVH) faisait refuser aliquoteimu.it, créé et capturé le 2026-10-04. On s'arrête à la veille.
    import datetime
    veille = datetime.date(*map(int, m.groups())) - datetime.timedelta(days=1)
    return veille.strftime('%Y%m%d')


def main(args):
    achete = '--achete' in args
    doms = [a.lower().strip() for a in args if not a.startswith('--')]
    if not doms:
        sys.exit(__doc__)
    code = 0
    for dom in doms:
        try:
            avant = None
            if achete:
                avant = creation(dom)
                # Sans date de création publiée, toute capture compte : on refuse plutôt que de deviner.
            rows = captures(dom, avant)
        except Exception as e:
            print(f'?        {dom}  vérification impossible : {e} — REFUSÉ tant qu\'elle n\'a pas abouti')
            code = max(code, 2)
            continue
        if rows:
            prem = rows[0][0]
            mois = len({r[0][:6] for r in rows})
            ex = ', '.join(sorted({re.sub(r'^https?://', '', r[1]).split('?')[0][:50] for r in rows})[:3])
            borne = f' avant sa création (jusqu\'au {avant[:4]}-{avant[4:6]}-{avant[6:]} inclus)' if avant else ''
            print(f'REFUSÉ   {dom}  déjà vécu{borne} : première capture {prem[:4]}-{prem[4:6]}-{prem[6:8]}, '
                  f'{mois} mois archivés{"+" if len(rows) >= 200 else ""} ({ex})')
            print(f'         voir https://web.archive.org/web/*/{dom}*')
            code = max(code, 1)
        else:
            borne = f' jusqu\'au {avant[:4]}-{avant[4:6]}-{avant[6:]} inclus, veille de la création' if avant else ''
            print(f'vierge   {dom}  aucune capture Wayback{borne}')
        time.sleep(1)
    sys.exit(code)


if __name__ == '__main__':
    main(sys.argv[1:])
