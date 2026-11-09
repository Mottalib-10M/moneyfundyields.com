# -*- coding: utf-8 -*-
"""Pages légales types d'un site de la trame : confidentialité, cookies, mentions légales / CGU.

Usage (dans le dossier du site, ou en donnant son chemin) :
    python3 scripts/gen-legal-pages.py .            # écrit les pages
    python3 scripts/gen-legal-pages.py . --dry-run  # montre ce qui serait écrit
    python3 scripts/gen-legal-pages.py . --force    # écrit même si GA4_ID est vide
    python3 scripts/gen-legal-pages.py . --layout   # remplace aussi, dans src/layouts/BaseLayout.astro,
                                                    # le bloc GA4 par celui de la trame (reste du layout gardé)

Décision de l'éditeur du 2026-10-17 (RECETTE §15.6) : Google Analytics 4 normal, AVEC
cookies, SANS bandeau, sur tous les sites ; Clarity reste sans cookie ; aucune publicité.
Les pages doivent alors dire vrai :
  - cookies _ga et _ga_<ID> : 13 mois au plus (390 jours, cookie_expires = 33 696 000 s,
    cookie_update = false dans BaseLayout.astro), au lieu des 2 ans par défaut de Google
    (référence des cookies Google : business.safety.google/adscookies) — recommandation
    CNIL (cnil.fr, « Cookies : solutions pour les outils de mesure d'audience ») : 13 mois,
    sans prolongation automatique à chaque visite ;
  - finalité : mesure d'audience ; IP non enregistrée par GA4 (support.google.com/analytics/
    answer/2763052) ; aucune publicité, aucun partage publicitaire ;
  - fournisseur : Google Ireland Limited, Gordon House, Barrow Street, Dublin 4, Irlande ;
  - transfert : Google LLC (États-Unis), EU–U.S. Data Privacy Framework + clauses types ;
  - conservation côté GA : 14 mois (réglage posé par seo-platform/scripts/create-ga4.ts ;
    options GA4 : 2 ou 14 mois, support.google.com/analytics/answer/7667196) ;
  - opposition : réglages du navigateur et module tools.google.com/dlpage/gaoptout ;
  - base juridique : intérêt légitime (art. 6-1 f RGPD) et l'équivalent local (nLPD/revDSG
    pour la Suisse, UK GDPR, LPRPDE/PIPEDA, APP 3, IPP 1, PDPA…). Jamais « consentement »,
    jamais de bandeau ni de choix proposé : il n'y en a pas.

Les pages rendent les deux états à la construction ({GA4_ID ? … : …}, {CLARITY_ID && …}) :
elles restent exactes si GA4_ID ou CLARITY_ID changent. Sans GA4_ID, le script ne touche à
rien (les textes en place sont exacts), sauf --force.

Ce qui est écrit, pour chaque langue gérée (fr, en, de, es, nl ; variantes fr-FR, fr-BE,
fr-CH, fr-LU, fr-CA, de-DE, de-AT, de-CH, en-GB, en-IE, en-CA, en-AU, en-NZ, en-SG, en-US,
es-ES, nl-NL, nl-BE, et la variante européenne par défaut) :
  - confidentialité et cookies : page réécrite en entier. Un passage propre au site se garde
    entre {/* site:debut */} et {/* site:fin */} : il est reporté tel quel avant « Vos droits » ;
  - mentions légales / CGU : si la page existe, seule sa section « Données personnelles »
    (ou « Cookies et données », « Personal data », « Datenschutz »…) est remplacée — le reste,
    propre au site, est gardé ; sinon une page type est écrite.
Les chemins viennent de src/i18n/routes.ts (routes « privacy », « cookies », « terms »), la
région de LANG_TAGS (site-config.ts). Une langue non gérée (it, pt, fi, sv, nb, da, pl, el, tr, id…)
est signalée : ses pages se rédigent à la main sur le modèle français, avec les mêmes faits.
Turc et indonésien (2026-10-28) : non générés à dessein. Avec GA4, la KVKK (loi n° 6698, art. 9 :
transfert à l'étranger par clauses types notifiées à l'Autorité) et l'UU PDP (loi n° 27/2022,
art. 56) demandent des faits que l'éditeur doit établir avant qu'un texte type puisse les affirmer.

Contrôle ensuite : npm run check (check-cookies.py vérifie GA4, consentement par défaut et
pages légales). L'ancienne version (7 sites de la vague du 2026-10-05) est dans
_trame/legacy/gen-legal-pages-7sites-2026-10-06.py.
"""
import os
import re
import sys

ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
DRY = '--dry-run' in sys.argv
FORCE = '--force' in sys.argv
LAYOUT = '--layout' in sys.argv
TRAME_LAYOUT = os.path.expanduser('~/Documents/GitHub/_trame/_template/src/layouts/BaseLayout.astro')
SITE = os.path.abspath(ARGS[0] if ARGS else '.')

GA_OPTOUT = 'https://tools.google.com/dlpage/gaoptout'
GOOGLE_IE = 'Google Ireland Limited, Gordon House, Barrow Street, Dublin 4'
MS_IE = 'Microsoft Ireland Operations Limited, One Microsoft Place, South County Business Park, Leopardstown, Dublin 18'
ID = "{GA4_ID.replace('G-', '')}"
EXT = 'rel="nofollow noopener" target="_blank"'
MAIL = '<a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>'


# --------------------------------------------------------------------------- #
# Lecture du site
# --------------------------------------------------------------------------- #
def lire(rel):
    p = os.path.join(SITE, rel)
    return open(p, encoding='utf-8').read() if os.path.isfile(p) else ''


def config():
    sc = lire('src/data/site-config.ts')
    if not sc:
        sys.exit(f'gen-legal-pages : pas de src/data/site-config.ts dans {SITE}')
    ga = re.search(r"export const GA4_ID\s*(?::\s*string\s*)?=\s*'([^']*)'", sc)
    tags = re.search(r'export const LANG_TAGS[^=]*=\s*(\{[^}]*\})', sc)
    lang_tags = dict(re.findall(r'"([a-z]{2})"\s*:\s*"([^"]+)"', tags.group(1))) if tags else {}
    lang_tags.update(dict(re.findall(r"'([a-z]{2})'\s*:\s*'([^']+)'", tags.group(1))) if tags else {})
    return (ga.group(1) if ga else ''), lang_tags


def routes():
    """{(id, lang): '/xx/slug/'} pour privacy, cookies, terms, et la liste LOCALES."""
    rt = lire('src/i18n/routes.ts')
    if not rt:
        sys.exit(f'gen-legal-pages : pas de src/i18n/routes.ts dans {SITE}')
    m = re.search(r'LOCALES\s*=\s*\[([^\]]*)\]', rt)
    locales = re.findall(r"'([a-z]{2})'", m.group(1)) if m else []
    out = {}
    # Fabrique de routes : const R = (id: string, fr: string, en: string, noindex = false) => ({ id,
    # paths: { fr: `/fr/${fr}/`, en: `/en/${en}/` } … }) ou, en raccourci, paths: { fr, nl } (chemins entiers).
    rdef = re.search(r'const (\w+)\s*=\s*\(\s*id\s*:\s*string\s*,\s*([^)]*?)\)[^\n]*', rt)
    fab, params, tpl = None, [], {}
    if rdef:
        fab = rdef.group(1)
        params = [p.split(':')[0].strip() for p in rdef.group(2).split(',') if p.strip() and 'noindex' not in p]
        tpl = dict(re.findall(r'\b([a-z]{2})\s*:\s*`([^`]*)`', rdef.group(0)))
        po = re.search(r'paths\s*:\s*\{([^}`]*)\}', rdef.group(0))
        if not tpl and po:
            tpl = {k: '${' + k + '}' for k in re.findall(r'\b([a-z]{2})\b', po.group(1))}
    for rid in ('privacy', 'cookies', 'terms'):
        lit = re.search(r"\{\s*id\s*:\s*'" + rid + r"'\s*,\s*paths\s*:\s*\{([^}]*)\}", rt)
        if lit:
            for lg, p in re.findall(r"([a-z]{2})\s*:\s*['`]([^'`]+)['`]", lit.group(1)):
                out[rid, lg] = p
            continue
        call = re.search(r"\b" + re.escape(fab or 'R') + r"\(\s*'" + rid + r"'\s*,([^)]*)\)", rt)
        if call and params:
            args = re.findall(r"'([^']*)'", call.group(1))
            vals = dict(zip(params, args))
            for lg, t in tpl.items():
                p = t
                for k, v in vals.items():
                    p = p.replace('${' + k + '}', v)
                if '${' not in p:
                    out[rid, lg] = p
    return locales, out


def fichier(chemin):
    base = os.path.join(SITE, 'src/pages', chemin.strip('/'))
    return base + '/index.astro' if os.path.isfile(base + '/index.astro') else base + '.astro'


# --------------------------------------------------------------------------- #
# Variantes juridiques par région (code pays de LANG_TAGS)
# loi : lois citées en tête de la confidentialité ; base : équivalent local de l'art. 6-1 f ;
# aut : autorité locale ajoutée à celle de LEGAL.supervisoryAuthority.
# --------------------------------------------------------------------------- #
REG = {
    'fr': {
        'FR': dict(loi=' et à la loi n° 78-17 du 6 janvier 1978 modifiée', base='', aut=''),
        'BE': dict(loi=' et à la loi belge du 30 juillet 2018 relative à la protection des personnes physiques à l’égard des traitements de données à caractère personnel',
                   base='', aut=' En Belgique, vous pouvez aussi saisir l’Autorité de protection des données (APD).'),
        'LU': dict(loi=' et à la loi luxembourgeoise du 1er août 2018 portant organisation de la CNPD', base='',
                   aut=' Au Luxembourg, vous pouvez aussi saisir la Commission nationale pour la protection des données (CNPD).'),
        'CH': dict(loi=' et, pour les visiteurs en Suisse, à la loi fédérale sur la protection des données (nLPD)',
                   base=' et art. 31, al. 1, nLPD, intérêt prépondérant',
                   aut=' En Suisse, vous pouvez aussi vous adresser au Préposé fédéral à la protection des données et à la transparence (PFPDT).'),
        'CA': dict(loi=' et, pour les visiteurs au Canada, à la Loi sur la protection des renseignements personnels et les documents électroniques (LPRPDE) et, au Québec, à la Loi sur la protection des renseignements personnels dans le secteur privé',
                   base=' ; au Canada, art. 5(3) de la LPRPDE, fins qu’une personne raisonnable estimerait acceptables dans les circonstances',
                   aut=' Au Québec, vous pouvez aussi vous adresser à la Commission d’accès à l’information.'),
        '': dict(loi='', base='', aut=''),
    },
    'en': {
        'GB': dict(loi=', the UK GDPR and the Data Protection Act 2018', base=' and Article 6(1)(f) UK GDPR',
                   aut=' In the United Kingdom you may also complain to the Information Commissioner’s Office (ICO).'),
        'IE': dict(loi=' and the Irish Data Protection Act 2018', base='',
                   aut=' In Ireland you may also complain to the Data Protection Commission.'),
        'CA': dict(loi=' and, for visitors in Canada, the Personal Information Protection and Electronic Documents Act (PIPEDA)',
                   base='; in Canada, section 5(3) of PIPEDA, purposes a reasonable person would consider appropriate in the circumstances',
                   aut=' In Quebec you may also contact the Commission d’accès à l’information.'),
        'AU': dict(loi=' and, for visitors in Australia, the Privacy Act 1988 and the Australian Privacy Principles',
                   base='; in Australia, Australian Privacy Principle 3, collection reasonably necessary for our activities',
                   aut=' In Australia you may also complain to the Office of the Australian Information Commissioner (OAIC).'),
        'NZ': dict(loi=' and, for visitors in New Zealand, the Privacy Act 2020', base='; in New Zealand, Information Privacy Principle 1 of the Privacy Act 2020, collection for a lawful purpose connected with our activities',
                   aut=' In New Zealand you may also complain to the Office of the Privacy Commissioner.'),
        'SG': dict(loi=' and, for visitors in Singapore, the Personal Data Protection Act 2012 (PDPA)',
                   base='; in Singapore, the legitimate interests exception of the PDPA, First Schedule, Part 3',
                   aut=' In Singapore you may also contact the Personal Data Protection Commission (PDPC).'),
        'US': dict(loi='; for visitors in the United States, no personal information is sold or shared within the meaning of the California Consumer Privacy Act (CCPA/CPRA)',
                   base='; for visitors in the United States, no personal information is sold or shared within the meaning of the CCPA/CPRA',
                   aut=''),
        'CH': dict(loi=' and, for visitors in Switzerland, the Swiss Federal Act on Data Protection (revFADP)',
                   base=' and Article 31(1) revFADP, overriding interest',
                   aut=' In Switzerland you may also contact the Federal Data Protection and Information Commissioner (FDPIC).'),
        '': dict(loi='', base='', aut=''),
    },
    'de': {
        'DE': dict(loi=' und des Bundesdatenschutzgesetzes (BDSG)', base='', aut=''),
        'AT': dict(loi=' und des österreichischen Datenschutzgesetzes (DSG)', base='',
                   aut=' In Österreich können Sie sich auch an die Datenschutzbehörde wenden.'),
        'CH': dict(loi=' und, für Besucher in der Schweiz, des Bundesgesetzes über den Datenschutz (revDSG)',
                   base=' sowie Art. 31 Abs. 1 revDSG, überwiegendes Interesse',
                   aut=' In der Schweiz können Sie sich auch an den Eidgenössischen Datenschutz- und Öffentlichkeitsbeauftragten (EDÖB) wenden.'),
        '': dict(loi='', base='', aut=''),
    },
    'es': {
        'ES': dict(loi=' y de la Ley Orgánica 3/2018 de Protección de Datos Personales y garantía de los derechos digitales (LOPDGDD)', base='',
                   aut=' En España, también puede reclamar ante la Agencia Española de Protección de Datos (AEPD).'),
        '': dict(loi='', base='', aut=''),
    },
    'nl': {
        'NL': dict(loi=' en de Uitvoeringswet AVG', base='', aut=' In Nederland kunt u ook een klacht indienen bij de Autoriteit Persoonsgegevens.'),
        'BE': dict(loi=' en de Belgische wet van 30 juli 2018 betreffende de bescherming van natuurlijke personen met betrekking tot de verwerking van persoonsgegevens', base='',
                   aut=' In België kunt u ook terecht bij de Gegevensbeschermingsautoriteit (GBA).'),
        '': dict(loi='', base='', aut=''),
    },
}


