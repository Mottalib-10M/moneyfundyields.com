#!/usr/bin/env python3
"""collect-portefeuille.py — l'état réel du portefeuille, pour la page /mapping.

Piloter une cinquantaine de sites de tête ne marche pas : on croit un site en
ligne alors qu'il ne se déploie plus depuis sept semaines, ou conforme alors
qu'aucun contrôle n'a tourné depuis un mois. Ce script constate, il ne suppose
rien, et écrit un JSON que la plateforme SEO affiche.

Pour chaque dépôt il établit :
  - en ligne ou non, vérifié par le DNS ET par le HTML servi (un dépôt peut
    porter un domaine qui appartient à quelqu'un d'autre : on compare alors le
    titre servi au titre construit localement) ;
  - la fraîcheur du déploiement : `last-modified` du HTML servi contre la date
    du dernier commit (c'est ainsi qu'on a trouvé deux sites figés) ;
  - les branchements de mesure : Search Console, Bing, Clarity ;
  - le passage en factory : date et résultat de chaque contrôle.

Les contrôles sont longs ; ils ne sont rejoués que si le dépôt a bougé depuis
la dernière collecte (--force pour tout refaire).

Usage : collect-portefeuille.py [--racine ~/Documents/GitHub] [--sortie <fichier.json>]
        [--sans-controles] [--force] [--site <nom>]
"""
import argparse, json, os, re, subprocess, sys, time
from datetime import datetime, timezone

RACINE_DEFAUT = os.path.expanduser('~/Documents/GitHub')
SCRIPTS = os.path.dirname(os.path.abspath(__file__))
# IP des hébergements du portefeuille : GitHub Pages et le serveur OVH.
IP_MAISON = re.compile(r'^(185\.199\.(108|109|110|111)\.153|51\.91\.236\.255|178\.32\.137\.139)$')


def sh(cmd, cwd=None, timeout=900):
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.returncode
    except Exception:
        return '', 1


def domaine_de(rep):
    for p in ('public/CNAME', 'CNAME'):
        f = os.path.join(rep, p)
        if os.path.isfile(f):
            d = open(f, encoding='utf8').read().strip().split('\n')[0].strip()
            if d:
                return d
    nom = os.path.basename(rep)
    return nom if '.' in nom and not nom.endswith(('-Mottalib55', '-Mottalib-10M')) else ''


def titre(html):
    m = re.search(r'<title>([^<]{0,120})', html or '')
    return m.group(1).strip() if m else ''


def dossier_build(rep):
    for d in ('dist', 'out', 'build'):
        p = os.path.join(rep, d)
        if os.path.isdir(p) and os.path.isfile(os.path.join(p, 'index.html')):
            return p
    return None


# Les briques ci-dessous attendent la sortie texte ; sh() rend (texte, code).
def sortie(cmd, timeout=40):
    return sh(cmd, timeout=timeout)[0]


def mesure(rep, dom, en_ligne_):
    """Search Console, Bing, Clarity : branchés ou non.

    Piège écarté ici : le gabarit écrit la balise SOUS CONDITION
    (`{GOOGLE_VERIFY_CODE && <meta …>}`) et la constante est souvent restée
    vide. Chercher la chaîne dans le code donne alors « branché » pour un site
    qui n'émet jamais la balise — 16 sites étaient dans ce cas.

    Donc : pour un site EN LIGNE, seul ce qui est réellement servi fait foi
    (DNS, HTML de la page d'accueil, fichiers de vérification). Pour un site
    pas encore publié, on retombe sur le code, mais en exigeant une valeur
    non vide.
    """
    txt = sortie(['dig', '+short', 'TXT', dom]) if dom else ''
    html = sortie(['curl', '-sL', '-m', '25', f'https://{dom}/']) if dom else ''

    if en_ligne_ and dom:
        sert = lambda f: sortie(['curl', '-sL', '-o', '/dev/null', '-w', '%{http_code}',
                                 '-m', '15', f'https://{dom}/{f}']).strip() == '200'
        return {
            'gsc': ('google-site-verification' in txt) or ('google-site-verification' in html),
            'bing': bool(re.search(r'\bMS=', txt)) or ('msvalidate.01' in html) or sert('BingSiteAuth.xml'),
            'clarity': 'clarity.ms' in html,
        }

    # pas en ligne : on lit le code, mais une constante vide ne compte pas
    src = ''
    for sd in ('src', 'app', 'public', 'components', 'index.html'):
        p_ = os.path.join(rep, sd)
        if os.path.isfile(p_):
            src += open(p_, encoding='utf8', errors='ignore').read()
        elif os.path.isdir(p_):
            for dp, dn, fn in os.walk(p_):
                dn[:] = [x for x in dn if x not in IGNORE]
                for f in fn:
                    if f.endswith(('.html', '.tsx', '.ts', '.astro', '.js', '.jsx', '.xml')):
                        try:
                            src += open(os.path.join(dp, f), encoding='utf8', errors='ignore').read(40000)
                        except Exception:
                            pass
    pub = os.path.join(rep, 'public')
    listing = os.listdir(pub) if os.path.isdir(pub) else []

    def code_rempli(nom):
        m = re.search(rf"{nom}\s*=\s*'([^']*)'", src)
        return bool(m and m.group(1).strip())

    def en_dur(motif):
        """La balise est-elle écrite avec une valeur, hors gabarit conditionnel ?"""
        return bool(re.search(rf'{motif}"?\s+content="[^"]{{8,}}"', src))

    return {
        'gsc': (code_rempli('GOOGLE_VERIFY_CODE') or en_dur('google-site-verification')
                or any(x.startswith('google') and x.endswith('.html') for x in listing)),
        'bing': (code_rempli('BING_VERIFY_CODE') or en_dur('msvalidate.01')
                 or os.path.isfile(os.path.join(pub, 'BingSiteAuth.xml'))),
        'clarity': 'clarity.ms' in src,
    }


