"""Contrôle SEO d'un site construit, contre les cibles du plan d'exécution 2026.

Usage : python3 _template/scripts/check-seo.py <dossier-site> [--verbose]

Cibles (§2.2, §2.3 et §2.5 du plan) :
  - <title> entre 50 et 60 caractères, <meta description> entre 150 et 160
    (japonais, coréen, chinois : 24 à 40 et 70 à 120, un caractère plein valant deux lettres)
  - nom du pays en tête de titre quand il y figure (RECETTE-SITE.md §6)
  - page pilier : au moins 3 liens vers des sources officielles (RECETTE-SITE.md §7)
  - page pilier (accueil d'une langue) : 2 000 à 3 000 mots
  - guides et outils secondaires       : 1 200 à 1 800 mots
  - pages « par montant »              : 500 à 700 mots + un tableau
  - pages « outil » (§2.2)             : 500 à 700 mots, declarees par `data-outil`
  - FAQ, méthodologie, à propos, widget : pas de cible de longueur
Les pages noindex sont ignorées.
"""
import re, glob, html, sys, os

site = sys.argv[1].rstrip('/')

# Astro sort dans `dist/`, Next en export statique dans `out/`. Sans ce choix, les
# cinq sites Next du portefeuille rendaient « 0 page, 0 a corriger » : un echec
# deguise en succes.
# Les dossiers d'archive ne sont pas servis : les compter reviendrait a auditer
# un site fantome, et fausserait l'unicite autant que le compte de pages.
ARCHIVES = ('_archives/', '/archive/', '/old/', '/backup/')
# Le dossier servi ne s'appelle pas toujours `dist` : salaryafter.com publie
# depuis `docs/` (usage GitHub Pages) et calorierule.com depuis `output/`. Ne
# connaitre que dist et out faisait mesurer le depot entier, chemins `/output/...`
# compris, et rendait le compte de defauts faux sur ces sites (2026-09-26).
# Quand deux candidats coexistent — un `dist/` obsolete laisse par Vite et le
# `docs/` que le generateur remplit vraiment — c'est celui qui porte le plus de
# pages qui est servi.
SORTIES = ('dist', 'out', 'build', 'docs', 'output', '_site', 'www')


def _compte_pages(chemin):
    n = 0
    for racine, _, fichiers in os.walk(chemin):
        n += sum(1 for f in fichiers if f.endswith('.html'))
    return n


_candidats = [d for d in SORTIES
              if os.path.isdir(f'{site}/{d}') and os.path.isfile(f'{site}/{d}/index.html')]
if _candidats:
    sortie = max(_candidats, key=lambda d: _compte_pages(f'{site}/{d}'))
else:
    sortie = '' if os.path.isfile(f'{site}/index.html') else 'dist'
verbose = '--verbose' in sys.argv
PRIMAIRES = []  # renseigne plus bas (sources_officielles.primaires_du_site)