# --------------------------------------------------------------------------- #
# Textes. «BASE», «LOI», «AUT» : variantes ci-dessus ; «ID» : G-ID sans « G- ».
# Apostrophe typographique partout (’) : les textes passent aussi dans des chaînes JS.
# --------------------------------------------------------------------------- #
T = {}

T['fr'] = dict(
    bc=dict(privacy='Confidentialité', cookies='Cookies', terms='Mentions légales'),
    title=dict(privacy='Politique de confidentialité', cookies='Cookies', terms='Mentions légales'),
    desc=dict(
        privacy_ga='Mesure d’audience Google Analytics avec cookies, sans publicité ; saisies gardées dans votre navigateur ; journaux de l’hébergeur ; vos droits et l’autorité de contrôle.',
        privacy_no='Saisies gardées dans votre navigateur, aucun cookie, journaux de l’hébergeur : les traitements de données du site, vos droits et l’autorité de contrôle.',
        cookies_ga='Des cookies de mesure d’audience Google Analytics, et eux seuls : noms, finalité, durée de 13 mois au plus, fournisseur et moyens de vous y opposer.',
        cookies_no='Le site ne dépose aucun cookie : vos saisies restent dans votre navigateur, rien n’est gardé sur votre appareil.',
        terms='Éditeur, directeur de la publication, hébergeur, absence de conseil, propriété intellectuelle, données personnelles et droit applicable.'),
    base='l’intérêt légitime de l’éditeur (art. 6-1 f du RGPD«BASE»)',
    privacy="""    <h1>Politique de confidentialité</h1>
    <p>Cette page décrit les traitements de données personnelles liés à l’utilisation de {SITE_URL}, conformément aux articles 12 à 14 du règlement (UE) 2016/679 (RGPD)«LOI».</p>
    <h2>1. Responsable du traitement</h2>
    <LegalIdentity lang={lang} />
    <p>Pour toute question relative à vos données : «MAIL». Aucun délégué à la protection des données n’a été désigné, les conditions de l’article 37 du RGPD n’étant pas réunies.</p>
    <h2>2. Vos saisies restent dans votre navigateur</h2>
    <p>Les calculs du site sont exécutés par votre navigateur. Les montants, dates et situations que vous saisissez <strong>ne sont transmis à aucun serveur</strong>, ne sont enregistrés nulle part et ne sont rattachés à aucun identifiant. Le site ne demande ni compte, ni nom, ni adresse électronique. Un lien de partage reprend vos saisies dans l’adresse de la page : ne le transmettez qu’aux personnes de votre choix.</p>
    <h2>3. Traitements réalisés</h2>
    <h3>Journaux de connexion de l’hébergeur</h3>
    <p>L’hébergeur enregistre, à chaque requête, l’adresse IP, la date et l’heure, la page demandée, le navigateur et la page de provenance. Finalité : sécurité du service et diagnostic des pannes. Base juridique : «B». Durée : celle de la politique de l’hébergeur.</p>
    {GA4_ID ? (<>
    <h3>Mesure d’audience avec Google Analytics</h3>
    <p>Le site utilise Google Analytics 4 pour compter ses visites et savoir quelles pages servent : pages vues, page de provenance, durée de la visite, type d’appareil et de navigateur, pays et ville approximatifs. Google Analytics dépose pour cela deux cookies sur votre terminal : <code>_ga</code>, qui distingue les visiteurs par un identifiant aléatoire, et <code>_ga_«ID»</code>, qui garde l’état de la visite. Leur durée de vie est réglée à 13 mois au plus (390 jours) et n’est pas prolongée à chaque visite ; Google prévoit 2 ans par défaut.</p>
    <p>L’adresse IP est anonymisée : Google Analytics 4 ne l’enregistre ni ne la conserve, il s’en sert seulement au moment de la collecte pour déduire un pays et une ville approximatifs. L’adresse de page transmise à Google Analytics est privée de ses paramètres : les saisies d’un lien de partage n’y figurent pas. Le site n’affiche pas de publicité : le stockage publicitaire, les données publicitaires, la personnalisation des annonces et les signaux Google sont désactivés, et les données de mesure ne sont partagées avec aucun annonceur.</p>
    <p>Finalité : mesure d’audience. Base juridique : «B». Fournisseur : «GOOGLE», Irlande. Conservation chez Google : 14 mois pour les données liées aux visites et aux identifiants, puis suppression ; seuls restent des totaux anonymes.</p>
    </>) : (<>
    <h3>Pas de mesure d’audience</h3>
    <p>Le site ne dépose aucun cookie et n’utilise aucun outil d’analyse d’audience ni de publicité.</p>
    </>)}
    {CLARITY_ID && (<>
    <h3>Mesure technique de la stabilité avec Microsoft Clarity, sans cookie</h3>
    <p>Pour repérer les erreurs, les pages lentes et les boutons qui ne réagissent pas, le site utilise Microsoft Clarity en mode sans cookie : Clarity ne dépose aucun cookie, chaque page vue reçoit un identifiant distinct, le texte des pages et vos saisies sont masqués. Clarity reçoit la structure de la page, les clics, le défilement, le type d’appareil, les temps de chargement et les erreurs. Finalité : stabilité du site. Base juridique : «B». Fournisseur : «MS», Irlande. Conservation : 30 jours pour les enregistrements de pages, 13 mois au plus pour les données agrégées.</p>
    </>)}
    <h3>Messages que vous nous envoyez</h3>
    <p>Si vous écrivez à l’adresse de contact, votre adresse électronique et votre message sont gardés le temps de vous répondre et, le cas échéant, de corriger une erreur, puis supprimés au plus tard trois ans après le dernier échange. Base juridique : «B».</p>
    <h2>4. Destinataires</h2>
    <p>Aucune donnée n’est vendue, louée ni cédée. Y accèdent l’hébergeur{GA4_ID && ', Google Ireland Limited pour Google Analytics'}{CLARITY_ID && ', Microsoft Ireland Operations Limited pour Clarity'}, comme sous-traitants au sens de l’article 28 du RGPD. Aucune régie publicitaire n’intervient sur le site.</p>
    <h2>5. Transferts hors de l’Union européenne</h2>
    <p>Les journaux de l’hébergeur peuvent être traités aux États-Unis.{GA4_ID && ' Les données de Google Analytics peuvent être transférées à Google LLC, aux États-Unis.'}{CLARITY_ID && ' Celles de Clarity peuvent l’être à Microsoft Corporation, aux États-Unis.'} Ces transferts sont encadrés par le cadre de protection des données UE–États-Unis (EU–U.S. Data Privacy Framework) et par les clauses contractuelles types de la Commission européenne.</p>
«SITE»    <h2>6. Vos droits</h2>
    <p>Vous disposez des droits d’accès, de rectification, d’effacement, de limitation, d’opposition et de portabilité prévus aux articles 15 à 22 du RGPD. Écrivez à «MAIL» ; nous répondons dans un délai d’un mois. Sans compte utilisateur, nous ne détenons le plus souvent aucune donnée permettant de vous identifier : nous vous le dirons alors.</p>
    {GA4_ID && (<p>Pour vous opposer à la mesure d’audience sans nous écrire : bloquez ou supprimez les cookies dans les réglages de votre navigateur, ou installez le <a href="«OPTOUT»" «EXT»>module de désactivation de Google Analytics</a>. Le site fonctionne alors de la même façon.</p>)}
    {CLARITY_ID && (<p>Pour la mesure de stabilité : bloquez le domaine <code>clarity.ms</code> dans votre navigateur ou avec un bloqueur de contenu.</p>)}
    <p>Vous pouvez introduire une réclamation auprès de l’autorité de contrôle : {LEGAL.supervisoryAuthority} (<a href={LEGAL.supervisoryAuthorityUrl} «EXT»>{LEGAL.supervisoryAuthorityUrl}</a>).«AUT»</p>
    <h2>7. Pas de décision automatisée</h2>
    <p>Le résultat d’un calcul est une estimation faite à votre demande, sur vos saisies, dans votre navigateur. Il ne produit aucun effet juridique et n’est pas une décision automatisée au sens de l’article 22 du RGPD. Aucun profilage n’est pratiqué.</p>
    <p>Voir aussi la page <a href={route('cookies', lang)}>cookies</a>. Dernière mise à jour : {LAST_UPDATED}.</p>""",
    cookies="""    <h1>Cookies</h1>
    {GA4_ID ? (<>
    <p>Le site dépose des cookies de mesure d’audience Google Analytics, et ceux-là seulement : ni cookie publicitaire, ni cookie de réseau social. Le détail des traitements figure dans la <a href={route('privacy', lang)}>politique de confidentialité</a>.</p>
    <h2>Les cookies déposés</h2>
    <table><thead><tr><th>Nom</th><th>Fournisseur</th><th>Finalité</th><th>Durée</th></tr></thead><tbody>
    <tr><td><code>_ga</code></td><td>Google Analytics</td><td>Distinguer les visiteurs par un identifiant aléatoire</td><td>13 mois au plus (390 jours)</td></tr>
    <tr><td><code>_ga_«ID»</code></td><td>Google Analytics</td><td>Garder l’état de la visite en cours</td><td>13 mois au plus (390 jours)</td></tr>
    </tbody></table>
    <p>Ces durées ne sont pas prolongées à chaque visite ; Google prévoit 2 ans par défaut, le site les réduit. Finalité : mesure d’audience (pages vues, provenance, appareil, pays approximatif). L’adresse IP est anonymisée : Google Analytics 4 ne l’enregistre ni ne la conserve. Pas de publicité ni de partage publicitaire : le stockage publicitaire, la personnalisation des annonces et les signaux Google sont désactivés.</p>
    <p>Fournisseur : «GOOGLE», Irlande. Les données peuvent être transférées à Google LLC, aux États-Unis, dans le cadre du EU–U.S. Data Privacy Framework et des clauses contractuelles types de la Commission européenne. Conservation chez Google : 14 mois. Base juridique : «B».</p>
    <h2>Vous opposer à ces cookies</h2>
    <p>Bloquez ou supprimez les cookies dans les réglages de votre navigateur, ou installez le <a href="«OPTOUT»" «EXT»>module de désactivation de Google Analytics</a>. Le site et ses calculs fonctionnent alors de la même façon.</p>
    </>) : (<>
    <p>Le site <strong>ne dépose aucun cookie</strong>. Le détail des traitements figure dans la <a href={route('privacy', lang)}>politique de confidentialité</a>.</p>
    </>)}
    {CLARITY_ID && (<><h2>Microsoft Clarity, sans cookie</h2><p>La stabilité des pages est mesurée avec Microsoft Clarity en mode sans cookie : Clarity ne dépose aucun cookie, chaque page vue reçoit un identifiant à usage unique, le contenu des pages et vos saisies sont masqués. Bloquer <code>clarity.ms</code> l’arrête.</p></>)}
    <h2>Vos saisies</h2>
    <p>Les calculs se font dans votre navigateur : ce que vous saisissez n’est envoyé à aucun serveur et disparaît à la fermeture de la page.</p>
    <p>Une question : «MAIL». Mise à jour : {LAST_UPDATED}.</p>""",
    terms_h2='Données personnelles et cookies',
    terms_sec="""    {GA4_ID ? (<p>Les saisies des calculateurs ne quittent pas votre navigateur. Le site dépose des cookies de mesure d’audience Google Analytics (<code>_ga</code>, <code>_ga_«ID»</code>, 13 mois au plus), sans publicité{CLARITY_ID && ' ; la stabilité des pages est mesurée avec Microsoft Clarity, sans cookie'}. Détails, base juridique et moyens de vous y opposer : <a href={route('privacy', lang)}>politique de confidentialité</a> et page <a href={route('cookies', lang)}>cookies</a>.</p>) : (<p>Les saisies des calculateurs ne quittent pas votre navigateur et le site ne dépose aucun cookie{CLARITY_ID && ' ; la stabilité des pages est mesurée de façon anonyme avec Microsoft Clarity, sans cookie'}. Voir la <a href={route('privacy', lang)}>politique de confidentialité</a> et la page <a href={route('cookies', lang)}>cookies</a>.</p>)}""",
    terms="""    <h1>Mentions légales</h1>
    <p>Informations publiées en application de l’article 6 III-1 de la loi n° 2004-575 du 21 juin 2004 pour la confiance dans l’économie numérique.</p>
    <h2>Éditeur du site</h2>
    <LegalIdentity lang={lang} />
    <p>Directeur de la publication : {AUTHOR_NAME}, responsable des contenus publiés sur {SITE_URL}.</p>
    <h2>Hébergeur</h2>
    <LegalIdentity mode="hosting" lang={lang} />
    <h2>Objet du site et absence de conseil</h2>
    <p>Le site met gratuitement à disposition des calculateurs et des guides, à titre informatif. Les résultats sont des estimations calculées à partir des textes et barèmes officiels cités sur chaque page ; ils ne constituent ni un conseil personnalisé, ni une décision, ni un engagement de l’administration. Méthode et limites : <a href={route('method', lang)}>méthode</a>.</p>
    <h2>Limites de responsabilité</h2>
    <p>Les paramètres sont mis à jour et les calculs vérifiés sur des cas de référence, sans garantie d’absence d’erreur. L’éditeur ne peut être tenu responsable d’une décision prise sur la seule base d’une estimation. Une erreur se signale par la page <a href={route('contact', lang)}>contact</a>.</p>
    <h2>Propriété intellectuelle</h2>
    <p>Textes, graphismes et code restent la propriété de l’éditeur ; les courtes citations sont autorisées avec un lien vers la page d’origine.</p>
    <h2>«H2»</h2>
«SEC»
    <h2>Signalement</h2>
    <p>Un contenu illicite se signale à «MAIL», avec l’adresse de la page et le motif.</p>
    <h2>Droit applicable</h2>
    <p>Droit français. À défaut d’accord amiable, les juridictions compétentes de {LEGAL.jurisdiction}. Mise à jour : {LAST_UPDATED}.</p>""",
)

