#!/usr/bin/env python3
"""Chaque page de contenu contient au moins un simulateur (RECETTE §9.3).

Une page « de contenu » est toute page indexable qui n'est ni une page de service (à propos,
contact, politique éditoriale, confidentialité, mentions, cookies, widget, glossaire,
méthodologie) ni la racine de redirection. Un simulateur est un champ que le visiteur peut
manipuler dans le <main> : <input> numérique ou texte décimal, <select>, ou groupe de gros
boutons de choix (<button aria-pressed>, le « 3 séances / 45 min » qui se touche du doigt),
rendu dans le HTML du build (île hydratée). Un lien vers un calculateur ne compte pas.

Usage : check-simulateurs.py <site>   → code de sortie 1 s'il manque au moins un simulateur.
"""
import glob, re, sys

# « conditions », « cgu », « cgv » : la page des conditions d'utilisation est une
# page légale au même titre que « terms », déjà reconnue ici, et que check-seo et
# check-trame rangeaient déjà parmi les pages de service. Seul ce contrôle lui
# réclamait un simulateur (valuablecircle.com, /conditions/, 2026-10-01).

# Turc et indonésien (tr-bayram, id-kalender, 2026-10-28) : /tr/hakkimizda/ et /tr/yontem/
# étaient prises pour des pages de contenu sans simulateur.
SERVICE = re.compile(r'/(?:tietoa|laskentatapa|yhteystiedot|toimitusperiaatteet|tietosuoja|kayttoehdot|evasteet|upota-laskuri|about|a-propos|om-oss|over-ons|uber-uns|ueber-uns|chi-siamo|sobre|quienes-somos|acerca|contact|contacto|contatti|kontakt|editorial|politique-editoriale|charte|politica-editorial|redaksjonell|redaktionel|redactie|redaktion|privacy|privacidad|privacidade|personvern|privatliv|datenschutz|confidentialite|conditions|cgu|cgv|terms|vilkar|vilkaar|villkor|integritet|mentions-legales|legal|disclaimer|privacidade|sobre|glossario|metodologia|impressum|aviso-legal|termos|cookies|cookie|politica-cookies|politica-privacidad|terminos|informasjonskapsler|widget|embed|glossary|glossaire|glosario|glossario|glossar|woordenlijst|ordliste|ordbog|ordlista|method|metod|metode|methode|domande-frequenti|o-nas|regulamin|polityka-prywatnosci|polityka-redakcyjna|slownik|nota-prawna|yasal-bilgiler|gizlilik|cerezler|hakkimizda|yontem|iletisim|yayin-ilkeleri|kullanim-kosullari|tentang-kami|privasi|kebijakan-privasi|ketentuan|syarat-ketentuan|kontak|kebijakan-redaksi)[^/]*/')
INPUT = re.compile(r'<input\b(?![^>]*type="(?:hidden|search|checkbox|radio|submit|button)")[^>]*>|<select\b|<button\b[^>]*\baria-pressed=', re.I)

site = sys.argv[1].rstrip('/')
out = 'dist' if glob.glob(f'{site}/dist/**/index.html', recursive=True) else 'out'
pages = missing = 0
bad = []
for p in sorted(glob.glob(f'{site}/{out}/**/index.html', recursive=True)):
    t = open(p, encoding='utf-8', errors='replace').read()
    if re.search(r'<meta[^>]+name="robots"[^>]+noindex', t) or 'http-equiv="refresh"' in t: continue
    url = p[len(site) + len(out) + 1:-len('index.html')] or '/'
    if SERVICE.search(url): continue
    m = re.search(r'<main\b.*?</main>', t, re.S)
    pages += 1
    if not INPUT.search(m.group(0) if m else t):
        missing += 1; bad.append(url)
for u in bad: print(f'!! {u}')
print(f'{site} : {pages} page(s) de contenu, {missing} sans simulateur')
if pages == 0: sys.exit('0 page examinée : le contrôle a échoué (RECETTE §0).')
sys.exit(1 if missing else 0)
