"""Contrôle de la trame éditoriale d'un site construit (RECETTE-SITE.md).

Usage : python3 check-trame.py <dossier-site> [--verbose] [--json]

Complète `check-seo.py` (snippets, longueurs, sources officielles) et
`check-unique.py` (similarité de la prose). Ici on contrôle ce qu'aucun des deux
ne voyait, c'est-à-dire la trame que le lecteur perçoit :

  §7   FAQ    — une question ne paraît que sur une page ; 6 à 8 sur le pilier
                et sur les guides de 1 200 mots et plus, 3 à 5 sur les pages
                courtes ; réponse de 40 à 90 mots ; le JSON-LD `FAQPage`
                correspond aux questions visibles dans le HTML.
  §8   Auteur — encart auteur sur toutes les pages, `Person` avec `jobTitle` et
                `knowsAbout`, `founder` et `foundingDate` sur l'`Organization`,
                `publishingPrinciples`, `dateModified` sur les guides.
  §8.4 Confiance — date en bas (en haut seulement sur une page de lecture), en toutes lettres, disclaimer.
  §10.1 Template — marqueurs « site généré » (dégradé violet, cartes flottantes,
                émoji en puce, grille de features…). Trois sur une page = défaut.
  §18.2 Pied et haut de page — liens légaux obligatoires présents partout.
  HTML  — aucun nom de balise ni d'attribut ne porte d'accent (une passe de
                correction orthographique a déjà écrit `<détails>`, que le
                navigateur ignore silencieusement).

Le script lit `dist/`, jamais les sources : c'est le HTML servi qui compte, et
un `dist/` périmé a déjà masqué deux bugs bloquants (journal du 16/09/2026).
"""
import re, glob, html, sys, os, json, collections

site = sys.argv[1].rstrip('/')

# Astro sort dans `dist/`, Next en export statique dans `out/`. Sans ce choix, les
# cinq sites Next du portefeuille rendaient « 0 page, 0 a corriger » : un echec
# deguise en succes.
# Les dossiers d'archive ne sont pas servis : les compter reviendrait a auditer
# un site fantome, et fausserait l'unicite autant que le compte de pages.
ARCHIVES = ('_archives/', '/archive/', '/old/', '/backup/')
# Le dossier servi n'est pas toujours `dist` : salaryafter.com publie depuis
# `docs/` et calorierule.com depuis `output/`. Ne chercher que dist et out
# faisait contrôler un build obsolète, ou rien du tout (2026-09-26).
# Quand deux candidats coexistent, c'est celui qui porte le plus de pages.
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
as_json = '--json' in sys.argv

SERVICE = re.compile(
    r'/[a-z-]*(faq|questions|preguntas|veelgestelde|haeufige|about|a-propos|ueber-uns|over-ons|'
    r'sobre-nosotros|sobre(?=/|$)|methodology|methodik|methodologie|methode|metodologia|method|widget|'
    # Italien : les pages de service d'un site italien n'étaient pas reconnues,
    # si bien que « chi siamo » ou « glossario » se voyaient reprocher
    # l'absence de FAQ (calcolalordonetto.it, 2026-09-24).
    # « metodo » : la page /method/ en italien (it-calendario-ponti, 2026-10-28).
    r'chi-siamo|contatti|metodo(?=/|$)|glossario|glossary|glossaire|termini|cookie-policy|informativa|'
    r'impressum|mentions|aviso|colofon|legal|privacy|datenschutz|confidentialite|privacidad|'
    # « cgu » : abréviation française de conditions générales d'utilisation, page de service
    # au même titre que /terms/ (cartegrisesimple.fr, 2026-09-20)
    r'cgu|cgv|'
    r'privacidade|cookies|terms|conditions|nutzungsbedingungen|terminos|termos|contact|editorial|'
    # Norvegien, danois, neerlandais (lonnetterskatt.no, 2026-09-27)
    r'om-oss|om-os|kontakt|ordliste|ordbog|metode|redaksjonell|redaktionel|personvern|privatliv|'
    r'vilkar|vilkaar|informasjonskapsler|woordenlijst|redactie|'
    # Polonais (kalkulatorwynagrodzen.pl, 2026-10-03)
    r'o-nas|regulamin|polityka-prywatnosci|polityka-redakcyjna|slownik|'
    # Finnois (fi-laskurit, 2026-10-05)
    r'tietoa|laskentatapa|yhteystiedot|toimitusperiaatteet|tietosuoja|kayttoehdot|evasteet|upota-laskuri|'
    # Espagnol et italien (calcularsueldoneto.mx, aliquoteimu.it, 2026-10-03)
    r'glosario|domande-frequenti|'
    # Turc et indonésien (tr-bayram, id-kalender, 2026-10-28) : mentions, confidentialité,
    # cookies, à propos, méthode, contact, ligne éditoriale.
    r'yasal-bilgiler|gizlilik|cerezler|hakkimizda|yontem(?=/|$)|iletisim|yayin-ilkeleri|kullanim-kosullari|'
    r'tentang-kami|privasi|kebijakan-privasi|ketentuan|syarat-ketentuan|kontak|kebijakan-redaksi|cookie(?=/|$))', re.I)