T['en'] = dict(
    bc=dict(privacy='Privacy', cookies='Cookies', terms='Legal notice'),
    title=dict(privacy='Privacy policy', cookies='Cookies', terms='Legal notice'),
    desc=dict(
        privacy_ga='Google Analytics audience measurement with cookies and no advertising; inputs kept in your browser; host logs; your rights and the supervisory authority.',
        privacy_no='Inputs kept in your browser, no cookies, host logs: the data processing behind the site, your rights and the supervisory authority you can contact.',
        cookies_ga='Google Analytics audience measurement cookies and nothing else: names, purpose, a lifetime of 13 months at most, the provider and how to object.',
        cookies_no='The site sets no cookies: what you type stays in your browser and nothing is kept on your device.',
        terms='Publisher, editor in charge, host, no advice, intellectual property, personal data and governing law for this site.'),
    base='the publisher’s legitimate interests (Article 6(1)(f) GDPR«BASE»)',
    privacy="""    <h1>Privacy policy</h1>
    <p>This page describes the processing of personal data linked to the use of {SITE_URL}, under Articles 12 to 14 of Regulation (EU) 2016/679 (GDPR)«LOI».</p>
    <h2>1. Controller</h2>
    <LegalIdentity lang={lang} />
    <p>For any question about your data: «MAIL». No data protection officer has been appointed, as the conditions of Article 37 GDPR are not met.</p>
    <h2>2. What you type stays in your browser</h2>
    <p>The site’s calculations run in your browser. The amounts, dates and circumstances you enter <strong>are sent to no server</strong>, are stored nowhere and are linked to no identifier. The site asks for no account, name or email address. A share link carries your inputs in the page address: only send it to people you choose.</p>
    <h2>3. Processing carried out</h2>
    <h3>Host access logs</h3>
    <p>For each request the host records the IP address, date and time, the page requested, the browser and the referring page. Purpose: security of the service and fault diagnosis. Legal basis: «B». Retention: as set by the host’s own policy.</p>
    {GA4_ID ? (<>
    <h3>Audience measurement with Google Analytics</h3>
    <p>The site uses Google Analytics 4 to count visits and see which pages are useful: pages viewed, referring page, visit length, device and browser type, approximate country and city. To do so Google Analytics sets two cookies on your device: <code>_ga</code>, which tells visitors apart with a random identifier, and <code>_ga_«ID»</code>, which keeps the state of the visit. Their lifetime is set to 13 months at most (390 days) and is not extended on each visit; Google’s default is 2 years.</p>
    <p>The IP address is anonymised: Google Analytics 4 neither logs nor stores it, and only uses it at collection time to derive an approximate country and city. The page address sent to Google Analytics is stripped of its parameters, so the inputs carried by a share link are not included. The site shows no advertising: ad storage, ad user data, ad personalisation and Google signals are switched off, and measurement data is shared with no advertiser.</p>
    <p>Purpose: audience measurement. Legal basis: «B». Provider: «GOOGLE», Ireland. Retention at Google: 14 months for visit-level and identifier-level data, then deletion; only anonymous totals remain.</p>
    </>) : (<>
    <h3>No audience measurement</h3>
    <p>The site sets no cookies and uses no analytics or advertising tool.</p>
    </>)}
    {CLARITY_ID && (<>
    <h3>Technical stability monitoring with Microsoft Clarity, cookie-free</h3>
    <p>To spot errors, slow pages and buttons that do not respond, the site uses Microsoft Clarity in cookie-free mode: Clarity sets no cookies, each page view gets its own identifier, and page text and your inputs are masked. Clarity receives the page structure, clicks, scrolling, device type, load times and errors. Purpose: site stability. Legal basis: «B». Provider: «MS», Ireland. Retention: 30 days for page recordings, 13 months at most for aggregated data.</p>
    </>)}
    <h3>Messages you send us</h3>
    <p>If you write to the contact address, your email address and message are kept for as long as needed to reply and, where relevant, fix an error, then deleted no later than three years after the last exchange. Legal basis: «B».</p>
    <h2>4. Recipients</h2>
    <p>No data is sold, rented or passed on. Access is limited to the host{GA4_ID && ', Google Ireland Limited for Google Analytics'}{CLARITY_ID && ', Microsoft Ireland Operations Limited for Clarity'}, acting as processors under Article 28 GDPR. No advertising network operates on the site.</p>
    <h2>5. Transfers outside the European Union</h2>
    <p>Host logs may be processed in the United States.{GA4_ID && ' Google Analytics data may be transferred to Google LLC in the United States.'}{CLARITY_ID && ' Clarity data may be transferred to Microsoft Corporation in the United States.'} These transfers rely on the EU–U.S. Data Privacy Framework and the European Commission’s standard contractual clauses.</p>
«SITE»    <h2>6. Your rights</h2>
    <p>You have the rights of access, rectification, erasure, restriction, objection and portability set out in Articles 15 to 22 GDPR. Write to «MAIL»; we reply within one month. With no user accounts, we usually hold no data that identifies you, and we will tell you so.</p>
    {GA4_ID && (<p>To object to audience measurement without writing to us: block or delete cookies in your browser settings, or install the <a href="«OPTOUT»" «EXT»>Google Analytics opt-out browser add-on</a>. The site works the same way.</p>)}
    {CLARITY_ID && (<p>For stability monitoring: block the <code>clarity.ms</code> domain in your browser or with a content blocker.</p>)}
    <p>You may lodge a complaint with the supervisory authority: {LEGAL.supervisoryAuthority} (<a href={LEGAL.supervisoryAuthorityUrl} «EXT»>{LEGAL.supervisoryAuthorityUrl}</a>).«AUT»</p>
    <h2>7. No automated decision-making</h2>
    <p>A calculation result is an estimate produced at your request, from your inputs, in your browser. It has no legal effect and is not an automated decision under Article 22 GDPR. No profiling takes place.</p>
    <p>See also the <a href={route('cookies', lang)}>cookies</a> page. Last updated: {LAST_UPDATED}.</p>""",
    cookies="""    <h1>Cookies</h1>
    {GA4_ID ? (<>
    <p>The site sets Google Analytics audience measurement cookies and those alone: no advertising cookie, no social media cookie. Details of the processing are in the <a href={route('privacy', lang)}>privacy policy</a>.</p>
    <h2>Cookies set</h2>
    <table><thead><tr><th>Name</th><th>Provider</th><th>Purpose</th><th>Lifetime</th></tr></thead><tbody>
    <tr><td><code>_ga</code></td><td>Google Analytics</td><td>Tell visitors apart with a random identifier</td><td>13 months at most (390 days)</td></tr>
    <tr><td><code>_ga_«ID»</code></td><td>Google Analytics</td><td>Keep the state of the current visit</td><td>13 months at most (390 days)</td></tr>
    </tbody></table>
    <p>These lifetimes are not extended on each visit; Google’s default is 2 years and the site shortens it. Purpose: audience measurement (pages viewed, referrer, device, approximate country). The IP address is anonymised: Google Analytics 4 neither logs nor stores it. No advertising and no ad sharing: ad storage, ad personalisation and Google signals are switched off.</p>
    <p>Provider: «GOOGLE», Ireland. Data may be transferred to Google LLC in the United States under the EU–U.S. Data Privacy Framework and the European Commission’s standard contractual clauses. Retention at Google: 14 months. Legal basis: «B».</p>
    <h2>Objecting to these cookies</h2>
    <p>Block or delete cookies in your browser settings, or install the <a href="«OPTOUT»" «EXT»>Google Analytics opt-out browser add-on</a>. The site and its calculators work the same way.</p>
    </>) : (<>
    <p>The site <strong>sets no cookies</strong>. Details of the processing are in the <a href={route('privacy', lang)}>privacy policy</a>.</p>
    </>)}
    {CLARITY_ID && (<><h2>Microsoft Clarity, cookie-free</h2><p>Page stability is monitored with Microsoft Clarity in cookie-free mode: Clarity sets no cookies, each page view gets a single-use identifier, and page content and your inputs are masked. Blocking <code>clarity.ms</code> stops it.</p></>)}
    <h2>What you type</h2>
    <p>Calculations run in your browser: what you enter is sent to no server and is gone when you close the page.</p>
    <p>Questions: «MAIL». Last updated: {LAST_UPDATED}.</p>""",
    terms_h2='Personal data and cookies',
    terms_sec="""    {GA4_ID ? (<p>What you type in the calculators stays in your browser. The site sets Google Analytics audience measurement cookies (<code>_ga</code>, <code>_ga_«ID»</code>, 13 months at most), with no advertising{CLARITY_ID && '; page stability is monitored with Microsoft Clarity, cookie-free'}. Details, legal basis and how to object: <a href={route('privacy', lang)}>privacy policy</a> and <a href={route('cookies', lang)}>cookies</a> page.</p>) : (<p>What you type in the calculators stays in your browser and the site sets no cookies{CLARITY_ID && '; page stability is monitored anonymously with Microsoft Clarity, cookie-free'}. See the <a href={route('privacy', lang)}>privacy policy</a> and the <a href={route('cookies', lang)}>cookies</a> page.</p>)}""",
    terms="""    <h1>Legal notice</h1>
    <p>Information about the publisher and the conditions of use of {SITE_URL}.</p>
    <h2>Publisher</h2>
    <LegalIdentity lang={lang} />
    <p>Editor in charge: {AUTHOR_NAME}, responsible for the content published on {SITE_URL}.</p>
    <h2>Host</h2>
    <LegalIdentity mode="hosting" lang={lang} />
    <h2>Purpose of the site and no advice</h2>
    <p>The site offers free calculators and guides for information. Results are estimates based on the official rules and rates cited on each page; they are neither personal advice, nor a decision, nor a commitment by any authority. Method and limits: <a href={route('method', lang)}>method</a>.</p>
    <h2>Liability</h2>
    <p>Parameters are updated and calculations checked against reference cases, with no guarantee that errors are absent. The publisher is not liable for a decision made on an estimate alone. Please report errors through the <a href={route('contact', lang)}>contact page</a>.</p>
    <h2>Intellectual property</h2>
    <p>Texts, design and code belong to the publisher; short quotations with a link to the original page are welcome.</p>
    <h2>«H2»</h2>
«SEC»
    <h2>Reporting content</h2>
    <p>Report unlawful content to «MAIL», with the page address and the reason.</p>
    <h2>Governing law</h2>
    <p>French law. Failing an amicable settlement, the competent courts of {LEGAL.jurisdiction}. Last updated: {LAST_UPDATED}.</p>""",
)