# Pages de service : pas de cible de longueur (plan §2.2, lignes 5 à 8).
SERVICE = re.compile(
    # Finnois (fi-laskurit, 2026-10-05)
    r'/[a-z-]*(tietoa|laskentatapa|yhteystiedot|toimitusperiaatteet|tietosuoja|kayttoehdot|evasteet|upota-laskuri|faq|questions|preguntas|veelgestelde|haeufige|about|a-propos|ueber-uns|over-ons|'
    r'sobre-nosotros|sobre(?=/|$)|methodology|methodik|methodologie|methode|metodologia|method|widget|'
    # pages légales : ni cible de longueur ni sources officielles (même liste que check-trame)
    # « disclaimer » : page de confiance comme les mentions légales. Lui imposer
    # 2 000 mots pousserait à diluer un avertissement, qui vaut par sa brièveté
    # (taxfreesalaries.com, 2026-09-25).
    # Italien : mêmes pages de service que check-trame, qui les reconnaissait déjà ;
    # check-seo reprochait à « chi siamo » ses 300 mots (lohnnetto.ch, 2026-10-03).
    # « metodo » (it) : même page de confiance que /method/, qui l'était déjà ; check-trame
    # la reconnaissait, check-seo lui demandait 1 200 mots (it-calendario-ponti, 2026-10-28).
    r'chi-siamo|contatti|metodo(?=/|$)|glossario|note-legali|protezione-dati|domande-frequenti|glosario|o-nas|regulamin|polityka-prywatnosci|polityka-redakcyjna|slownik|'
    r'impressum|mentions|aviso|colofon|legal|privacy|datenschutz|confidentialite|privacidad|'
    r'disclaimer|haftungsausschluss|'
    # « cgu » : abréviation française de conditions générales d'utilisation, page de service
    # au même titre que /terms/ (cartegrisesimple.fr, 2026-09-20)
    # « agb » en allemand et « protection-donnees » en francais sont les memes
    # pages de service que /terms/ et /confidentialite/ (salairenet.ch, 2026-09-27).
    r'cgu|cgv|agb|protection-donnees|proteccion-datos|'
    # « cookies » au pluriel seulement ne reconnaissait pas /cookie-policy/, qui est
    # la meme page de service (calcolalordonetto.it, 2026-09-26).
    # « newsletter » : page d'inscription a une lettre, page de service comme /contact/.
    # Lui imposer 2 000 mots reviendrait a noyer un formulaire d'inscription dans un
    # article (epargnemalin.fr, 2026-09-27).
    r'newsletter|abonnement|inscription|subscribe|'
    r'privacidade|cookie|terms|conditions|nutzungsbedingungen|terminos|termos|contact|editorial|'
    # « sources » : la page qui liste les references du site est une page de
    # confiance au meme titre que la methodologie. Lui imposer une cible de
    # 1 200 mots obligerait a diluer une liste de references, c'est-a-dire a
    # degrader exactement ce qu'elle sert a rendre verifiable.
    r'sources|fuentes|fontes|quellen|bronnen|kaellor|'
    # Italien : les noms de pages de service manquaient a la liste, si bien que
    # « chi-siamo », « contatti », « termini » et « aggiornamenti » etaient
    # comptes comme pages piliers et sommes de faire 2 000 mots
    # (calcolalordonetto.it, 2026-09-26). « aggiornamenti », comme un journal des
    # modifications, vaut par sa precision et non par sa longueur.
    r'chi-siamo|contatti|termini|aggiornamenti|note-legali|informativa|'
    # Et les equivalents suedois, neerlandais et portugais du meme registre.
    r'om-oss|kontakt|villkor|integritetspolicy|contacto|contato|actualizaciones|'
    # Norvegien, danois et neerlandais : ordliste, metode, redaksjonell policy, om os,
    # woordenlijst… sont les memes pages de confiance que glossary et methodology
    # (lonnetterskatt.no, 2026-09-27).
    r'ordliste|ordbog|metode|redaksjonell|redaktionel|personvern|privatliv|vilkar|vilkaar|'
    r'informasjonskapsler|om-os|woordenlijst|redactie|'
    r'atualizacoes|nyheter|updates|glossar|glossario|glossaire|glossary|ordlista|'
    # Turc et indonésien : mêmes pages de service que check-trame (tr-bayram, id-kalender,
    # 2026-10-28 ; tr-bayram avait allongé « yontem » et « hakkimizda » pour passer).
    r'yasal-bilgiler|gizlilik|cerezler|hakkimizda|yontem(?=/|$)|iletisim|yayin-ilkeleri|kullanim-kosullari|'
    r'tentang-kami|privasi|kebijakan-privasi|ketentuan|syarat-ketentuan|kontak|kebijakan-redaksi)',
    re.I)
# Page de longue traîne « par montant » (ou par ancienneté, cf. AU) : un segment
# d'URL portant un nombre. Les millésimes (2024-2030) sont exclus, sinon un slug
# comme « sozialabgaben-2026 » serait pris pour un montant.
ENUM = (r'things|reasons|steps|tips|mistakes|erreurs|astuces|etapes|raisons|conseils|'
        r'choses|fehler|tipps|schritte|gruende|errores|consejos|pasos|razones|'
        r'erros|dicas|passos|motivos|errori|consigli|passi|motivi')