# Liens que le pied de page doit porter sur toutes les pages (§8.4 identité
# légale, §12). On accepte n'importe laquelle des variantes linguistiques.
FOOTER_LINKS = {
    'legal':   r'(kayttoehdot|impressum|mentions-legales|aviso-legal|legal-notice|colofon|legal|'
               r'terms|conditions|voorwaarden|disclaimer|villkor|betingelser|vilkar|vilkaar|regulamin|nota-prawna|'
               # Turc et indonésien (2026-10-28)
               r'yasal-bilgiler|kullanim-kosullari|ketentuan)',
    'privacy': r'(tietosuoja|datenschutz|privacy|confidentialite|confidentialidade|privacidad|'
               r'privacidade|protection-donnees|gegevensbescherming|persondata|personvern|'
               r'integritetspolicy|privatliv|polityka-prywatnosci|gizlilik|privasi)',
    'about':   r'(tietoa|about|a-propos|ueber-uns|over-ons|sobre|chi-siamo|om-os|om-oss|o-nas|hakkimizda|tentang-kami)',
    'method':  r'(laskentatapa|method|methode|methodik|methodologie|metodolog|metod|metode|yontem)',
}

# §10.1 — réglages par défaut de Tailwind et des bibliothèques de composants.
TEMPLATE_MARKERS = {
    'dégradé violet/indigo': r'(from|via|to)-(purple|violet|indigo|fuchsia)-\d',
    'carte flottante rounded-2xl+shadow-lg': r'rounded-(2xl|3xl)[^"]*shadow-(lg|xl|2xl)',
    'backdrop-blur': r'backdrop-blur',
    'badge pilule multicolore': r'rounded-full[^"]*bg-(pink|purple|indigo|teal|cyan)-\d',
    'grille de features 3 colonnes': r'grid-cols-3[^"]*gap-\d[^"]*(feature|card)',
}
# Émoji en tête de puce ou de titre : marqueur le plus visible du texte généré.
EMOJI_BULLET = re.compile(
    r'<(li|h[2-4])[^>]*>\s*(<[^>]+>\s*)?[\U0001F300-\U0001FAFF✀-➿⬀-⯿]')

DISCLAIMER = re.compile(
    r'(estimation|indicati[efv]|orientativ|ne constitu|do not constitute|uppskattning|ersätter inte|anslag|erstatter ikke|目安|仅供参考|참고용|ориентировочн|не заменяет|справочный|अनुमान|अनुमानित|অনুমান|تقدير|إرشادية|schätzung|richtwert|schatting|indicação|'
    r'no sustituye|ne remplace|ersetzt kein|vervangt geen|does not replace|'
    r'not (?:legal|financial|professional|tax|medical|veterinary) advice|unverbindlich|'
    # « stellt keine Anlageberatung dar », « stellt keine Steuerberatung dar » : la
    # tournure allemande courante, qui n'emploie ni « ersetzt » ni « unverbindlich ».
    r'stellt kein\w* [^.]{0,40}(?:beratung|empfehlung) dar|'
    r'estimates? only|guide only|for guidance|does not constitute|'
    r'not a substitute for|no substitute for|informational purposes only|'
    r'a titre informatif|à titre informatif|nur zur information|'
    # Polonais : « wyniki mają charakter szacunkowy », « nie stanowi doradztwa podatkowego »
    r'charakter szacunkow|nie stanowi\w* doradztw|to nie jest doradztwo|'
    # Grec (ypologismosmisthou.gr, 2026-10-03) : « ενδεικτικοί υπολογισμοί », « δεν αποτελούν συμβουλή ».
    r'ενδεικτικ|δεν αποτελ|'
    # Finnois (fi-laskurit, 2026-10-05) : « tulokset ovat arvioita », « ei korvaa verokorttia ».
    r'arvio|ei korvaa|eivätkä ne korvaa|'
    # Turc (de-einbuergerung, 2026-10-22) : « Hukuki danışmanlık değildir », « tahmini ».
    r'danışmanlık değildir|tahmin|'
    # Italien (it-calendario-ponti, 2026-10-28) : « il sito non sostituisce una consulenza ».
    r'non sostituisc|'
    # Portugais (br-feriados, 2026-10-28) : « não substitui orientação jurídica ».
    r'n[ãa]o substitu|n[ãa]o constitu|'
    # Turc (tr-bayram, 2026-10-28) : « yatırım / hukuki tavsiye değildir », « bilgi amaçlıdır »,
    # « resmi kaynağın yerine geçmez ».
    r'tavsiye(?:si)? değildir|bilgi(?:lendirme)? amaçl|yerine geçmez|'
    # Indonésien (id-kalender, 2026-10-28) : « bukan nasihat hukum », « hanya untuk informasi »,
    # « bersifat panduan », « tidak menggantikan ».
    r'bukan nasihat|hanya untuk informasi|hanya sebagai informasi|bersifat (?:panduan|informatif)|tidak menggantikan)', re.I)