T['de'] = dict(
    bc=dict(privacy='Datenschutz', cookies='Cookies', terms='Impressum'),
    title=dict(privacy='Datenschutzerklärung', cookies='Cookies', terms='Impressum'),
    desc=dict(
        privacy_ga='Reichweitenmessung mit Google Analytics und Cookies, ohne Werbung; Eingaben bleiben im Browser; Server-Logs des Hosters; Ihre Rechte und die Aufsichtsbehörde.',
        privacy_no='Eingaben bleiben im Browser, keine Cookies, Server-Logs des Hosters: welche Daten die Seite verarbeitet, Ihre Rechte und die zuständige Aufsichtsbehörde.',
        cookies_ga='Cookies der Reichweitenmessung von Google Analytics und sonst keine: Namen, Zweck, Laufzeit von höchstens 13 Monaten, Anbieter und Widerspruch.',
        cookies_no='Die Seite setzt keine Cookies: Ihre Eingaben bleiben in Ihrem Browser, auf Ihrem Gerät wird nichts gespeichert.',
        terms='Anbieter, inhaltlich Verantwortlicher, Hoster, keine Beratung, Urheberrecht, Datenschutz und anwendbares Recht dieser Seite.'),
    base='das berechtigte Interesse des Anbieters (Art. 6 Abs. 1 lit. f DSGVO«BASE»)',
    privacy="""    <h1>Datenschutzerklärung</h1>
    <p>Diese Seite beschreibt die Verarbeitung personenbezogener Daten bei der Nutzung von {SITE_URL} nach Art. 12 bis 14 der Verordnung (EU) 2016/679 (DSGVO)«LOI».</p>
    <h2>1. Verantwortlicher</h2>
    <LegalIdentity lang={lang} />
    <p>Fragen zu Ihren Daten: «MAIL». Ein Datenschutzbeauftragter ist nicht benannt, da die Voraussetzungen des Art. 37 DSGVO nicht vorliegen.</p>
    <h2>2. Ihre Eingaben bleiben im Browser</h2>
    <p>Die Berechnungen laufen in Ihrem Browser. Beträge, Daten und Angaben zu Ihrer Situation <strong>werden an keinen Server übertragen</strong>, nirgends gespeichert und keiner Kennung zugeordnet. Die Seite verlangt weder Konto noch Namen noch E-Mail-Adresse. Ein Teilen-Link enthält Ihre Eingaben in der Adresse der Seite: Geben Sie ihn nur an Personen Ihrer Wahl weiter.</p>
    <h2>3. Verarbeitungen</h2>
    <h3>Server-Logs des Hosters</h3>
    <p>Der Hoster speichert bei jedem Abruf IP-Adresse, Datum und Uhrzeit, die abgerufene Seite, den Browser und die verweisende Seite. Zweck: Sicherheit des Dienstes und Fehlerdiagnose. Rechtsgrundlage: «B». Dauer: nach den Richtlinien des Hosters.</p>
    {GA4_ID ? (<>
    <h3>Reichweitenmessung mit Google Analytics</h3>
    <p>Die Seite nutzt Google Analytics 4, um Besuche zu zählen und zu sehen, welche Seiten weiterhelfen: aufgerufene Seiten, verweisende Seite, Besuchsdauer, Geräte- und Browsertyp, ungefähres Land und ungefähre Stadt. Dazu setzt Google Analytics zwei Cookies auf Ihrem Gerät: <code>_ga</code>, das Besucher über eine zufällige Kennung unterscheidet, und <code>_ga_«ID»</code>, das den Stand des Besuchs speichert. Ihre Laufzeit ist auf höchstens 13 Monate (390 Tage) eingestellt und verlängert sich nicht bei jedem Besuch; Google sieht standardmäßig 2 Jahre vor.</p>
    <p>Die IP-Adresse wird anonymisiert: Google Analytics 4 protokolliert und speichert sie nicht, sondern nutzt sie nur bei der Erfassung, um Land und Stadt ungefähr zu bestimmen. Die an Google Analytics übermittelte Seitenadresse enthält keine Parameter, die Eingaben eines Teilen-Links gehen also nicht mit. Die Seite zeigt keine Werbung: Werbe-Speicherung, Werbedaten, personalisierte Anzeigen und Google-Signale sind abgeschaltet, Messdaten gehen an keinen Werbetreibenden.</p>
    <p>Zweck: Reichweitenmessung. Rechtsgrundlage: «B». Anbieter: «GOOGLE», Irland. Speicherdauer bei Google: 14 Monate für Besuchs- und Kennungsdaten, danach Löschung; es bleiben nur anonyme Summen.</p>
    </>) : (<>
    <h3>Keine Reichweitenmessung</h3>
    <p>Die Seite setzt keine Cookies und nutzt keine Analyse- oder Werbewerkzeuge.</p>
    </>)}
    {CLARITY_ID && (<>
    <h3>Technische Stabilitätsmessung mit Microsoft Clarity, ohne Cookies</h3>
    <p>Um Fehler, langsame Seiten und nicht reagierende Schaltflächen zu finden, nutzt die Seite Microsoft Clarity im cookiefreien Modus: Clarity setzt keine Cookies, jeder Seitenaufruf erhält eine eigene Kennung, Seitentext und Ihre Eingaben sind maskiert. Clarity erhält die Seitenstruktur, Klicks, Scrollen, Gerätetyp, Ladezeiten und Fehler. Zweck: Stabilität der Seite. Rechtsgrundlage: «B». Anbieter: «MS», Irland. Speicherdauer: 30 Tage für Seitenaufzeichnungen, höchstens 13 Monate für zusammengefasste Daten.</p>
    </>)}
    <h3>Nachrichten an uns</h3>
    <p>Schreiben Sie an die Kontaktadresse, werden Ihre E-Mail-Adresse und Ihre Nachricht so lange aufbewahrt, wie es für die Antwort und gegebenenfalls eine Fehlerkorrektur nötig ist, und spätestens drei Jahre nach dem letzten Austausch gelöscht. Rechtsgrundlage: «B».</p>
    <h2>4. Empfänger</h2>
    <p>Daten werden weder verkauft noch vermietet noch weitergegeben. Zugriff haben nur der Hoster{GA4_ID && ', Google Ireland Limited für Google Analytics'}{CLARITY_ID && ', Microsoft Ireland Operations Limited für Clarity'}, jeweils als Auftragsverarbeiter nach Art. 28 DSGVO. Werbenetzwerke sind auf der Seite nicht tätig.</p>
    <h2>5. Übermittlung außerhalb der Europäischen Union</h2>
    <p>Server-Logs des Hosters können in den USA verarbeitet werden.{GA4_ID && ' Daten von Google Analytics können an Google LLC in den USA übermittelt werden.'}{CLARITY_ID && ' Daten von Clarity können an die Microsoft Corporation in den USA übermittelt werden.'} Grundlage sind das EU-U.S. Data Privacy Framework und die Standardvertragsklauseln der Europäischen Kommission.</p>
«SITE»    <h2>6. Ihre Rechte</h2>
    <p>Sie haben die Rechte auf Auskunft, Berichtigung, Löschung, Einschränkung, Widerspruch und Datenübertragbarkeit nach Art. 15 bis 22 DSGVO. Schreiben Sie an «MAIL»; wir antworten innerhalb eines Monats. Ohne Benutzerkonten haben wir meist keine Daten, die Sie identifizieren; das teilen wir Ihnen dann mit.</p>
    {GA4_ID && (<p>Der Reichweitenmessung widersprechen Sie auch ohne Nachricht an uns: Blockieren oder löschen Sie Cookies in den Einstellungen Ihres Browsers, oder installieren Sie das <a href="«OPTOUT»" «EXT»>Browser-Add-on zur Deaktivierung von Google Analytics</a>. Die Seite funktioniert dann genauso.</p>)}
    {CLARITY_ID && (<p>Für die Stabilitätsmessung: Blockieren Sie die Domain <code>clarity.ms</code> im Browser oder mit einem Inhaltsblocker.</p>)}
    <p>Sie können sich bei der Aufsichtsbehörde beschweren: {LEGAL.supervisoryAuthority} (<a href={LEGAL.supervisoryAuthorityUrl} «EXT»>{LEGAL.supervisoryAuthorityUrl}</a>).«AUT»</p>
    <h2>7. Keine automatisierte Entscheidung</h2>
    <p>Ein Rechenergebnis ist eine Schätzung, die auf Ihre Anfrage aus Ihren Eingaben in Ihrem Browser entsteht. Es hat keine Rechtswirkung und ist keine automatisierte Entscheidung nach Art. 22 DSGVO. Ein Profiling findet nicht statt.</p>
    <p>Siehe auch die Seite <a href={route('cookies', lang)}>Cookies</a>. Stand: {LAST_UPDATED}.</p>""",
    cookies="""    <h1>Cookies</h1>
    {GA4_ID ? (<>
    <p>Die Seite setzt Cookies der Reichweitenmessung von Google Analytics und nur diese: keine Werbe-Cookies, keine Cookies sozialer Netzwerke. Einzelheiten stehen in der <a href={route('privacy', lang)}>Datenschutzerklärung</a>.</p>
    <h2>Gesetzte Cookies</h2>
    <table><thead><tr><th>Name</th><th>Anbieter</th><th>Zweck</th><th>Laufzeit</th></tr></thead><tbody>
    <tr><td><code>_ga</code></td><td>Google Analytics</td><td>Besucher über eine zufällige Kennung unterscheiden</td><td>höchstens 13 Monate (390 Tage)</td></tr>
    <tr><td><code>_ga_«ID»</code></td><td>Google Analytics</td><td>Stand des laufenden Besuchs speichern</td><td>höchstens 13 Monate (390 Tage)</td></tr>
    </tbody></table>
    <p>Die Laufzeiten verlängern sich nicht bei jedem Besuch; Google sieht standardmäßig 2 Jahre vor, die Seite verkürzt sie. Zweck: Reichweitenmessung (aufgerufene Seiten, Herkunft, Gerät, ungefähres Land). Die IP-Adresse wird anonymisiert: Google Analytics 4 protokolliert und speichert sie nicht. Werbung und Weitergabe zu Werbezwecken gibt es nicht: Werbe-Speicherung, personalisierte Anzeigen und Google-Signale sind abgeschaltet.</p>
    <p>Anbieter: «GOOGLE», Irland. Daten können an Google LLC in den USA übermittelt werden, auf Grundlage des EU-U.S. Data Privacy Framework und der Standardvertragsklauseln der Europäischen Kommission. Speicherdauer bei Google: 14 Monate. Rechtsgrundlage: «B».</p>
    <h2>Widerspruch</h2>
    <p>Blockieren oder löschen Sie Cookies in den Einstellungen Ihres Browsers, oder installieren Sie das <a href="«OPTOUT»" «EXT»>Browser-Add-on zur Deaktivierung von Google Analytics</a>. Die Seite und ihre Rechner funktionieren dann genauso.</p>
    </>) : (<>
    <p>Die Seite <strong>setzt keine Cookies</strong>. Einzelheiten stehen in der <a href={route('privacy', lang)}>Datenschutzerklärung</a>.</p>
    </>)}
    {CLARITY_ID && (<><h2>Microsoft Clarity, ohne Cookies</h2><p>Die Stabilität der Seiten wird mit Microsoft Clarity im cookiefreien Modus gemessen: Clarity setzt keine Cookies, jeder Seitenaufruf erhält eine Einmal-Kennung, Seiteninhalt und Ihre Eingaben sind maskiert. Wer <code>clarity.ms</code> blockiert, stoppt die Messung.</p></>)}
    <h2>Ihre Eingaben</h2>
    <p>Die Berechnungen laufen in Ihrem Browser: Was Sie eingeben, geht an keinen Server und ist nach dem Schließen der Seite verschwunden.</p>
    <p>Fragen: «MAIL». Stand: {LAST_UPDATED}.</p>""",
    terms_h2='Datenschutz und Cookies',
    terms_sec="""    {GA4_ID ? (<p>Ihre Eingaben in den Rechnern verlassen Ihren Browser nicht. Die Seite setzt Cookies der Reichweitenmessung von Google Analytics (<code>_ga</code>, <code>_ga_«ID»</code>, höchstens 13 Monate), ohne Werbung{CLARITY_ID && '; die Stabilität der Seiten wird mit Microsoft Clarity ohne Cookies gemessen'}. Einzelheiten, Rechtsgrundlage und Widerspruch: <a href={route('privacy', lang)}>Datenschutzerklärung</a> und Seite <a href={route('cookies', lang)}>Cookies</a>.</p>) : (<p>Ihre Eingaben in den Rechnern verlassen Ihren Browser nicht, und die Seite setzt keine Cookies{CLARITY_ID && '; die Stabilität der Seiten wird anonym mit Microsoft Clarity ohne Cookies gemessen'}. Siehe <a href={route('privacy', lang)}>Datenschutzerklärung</a> und Seite <a href={route('cookies', lang)}>Cookies</a>.</p>)}""",
    terms="""    <h1>Impressum</h1>
    <p>Angaben gemäß § 5 Digitale-Dienste-Gesetz (DDG) und § 18 Abs. 2 Medienstaatsvertrag (MStV) für {SITE_URL}.</p>
    <h2>Anbieter</h2>
    <LegalIdentity lang={lang} />
    <p>Inhaltlich verantwortlich nach § 18 Abs. 2 MStV: {AUTHOR_NAME}, Anschrift wie oben.</p>
    <h2>Hosting</h2>
    <LegalIdentity mode="hosting" lang={lang} />
    <h2>Zweck des Angebots und keine Beratung</h2>
    <p>Die Seite stellt kostenlose Rechner und Ratgeber zur Information bereit. Die Ergebnisse sind unverbindliche Schätzungen auf Grundlage der auf jeder Seite genannten amtlichen Regeln und Werte; sie ersetzen weder eine Beratung noch einen Bescheid. Methode und Grenzen: <a href={route('method', lang)}>Methodik</a>.</p>
    <h2>Haftung</h2>
    <p>Die Parameter werden aktualisiert und die Rechnungen an Referenzfällen geprüft; eine Gewähr für Fehlerfreiheit besteht nicht. Für Entscheidungen, die allein auf einer Schätzung beruhen, haftet der Anbieter nicht. Fehler melden Sie über die <a href={route('contact', lang)}>Kontaktseite</a>.</p>
    <h2>Urheberrecht</h2>
    <p>Texte, Gestaltung und Code gehören dem Anbieter; kurze Zitate mit Link auf die Ursprungsseite sind erlaubt.</p>
    <h2>«H2»</h2>
«SEC»
    <h2>Meldung rechtswidriger Inhalte</h2>
    <p>Rechtswidrige Inhalte melden Sie an «MAIL», mit Adresse der Seite und Grund.</p>
    <h2>Anwendbares Recht</h2>
    <p>Es gilt französisches Recht. Ohne gütliche Einigung sind die Gerichte von {LEGAL.jurisdiction} zuständig. Stand: {LAST_UPDATED}.</p>""",
)