AMOUNT = re.compile(
    # Le nombre d'une page par montant est un mot a lui seul : « /2000-euros/ ».
    # Colle a des lettres, c'est un nom, pas une somme : « /guide/sp500/ » se
    # voyait reclamer un tableau de montants (rightetf.com, 2026-09-26).
    r'(?<![a-z0-9])(?!20[2-3]\d(?!\d))\d{3,}'
    r'|-\d{1,2}-(?:years?|ans|jahre)'
    # Une page par valeur commence par son nombre : « 10-cm-to-inches ». Le
    # millésime seul et les titres d'énumération sont écartés.
    r'|/(?!20[2-3]\d(?:/|$))\d{1,3}(?:[.,]\d+)?-(?!(?:' + ENUM + r')\b)')

# Plancher de mots par type (plan §2.3). Le plafond n'est pas contrôlé : dépasser
# la cible n'est pas un défaut, seul le contenu trop mince en est un.
TARGETS = {'pilier': 2000, 'guide': 1200, 'montant': 500, 'index': 800, 'outil': 500}

# Sources officielles de la page pilier (RECETTE §7, §26 du 2026-10-16) : la liste est
# partagée avec check-regles.py — sources_officielles.py + sources-officielles.txt, à côté
# de ce script. Libellés publics (gov, gouv, gob, govt, gv), suffixes publics (gc.ca, admin.ch,
# bund.de, europa.eu…), liste par pays, et sources propres au site dans
# `scripts/sources-primaires.txt` (un domaine par ligne, chacun précédé d'une ligne de
# commentaire qui dit pourquoi il fait autorité — sans lui, le contrôle s'arrête).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sources_officielles
PRIMAIRES = sources_officielles.primaires_du_site(site, strict=True)

# La regle « le titre ne s'ouvre pas sur le pays » vise « France Salaire
# Calculateur ». Elle se trompe quand l'adjectif de nationalite fait partie d'un
# nom propre : « Australian Shepherd », « Berger Allemand », « Italian Greyhound »
# sont les mots que la personne tape, et les deplacer nuirait. Un site declare
# donc ses prefixes legitimes dans `scripts/titres-exceptions.txt`, un par ligne,
# chacun precede d'un commentaire disant pourquoi. Le commentaire est obligatoire :
# sans lui, la liste redevient un moyen de faire taire le controle.
def _titres_exceptions(racine):
    chemin = os.path.join(racine, 'scripts', 'titres-exceptions.txt')
    if not os.path.isfile(chemin):
        return ()
    prefixes, justifie = [], False
    for ligne in open(chemin, encoding='utf-8'):
        ligne = ligne.strip()
        if not ligne:
            continue
        if ligne.startswith('#'):
            justifie = True
            continue
        if not justifie:
            sys.exit(f"{chemin} : « {ligne} » sans commentaire de justification.\n"
                     "Chaque prefixe doit dire pourquoi il est legitime en tete de titre.")
        prefixes.append(ligne.lower())
        # Un commentaire couvre le bloc qui le suit : exiger une justification par
        # ligne n'aurait pas de sens pour une liste homogene de trente-six races.
        # La ligne vide referme le bloc et redemande une justification.
    return tuple(prefixes)


EXCEPTIONS_TITRE = _titres_exceptions(site)


from snippets_regles import COUNTRY, GENERIC_START  # listes partagees avec check-snippets.py


# §21 : citabilite par les assistants. Un paragraphe cite doit se suffire a
# lui-meme une fois extrait de la page. L'etude SE Ranking situe les passages
# repris entre 134 et 167 mots et montre que 44 % des citations proviennent des
# 30 premiers pour cent de la page. On retient le plancher plutot que la
# fourchette : un paragraphe plus long reste extractible, un paragraphe de
# quinze mots ne l'est jamais.
#
# La longueur du premier paragraphe n'est volontairement pas controlee. Mesuree
# sur le portefeuille le 2026-09-22, la cible de 40 a 60 mots echouait sur 96 a
# 99 % des pages de tous les sites, y compris les meilleurs : le premier <p> est
# presque toujours un chapeau ou une signature, pas la reponse. Une regle qui
# signale tout ne distingue rien.
CITABLE_MIN = 120
PART_HAUTE = 0.30
_HORS_CORPS = re.compile(r'<(script|style|nav|header|footer|aside)\b.*?</\1>', re.S | re.I)
_PARA = re.compile(r'<p\b[^>]*>(.*?)</p>', re.S | re.I)