ISO_DATE = re.compile(r'\b20\d{2}-\d{2}-\d{2}\b')
# La date de mise à jour est désormais écrite dans la langue du site
# (« 4 de julho de 2026 »), le format ISO restant dans l'attribut `datetime`.
# Chercher la date dans le texte visible ne prouvait donc plus rien : c'est
# l'élément <time> daté qu'il faut trouver, en haut comme en bas.
TIME_DATE = re.compile(r'<time[^>]+datetime="20\d{2}-\d{2}-\d{2}', re.I)
# Champ de simulateur dans le <main> (même définition que check-simulateurs.py).
SIMU_INPUT = re.compile(r'<input\b(?![^>]*type="(?:hidden|search|checkbox|radio|submit|button)")[^>]*>|<select\b|<button\b[^>]*\baria-pressed=|role="slider"', re.I)


def _norm(t: str) -> str:
    """Texte comparable : sans espaces, et sans les signes que la passe
    typographique du build reecrit apres coup."""
    t = t.replace('\u2014', ',')
    return re.sub(r'[\s,]+', '', t)


def main_words(doc: str) -> int:
    """Longueur du contenu principal, en mots.

    Japonais, coréen, chinois : ces langues n'emploient pas l'espace comme séparateur,
    un comptage par espaces renvoyait 30 mots pour une page de 3 000 caractères et
    faisait passer toutes les pages CJK pour du contenu mince (gfp, 2026-09-20).
    Équivalence retenue, la même que check-seo : un caractère plein vaut deux lettres.
    """
    m = re.search(r'<main[^>]*>(.*?)</main>', doc, re.S)
    t = strip_tags(m.group(1) if m else doc)
    if re.search(r'<html[^>]*\blang="(ja|ko|zh)', doc, re.I):
        return len(re.sub(r'\s+', '', t)) // 2
    return len(t.split())


def strip_tags(t: str) -> str:
    t = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', t, flags=re.S)
    t = html.unescape(re.sub(r'<[a-zA-Z/!][^>]*>', ' ', t))   # « (< 5 ans) » n'est pas une balise
    # Apostrophes et espaces typographiques : le JSON-LD et le HTML n'emploient
    # pas toujours les mêmes, et la comparaison échouait sur ce seul détail.
    t = t.replace('\u2019', "'").replace('\u202f', ' ').replace('\xa0', ' ')
    return re.sub(r'\s+', ' ', t).strip()


def kind(path: str) -> str:
    if SERVICE.search(path):
        return 'service'
    if path.strip('/').count('/') == 0:
        return 'pilier'
    return 'secondaire'