T['es'] = dict(
    bc=dict(privacy='Privacidad', cookies='Cookies', terms='Aviso legal'),
    title=dict(privacy='Política de privacidad', cookies='Cookies', terms='Aviso legal'),
    desc=dict(
        privacy_ga='Medición de audiencia con Google Analytics y cookies, sin publicidad; los datos introducidos quedan en su navegador; registros del alojamiento; sus derechos.',
        privacy_no='Los datos introducidos quedan en su navegador, sin cookies, registros del alojamiento: los tratamientos del sitio, sus derechos y la autoridad de control.',
        cookies_ga='Cookies de medición de audiencia de Google Analytics y ninguna más: nombres, finalidad, duración máxima de 13 meses, proveedor y cómo oponerse.',
        cookies_no='El sitio no instala cookies: lo que introduce se queda en su navegador y no se guarda nada en su dispositivo.',
        terms='Titular, responsable de contenidos, alojamiento, ausencia de asesoramiento, propiedad intelectual, datos personales y ley aplicable.'),
    base='el interés legítimo del titular (art. 6.1.f RGPD«BASE»)',
    privacy="""    <h1>Política de privacidad</h1>
    <p>Esta página describe los tratamientos de datos personales ligados al uso de {SITE_URL}, conforme a los artículos 12 a 14 del Reglamento (UE) 2016/679 (RGPD)«LOI».</p>
    <h2>1. Responsable del tratamiento</h2>
    <LegalIdentity lang={lang} />
    <p>Para cualquier pregunta sobre sus datos: «MAIL». No se ha designado delegado de protección de datos, al no darse las condiciones del artículo 37 del RGPD.</p>
    <h2>2. Lo que introduce se queda en su navegador</h2>
    <p>Los cálculos se ejecutan en su navegador. Los importes, fechas y circunstancias que introduce <strong>no se envían a ningún servidor</strong>, no se guardan en ningún sitio y no se asocian a ningún identificador. El sitio no pide cuenta, nombre ni correo electrónico. Un enlace para compartir incluye sus datos en la dirección de la página: compártalo solo con quien usted elija.</p>
    <h2>3. Tratamientos realizados</h2>
    <h3>Registros del alojamiento</h3>
    <p>El proveedor de alojamiento registra en cada petición la dirección IP, la fecha y la hora, la página solicitada, el navegador y la página de procedencia. Finalidad: seguridad del servicio y diagnóstico de averías. Base jurídica: «B». Plazo: el de la política del proveedor.</p>
    {GA4_ID ? (<>
    <h3>Medición de audiencia con Google Analytics</h3>
    <p>El sitio usa Google Analytics 4 para contar las visitas y saber qué páginas resultan útiles: páginas vistas, página de procedencia, duración de la visita, tipo de dispositivo y de navegador, país y ciudad aproximados. Para ello Google Analytics instala dos cookies en su dispositivo: <code>_ga</code>, que distingue a los visitantes con un identificador aleatorio, y <code>_ga_«ID»</code>, que conserva el estado de la visita. Su duración está fijada en 13 meses como máximo (390 días) y no se prolonga en cada visita; Google prevé 2 años por defecto.</p>
    <p>La dirección IP se anonimiza: Google Analytics 4 no la registra ni la conserva, solo la usa en el momento de la recogida para deducir un país y una ciudad aproximados. La dirección de página enviada a Google Analytics va sin sus parámetros, de modo que los datos de un enlace para compartir no se incluyen. El sitio no muestra publicidad: el almacenamiento publicitario, los datos publicitarios, la personalización de anuncios y las señales de Google están desactivados, y los datos de medición no se comparten con ningún anunciante.</p>
    <p>Finalidad: medición de audiencia. Base jurídica: «B». Proveedor: «GOOGLE», Irlanda. Conservación en Google: 14 meses para los datos de visitas e identificadores, después se suprimen; solo quedan totales anónimos.</p>
    </>) : (<>
    <h3>Sin medición de audiencia</h3>
    <p>El sitio no instala cookies y no usa ninguna herramienta de analítica ni de publicidad.</p>
    </>)}
    {CLARITY_ID && (<>
    <h3>Medición técnica de la estabilidad con Microsoft Clarity, sin cookies</h3>
    <p>Para detectar errores, páginas lentas y botones que no responden, el sitio usa Microsoft Clarity en modo sin cookies: Clarity no instala cookies, cada página vista recibe un identificador propio y el texto de las páginas y sus datos quedan ocultos. Clarity recibe la estructura de la página, los clics, el desplazamiento, el tipo de dispositivo, los tiempos de carga y los errores. Finalidad: estabilidad del sitio. Base jurídica: «B». Proveedor: «MS», Irlanda. Conservación: 30 días para las grabaciones de páginas, 13 meses como máximo para los datos agregados.</p>
    </>)}
    <h3>Mensajes que nos envía</h3>
    <p>Si escribe a la dirección de contacto, su correo y su mensaje se conservan el tiempo necesario para responderle y, en su caso, corregir un error, y se suprimen como tarde tres años después del último intercambio. Base jurídica: «B».</p>
    <h2>4. Destinatarios</h2>
    <p>Ningún dato se vende, alquila ni cede. Solo acceden el proveedor de alojamiento{GA4_ID && ', Google Ireland Limited para Google Analytics'}{CLARITY_ID && ', Microsoft Ireland Operations Limited para Clarity'}, como encargados del tratamiento según el artículo 28 del RGPD. Ninguna red publicitaria interviene en el sitio.</p>
    <h2>5. Transferencias fuera de la Unión Europea</h2>
    <p>Los registros del alojamiento pueden tratarse en Estados Unidos.{GA4_ID && ' Los datos de Google Analytics pueden transferirse a Google LLC, en Estados Unidos.'}{CLARITY_ID && ' Los de Clarity pueden transferirse a Microsoft Corporation, en Estados Unidos.'} Estas transferencias se basan en el Marco de Privacidad de Datos UE-EE. UU. (EU–U.S. Data Privacy Framework) y en las cláusulas contractuales tipo de la Comisión Europea.</p>
«SITE»    <h2>6. Sus derechos</h2>
    <p>Tiene derecho de acceso, rectificación, supresión, limitación, oposición y portabilidad (artículos 15 a 22 del RGPD). Escriba a «MAIL»; respondemos en el plazo de un mes. Sin cuentas de usuario, lo habitual es que no tengamos ningún dato que le identifique, y se lo diremos.</p>
    {GA4_ID && (<p>Para oponerse a la medición de audiencia sin escribirnos: bloquee o elimine las cookies en la configuración de su navegador, o instale el <a href="«OPTOUT»" «EXT»>complemento de inhabilitación de Google Analytics</a>. El sitio funciona igual.</p>)}
    {CLARITY_ID && (<p>Para la medición de estabilidad: bloquee el dominio <code>clarity.ms</code> en su navegador o con un bloqueador de contenidos.</p>)}
    <p>Puede presentar una reclamación ante la autoridad de control: {LEGAL.supervisoryAuthority} (<a href={LEGAL.supervisoryAuthorityUrl} «EXT»>{LEGAL.supervisoryAuthorityUrl}</a>).«AUT»</p>
    <h2>7. Sin decisiones automatizadas</h2>
    <p>El resultado de un cálculo es una estimación hecha a petición suya, con sus datos, en su navegador. No produce efectos jurídicos y no es una decisión automatizada en el sentido del artículo 22 del RGPD. No se elaboran perfiles.</p>
    <p>Véase también la página de <a href={route('cookies', lang)}>cookies</a>. Última actualización: {LAST_UPDATED}.</p>""",
    cookies="""    <h1>Cookies</h1>
    {GA4_ID ? (<>
    <p>El sitio instala cookies de medición de audiencia de Google Analytics y solo esas: ninguna cookie publicitaria ni de redes sociales. El detalle de los tratamientos está en la <a href={route('privacy', lang)}>política de privacidad</a>.</p>
    <h2>Cookies instaladas</h2>
    <table><thead><tr><th>Nombre</th><th>Proveedor</th><th>Finalidad</th><th>Duración</th></tr></thead><tbody>
    <tr><td><code>_ga</code></td><td>Google Analytics</td><td>Distinguir a los visitantes con un identificador aleatorio</td><td>13 meses como máximo (390 días)</td></tr>
    <tr><td><code>_ga_«ID»</code></td><td>Google Analytics</td><td>Conservar el estado de la visita en curso</td><td>13 meses como máximo (390 días)</td></tr>
    </tbody></table>
    <p>Estas duraciones no se prolongan en cada visita; Google prevé 2 años por defecto y el sitio las reduce. Finalidad: medición de audiencia (páginas vistas, procedencia, dispositivo, país aproximado). La dirección IP se anonimiza: Google Analytics 4 no la registra ni la conserva. Sin publicidad ni cesión publicitaria: el almacenamiento publicitario, la personalización de anuncios y las señales de Google están desactivados.</p>
    <p>Proveedor: «GOOGLE», Irlanda. Los datos pueden transferirse a Google LLC, en Estados Unidos, en el marco del EU–U.S. Data Privacy Framework y de las cláusulas contractuales tipo de la Comisión Europea. Conservación en Google: 14 meses. Base jurídica: «B».</p>
    <h2>Cómo oponerse a estas cookies</h2>
    <p>Bloquee o elimine las cookies en la configuración de su navegador, o instale el <a href="«OPTOUT»" «EXT»>complemento de inhabilitación de Google Analytics</a>. El sitio y sus calculadoras funcionan igual.</p>
    </>) : (<>
    <p>El sitio <strong>no instala cookies</strong>. El detalle de los tratamientos está en la <a href={route('privacy', lang)}>política de privacidad</a>.</p>
    </>)}
    {CLARITY_ID && (<><h2>Microsoft Clarity, sin cookies</h2><p>La estabilidad de las páginas se mide con Microsoft Clarity en modo sin cookies: Clarity no instala cookies, cada página vista recibe un identificador de un solo uso y el contenido y sus datos quedan ocultos. Bloquear <code>clarity.ms</code> la detiene.</p></>)}
    <h2>Lo que introduce</h2>
    <p>Los cálculos se hacen en su navegador: lo que introduce no se envía a ningún servidor y desaparece al cerrar la página.</p>
    <p>Preguntas: «MAIL». Última actualización: {LAST_UPDATED}.</p>""",
    terms_h2='Datos personales y cookies',
    terms_sec="""    {GA4_ID ? (<p>Lo que introduce en las calculadoras no sale de su navegador. El sitio instala cookies de medición de audiencia de Google Analytics (<code>_ga</code>, <code>_ga_«ID»</code>, 13 meses como máximo), sin publicidad{CLARITY_ID && '; la estabilidad de las páginas se mide con Microsoft Clarity, sin cookies'}. Detalles, base jurídica y cómo oponerse: <a href={route('privacy', lang)}>política de privacidad</a> y página de <a href={route('cookies', lang)}>cookies</a>.</p>) : (<p>Lo que introduce en las calculadoras no sale de su navegador y el sitio no instala cookies{CLARITY_ID && '; la estabilidad de las páginas se mide de forma anónima con Microsoft Clarity, sin cookies'}. Véase la <a href={route('privacy', lang)}>política de privacidad</a> y la página de <a href={route('cookies', lang)}>cookies</a>.</p>)}""",
    terms="""    <h1>Aviso legal</h1>
    <p>Información exigida por el artículo 10 de la Ley 34/2002, de servicios de la sociedad de la información y de comercio electrónico (LSSI-CE), para {SITE_URL}.</p>
    <h2>Titular del sitio</h2>
    <LegalIdentity lang={lang} />
    <p>Responsable de los contenidos: {AUTHOR_NAME}.</p>
    <h2>Alojamiento</h2>
    <LegalIdentity mode="hosting" lang={lang} />
    <h2>Objeto del sitio y ausencia de asesoramiento</h2>
    <p>El sitio ofrece gratis calculadoras y guías con fines informativos. Los resultados son estimaciones basadas en las normas y cuantías oficiales citadas en cada página; no son asesoramiento personalizado, ni una resolución, ni un compromiso de la Administración. Método y límites: <a href={route('method', lang)}>metodología</a>.</p>
    <h2>Responsabilidad</h2>
    <p>Los parámetros se actualizan y los cálculos se comprueban con casos de referencia, sin garantía de ausencia de errores. El titular no responde de una decisión tomada solo a partir de una estimación. Los errores se comunican por la página de <a href={route('contact', lang)}>contacto</a>.</p>
    <h2>Propiedad intelectual</h2>
    <p>Textos, diseño y código pertenecen al titular; se permiten citas breves con enlace a la página de origen.</p>
    <h2>«H2»</h2>
«SEC»
    <h2>Comunicación de contenidos ilícitos</h2>
    <p>Comunique cualquier contenido ilícito a «MAIL», con la dirección de la página y el motivo.</p>
    <h2>Ley aplicable</h2>
    <p>Ley francesa. A falta de acuerdo amistoso, son competentes los tribunales de {LEGAL.jurisdiction}. Última actualización: {LAST_UPDATED}.</p>""",
)