# ── hébergeur : en-têtes d'abord (fiables), IP ensuite ────────────────────────
IP_HEBERGEUR = [
    (re.compile(r'^185\.199\.(108|109|110|111)\.153$'), 'GitHub Pages'),
    (re.compile(r'^(51\.91\.236\.255|178\.32\.137\.139)$'), 'OVH'),
    (re.compile(r'^216\.198\.79\.\d+$|^76\.76\.21\.\d+$'), 'Vercel'),
    (re.compile(r'^75\.2\.60\.5$|^99\.83\.190\.102$'), 'Netlify'),
]


def hebergeur(dom):
    tetes = sortie(['curl', '-sIL', '-m', '25', f'https://{dom}/'])
    b = tetes.lower()
    if 'x-vercel-id' in b or re.search(r'^server:\s*vercel', b, re.M):
        return 'Vercel'
    if 'x-nf-request-id' in b:
        return 'Netlify'
    if re.search(r'^server:\s*github\.com', b, re.M):
        return 'GitHub Pages'
    if 'x-amz-cf-id' in b or re.search(r'^server:\s*amazons3|cloudfront', b, re.M):
        return 'CloudFront'
    if 'cf-ray' in b:
        return 'Cloudflare'
    ip = (sortie(['dig', '+short', dom, 'A']).split('\n') or [''])[0].strip()
    for motif, nom in IP_HEBERGEUR:
        if motif.match(ip):
            return nom
    m = re.search(r'^server:\s*(.+)$', b, re.M)
    return (m.group(1).strip().split('/')[0].title() if m else 'inconnu')


# ── appartenance : des chaînes rares du HTML servi sont-elles dans nos sources ?
EXT = ('.astro', '.ts', '.tsx', '.js', '.jsx', '.json', '.md', '.mdx', '.html', '.yml')
IGNORE = {'node_modules', '.git', '.next', 'dist', 'out', 'build', '.astro', '.vercel'}


def sources(rep, plafond=6000):
    txt = []
    for dp, dn, fn in os.walk(rep):
        dn[:] = [d for d in dn if d not in IGNORE]
        for f in fn:
            if f.endswith(EXT):
                try:
                    txt.append(open(os.path.join(dp, f), encoding='utf8', errors='ignore').read())
                except Exception:
                    pass
                if len(txt) > plafond:
                    return '\n'.join(txt)
    return '\n'.join(txt)


def empreintes(html):
    """Chaînes distinctives du HTML servi : titre, description, et texte visible long."""
    out = []
    m = re.search(r'<title[^>]*>([^<]{10,120})', html)
    if m:
        out.append(m.group(1).strip())
    m = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]{30,200})"', html)
    if m:
        out.append(m.group(1).strip())
    visible = re.sub(r'<script[\s\S]*?</script>|<style[\s\S]*?</style>', ' ', html)
    visible = re.sub(r'<[^>]+>', '\n', visible)
    for p in re.findall(r'[A-ZÉÀÂÎÔÛÄÖÜ][^\n]{45,130}', visible):
        p = p.strip()
        if 'http' not in p and '{' not in p and p.count(' ') > 6:
            out.append(p)
        if len(out) >= 9:
            break
    return out