def jsonld(doc: str):
    """Tous les objets JSON-LD de la page, arbre entièrement aplati.

    Les nœuds utiles sont rarement à la racine : `Person` vit dans
    `Organization.founder` ou `WebApplication.author`, et on manquerait
    l'essentiel en ne lisant que le premier niveau et `@graph`.
    """
    out = []

    def descendre(node):
        if isinstance(node, list):
            for n in node:
                descendre(n)
        elif isinstance(node, dict):
            out.append(node)
            for v in node.values():
                if isinstance(v, (dict, list)):
                    descendre(v)

    for m in re.finditer(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', doc, re.S):
        try:
            descendre(json.loads(html.unescape(m.group(1))))
        except Exception:
            out.append({'@type': '__INVALIDE__'})
    return out


def typed(nodes, name):
    """Le nœud le plus riche de ce type, pas le premier rencontré.

    Un même type apparaît souvent deux fois : une référence minimale
    (`WebApplication.author` = nom seul) et la fiche complète. Prendre le
    premier dans l'ordre de l'arbre faisait passer la fiche complète pour
    incomplète.
    """
    candidats = [n for n in nodes
                 if name == n.get('@type', '')
                 or (isinstance(n.get('@type'), list) and name in n['@type'])]
    return max(candidats, key=len, default=None)


pages, questions_seen = [], collections.defaultdict(list)

# ---- §13 : la favicon est declaree sur toutes les pages ------------------
# Le robot qui collecte les favicons interroge la racine du domaine et
# /favicon.ico avant de lire quoi que ce soit d'autre. Une page qui ne declare
# rien laisse Search Console afficher une icone generique pendant des semaines,
# et la marque disparait des resultats de recherche.
# Constate le 2026-09-26 : huit sites du portefeuille declaraient bien leur
# favicon sur leurs pages de contenu et rien du tout sur leur racine, qui est
# justement la premiere porte frappee par le robot.
ICONE = re.compile(r'<link[^>]*rel="[^"]*\bicon\b[^"]*"[^>]*href="([^"]+)"', re.I)

def controle_favicon(doc):
    """Les defauts de declaration d'icone d'une page. Liste vide si tout va bien.

    Une declaration commentee n'est pas une declaration : les 98 pages
    d'uaepriceindex.com portaient un `<!-- <link rel="apple-touch-icon" ... > -->`
    laisse en attente d'un PNG, et le controle la comptait comme une icone promise
    puis absente (2026-09-27).
    """
    doc = re.sub(r'<!--.*?-->', ' ', doc, flags=re.S)
    refs = [h for h in ICONE.findall(doc)]
    if not refs:
        return ['aucune favicon declaree']
    manquants = []
    for href in {r.split('?')[0] for r in refs}:
        if href.startswith(('http://', 'https://', 'data:')):
            continue  # hors du site : on ne peut pas le verifier ici
        chemin = f"{site}/{sortie}/{href.lstrip('/')}"
        if not os.path.isfile(chemin):
            manquants.append(href)
    return [f'favicon declaree mais absente du build : {h}' for h in sorted(manquants)]

for f in sorted(x for x in glob.glob(f'{site}/{sortie}/**/index.html', recursive=True)
                if not any(a in x for a in ARCHIVES)):
    doc = open(f, encoding='utf-8').read()
    rel = os.path.relpath(os.path.dirname(f), f'{site}/{sortie}').replace(os.sep, '/')
    path = '/' + ('' if rel == '.' else rel + '/')
    if 'http-equiv="refresh"' in doc:
        continue                                   # page de redirection (dont la racine multilingue)
    noindex = 'content="noindex' in doc
    k = kind(path)
    nodes = jsonld(doc)
    flags = []

    # ---- HTML : aucun nom de balise ni d'attribut ne porte d'accent -------
    # Le 2026-09-24, une passe de correction d'accents a transformé 70 balises
    # `<details>` en `<détails>` sur netsalaire.com et salairenet.ch. Le
    # navigateur traite l'inconnue comme un `<span>` : l'accordéon reste ouvert,
    # la FAQ s'affiche dépliée, et rien ne le signale. Aucun nom de balise ni
    # d'attribut HTML ne comporte d'accent : un accent y est donc toujours une
    # faute, et un contrôle d'une ligne suffit à la rendre impossible.
    accents = {m.group(1) for m in re.finditer(r'<\s*/?\s*([A-Za-zÀ-ÿ][-\wÀ-ÿ]*)', doc)
               if re.search(r'[À-ÿ]', m.group(1))}
    accents |= {m.group(1) for m in re.finditer(r'\s([A-Za-zÀ-ÿ][-\wÀ-ÿ]*)=["\']', doc)
                if re.search(r'[À-ÿ]', m.group(1))}
    for nom in sorted(accents):
        flags.append(f'balise ou attribut accentué : « {nom} » n\'existe pas en HTML')

    # ---- §7 FAQ ---------------------------------------------------------
    faq = typed(nodes, 'FAQPage')
    visible_text = strip_tags(re.sub(r'<script[^>]*>.*?</script>', ' ', doc, flags=re.S))
    visible_nospace = _norm(visible_text)
    visible_q = {strip_tags(m.group(1)).rstrip('  ?¿')
                 for m in re.finditer(r'<(?:summary|dt|h[34])[^>]*>(.*?)</(?:summary|dt|h[34])>',
                                      doc, re.S)}
    cjk = re.search(r'<html[^>]*\blang="(ja|ko|zh)', doc, re.I) is not None
    if faq:
        qa = faq.get('mainEntity', [])
        qa = qa if isinstance(qa, list) else [qa]
        for item in qa:
            q = strip_tags(str(item.get('name', '')))
            a = item.get('acceptedAnswer', {})
            a = strip_tags(str(a.get('text', '') if isinstance(a, dict) else a))
            if q:
                if not noindex:
                    # Une question partagée avec des pages en noindex ne
                    # concurrence rien : elles ne sont jamais servies à un
                    # moteur (howmanyof.com, 2026-09-25).
                    questions_seen[q.lower().rstrip(' ?¿!.')].append(path)
            # Japonais, coréen, chinois : compter les mots séparés par une espace n'a pas
            # de sens (le japonais n'en met pas, le coréen agglutine). On mesure alors en
            # caractères, avec la même équivalence que check-seo : un caractère plein vaut
            # environ deux lettres latines, donc 40-90 mots ≈ 120-280 caractères.
            if cjk:
                n = len(a.replace(' ', ''))
                if not 120 <= n <= 280:
                    flags.append(f'réponse FAQ {n} caractères ∉[120,280] : « {q[:40]} »')
            else:
                n = len(a.split())
                if not 40 <= n <= 90:
                    flags.append(f'réponse FAQ {n} mots ∉[40,90] : « {q[:40]} »')
            # §7 : le balisage doit correspondre au visible. La question peut être dans un
            # <summary>, un titre, ou un bouton d'accordéon : on la cherche dans tout le texte.
            if q and not any(q.rstrip(' ?¿') in v or v in q for v in visible_q) \
                    and q.rstrip(' ?¿') not in visible_text:
                flags.append(f'question FAQ absente du HTML visible : « {q[:40]} »')
            # La réponse aussi doit être dans le HTML servi : un accordéon qui ne l'insère
            # qu'au clic déclare à Google un texte que la page ne contient pas
            # (116 pages d'epargnemalin.fr, 2026-09-19).
            # Comparaison sans les espaces : une balise fermée juste avant un point
            # (« <strong>63 ans</strong>. ») laisse « 63 ans . » dans le texte extrait.
            # `typo-nbsp.mjs` remplace le tiret cadratin par une virgule dans le
            # texte visible, mais saute les <script> : le JSON-LD garde donc le
            # tiret et la comparaison echouait sur toute reponse qui en
            # contenait un. Faux positif vu le 2026-09-25 sur la page d'accueil
            # francaise de fdeinsider.com. On normalise les deux cotes de la
            # meme facon avant de comparer.
            if a and _norm(a[:80]) not in visible_nospace:
                flags.append(f'réponse FAQ absente du HTML servi : « {q[:40]} »')
        # Un guide de 1 200 mots et plus est un pilier secondaire : il porte
        # assez de matière pour 6 à 8 questions, et les élaguer à 5 reviendrait
        # à jeter du contenu utile (journal du 17/09/2026).
        # Le pilier doit porter 6 à 8 questions. Un guide de 1 200 mots ou plus
        # a le droit d'aller jusqu'à 8 sans y être contraint : le plafond est
        # relevé, le plancher reste celui d'une page secondaire.
        lo, hi = (6, 8) if k == 'pilier' else (3, 8 if main_words(doc) >= 1200 else 5)
        if k != 'service' and not lo <= len(qa) <= hi:
            flags.append(f'{len(qa)} questions ∉[{lo},{hi}] ({k})')
    elif k != 'service' and not noindex:
        flags.append('pas de FAQPage')

    # ---- §8 E-E-A-T -----------------------------------------------------
    if not noindex:
        # Décision du 2026-09-20 : l'auteur du portefeuille n'est plus une personne
        # physique mais la société éditrice. Un `Person` reste accepté (sites non
        # encore migrés) ; à défaut, une `Organization` complète tient le rôle.
        person = typed(nodes, 'Person')
        org = typed(nodes, 'Organization')
        if person:
            for champ in ('jobTitle', 'knowsAbout'):
                if not person.get(champ):
                    flags.append(f'Person sans {champ}')
        elif not org:
            flags.append('ni Person ni Organization comme auteur')
        if org:
            if not org.get('foundingDate'):
                flags.append('Organization sans foundingDate')
            if not org.get('publishingPrinciples'):
                flags.append('Organization sans publishingPrinciples')
            # `knowsAbout` porte l'expertise quand l'auteur est la société. Les sites
            # déclarent souvent deux Organization (l'éditrice et celle du site) : il
            # suffit que l'une d'elles la porte (brutanet.fr, 2026-09-20).
            if not person and not any(
                    n.get('knowsAbout') for n in nodes
                    if 'Organization' in str(n.get('@type', ''))):
                flags.append('Organization auteur sans knowsAbout')
        # Encart auteur visible, pas seulement dans le JSON-LD.
        if not re.search(r'(rel="author"|itemprop="author"|class="[^"]*author|data-author'
                          r'|src="/team/)', doc):
            flags.append('pas d\'encart auteur visible')
        # §8.2 : dateModified sur les guides et pages secondaires.
        if k == 'secondaire' and not any(n.get('dateModified') for n in nodes):
            flags.append('pas de dateModified')

    # ---- §8.4 confiance : où se montre la date de mise à jour -------------
    # Règle du 2026-10-15 (pensionretraite.com) : sur une page qui commence par un
    # simulateur, et sur un accueil, la date ne se met pas au-dessus du simulateur :
    # elle repousse le titre sans rien apprendre au visiteur. Elle vit en bas de page
    # et dans WebPage.dateModified. Une page de lecture (article, guide dont le
    # simulateur vient après le texte) garde une petite date en haut. Partout, la
    # date affichée est écrite en toutes lettres, jamais « 2026-10-07 ».
    if not noindex:
        mm = re.search(r'<main\b.*?</main>', doc, re.S)
        main = mm.group(0) if mm else doc
        h2 = re.search(r'<h2\b', main)
        first_in = SIMU_INPUT.search(main)
        h1end = main.find('</h1>')
        h1end = main.find('</h1>')
        accueil = path == '/' or re.fullmatch(r'[a-z]{2}(?:-[a-z]{2,4})?', path.strip('/')) is not None
        # « Commence par un simulateur » : moins de 250 mots entre le titre et le premier
        # champ. Le premier H2 ne suffit pas : le panneau du simulateur a souvent le sien
        # (« Votre situation », pensionretraite.com).
        mene_par_simu = bool(first_in) and len(strip_tags(main[max(h1end, 0):first_in.start()]).split()) < 250
        foot = doc[doc.rfind('<footer'):] if '<footer' in doc else doc[-4000:]
        if mene_par_simu or accueil:
            # Tout ce qui précède le simulateur (ou le premier H2 d'un accueil sans simulateur).
            stop = first_in.start() if first_in else (h2.start() if h2 else len(main))
            avant = (doc[:mm.start()] if mm else '') + main[:stop]
            avant = re.sub(r'<script.*?</script>', ' ', avant, flags=re.S)
            if TIME_DATE.search(avant):
                flags.append('date de mise à jour au-dessus du simulateur : la mettre en bas de page (§8.4)')
        elif k != 'service' and any(str(x.get('@type')) in ('Article', 'BlogPosting', 'NewsArticle') for x in nodes):
            # Page de lecture = article déclaré (Article, BlogPosting). Une page pays ou une
            # page de liste, même longue, est un accueil de rubrique (pensionretraite.com).
            # « En haut » veut dire à hauteur du titre : la signature « Par X · Mis à
            # jour le … » se place souvent juste sous le <h1> (netsalaire.com, 2026-09-24).
            head = doc[:doc.find('</h1>') + 2000] if '</h1>' in doc else doc[:4000]
            if not TIME_DATE.search(head):
                flags.append('pas de date de mise à jour en haut (page de lecture)')
        if not (TIME_DATE.search(foot) or ISO_DATE.search(strip_tags(foot)) or TIME_DATE.search(doc[-6000:])):
            flags.append('pas de date de mise à jour en bas')
        # Seule la date de mise à jour est visée : « Stand 2026-10-01 » ou une période
        # « 2026-01-01 bis 2026-12-31 » dans un tableau de paramètres restent permises.
        if re.search(r'<time\b[^>]*>\s*20\d{2}-\d{2}-\d{2}\s*</time>', doc):
            flags.append('date affichée au format 2026-10-07 : l\'écrire en toutes lettres (§8.4)')
        if not DISCLAIMER.search(strip_tags(doc)):
            flags.append('pas de disclaimer')

    # ---- haut et pied de page -------------------------------------------
    embed = path.startswith('/embed/')
    if embed:
        # Une page servie en iframe n'affiche jamais d'icone : l'onglet est
        # celui du site hote. On ne lui demande donc pas de favicon.
        pages.append({'path': path, 'kind': 'iframe', 'noindex': noindex, 'flags': flags})
        continue
    # Une page en noindex (console d'administration, page technique) n'a pas à porter
    # l'en-tête et le pied publics : elle n'est pas indexée, la règle ne la vise pas.
    # La favicon non plus : la regle existe pour le robot qui collecte les icones,
    # et ce robot ne visite pas une page qu'il n'indexe pas (netsalaire.com et
    # bmi-imc.com, dont la seule page signalee etait /admin/, 2026-09-26).
    if noindex:
        pages.append({'path': path, 'kind': k, 'noindex': noindex, 'flags': flags})
        continue

    flags.extend(controle_favicon(doc))
    if '<header' not in doc:
        flags.append('pas de <header>')
    if '<nav' not in doc:
        flags.append('pas de <nav>')
    if '<footer' not in doc:
        flags.append('pas de <footer>')
    else:
        foot = doc[doc.rfind('<footer'):]
        for nom, motif in FOOTER_LINKS.items():
            if not re.search(rf'href="[^"]*{motif}', foot, re.I):
                flags.append(f'pied sans lien {nom}')

    # ---- §10.1 marqueurs de template ------------------------------------
    marqueurs = [nom for nom, motif in TEMPLATE_MARKERS.items()
                 if re.search(motif, doc, re.I)]
    if EMOJI_BULLET.search(doc):
        marqueurs.append('émoji en tête de puce ou de titre')
    if len(marqueurs) >= 3:
        flags.append('template : ' + ', '.join(marqueurs))
    elif marqueurs and verbose:
        flags.append('(template, sous le seuil) ' + ', '.join(marqueurs))

    pages.append({'path': path, 'kind': k, 'noindex': noindex, 'flags': flags})

# ---- §10.1 : la page racine est une page, pas un gabarit -----------------
# Elle redirige et porte noindex, mais elle reste la première URL du domaine :
# sans JS elle est tout ce que voit le visiteur, et sur un site multilingue elle
# est le seul chemin vers les autres langues.
racine = f'{site}/{sortie}/index.html'
if os.path.exists(racine):
    doc = open(racine, encoding='utf-8').read()
    flags = []

    m = re.search(r'<title>(.*?)</title>', doc, re.S)
    titre = strip_tags(m.group(1)).strip() if m else ''
    if not titre:
        flags.append('pas de <title>')
    elif titre.lower() in {'redirect', 'redirection', 'index', 'home'}:
        flags.append(f'titre de gabarit : « {titre} » — mettre le nom du site')

    m = re.search(r'rel="canonical"[^>]*href="([^"]*)"', doc)
    canon = m.group(1) if m else ''
    if not canon:
        flags.append('pas de canonical')
    elif not canon.startswith('http'):
        flags.append(f'canonical relatif ({canon}) — doit être absolu')

    # Texte d'un lien : visible, ou aria-label / title / alt d'image (lien-icône accessible).
    liens = [(strip_tags(t).strip() + ' ' + ' '.join(re.findall(r'(?:aria-label|title|alt)="([^"]*)"', attrs + t))).strip()
             for attrs, t in re.findall(r'<a\b([^>]*)>(.*?)</a>', doc, re.S)]
    muets = [t for t in liens if not re.search(r'\w{2}', t)]
    if muets:
        flags.append(f'{len(muets)} lien(s) sans texte lisible '
                     f'({", ".join(repr(t) for t in muets[:3])})')

    # Un dossier de langue dont l'accueil n'est qu'un renvoi (meta refresh) n'est plus une langue
    # publiée : langue retirée du site, ses anciennes adresses renvoient ailleurs
    # (citizenshiptestfree.com, arbre /fr/ devenu des renvois vers le site canadien le 2026-10-25).
    def renvoi_seul(d):
        f = f'{site}/{sortie}/{d}/index.html'
        return os.path.exists(f) and 'http-equiv="refresh"' in open(f, encoding='utf-8').read()
    locales = sorted(d for d in os.listdir(f'{site}/{sortie}')
                     if re.fullmatch(r'[a-z]{2}', d)
                     and os.path.isdir(f'{site}/{sortie}/{d}')
                     and not renvoi_seul(d))
    if len(liens) < len(locales):
        flags.append(f'{len(locales)} langue(s) publiée(s) ({", ".join(locales)}) '
                     f'mais {len(liens)} lien(s) : une langue est inatteignable sans JS')

    flags.extend(controle_favicon(doc))

    pages.append({'path': '/', 'kind': 'racine', 'noindex': True, 'flags': flags})

# ---- §13 : IndexNow — clé propre au site, lue dans sa config (§26 du 2026-10-16) ----
# L'ancienne trame écrivait dans scripts/indexnow.sh la clé et l'URL de lohnnetto.ch
# (ex-nettolohn-rechner.ch) : chaque site copié aurait pingé avec la clé d'un autre.
CLE_TRAME = 'c1f0e5f4b7a94d2e9b3c8a7d6e5f4a3b'
flags = []
_cfg = f'{site}/src/data/site-config.ts'
_cfg = open(_cfg, encoding='utf-8').read() if os.path.exists(_cfg) else ''
_m = re.search(r"INDEXNOW_KEY\s*=\s*['\"]([^'\"]*)['\"]", _cfg)
_cle = _m.group(1) if _m else ''
_url = re.search(r"SITE_URL\s*=\s*['\"]([^'\"]*)['\"]", _cfg)
_dom = re.sub(r'^https?://', '', _url.group(1)).strip('/') if _url else ''
_sh = f'{site}/scripts/indexnow.sh'
if os.path.exists(_sh):
    _src = open(_sh, encoding='utf-8').read()
    # Une clé écrite en dur n'est un défaut que si ce n'est pas celle du site.
    _durs = set(re.findall(r'^\s*KEY=["\']?([0-9a-fA-F]{16,})', _src, re.M)) | ({CLE_TRAME} & set(re.findall(r'[0-9a-f]{32}', _src)))
    _etr = sorted(k for k in _durs if k != _cle)
    if _etr:
        flags.append(f'scripts/indexnow.sh envoie la clé {_etr[0][:8]}… qui n\'est pas INDEXNOW_KEY du site — '
                     'reprendre celui de la trame (clé et site lus dans src/data/site-config.ts)')
if _cle:
    if _cle == CLE_TRAME and _dom != 'lohnnetto.ch':
        flags.append(f'INDEXNOW_KEY = clé de lohnnetto.ch — générer la clé du site (secrets.token_hex(16))')
    if not os.path.exists(f'{site}/public/{_cle}.txt'):
        flags.append(f'public/{_cle}.txt manquant : IndexNow refusera la clé (403)')
if flags:
    pages.append({'path': '(indexnow)', 'kind': 'config', 'noindex': True, 'flags': flags})

# ---- §10.3 : le nom affiché est celui du domaine (règle du 2026-10-25) ----
# Les mots exacts du domaine, rendus lisibles par les majuscules, les espaces et la couleur
# (monare.fr → « Mon ARE »), jamais d'autres mots (« Simulateur ARE ») : la marque se retient
# par l'adresse. On compare les lettres seules, sans accents ni espaces, dans chaque langue ;
# l'extension peut faire partie du nom (« NZSalary.com »), un nom sans lettre latine est admis.
def _lettres(t, translit=False):
    import unicodedata
    # ä, ö, ü, ß s'écrivent ae, oe, ue, ss dans un domaine allemand (stromerpraemie.de « Stromerprämie »),
    # mais a, o dans un domaine suédois ou finnois (lonkalkylator.se « Lönkalkylator ») : on accepte les deux.
    # « ı » turc (sans point) n'a pas de décomposition NFD : il s'écrit « i » dans un domaine
    # (« Bayram Takvimi » → bayramtakvimi, 2026-10-28).
    t = t.lower().replace('ß', 'ss').replace('ı', 'i')
    if translit:
        t = t.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFD', t))
flags = []
_noms = re.search(r'SITE_NAMES[^=]*=\s*(\{[^}]*\})', _cfg)
_label = _dom.removeprefix('www.').split('.')[0] if _dom else ''
if _noms and _label and not _label.startswith('example'):
    for _lang, _nom in re.findall(r'["\']?(\w+)["\']?\s*:\s*["\']([^"\']*)["\']', _noms.group(1)):
        if _lettres(_nom) and not {_lettres(_nom), _lettres(_nom, True)} & {_lettres(_label), _lettres(_dom.removeprefix('www.'))}:
            flags.append(f'nom affiché « {_nom} » ({_lang}) ≠ domaine {_dom} : reprendre les mots du domaine '
                         f'(majuscules, espaces, BRAND_ACCENT en couleur)')
if flags:
    pages.append({'path': '(marque)', 'kind': 'config', 'noindex': True, 'flags': flags})

# ---- §3 : 100 pages au plus, toutes langues comprises (règle absolue du 2026-10-16) ----
# Sur les 22 sites en ligne avant juin, le nombre de pages joue contre les clics (−0,40) et
# l'indexation est le facteur le plus fort (0,75) : les gagnants ont 18 à 42 pages.
# On compte chaque page HTML servie, légales, widget et /embed/ comprises ; seule la 404 est exclue.
PLAFOND_PAGES = 100
_servies = []
for _racine, _, _fichiers in os.walk(f'{site}/{sortie}'):
    _rel = os.path.relpath(_racine, f'{site}/{sortie}').replace(os.sep, '/') + '/'
    if any(a in '/' + _rel for a in ARCHIVES):
        continue
    _servies += [_rel + f for f in _fichiers if f.endswith('.html') and f != '404.html']
if len(_servies) > PLAFOND_PAGES:
    _par_langue = collections.Counter(p.split('/')[0] if re.fullmatch(r'[a-z]{2}', p.split('/')[0]) else '(racine)'
                                      for p in _servies)
    pages.append({'path': '(périmètre)', 'kind': 'config', 'noindex': True, 'flags': [
        f'{len(_servies)} pages HTML servies pour {PLAFOND_PAGES} au plus, toutes langues comprises '
        f'(RECETTE §3, règle absolue) — {", ".join(f"{k} : {v}" for k, v in sorted(_par_langue.items()))}. '
        'Fusionner ou supprimer les pages les plus faibles.']})

# ---- §7 : une question ne paraît que sur une seule page ------------------
doublons = {q: p for q, p in questions_seen.items() if len(set(p)) > 1}
for q, paths in doublons.items():
    for p in set(paths):
        for page in pages:
            if page['path'] == p:
                page['flags'].append(f'question FAQ partagée avec {len(set(paths))-1} '
                                     f'autre(s) page(s) : « {q[:50]} »')

if as_json:
    print(json.dumps({'site': site, 'pages': pages,
                      'faq_doublons': {q: sorted(set(p)) for q, p in doublons.items()}},
                     ensure_ascii=False, indent=1))
    sys.exit(0)

mauvaises = 0
for page in pages:
    if page['flags']:
        mauvaises += 1
        print(f"!! {page['path']:52s} {page['kind']:11s}")
        for fl in page['flags']:
            print(f"     · {fl}")
    elif verbose:
        print(f"   {page['path']:52s} {page['kind']:11s} ok")

print(f"\n{site} : {len(pages)} pages, {mauvaises} à corriger, "
      f"{len(doublons)} question(s) de FAQ recyclée(s)")
sys.exit(1 if mauvaises else 0)
