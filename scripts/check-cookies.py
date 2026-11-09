"""Contrôle « cookies » — RECETTE-SITE.md §15.6 (décisions de l'éditeur du 2026-10-06 et du 2026-10-17).

Usage : python3 scripts/check-cookies.py <dossier-site> [--verbose]
        python3 scripts/check-cookies.py --test     # cas bons et mauvais (tests/controles.sh)

Règle : aucun bandeau cookies ; Microsoft Clarity gardé en mode SANS COOKIE ; Google
Analytics 4 admis AVEC cookies et SANS bandeau (décision du 2026-10-17), à des conditions
précises ; aucun autre traceur, aucune publicité.

Le contrôle lit la sortie servie (dist/, out/…), pas le code : c'est ce que reçoit
le visiteur qui compte. Le G-ID attendu est lu dans src/data/site-config.ts (GA4_ID).
  1. Aucun bandeau : ni #consent-banner, ni [data-consent-manage], ni composant de
     bandeau connu (cookie-banner, cookieconsent, Cookiebot, OneTrust, tarteaucitron…).
  2. Aucun traceur autre que Clarity et GA4 : ni AdSense, ni publicité (doubleclick),
     ni pixel Meta, Hotjar, Matomo, Plausible… (pages et scripts servis).
  3. GA4, s'il est servi, n'est admis que si TOUT tient :
     a. un seul G-ID dans tout le site, celui de GA4_ID dans site-config.ts (gtag sans
        G-ID, deux G-ID, ou GA4 servi alors que GA4_ID est vide : bloquant) ;
     b. consentement par défaut gtag('consent','default',{…}) placé avant gtag/js :
        analytics_storage 'granted', ad_storage / ad_user_data / ad_personalization
        'denied', sans lecture de localStorage (ni consent-choice) ;
     c. gtag('config', '<G-ID>', {anonymize_ip: true, …}) ;
     d. pages légales de chaque langue : la page cookies et la page confidentialité
        nomment Google Analytics et le cookie _ga ; la confidentialité nomme Google
        Ireland et le module de désactivation (tools.google.com/dlpage/gaoptout) ;
        aucune phrase n'y dit qu'aucun cookie n'est déposé (hors phrases sur Clarity ou
        le calculateur intégré) ni qu'aucun outil de mesure d'audience n'est utilisé.
  4. Clarity, s'il est chargé : le signal consentv2 { ad_Storage:'denied',
     analytics_Storage:'denied' } est mis en file AVANT l'adresse clarity.ms/tag/,
     dans la page ; <body data-clarity-mask="true"> masque tout le contenu par le code ;
     l'ancien chargement conditionnel (__clarityLoad, consent-choice) a disparu.
  5. Pages légales présentes : une page de confidentialité et une page de mentions
     légales / CGU par langue servie ; sans GA4, chaque page cookies ou confidentialité
     dit qu'aucun cookie n'est déposé ; elle nomme Clarity si Clarity est chargé ; aucune
     phrase des pages légales ne décrit un bandeau, un choix de consentement ou AdSense,
     ni (sans GA4) GA4 / Google Analytics (une phrase négative, « il n'y a pas de
     bandeau », est admise).
Sortie : 0 si tout est conforme, 1 sinon.
"""
import re
import sys
from pathlib import Path

SORTIES = ('dist', 'out', 'build', 'docs', 'output', '_site', 'www')

BANDEAU = re.compile(
    r'id=["\']consent-banner|data-consent-manage|id=["\']cookie-?banner|class=["\'][^"\']*\bcookie-?banner'
    r'|cookieconsent|cookiebot|onetrust|tarteaucitron|klaro\.js|iubenda|didomi|axeptio|termly',
    re.I)
# Traceurs de GA4 : admis seulement aux conditions du point 3.
GA4_TRACE = re.compile(r'googletagmanager\.com|google-analytics\.com|\bgtag\s*\(|(?-i:\bG-[A-Z0-9]{10}\b)', re.I)
TRACEURS = re.compile(
    r'pagead2\.googlesyndication|adsbygoogle|doubleclick\.net|connect\.facebook\.net|fbq\s*\('
    r'|static\.hotjar\.com|matomo\.(js|php)|plausible\.io/js|cdn\.segment\.com|mixpanel\.com'
    r'|cloudflareinsights\.com|umami\.is|simpleanalytics',
    re.I)