T['nl'] = dict(
    bc=dict(privacy='Privacy', cookies='Cookies', terms='Disclaimer'),
    title=dict(privacy='Privacyverklaring', cookies='Cookies', terms='Disclaimer en colofon'),
    desc=dict(
        privacy_ga='Bezoekersmeting met Google Analytics en cookies, zonder advertenties; uw invoer blijft in uw browser; serverlogs van de host; uw rechten en de toezichthouder.',
        privacy_no='Uw invoer blijft in uw browser, geen cookies, serverlogs van de host: welke gegevens de site verwerkt, uw rechten en de bevoegde toezichthouder.',
        cookies_ga='Cookies voor bezoekersmeting van Google Analytics en verder geen: namen, doel, een looptijd van hoogstens 13 maanden, aanbieder en bezwaar.',
        cookies_no='De site plaatst geen cookies: wat u invult blijft in uw browser en er wordt niets op uw apparaat bewaard.',
        terms='Uitgever, verantwoordelijke voor de inhoud, host, geen advies, intellectueel eigendom, persoonsgegevens en toepasselijk recht.'),
    base='het gerechtvaardigd belang van de uitgever (art. 6 lid 1 sub f AVG«BASE»)',
    privacy="""    <h1>Privacyverklaring</h1>
    <p>Deze pagina beschrijft de verwerking van persoonsgegevens bij het gebruik van {SITE_URL}, op grond van de artikelen 12 tot en met 14 van Verordening (EU) 2016/679 (AVG)«LOI».</p>
    <h2>1. Verwerkingsverantwoordelijke</h2>
    <LegalIdentity lang={lang} />
    <p>Vragen over uw gegevens: «MAIL». Er is geen functionaris voor gegevensbescherming aangesteld, omdat niet aan de voorwaarden van artikel 37 AVG is voldaan.</p>
    <h2>2. Uw invoer blijft in uw browser</h2>
    <p>De berekeningen draaien in uw browser. Bedragen, data en omstandigheden die u invult <strong>worden naar geen enkele server gestuurd</strong>, nergens opgeslagen en aan geen enkele identificatie gekoppeld. De site vraagt geen account, naam of e-mailadres. Een deellink bevat uw invoer in het adres van de pagina: stuur hem alleen naar mensen die u kiest.</p>
    <h2>3. Verwerkingen</h2>
    <h3>Serverlogs van de host</h3>
    <p>De host legt bij elk verzoek het IP-adres, de datum en tijd, de opgevraagde pagina, de browser en de verwijzende pagina vast. Doel: beveiliging van de dienst en storingsonderzoek. Grondslag: «B». Bewaartermijn: volgens het beleid van de host.</p>
    {GA4_ID ? (<>
    <h3>Bezoekersmeting met Google Analytics</h3>
    <p>De site gebruikt Google Analytics 4 om bezoeken te tellen en te zien welke pagina’s helpen: bekeken pagina’s, verwijzende pagina, duur van het bezoek, type apparaat en browser, land en stad bij benadering. Daarvoor plaatst Google Analytics twee cookies op uw apparaat: <code>_ga</code>, dat bezoekers onderscheidt met een willekeurige code, en <code>_ga_«ID»</code>, dat de stand van het bezoek bewaart. De looptijd is ingesteld op hoogstens 13 maanden (390 dagen) en wordt niet bij elk bezoek verlengd; Google gaat standaard uit van 2 jaar.</p>
    <p>Het IP-adres wordt geanonimiseerd: Google Analytics 4 legt het niet vast en bewaart het niet, en gebruikt het alleen bij het verzamelen om land en stad bij benadering te bepalen. Het paginaadres dat naar Google Analytics gaat, is ontdaan van parameters, zodat de invoer uit een deellink niet wordt meegestuurd. De site toont geen advertenties: advertentieopslag, advertentiegegevens, gepersonaliseerde advertenties en Google-signalen staan uit, en meetgegevens worden met geen enkele adverteerder gedeeld.</p>
    <p>Doel: bezoekersmeting. Grondslag: «B». Aanbieder: «GOOGLE», Ierland. Bewaartermijn bij Google: 14 maanden voor gegevens op het niveau van bezoeken en codes, daarna verwijdering; alleen anonieme totalen blijven over.</p>
    </>) : (<>
    <h3>Geen bezoekersmeting</h3>
    <p>De site plaatst geen cookies en gebruikt geen analyse- of advertentietools.</p>
    </>)}
    {CLARITY_ID && (<>
    <h3>Technische stabiliteitsmeting met Microsoft Clarity, zonder cookies</h3>
    <p>Om fouten, trage pagina’s en knoppen die niet reageren op te sporen, gebruikt de site Microsoft Clarity in de modus zonder cookies: Clarity plaatst geen cookies, elke paginaweergave krijgt een eigen code en de tekst van de pagina’s en uw invoer worden afgeschermd. Clarity ontvangt de opbouw van de pagina, klikken, scrollen, type apparaat, laadtijden en fouten. Doel: stabiliteit van de site. Grondslag: «B». Aanbieder: «MS», Ierland. Bewaartermijn: 30 dagen voor paginaopnames, hoogstens 13 maanden voor samengevoegde gegevens.</p>
    </>)}
    <h3>Berichten die u ons stuurt</h3>
    <p>Schrijft u naar het contactadres, dan bewaren we uw e-mailadres en bericht zo lang als nodig is om te antwoorden en zo nodig een fout te herstellen, en verwijderen we ze uiterlijk drie jaar na het laatste contact. Grondslag: «B».</p>
    <h2>4. Ontvangers</h2>
    <p>Er worden geen gegevens verkocht, verhuurd of doorgegeven. Toegang hebben alleen de host{GA4_ID && ', Google Ireland Limited voor Google Analytics'}{CLARITY_ID && ', Microsoft Ireland Operations Limited voor Clarity'}, als verwerkers in de zin van artikel 28 AVG. Er is geen advertentienetwerk actief op de site.</p>
    <h2>5. Doorgifte buiten de Europese Unie</h2>
    <p>Serverlogs van de host kunnen in de Verenigde Staten worden verwerkt.{GA4_ID && ' Gegevens van Google Analytics kunnen worden doorgegeven aan Google LLC in de Verenigde Staten.'}{CLARITY_ID && ' Gegevens van Clarity kunnen worden doorgegeven aan Microsoft Corporation in de Verenigde Staten.'} Deze doorgifte steunt op het EU-VS-kader voor gegevensbescherming (EU–U.S. Data Privacy Framework) en de standaardcontractbepalingen van de Europese Commissie.</p>
«SITE»    <h2>6. Uw rechten</h2>
    <p>U hebt recht op inzage, rectificatie, wissing, beperking, bezwaar en overdraagbaarheid (artikelen 15 tot en met 22 AVG). Schrijf naar «MAIL»; we antwoorden binnen een maand. Zonder gebruikersaccounts hebben we meestal geen gegevens die u identificeren; dat laten we u dan weten.</p>
    {GA4_ID && (<p>Bezwaar maken tegen de bezoekersmeting kan ook zonder ons te schrijven: blokkeer of verwijder cookies in de instellingen van uw browser, of installeer de <a href="«OPTOUT»" «EXT»>browser-add-on voor het uitschakelen van Google Analytics</a>. De site werkt dan precies hetzelfde.</p>)}
    {CLARITY_ID && (<p>Voor de stabiliteitsmeting: blokkeer het domein <code>clarity.ms</code> in uw browser of met een contentblocker.</p>)}
    <p>U kunt een klacht indienen bij de toezichthouder: {LEGAL.supervisoryAuthority} (<a href={LEGAL.supervisoryAuthorityUrl} «EXT»>{LEGAL.supervisoryAuthorityUrl}</a>).«AUT»</p>
    <h2>7. Geen geautomatiseerde besluiten</h2>
    <p>Een rekenresultaat is een schatting die op uw verzoek, met uw invoer, in uw browser wordt gemaakt. Het heeft geen rechtsgevolg en is geen geautomatiseerd besluit in de zin van artikel 22 AVG. Er vindt geen profilering plaats.</p>
    <p>Zie ook de pagina <a href={route('cookies', lang)}>cookies</a>. Laatst bijgewerkt: {LAST_UPDATED}.</p>""",
    cookies="""    <h1>Cookies</h1>
    {GA4_ID ? (<>
    <p>De site plaatst cookies voor bezoekersmeting van Google Analytics en alleen die: geen advertentiecookies, geen cookies van sociale netwerken. Alle details staan in de <a href={route('privacy', lang)}>privacyverklaring</a>.</p>
    <h2>Geplaatste cookies</h2>
    <table><thead><tr><th>Naam</th><th>Aanbieder</th><th>Doel</th><th>Looptijd</th></tr></thead><tbody>
    <tr><td><code>_ga</code></td><td>Google Analytics</td><td>Bezoekers onderscheiden met een willekeurige code</td><td>hoogstens 13 maanden (390 dagen)</td></tr>
    <tr><td><code>_ga_«ID»</code></td><td>Google Analytics</td><td>De stand van het lopende bezoek bewaren</td><td>hoogstens 13 maanden (390 dagen)</td></tr>
    </tbody></table>
    <p>Deze looptijden worden niet bij elk bezoek verlengd; Google gaat standaard uit van 2 jaar en de site verkort dat. Doel: bezoekersmeting (bekeken pagina’s, herkomst, apparaat, land bij benadering). Het IP-adres wordt geanonimiseerd: Google Analytics 4 legt het niet vast en bewaart het niet. Geen advertenties en geen delen voor advertenties: advertentieopslag, gepersonaliseerde advertenties en Google-signalen staan uit.</p>
    <p>Aanbieder: «GOOGLE», Ierland. Gegevens kunnen worden doorgegeven aan Google LLC in de Verenigde Staten, op grond van het EU–U.S. Data Privacy Framework en de standaardcontractbepalingen van de Europese Commissie. Bewaartermijn bij Google: 14 maanden. Grondslag: «B».</p>
    <h2>Bezwaar tegen deze cookies</h2>
    <p>Blokkeer of verwijder cookies in de instellingen van uw browser, of installeer de <a href="«OPTOUT»" «EXT»>browser-add-on voor het uitschakelen van Google Analytics</a>. De site en de rekenhulpen werken dan precies hetzelfde.</p>
    </>) : (<>
    <p>De site <strong>plaatst geen cookies</strong>. Alle details staan in de <a href={route('privacy', lang)}>privacyverklaring</a>.</p>
    </>)}
    {CLARITY_ID && (<><h2>Microsoft Clarity, zonder cookies</h2><p>De stabiliteit van de pagina’s wordt gemeten met Microsoft Clarity in de modus zonder cookies: Clarity plaatst geen cookies, elke paginaweergave krijgt een eenmalige code en de inhoud en uw invoer worden afgeschermd. Wie <code>clarity.ms</code> blokkeert, stopt de meting.</p></>)}
    <h2>Wat u invult</h2>
    <p>De berekeningen gebeuren in uw browser: wat u invult gaat naar geen enkele server en is weg zodra u de pagina sluit.</p>
    <p>Vragen: «MAIL». Laatst bijgewerkt: {LAST_UPDATED}.</p>""",
    terms_h2='Persoonsgegevens en cookies',
    terms_sec="""    {GA4_ID ? (<p>Wat u in de rekenhulpen invult, verlaat uw browser niet. De site plaatst cookies voor bezoekersmeting van Google Analytics (<code>_ga</code>, <code>_ga_«ID»</code>, hoogstens 13 maanden), zonder advertenties{CLARITY_ID && '; de stabiliteit van de pagina’s wordt gemeten met Microsoft Clarity, zonder cookies'}. Details, grondslag en bezwaar: <a href={route('privacy', lang)}>privacyverklaring</a> en pagina <a href={route('cookies', lang)}>cookies</a>.</p>) : (<p>Wat u in de rekenhulpen invult, verlaat uw browser niet en de site plaatst geen cookies{CLARITY_ID && '; de stabiliteit van de pagina’s wordt anoniem gemeten met Microsoft Clarity, zonder cookies'}. Zie de <a href={route('privacy', lang)}>privacyverklaring</a> en de pagina <a href={route('cookies', lang)}>cookies</a>.</p>)}""",
    terms="""    <h1>Disclaimer en colofon</h1>
    <p>Gegevens van de aanbieder (artikel 3:15d BW) en gebruiksvoorwaarden van {SITE_URL}.</p>
    <h2>Uitgever</h2>
    <LegalIdentity lang={lang} />
    <p>Verantwoordelijk voor de inhoud: {AUTHOR_NAME}.</p>
    <h2>Hosting</h2>
    <LegalIdentity mode="hosting" lang={lang} />
    <h2>Doel van de site en geen advies</h2>
    <p>De site biedt gratis rekenhulpen en uitleg ter informatie. De uitkomsten zijn schattingen op basis van de officiële regels en bedragen die op elke pagina worden genoemd; ze zijn geen persoonlijk advies, geen besluit en geen toezegging van een instantie. Methode en grenzen: <a href={route('method', lang)}>methode</a>.</p>
    <h2>Aansprakelijkheid</h2>
    <p>De parameters worden bijgewerkt en de berekeningen getoetst aan referentiegevallen, zonder garantie dat ze foutloos zijn. De uitgever is niet aansprakelijk voor een beslissing die alleen op een schatting berust. Fouten meldt u via de <a href={route('contact', lang)}>contactpagina</a>.</p>
    <h2>Intellectueel eigendom</h2>
    <p>Teksten, vormgeving en code zijn eigendom van de uitgever; korte citaten met een link naar de oorspronkelijke pagina zijn toegestaan.</p>
    <h2>«H2»</h2>
«SEC»
    <h2>Melden van onrechtmatige inhoud</h2>
    <p>Meld onrechtmatige inhoud aan «MAIL», met het adres van de pagina en de reden.</p>
    <h2>Toepasselijk recht</h2>
    <p>Frans recht. Bij gebreke van een minnelijke regeling zijn de rechters van {LEGAL.jurisdiction} bevoegd. Laatst bijgewerkt: {LAST_UPDATED}.</p>""",
)