# Le japonais n'ecrit pas d'espaces : compter les mots en decoupant sur l'espace
# donnait 213 « mots » pour une page entiere de 3 750 caracteres, aussi fournie que
# ses versions francaise et anglaise. Un caractere japonais ou chinois porte environ
# deux lettres et demie de texte latin, et le coreen se comporte de meme une fois
# ses particules comptees. Sur ces langues, la longueur se mesure donc en caracteres
# ramenes a un equivalent-mot (pensionretraite.com, 2026-09-27).
CAR_PAR_MOT = 2.5


def _mots(texte: str, cjk: bool = False) -> int:
    if cjk:
        return int(len(re.sub(r'\s', '', texte)) / CAR_PAR_MOT)
    return len(texte.split())


def paragraphes(doc: str, cjk: bool = False) -> list[int]:
    """Longueurs en mots des paragraphes du corps, dans l'ordre de lecture."""
    corps = _HORS_CORPS.sub(' ', doc)
    out = []
    for m in _PARA.finditer(corps):
        t = html.unescape(re.sub(r'<[^>]+>', ' ', m.group(1)))
        n = _mots(t, cjk)
        if n >= 8:
            out.append(n)
    return out


def main_words(doc: str, cjk: bool = False) -> int:
    m = re.search(r'<main[^>]*>(.*?)</main>', doc, re.S)
    t = m.group(1) if m else doc
    t = re.sub(r'<script.*?</script>', '', t, flags=re.S)
    t = re.sub(r'<[^>]+>', ' ', t)
    return _mots(t, cjk)


def kind(path: str) -> str:
    if SERVICE.search(path):
        return 'service'
    if path.strip('/').count('/') == 0:          # /de/, /en/ … : page pilier
        return 'pilier'
    return 'montant' if AMOUNT.search(path) else 'guide'


rows, flagged, titres = [], 0, []
# Une page dont le chemin est le parent d'autres pages est un INDEX : son role
# est d'orienter, pas de traiter un sujet au fond. Lui imposer les 2 000 mots
# d'une page pilier ne produit que du remplissage, et du remplissage nuit
# (retour du 21/09/2026 : « pas besoin d'ajouter pour ajouter, ça peut être pire »).
_fichiers = sorted(x for x in glob.glob(f'{site}/{sortie}/**/index.html', recursive=True)
                   if not any(a in x for a in ARCHIVES))
_chemins = {('/' + os.path.relpath(os.path.dirname(x), f'{site}/{sortie}').replace(os.sep, '/') + '/')
            .replace('/./', '/') for x in _fichiers}


def est_index(path: str) -> bool:
    return path != '/' and any(c != path and c.startswith(path) for c in _chemins)