CLARITY_TAG = re.compile(r'clarity\.ms/tag/')
CONSENTV2_DENIED = re.compile(
    r"clarity\(\s*['\"]consentv2['\"]\s*,\s*\{(?=[^}]*ad_Storage\s*:\s*['\"]denied['\"])"
    r"(?=[^}]*analytics_Storage\s*:\s*['\"]denied['\"])[^}]*\}")
ANCIEN_CLARITY = re.compile(r'__clarityLoad|consent-choice')

# Pages légales, reconnues à leur adresse (toutes langues du portefeuille).
P_PRIVACY = re.compile(r'(privacy|privacidad|privacidade|confidentialit|datenschutz|privacybeleid|riservatezza'
                       r'|prywatnos|integritet|personvern|tietosuoja|aporrito|aporrhto|gdpr|privatliv'
                       # Turc et indonésien (tr-bayram, id-kalender, 2026-10-28)
                       r'|gizlilik|kisisel-veri|kvkk|privasi)', re.I)
P_COOKIES = re.compile(r'(cookie|temoins|evaste|kakor|informasjonskapsl|ciasteczk|cerez)', re.I)
P_LEGAL = re.compile(r'(mentions-legales|legal|impressum|aviso-legal|note-legali|terms|cgu|conditions'
                     r'|voorwaarden|colofon|vilkar|vilkaar|villkor|kayttoehdot|agb|termini|termos|regulamin'
                     r'|nota-prawna|condiciones|disclaimer|oroi|nomik|colophon|imprint'
                     r'|yasal|kullanim-kosullari|ketentuan|syarat)', re.I)

NEGATION = re.compile(
    r"\b(no|not|none|never|without|nor|aucun|aucune|pas|ni|sans|jamais|kein|keine|keinen|keinem|nicht|ohne"
    r"|geen|niet|zonder|nessun|nessuna|non|senza|ningún|ninguna|ninguno|sin|nunca|nenhum|nenhuma|não|sem"
    r"|inga|ingen|inte|utan|ikke|uten|ei|eikä|ilman|nie|żadnych|żadnego|żadne|bez|δεν|κανένα|καμία|χωρίς"
    r"|μη|لا|ليس|بدون"
    # Indonésien et turc (id-kalender, tr-bayram, 2026-10-28) : « tidak menaruh cookie », « tanpa cookie »,
    # « hiçbir çerez », « çerez yok ». Le turc nie surtout par suffixe verbal : « kullanmaz »,
    # « kullanmıyor », « bırakmamaktadır » (namaz excepté).
    # (« tak » est exclu : il veut dire « oui » en polonais ; suffixes en minuscules seulement,
    # pour ne pas lire « Gómez » comme une négation.)
    r"|tidak|tanpa|bukan|belum|hiçbir|hiç|yok|değil|olmadan"
    r"|(?-i:[a-zçğıöşü]\w*(?<!\bna)m[ae]z|[a-zçğıöşü]\w*m[ıiuü]yor\w*|[a-zçğıöşü]\w*m[ae]m[ae]kt[ae]d[ıi]r))\b"
    # Le chinois n'a pas d'espaces : \b ne s'y applique pas (sg-car-cost, 2026-10-24 : « 本网站不设置 Cookie » non lu).
    r"|(不|没有|沒有|无|無|未)", re.I)
COOKIE_MOT = re.compile(r'(cookie|t[ée]moin|evästeit|evästet|eväste|kakor|kaka|informasjonskapsl|ciasteczk|cookies|çerez)', re.I)
BANDEAU_MOT = re.compile(r'(bandeau|banni[eè]re|banner|baner|banier|bannière|pop-?up|μπάνερ|banderol|aviso de cookies'
                         r'|cookie[- ]?(settings|einstellungen|instellingen|preferences|inställningar|innstillinger'
                         r'|asetukset|ustawienia)|gérer les cookies|paramètres des cookies|gestione dei cookie|çerez (?:ayarları|bildirimi)|pengaturan cookie'
                         r'|configurar cookies|gestionar cookies)', re.I)