# Section « données personnelles » d'une page de mentions existante, toutes langues.
SECTION_DONNEES = re.compile(
    r'(cookie|donn[ée]es personnelles|renseignements personnels|t[ée]moins'
    r'|personal (data|information)|cookies and personal|privacy and cookies|data protection'
    r'|datenschutz|daten und cookies|cookies und daten'
    r'|datos personales|privacidad y cookies|cookies y datos|persoonsgegevens|privacy en cookies)', re.I)


def remplir(txt, lang, region):
    r = REG[lang].get(region, REG[lang][''])
    base = T[lang]['base'].replace('«BASE»', r['base'])
    out = (txt.replace('«B»', base).replace('«LOI»', r['loi']).replace('«AUT»', r['aut'])
              .replace('«ID»', ID).replace('«MAIL»', MAIL).replace('«OPTOUT»', GA_OPTOUT)
              .replace('«EXT»', EXT).replace('«GOOGLE»', GOOGLE_IE).replace('«MS»', MS_IE))
    if lang == 'fr' and region == 'CA':
        # Français du Canada : « témoin » (OQLF) ; les identifiants de route restent en anglais.
        out = re.sub(r"(?<!['/_])\bcookies\b(?!['/])", 'témoins', out)
        out = re.sub(r"(?<!['/_])\bcookie\b(?!['/])", 'témoin', out)
        out = re.sub(r"(?<!['/_])\bCookies\b(?!['/])", 'Témoins', out)
        out = out.replace('<h1>Témoins</h1>', '<h1>Témoins (cookies)</h1>')
    return out