for f in _fichiers:
    doc = open(f, encoding='utf-8').read()
    if 'content="noindex' in doc:
        continue
    path = '/' + os.path.relpath(os.path.dirname(f), f'{site}/{sortie}').replace(os.sep, '/').strip('/') + '/'
    if path in ('//', '/./'):
        # Racine : on ne la saute que si c'est une redirection de langue. Un site sans
        # préfixe (plantcare101.com, 2026-10-04) a sa vraie page d'accueil ici.
        if re.search(r'http-equiv=["\']refresh["\']', doc, re.I):
            continue
        path = '/'
    # Une page de redirection n'est pas une page : elle ne porte ni texte ni
    # sources, et son canonique designe la page d'arrivee. La compter revenait a
    # reprocher a rightetf.com une page pilier de 33 mots (2026-09-26).
    if re.search(r'http-equiv=["\']refresh["\']', doc, re.I):
        continue

    t = re.search(r'<title>(.*?)</title>', doc, re.S)
    t = html.unescape(t.group(1)) if t else ''
    d = re.search(r'name="description" content="(.*?)"', doc, re.S)
    d = html.unescape(d.group(1)) if d else ''
    # Japonais, coréen, chinois : un caractère plein porte autant qu'environ deux lettres
    # latines et Google tronque bien plus tôt. Cibles adaptées (règle du 2026-09-20).
    cjk = re.search(r'<html[^>]*\blang="(ja|ko|zh)', doc, re.I) is not None
    w, k = main_words(doc, cjk), kind(path)

    flags = []
    tmin, tmax, dmin, dmax = (24, 40, 70, 120) if cjk else (50, 60, 150, 160)
    if not tmin <= len(t) <= tmax:
        flags.append(f'titre {len(t)}∉[{tmin},{tmax}]')
    if not dmin <= len(d) <= dmax:
        flags.append(f'description {len(d)}∉[{dmin},{dmax}]')
    # §11 (règle du 2026-09-19) : le titre s'ouvre sur le TERME-CLÉ de la page (ARE, Brutto-Netto,
    # Paro, WW, EI, Final Pay…), puis le pays, puis le reste. Jamais sur le pays, un mot d'outil
    # (calculateur, Rechner…), un mot de rubrique (à propos, FAQ…) ou une question.
    first = t.strip().lower()
    if first.startswith(tuple(c.lower() for c in COUNTRY)) \
            and not first.startswith(EXCEPTIONS_TITRE):
        flags.append('titre ouvert par le pays : le terme-clé passe avant')
    elif GENERIC_START.match(first):
        flags.append(f'titre ouvert par un mot générique « {t.split()[0]} » : le terme-clé passe avant')
    # E-E-A-T : la page pilier cite au moins trois textes officiels.
    if k == 'pilier':
        n_src = len(sources_officielles.urls_officielles(doc, PRIMAIRES))
        if n_src < 3:
            flags.append(f'{n_src} source(s) officielle(s) < 3')
    # Une page parente est un index a toute profondeur, pas seulement a la racine :
    # /fr/categories/ oriente vers ses vingt-quatre categories exactement comme
    # /fr/ oriente vers le site. La condition sur « pilier » reservait la regle au
    # premier niveau, si bien qu'une page de sommaire a un niveau de plus se voyait
    # demander les 1 200 mots d'un guide, c'est-a-dire du remplissage
    # (rightetf.com, /fr/categories/, /fr/guide/, /fr/blog/, 2026-09-26).
    cible = 'index' if (k in ('pilier', 'guide') and est_index(path)) else k
    # Un sommaire n'est pas toujours le parent des pages qu'il liste : sur un site
    # de calculateurs, /rechner/ oriente vers quarante outils qui vivent a la racine,
    # et aucun chemin ne le trahit. Lui demander les 2 000 mots d'une page pilier
    # revenait a ecrire un article autour d'une grille de liens. Le site le declare
    # en posant `data-sommaire` sur cette grille, dans `<main>` ; sans la marque, la
    # regle d'origine s'applique (bruttonettorechnen.de, 2026-09-27).
    if k in ('pilier', 'guide') and cible != 'index' \
            and re.search(r'<main[^>]*>.*?data-sommaire', doc, re.S):
        cible = 'index'
    # Une page dont le contenu principal EST l'outil, screener, comparateur,
    # simulateur, ne se juge pas comme un guide : le §2.2 lui demande d'expliquer
    # ce qu'elle calcule, sur quelles donnees et avec quelles limites, soit la
    # meme substance qu'une page par montant, pas 1 200 mots d'article autour d'un
    # formulaire. Le site le declare, en posant `data-outil` sur son cadre, faute
    # de quoi la regle d'origine s'applique (rightetf.com, 2026-09-26).
    # La regle vaut aussi pour une page a la racine qui n'est pas la page d'accueil :
    # sur un site de calculateurs, /calculadora-inss/ est un outil et non la page
    # pilier du site. Seules les racines de langue restent des piliers, parce que
    # ce sont elles qui portent le sujet du site (calculosalarial.com, 2026-09-26).
    racine_de_langue = path == '/' or re.fullmatch(r'/[a-z]{2}(-[a-z]{2})?/', path)
    if cible in ('guide', 'pilier') and not racine_de_langue \
            and re.search(r'<main[^>]*>.*?data-outil', doc, re.S):
        cible = 'outil'
    # Japonais, coreen, chinois : la meme regle que pour le titre vaut pour la
    # longueur du corps. Le japonais n'ecrit pas d'espaces, si bien qu'une page
    # entiere se comptait en deux cents « mots », et le coreen en ecrit moins que
    # le francais pour le meme contenu. Les cibles sont donc divisees par deux sur
    # ces langues, comme les bornes du titre (pensionretraite.com, 2026-09-27).
    if cible in TARGETS and w < TARGETS[cible]:
        flags.append(f'{w} mots < {TARGETS[cible]} ({cible})')
    # §11 : métadonnées sociales. Une page partagée sans elles s'affiche en lien
    # nu dans WhatsApp, LinkedIn ou X — aucun titre, aucune image. La trame sait
    # fabriquer ces images (generate-og-images.mjs), mais rien ne vérifiait
    # qu'elles étaient posées : relevé du 2026-09-24, 630 pages de dosageguide.com
    # et 125 de pensionretraite.com n'avaient aucun og:image.
    if not re.search(r'property=["\']og:title["\']', doc):
        flags.append('pas de og:title (§11)')
    if not re.search(r'property=["\']og:image["\']', doc):
        flags.append('pas de og:image (§11)')
    if not re.search(r'name=["\']twitter:card["\']', doc):
        flags.append('pas de twitter:card (§11)')

    # §21 : la page doit offrir quelque chose a citer, et l'offrir tot.
    if k in ('pilier', 'guide', 'montant'):
        paras = paragraphes(doc, cjk)
        if not paras:
            flags.append('aucun paragraphe de corps (§21)')
        else:
            total, cumul, trouve = sum(paras), 0, False
            for n in paras:
                if cumul / max(1, total) <= PART_HAUTE and n >= CITABLE_MIN:
                    trouve = True
                    break
                cumul += n
            if not trouve:
                flags.append(f'aucun bloc ≥{CITABLE_MIN} mots dans les {int(PART_HAUTE*100)} premiers % (§21)')
    if k == 'montant' and '<table' not in doc:
        flags.append('pas de tableau')

    flagged += bool(flags)
    rows.append((bool(flags), path, len(t), len(d), w, k, ' · '.join(flags)))
    titres.append((path, t))