CONSENT_MOT = re.compile(r'(consent|consentement|einwilligung|zustimmung|toestemming|consenso|consentimiento'
                         r'|consentimento|samtycke|samtykke|suostum|zgod[aęy]|συγκατάθεσ|موافقة|açık rıza|persetujuan)', re.I)
GOOGLE_MOT = re.compile(r'(google analytics|\bGA4\b|_ga\b|_gid\b)', re.I)
PUB_MOT = re.compile(r'(adsense|google ads|doubleclick)', re.I)
GA_ID = re.compile(r'(?<![A-Za-z0-9_-])G-[A-Z0-9]{10}(?![A-Za-z0-9_-])')
GA_CONSENT = re.compile(r"gtag\(\s*['\"]consent['\"]\s*,\s*['\"]default['\"]\s*,\s*\{([^}]*)\}\s*\)")
GA_CONFIG = re.compile(r"gtag\(\s*['\"]config['\"]\s*,\s*['\"](G-[A-Z0-9]+)['\"]\s*,\s*\{([^}]*)\}\s*\)")
GA_JS = re.compile(r'googletagmanager\.com/gtag/js\?id=([A-Za-z0-9-]*)')
# Phrases fausses dès que GA4 est servi (toutes langues gérées par gen-legal-pages.py).
SANS_AUDIENCE = re.compile(
    r"(aucun(e)? (outil|service|mesure|statistique)s? (d.analyse |de mesure |de statistiques )?d.audience"
    r"|aucune statistique|n.utilise aucun outil d.analyse|no (audience measurement|analytics|web analytics|usage statistics)"
    r"|keine (Reichweitenmessung|Webanalyse|Besucherstatistik|Analyse-?Tools?)"
    r"|ning[uú]n(a)? (servicio|herramienta) de (medici[oó]n|anal[ií]tica)|geen (bezoekersstatistieken|analysetools?|webanalyse))",
    re.I)
CONTEXTE_SANS_COOKIE = re.compile(r'(clarity|int[ée]gr|embed|iframe|eingebettet|eingebunden|ingesloten|insluit|incrust|widget)', re.I)


def ga4_attendu(site: Path):
    """GA4_ID de src/data/site-config.ts ('' si absent ou vide)."""
    f = site / 'src' / 'data' / 'site-config.ts'
    if not f.is_file():
        return ''
    m = re.search(r"export\s+const\s+GA4_ID\s*(?::\s*string\s*)?=\s*['\"]([^'\"]*)['\"]", f.read_text(errors='ignore'))
    return m.group(1).strip() if m else ''

LANGS = ('fr', 'en', 'de', 'nl', 'it', 'es', 'pt', 'pl', 'fi', 'sv', 'nb', 'no', 'da', 'el', 'ar', 'tr', 'id')


def sortie_de(site: Path):
    cands = [site / d for d in SORTIES if (site / d / 'index.html').is_file()]
    if not cands:
        return None
    return max(cands, key=lambda d: sum(1 for _ in d.rglob('*.html')))