def contient(texte, phrases):
    """Combien de ces phrases se retrouvent dans ce texte ? On tolère une fin
    tronquée (année, suffixe de marque) en retombant sur un préfixe long."""
    n = 0
    for e in phrases:
        for frag in (e, e[:60], e[:45]):
            # 12 caractères : « Simulateur ARE » est court mais déjà distinctif
            if len(frag) >= 12 and frag in texte:
                n += 1
                break
    return n


def appartient(rep, html):
    """(verdict, détail). On cherche dans LES DEUX SENS, car les deux peuvent
    échouer séparément : le site en ligne peut être plus récent que la copie
    locale (adequattaxi.fr), ou la copie locale n'avoir aucun build (taxineo.fr).
    Deux correspondances suffisent : un titre seul peut coïncider entre deux
    sites du même sujet, deux phrases longues non."""
    src = sources(rep)
    b = dossier_build(rep)
    if b:                                   # le HTML construit, s'il existe
        try:
            src += '\n' + open(os.path.join(b, 'index.html'), encoding='utf8', errors='ignore').read()
        except Exception:
            pass
    emp_live = empreintes(html)
    aller = contient(src, emp_live) if src else 0
    # sens inverse : nos propres phrases distinctives apparaissent-elles en ligne ?
    emp_nous = []
    for m in re.finditer(r'<title[^>]*>([^<]{10,120})', src or ''):
        emp_nous.append(m.group(1).strip())
    for m in re.finditer(r'"([A-ZÉÀÂÎÔÛ][^"\n]{45,130})"', src or ''):
        emp_nous.append(m.group(1).strip())
        if len(emp_nous) >= 40:
            break
    retour = contient(html, emp_nous[:40])
    return (aller >= 2 or retour >= 2), f'{aller} aller / {retour} retour'


def en_ligne(dom, rep, force=None):
    """(statut, hébergeur, titre, preuve).

    « Répond » ne veut pas dire « à nous » : plusieurs projets portent un nom de
    domaine provisoire déjà pris par un concurrent du même sujet. On tranche en
    comparant le HTML servi à nos sources, dans les deux sens. Quand une seule
    correspondance ressort, on ne tranche pas : on marque « à vérifier » et on
    attend une décision humaine (champ `appartenance` de pilotage.json)."""
    if not dom:
        return 'sans-domaine', '', '', ''
    if not sortie(['dig', '+short', dom, 'A']).strip():
        return 'a-publier', '', '', 'aucun DNS'
    html = sortie(['curl', '-sL', '-m', '25', f'https://{dom}/'])
    if not html:
        return 'injoignable', hebergeur(dom), '', ''
    t = titre(html)
    heb = hebergeur(dom)
    # Preuve d'infrastructure : GitHub Pages ne sert un domaine personnalisé que
    # pour le dépôt qui le revendique, et notre serveur OVH n'héberge que nous.
    # Aucune comparaison de texte n'est alors nécessaire.
    chez_nous = heb == 'OVH' or (heb == 'GitHub Pages'
                                 and 'mottalib' in sortie(['dig', '+short', f'www.{dom}', 'CNAME']).lower())
    if chez_nous and force != 'tiers':
        return 'en-ligne', heb, t, f'servi par notre {heb}'
    if force == 'nous':
        return 'en-ligne', heb, t, 'confirmé à la main'
    if force == 'tiers':
        return 'domaine-pris', heb, t, 'confirmé à la main'
    ok, detail = appartient(rep, html)
    if ok:
        return 'en-ligne', heb, t, detail
    if detail.startswith('0 aller / 0'):
        return 'domaine-pris', heb, t, detail
    return 'a-verifier', heb, t, detail