for bad, path, lt, ld, w, k, msg in rows:
    if bad or verbose:
        print(f"{'!! ' if bad else '   '}{path:52s} T{lt:3d} D{ld:3d} W{w:5d} {k:8s} {msg}")

# ── §11 : les titres ne sortent pas d'un moule ───────────────────────────────
# Un gabarit de titre partagé n'est pas une faute en soi : sur des pages par
# pays ou par montant, la régularité est voulue. Deux cas le sont, eux :
#   - un marqueur de gabarit resté dans le titre livré ({{…}}, __TITLE__) ;
#   - deux pages indexables qui servent exactement le même titre — typiquement
#     les versions traduites d'une page dont seul le corps a été traduit
#     (rightetf.com, 515 titres servis à l'identique en en/fr/de, 2026-09-22).
# Le second cas se lit comme de la duplication par Google et annule le bénéfice
# des versions linguistiques.
GABARIT_RESTANT = re.compile(r'\{\{|\}\}|__[A-Z][A-Z_]*__|%%[A-Z_]+%%')

doublons = {}
for path, t in titres:
    if t:
        doublons.setdefault(t, []).append(path)

for path, t in titres:
    if GABARIT_RESTANT.search(t):
        print(f'!! {path:52s} marqueur de gabarit dans le titre : {t[:46]}')
        flagged += 1

for t, paths in sorted(doublons.items(), key=lambda kv: -len(kv[1])):
    if len(paths) > 1:
        print(f'!! {len(paths)} pages partagent le titre « {t[:52]} »')
        for p in paths[:4]:
            print(f'       {p}')
        if len(paths) > 4:
            print(f'       … et {len(paths) - 4} autres')
        flagged += len(paths)

# Contrôle de site, pas de page : la page widget en iframe est le levier de
# backlinks de RECETTE-SITE.md §13. Elle est en noindex, donc invisible pour la
# boucle ci-dessus ; sans ce contrôle la règle n'est appliquée nulle part.
site_flags = []
if not glob.glob(f'{site}/{sortie}/**/widget/index.html', recursive=True):
    site_flags.append('pas de page widget (§13)')
if not glob.glob(f'{site}/{sortie}/embed/**/index.html', recursive=True):
    site_flags.append("pas de page d'iframe /embed/ (§13)")
for m in site_flags:
    print(f'!! site{" ":48s} {m}')

print(f'{site} : {len(rows)} pages indexables, {flagged} à corriger'
      + (f', {len(site_flags)} défaut(s) de site' if site_flags else ''))