def imports(depth, body):
    up = '../' * depth
    noms = [n for n in ('AUTHOR_NAME', 'CLARITY_ID', 'CONTACT_EMAIL', 'GA4_ID', 'LAST_UPDATED', 'LEGAL',
                        'SITE_NAMES', 'SITE_URL') if re.search(r'\b' + n + r'\b', body) or n in ('GA4_ID', 'CLARITY_ID', 'SITE_NAMES')]
    lignes = [f"import PageLayout from '{up}layouts/PageLayout.astro';"]
    if 'LegalIdentity' in body:
        lignes.append(f"import LegalIdentity from '{up}components/LegalIdentity.astro';")
    exports = set(re.findall(r'export const (\w+)', lire('src/data/site-config.ts')))
    absents = [n for n in noms if n not in exports and n in ('CLARITY_ID', 'GA4_ID')]
    noms = [n for n in noms if n not in absents]
    lignes.append(f"import {{ {', '.join(noms)} }} from '{up}data/site-config';")
    # Site ancien sans CLARITY_ID (ou GA4_ID) dans site-config : la mesure correspondante n'existe pas.
    lignes += [f"const {n} = '';" for n in absents]
    lignes.append(f"import {{ route }} from '{up}i18n/routes';")
    return '\n'.join(lignes)


def page(lang, kind, region, depth, body):
    t = T[lang]
    titre = remplir(t['title'][kind], lang, region)
    bc = remplir(t['bc'][kind], lang, region)
    if kind == 'terms':
        desc = f"'{t['desc']['terms']}'"
    else:
        desc = f"GA4_ID ? '{t['desc'][kind + '_ga']}' : '{t['desc'][kind + '_no']}'"
    desc = remplir(desc, lang, region)
    return ("---\n" + imports(depth, body) + f"\nconst lang = '{lang}';\n"
            f"const title = `{titre} – ${{SITE_NAMES[lang]}}`;\n"
            f"const description = {desc};\n"
            "---\n"
            "{/* Page générée par scripts/gen-legal-pages.py (trame, décision GA4 du 2026-10-17). Ne pas\n"
            "     retoucher à la main : relancer le script. Un passage propre au site se garde entre\n"
            "     les marqueurs site:debut et site:fin. */}\n"
            "<PageLayout title={title} description={description} lang={lang} noindex={true} "
            f"breadcrumbs={{[{{ label: '{bc}' }}]}} showAuthor={{false}}>\n"
            '  <div class="prose prose-slate max-w-none">\n' + body + "\n  </div>\n</PageLayout>\n")


def bloc_site(ancien):
    m = re.search(r'[ \t]*\{/\* site:debut \*/\}[\s\S]*?\{/\* site:fin \*/\}\n?', ancien or '')
    return m.group(0) if m else ''


def section_terms(lang, region):
    t = T[lang]
    return (f"    <h2>{remplir(t['terms_h2'], lang, region)}</h2>\n"
            + remplir(t['terms_sec'], lang, region))


def patch_terms(src, lang, region):
    """Remplace la section « données personnelles » d'une page de mentions existante.
    Renvoie (nouveau_source, mode) ; mode = 'section' | 'ajout' | 'deja'."""
    sec = section_terms(lang, region)
    if 'gen-legal-pages:terms' in src:
        nouveau = re.sub(r'[ \t]*\{/\* gen-legal-pages:terms \*/\}[\s\S]*?\{/\* /gen-legal-pages:terms \*/\}',
                         lambda _: '    {/* gen-legal-pages:terms */}\n' + sec + '\n    {/* /gen-legal-pages:terms */}', src)
        return nouveau, 'deja'
    marque = '    {/* gen-legal-pages:terms */}\n' + sec + '\n    {/* /gen-legal-pages:terms */}\n'
    for m in re.finditer(r'[ \t]*<h2[^>]*>([\s\S]*?)</h2>', src):
        if SECTION_DONNEES.search(re.sub(r'<[^>]+>', '', m.group(1))):
            fin = re.search(r'\n[ \t]*<h2|\n[ \t]*</div>\s*\n?\s*</PageLayout>', src[m.end():])
            stop = m.end() + fin.start() + 1 if fin else len(src)
            return src[:m.start()] + marque + src[stop:], 'section'
    # Pas de section : avant le dernier <h2> (droit applicable, en général).
    h2s = list(re.finditer(r'\n[ \t]*<h2', src))
    if h2s:
        k = h2s[-1].start() + 1
        return src[:k] + marque + src[k:], 'ajout'
    k = src.rfind('</div>')
    return src[:k] + marque + '  ' + src[k:], 'ajout'


def ajoute_imports(src, depth):
    """Ajoute à la page de mentions les noms qu'utilise la section (GA4_ID, CLARITY_ID, route)."""
    up = '../' * depth
    fm = src.split('---', 2)
    if len(fm) < 3:
        return src
    tete = fm[1]
    m = re.search(r"import\s*\{([^}]*)\}\s*from\s*'[./]*data/site-config(\.ts)?';", tete)
    exports = set(re.findall(r'export const (\w+)', lire('src/data/site-config.ts')))
    besoin = {n for n in ('GA4_ID', 'CLARITY_ID', 'CONTACT_EMAIL') if n in exports}
    absents = [n for n in ('GA4_ID', 'CLARITY_ID') if n not in exports and not re.search(r'const ' + n + r'\b', tete)]
    if m:
        noms = {n.strip() for n in m.group(1).split(',') if n.strip()}
        tete = tete.replace(m.group(0), m.group(0).replace(m.group(1), ' ' + ', '.join(sorted(noms | besoin)) + ' '))
    else:
        tete += f"import {{ {', '.join(sorted(besoin))} }} from '{up}data/site-config';\n"
    if not re.search(r'\broute\b', tete):
        tete += f"import {{ route }} from '{up}i18n/routes';\n"
    tete += ''.join(f"const {n} = '';\n" for n in absents)
    return '---' + tete + '---' + fm[2]


BLOC_GA4 = re.compile(r'(?:[ \t]*\{/\*[^*]*?(?:GA4|régime)[\s\S]*?\*/\}\n)*[ \t]*\{GA4_ID && [\s\S]*?</>\)\}\n(?:[ \t]*\{/\*[^*]*?GA4[\s\S]*?\*/\}\n[ \t]*\{GA4_ID && [\s\S]*?</>\)\}\n)?')


def patch_layout():
    """Remplace le(s) bloc(s) GA4 du BaseLayout du site par ceux de la trame, sans toucher au reste."""
    f = os.path.join(SITE, 'src/layouts/BaseLayout.astro')
    if not os.path.isfile(f) or not os.path.isfile(TRAME_LAYOUT):
        sys.exit(f'gen-legal-pages --layout : {f} ou {TRAME_LAYOUT} introuvable')
    trame = BLOC_GA4.search(open(TRAME_LAYOUT, encoding='utf-8').read())
    src = open(f, encoding='utf-8').read()
    site = BLOC_GA4.search(src)
    if not trame or not site:
        sys.exit('gen-legal-pages --layout : bloc {GA4_ID && …} introuvable ; reporter le bloc GA4 de la trame à la main.')
    if site.group(0) == trame.group(0):
        print('  src/layouts/BaseLayout.astro : bloc GA4 déjà celui de la trame')
        return
    nouveau = src[:site.start()] + trame.group(0) + src[site.end():]
    if 'CONSENT_MODE' not in re.search(r'^---[\s\S]*?---', nouveau).group(0):
        sys.exit('gen-legal-pages --layout : CONSENT_MODE non importé dans le layout ; à reprendre à la main.')
    if DRY:
        print('  (essai) src/layouts/BaseLayout.astro : bloc GA4 remplacé par celui de la trame')
        return
    open(f, 'w', encoding='utf-8').write(nouveau)
    print('  src/layouts/BaseLayout.astro : bloc GA4 remplacé par celui de la trame')


def main():
    if not os.path.isdir(os.path.join(SITE, 'src')):
        sys.exit(__doc__)
    ga4, tags = config()
    if not ga4 and not FORCE:
        print(f'gen-legal-pages : GA4_ID vide dans {SITE}/src/data/site-config.ts — pages en place laissées telles quelles '
              f'(elles sont exactes sans GA4). --force pour écrire quand même les pages types.')
        return
    if LAYOUT:
        patch_layout()
    locales, chemins = routes()
    if not locales:
        sys.exit('gen-legal-pages : LOCALES introuvable dans src/i18n/routes.ts')
    defaut_region = next((tags[l].split('-')[1] for l in locales if '-' in tags.get(l, '')), '')
    ecrits, ignores = [], []
    for lang in locales:
        if lang not in T:
            ignores.append(lang)
            continue
        tag = tags.get(lang, lang)
        region = tag.split('-')[1].upper() if '-' in tag else defaut_region
        for kind in ('privacy', 'cookies', 'terms'):
            chemin = chemins.get((kind, lang))
            if not chemin:
                ignores.append(f'{lang}:{kind} (route absente de routes.ts)')
                continue
            f = fichier(chemin)
            depth = os.path.relpath(f, os.path.join(SITE, 'src')).count(os.sep)
            ancien = open(f, encoding='utf-8').read() if os.path.isfile(f) else ''
            if kind == 'terms' and ancien and 'gen-legal-pages.py (trame' not in ancien:
                src, mode = patch_terms(ancien, lang, region)
                src = ajoute_imports(src, depth)
                ecrits.append((f, src, f'section « données personnelles » ({mode})'))
                continue
            body = remplir(T[lang][kind], lang, region)
            if kind == 'terms':
                body = body.replace('    <h2>«H2»</h2>\n«SEC»',
                                    '    {/* gen-legal-pages:terms */}\n' + section_terms(lang, region) + '\n    {/* /gen-legal-pages:terms */}')
            bloc = bloc_site(ancien)
            body = body.replace('«SITE»', bloc)
            neuf = page(lang, kind, region, depth, body)
            # Un modèle sans «SITE» (mentions) ne doit pas perdre le passage propre au site ni ses imports
            # (rentindexer.com, 2026-10-24 : bloc licences effacé sur 5 pages).
            if bloc and bloc.strip() not in neuf:
                neuf = neuf.replace('\n  </div>\n</PageLayout>\n', '\n' + bloc.rstrip('\n') + '\n  </div>\n</PageLayout>\n', 1)
            if ancien.startswith('---\n'):
                fm = ancien.split('---\n', 2)[1]
                manquants = [l for l in fm.splitlines() if l.startswith('import ') and l not in neuf]
                if manquants:
                    neuf = neuf.replace('---\n', '---\n' + '\n'.join(manquants) + '\n', 1)
            ecrits.append((f, neuf, 'page entière'))
    for f, src, quoi in ecrits:
        rel = os.path.relpath(f, SITE)
        if DRY:
            print(f'  (essai) {rel} : {quoi}')
            continue
        os.makedirs(os.path.dirname(f), exist_ok=True)
        open(f, 'w', encoding='utf-8').write(src)
        print(f'  {rel} : {quoi}')
    print(f'gen-legal-pages : {len(ecrits)} page(s) {"à écrire" if DRY else "écrite(s)"}, GA4 {ga4 or "absent"}'
          + (f' ; non gérées, à rédiger à la main : {", ".join(ignores)}' if ignores else ''))


if __name__ == '__main__':
    main()