def texte(html):
    t = re.sub(r'<(script|style|noscript|svg)[\s\S]*?</\1>', ' ', html, flags=re.I)
    corps = re.search(r'<main[\s\S]*?</main>', t, flags=re.I)
    t = corps.group(0) if corps else re.sub(r'<(nav|header|footer)[\s\S]*?</\1>', ' ', t, flags=re.I)
    t = re.sub(r'</(h[1-6]|p|li|td|th|tr|dt|dd)>', '. ', t, flags=re.I)  # un titre n'est pas le début du paragraphe
    t = re.sub(r'<[^>]+>', ' ', t)
    t = re.sub(r'&nbsp;|&#160;| | ', ' ', t)
    t = re.sub(r'&[a-z#0-9]+;', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()


def phrases(t):
    return [p.strip() for p in re.split(r'(?<=[.!?;:])\s+', t) if p.strip()]


def lang_de(rel: str, html: str):
    m = re.search(r'<html[^>]*\blang=["\']([a-zA-Z]{2})', html)
    if m:
        return m.group(1).lower()
    seg = rel.split('/')[0]
    return seg if seg in LANGS else '?'


def slug(rel: str):
    parts = [p for p in rel.replace('index.html', '').replace('.html', '').split('/') if p]
    return parts[-1] if parts else ''


def controle_ga4(html, attendu, ga_ids):
    """Conditions du point 3 (a, b, c) sur une page qui sert GA4."""
    e = []
    ids = set(GA_ID.findall(html))
    ga_ids.update(ids)
    if not attendu:
        return ['GA4 servi alors que GA4_ID est vide dans site-config.ts']
    if not ids:
        e.append('gtag sans G-ID')
    if ids - {attendu}:
        e.append(f'G-ID autre que celui de site-config.ts ({", ".join(sorted(ids - {attendu}))} ≠ {attendu})')
    js = GA_JS.search(html)
    if not js or js.group(1) != attendu:
        e.append(f'gtag/js absent ou sans le G-ID {attendu}')
    cs = GA_CONSENT.findall(html)
    c = GA_CONSENT.search(html)
    if len(cs) != 1:
        e.append(f"{len(cs)} gtag('consent','default') au lieu d'un")
    elif js and c.start() > js.start():
        e.append("gtag('consent','default') placé après gtag/js")
    if c:
        corps = c.group(1)
        for cle, val in (('analytics_storage', 'granted'), ('ad_storage', 'denied'),
                         ('ad_user_data', 'denied'), ('ad_personalization', 'denied')):
            if not re.search(cle + r"\s*:\s*['\"]" + val + r"['\"]", corps):
                e.append(f"consentement par défaut : {cle} doit valoir '{val}'")
    ga_scripts = ' '.join(x for x in re.findall(r'<script[^>]*>([\s\S]*?)</script>', html, re.I) if 'gtag(' in x)
    if re.search(r'localStorage|consent-choice', ga_scripts):
        e.append('le chargement de GA4 lit localStorage / consent-choice (ancien régime à bandeau)')
    cf = GA_CONFIG.search(html)
    if not cf or cf.group(1) != attendu or not re.search(r'anonymize_ip\s*:\s*true', cf.group(2)):
        e.append(f"gtag('config','{attendu}',{{anonymize_ip:true}}) absent")
    return e


def autotest():
    """Cas connus : GA4 conforme passe ; deux G-ID, consentement faux, AdSense, page légale fausse échouent."""
    import subprocess, tempfile
    gid = 'G-TEST000000'
    tete = ("<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}"
            "gtag('consent','default',{analytics_storage:'granted',ad_storage:'denied',ad_user_data:'denied',"
            "ad_personalization:'denied'});</script><script async src=\"https://www.googletagmanager.com/gtag/js?id=%s\">"
            "</script><script>gtag('js',new Date());gtag('config','%s',{anonymize_ip:true});</script>")
    priv_ok = ("<main><h1>Confidentialité</h1><p>Google Analytics dépose les cookies _ga et _ga_TEST000000. "
               "Fournisseur : Google Ireland Limited. <a href=\"https://tools.google.com/dlpage/gaoptout\">module</a>.</p></main>")
    legal_ok = "<main><h1>Mentions légales</h1><p>Éditeur : Radif Partners.</p></main>"
    def site(head, priv, cfg_id=gid):
        d = Path(tempfile.mkdtemp())
        (d / 'src/data').mkdir(parents=True)
        (d / 'src/data/site-config.ts').write_text(f"export const GA4_ID = '{cfg_id}';\n")
        pages = {'index.html': '<main>x</main>', 'fr/index.html': '<main>x</main>', 'fr/a/index.html': '<main>x</main>',
                 'fr/confidentialite/index.html': priv, 'fr/cookies/index.html': priv, 'fr/mentions-legales/index.html': legal_ok}
        for rel, corps in pages.items():
            f = d / 'dist' / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(f'<html lang="fr"><head>{head}</head><body>{corps}</body></html>')
        return d
    cas = [
        ('GA4 conforme', site(tete % (gid, gid), priv_ok), 0),
        ('deux G-ID', site(tete % (gid, 'G-AUTRE00000'), priv_ok), 1),
        ('G-ID différent de site-config', site(tete % (gid, gid), priv_ok, 'G-AUTRE00000'), 1),
        ('GA4 servi, GA4_ID vide', site(tete % (gid, gid), priv_ok, ''), 1),
        ('publicité refusée manquante', site((tete % (gid, gid)).replace("ad_storage:'denied'", "ad_storage:'granted'"), priv_ok), 1),
        ('localStorage lu', site((tete % (gid, gid)).replace('gtag(\'consent\'', "localStorage.getItem('consent-choice');gtag('consent'"), priv_ok), 1),
        ('AdSense', site(tete % (gid, gid) + '<script src="https://pagead2.googlesyndication.com/x.js"></script>', priv_ok), 1),
        ('page qui dit « aucun cookie »', site(tete % (gid, gid), priv_ok.replace('</p>', ' Le site ne dépose aucun cookie.</p>')), 1),
        ('page sans Google Analytics', site(tete % (gid, gid), legal_ok.replace('Mentions légales', 'Confidentialité')), 1),
    ]
    echecs = 0
    for nom, d, attendu in cas:
        r = subprocess.run([sys.executable, '-I', __file__, str(d)], capture_output=True, text=True).returncode
        ok = (r == 0) == (attendu == 0)
        echecs += not ok
        print(f'{"ok   " if ok else "ÉCHEC"} {nom} (code {r})')
        import shutil; shutil.rmtree(d, ignore_errors=True)
    sys.exit(1 if echecs else 0)


def main():
    if '--test' in sys.argv:
        autotest()
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    site = Path(sys.argv[1]).resolve()
    verbose = '--verbose' in sys.argv
    sortie = sortie_de(site)
    if not sortie:
        print(f'check-cookies : pas de build dans {site} — lancer le build avant.')
        sys.exit(1)

    erreurs = []
    html_files = [f for f in sortie.rglob('*.html')
                  if not any(a in f.as_posix() for a in ('/_archives/', '/archive/', '/old/', '/backup/'))]
    clarity_pages = 0
    ga4_pages = 0
    ga_ids = set()
    attendu = ga4_attendu(site)
    langues = {}
    legales = {}  # lang -> {'privacy': [...], 'cookies': [...], 'legal': [...]}

    for f in html_files:
        rel = f.relative_to(sortie).as_posix()
        html = f.read_text(errors='ignore')
        if (m := BANDEAU.search(html)):
            erreurs.append(f'{rel} : bandeau ou gestion des cookies ({m.group(0)})')
        if (m := TRACEURS.search(html)):
            erreurs.append(f'{rel} : traceur interdit ({m.group(0)})')
        if GA4_TRACE.search(html):
            ga4_pages += 1
            erreurs.extend(f'{rel} : {e}' for e in controle_ga4(html, attendu, ga_ids))
        if (m := ANCIEN_CLARITY.search(html)):
            erreurs.append(f'{rel} : ancien chargement de Clarity soumis au bandeau ({m.group(0)})')
        tag = CLARITY_TAG.search(html)
        if tag:
            clarity_pages += 1
            c = CONSENTV2_DENIED.search(html)
            if not c or c.start() > tag.start():
                erreurs.append(f'{rel} : Clarity chargé sans consentv2 « denied » mis en file avant clarity.ms/tag/')
            # Contenu masqué par le code, pas seulement par le réglage du projet Clarity :
            # les pages légales l'affirment, il faut que ce soit vrai quel que soit le projet.
            if not re.search(r'<body[^>]*data-clarity-mask=["\']true', html, re.I):
                erreurs.append(f'{rel} : Clarity chargé sans data-clarity-mask="true" sur <body>')
        if 'http-equiv="refresh"' in html.lower() or re.search(r'<meta[^>]+refresh', html, re.I):
            continue
        lg = lang_de(rel, html)
        langues[lg] = langues.get(lg, 0) + 1
        s = slug(rel)
        if not s:
            continue
        kind = None
        if P_COOKIES.search(s):
            kind = 'cookies'
        elif P_PRIVACY.search(s):
            kind = 'privacy'
        elif P_LEGAL.search(s):
            kind = 'legal'
        if kind:
            legales.setdefault(lg, {'privacy': [], 'cookies': [], 'legal': []})[kind].append((rel, html))

    # Scripts servis : un traceur peut être injecté par un bundle.
    for f in sortie.rglob('*.js'):
        js = f.read_text(errors='ignore')
        m = re.search(r'pagead2\.googlesyndication|connect\.facebook\.net'
                      r'|static\.hotjar\.com', js)
        if m:
            erreurs.append(f'{f.relative_to(sortie).as_posix()} : traceur interdit dans un script ({m.group(0)})')

    # Pages légales par langue servie (langues ayant au moins 3 pages).
    for lg, n in sorted(langues.items()):
        if n < 3:
            continue
        lp = legales.get(lg, {'privacy': [], 'cookies': [], 'legal': []})
        if not lp['privacy'] and not lp['cookies']:
            erreurs.append(f'[{lg}] aucune page de confidentialité ni de cookies')
        if not lp['legal']:
            erreurs.append(f'[{lg}] aucune page de mentions légales / CGU')
        for kind in ('cookies', 'privacy'):
            for rel, html in lp[kind]:
                t = texte(html)
                ph = phrases(t)
                if ga4_pages:
                    if not re.search(r'google analytics', t, re.I) or not re.search(r'\b_ga\b', t):
                        erreurs.append(f'{rel} : GA4 est servi mais la page ne nomme pas Google Analytics et le cookie _ga')
                    if kind == 'privacy' and (not re.search(r'google ireland', t, re.I)
                                              or 'tools.google.com/dlpage/gaoptout' not in html):
                        erreurs.append(f'{rel} : GA4 est servi mais la page ne nomme pas Google Ireland ni le module '
                                       f'de désactivation (tools.google.com/dlpage/gaoptout)')
                elif not any(COOKIE_MOT.search(p) and NEGATION.search(p) for p in ph):
                    erreurs.append(f'{rel} : ne dit pas qu\'aucun cookie n\'est déposé')
                if clarity_pages and 'clarity' not in t.lower():
                    erreurs.append(f'{rel} : Clarity est chargé mais la page ne le nomme pas')
        for kind in ('cookies', 'privacy', 'legal'):
            for rel, html in lp[kind]:
                tx = texte(html)
                # Phrase entiere (coupee aux seuls . ! ?) : « Clarity en mode sans cookie : aucun cookie, ... »
                # reste une phrase sur Clarity meme si phrases() la coupe aux deux-points.
                entieres = [q for q in re.split(r'(?<=[.!?])\s+', tx) if q.strip()]
                for p in phrases(tx):
                    contexte = next((q for q in entieres if p in q), p)
                    if ga4_pages:
                        # GA4 dépose des cookies : plus de « aucun cookie » ni de « aucune mesure d'audience ».
                        if (m := SANS_AUDIENCE.search(p)):
                            erreurs.append(f'{rel} : GA4 est servi, la page dit « {m.group(0)} » : « {p[:140]} »')
                        elif COOKIE_MOT.search(p) and NEGATION.search(p) and not CONTEXTE_SANS_COOKIE.search(contexte) \
                                and not re.search(r'google|_ga\b|bloqu|block|supprim|delet|lösch|verwijder|elimin|borr|publicit|pubblicit|reklam|advertis|werbe|anuncio|advertentie|social|społeczno|réseau|netzwerk', p, re.I):
                            erreurs.append(f'{rel} : GA4 est servi, la page dit qu\'aucun cookie n\'est déposé : « {p[:140]} »')
                    if NEGATION.search(p):
                        continue
                    motifs = [('bandeau', BANDEAU_MOT), ('consentement', CONSENT_MOT), ('publicité Google', PUB_MOT)]
                    if not ga4_pages:
                        motifs.append(('Google Analytics', GOOGLE_MOT))
                    for nom, motif in motifs:
                        if motif.search(p):
                            erreurs.append(f'{rel} : mention de {nom} : « {p[:140]} »')

    if ga4_pages and len(ga_ids) > 1:
        erreurs.append(f'plusieurs G-ID servis : {", ".join(sorted(ga_ids))}')

    if erreurs:
        print(f'check-cookies : {len(erreurs)} défaut(s) dans {site.name}')
        for e in erreurs[: (None if verbose else 40)]:
            print('  - ' + e)
        if not verbose and len(erreurs) > 40:
            print(f'  … {len(erreurs) - 40} de plus (--verbose)')
        sys.exit(1)
    print(f'check-cookies : 0 défaut ({len(html_files)} pages, Clarity sur {clarity_pages}, '
          f'GA4 {attendu + " " if ga4_pages else ""}sur {ga4_pages}, '
          f'langues {", ".join(sorted(k for k, v in langues.items() if v >= 3))})')


if __name__ == '__main__':
    main()