def fraicheur(dom, rep):
    """Retard, en jours, du contenu servi sur le dernier commit."""
    out, _ = sh(['curl', '-sI', '-m', '25', f'https://{dom}/'])
    m = re.search(r'(?im)^last-modified:\s*(.+)$', out)
    if not m:
        return None
    try:
        t_servi = datetime.strptime(m.group(1).strip(), '%a, %d %b %Y %H:%M:%S %Z').replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    ts, _ = sh(['git', 'log', '-1', '--format=%ct'], cwd=rep)
    if not ts.isdigit():
        return None
    return max(0, int((int(ts) - t_servi.timestamp()) // 86400))


def nombre(motif, texte, defaut=None):
    m = re.search(motif, texte)
    return int(m.group(1)) if m else defaut


def controles(rep):
    """Passe le site dans la factory. Renvoie le résultat de chaque contrôle."""
    b = dossier_build(rep)
    if not b:
        return {'etat': 'pas-de-build'}
    rel = os.path.basename(b)
    res = {'etat': 'ok', 'date': datetime.now().strftime('%Y-%m-%d')}

    out, _ = sh(['python3', os.path.join(SCRIPTS, 'check-trame.py'), '.'], cwd=rep)
    res['pages'] = nombre(r'(\d+) pages,', out)
    res['trame'] = nombre(r'(\d+) à corriger', out)

    out, _ = sh(['python3', os.path.join(SCRIPTS, 'check-seo.py'), '.'], cwd=rep)
    res['seo'] = nombre(r'(\d+) à corriger', out)

    out, _ = sh(['python3', os.path.join(SCRIPTS, 'check-unique.py'), '.'], cwd=rep)
    res['doublons'] = nombre(r'(\d+) paire', out, 0)

    out, _ = sh(['node', os.path.join(SCRIPTS, 'typo-nbsp.mjs'), rel, '--check'], cwd=rep)
    res['typo'] = ((nombre(r'(\d+) espace', out, 0) or 0)
                   + (nombre(r'(\d+) décimale', out, 0) or 0)
                   + (nombre(r'(\d+) mot', out, 0) or 0))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--racine', default=RACINE_DEFAUT)
    ap.add_argument('--sortie', default=os.path.join(
        RACINE_DEFAUT, 'a-publier/Mottalib-10M/seo-platform/src/data/portefeuille.json'))
    ap.add_argument('--sans-controles', action='store_true')
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--site')
    a = ap.parse_args()

    # décisions humaines : appartenance confirmée à la main quand l'automatique hésite
    forcages = {}
    pil = os.path.join(os.path.dirname(a.sortie), 'pilotage.json')
    if os.path.isfile(pil):
        try:
            for k, v in json.load(open(pil, encoding='utf8')).items():
                if isinstance(v, dict) and v.get('appartenance'):
                    forcages[k] = v['appartenance']
        except Exception:
            pass

    ancien = {}
    if os.path.isfile(a.sortie):
        try:
            ancien = {s['repo']: s for s in json.load(open(a.sortie, encoding='utf8'))['sites']}
        except Exception:
            pass

    depots = []
    for base in ('en-ligne', 'a-publier/Mottalib-10M', 'a-publier/simulateurs-2026',
                 'a-publier/domaine-a-choisir'):
        d = os.path.join(a.racine, base)
        if not os.path.isdir(d):
            continue
        for n in sorted(os.listdir(d)):
            rep = os.path.join(d, n)
            if os.path.isdir(os.path.join(rep, '.git')):
                depots.append((base, n, rep))

    sites = []
    for i, (base, nom, rep) in enumerate(depots, 1):
        if a.site and a.site != nom:
            if nom in ancien:
                sites.append(ancien[nom])
            continue
        print(f'[{i}/{len(depots)}] {nom}', file=sys.stderr, flush=True)
        dom = domaine_de(rep)
        tete, _ = sh(['git', 'rev-parse', 'HEAD'], cwd=rep)
        statut, heb, t, preuve = en_ligne(dom, rep, forcages.get(nom) or forcages.get(dom))
        s = {
            'repo': nom, 'domaine': dom, 'dossier': base, 'statut': statut,
            'hebergeur': heb, 'preuve': preuve, 'titre': t, 'commit': tete[:7],
            'dernierCommit': sh(['git', 'log', '-1', '--format=%cs'], cwd=rep)[0],
            'mesure': mesure(rep, dom, statut == 'en-ligne'),
            'retardJours': fraicheur(dom, rep) if statut == 'en-ligne' else None,
        }
        prec = ancien.get(nom)
        if getattr(a, 'sans_controles'):
            s['factory'] = (prec or {}).get('factory', {'etat': 'non-controle'})
        elif prec and not a.force and prec.get('commit') == tete[:7] and prec.get('factory', {}).get('etat') == 'ok':
            s['factory'] = prec['factory']          # rien n'a bougé : on garde
        else:
            s['factory'] = controles(rep)
        sites.append(s)

    os.makedirs(os.path.dirname(a.sortie), exist_ok=True)
    json.dump({'genereLe': datetime.now().strftime('%Y-%m-%d %H:%M'), 'sites': sites},
              open(a.sortie, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    en = sum(1 for s in sites if s['statut'] == 'en-ligne')
    print(f"\n{len(sites)} dépôts — {en} en ligne — écrit dans {a.sortie}")


if __name__ == '__main__':
    main()
