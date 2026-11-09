"""Favicon et logo aux couleurs du drapeau du pays — RECETTE §19.1 (règle du 2026-10-04).

Usage : python3 gen-flag-icon.py <code-pays> <symbole> [dossier-site]
        symbole : un texte court (€, zł, $, kr, ALG…) ou un pictogramme : « maison », « eclair », « dent ».
Deux sites du même pays ne partagent jamais le même dessin : la devise va au site principal,
les autres prennent le sigle ou le pictogramme de leur sujet (registre : _trame/icones-drapeau.txt).
Écrit public/favicon.svg et public/logo.svg, puis lancer `node scripts/gen-icons.mjs`
pour les PNG et l'ICO.

Pourquoi : dans les résultats Google, le favicon est la seule image à côté du titre. Les
couleurs du drapeau disent le pays au premier coup d'œil et inspirent confiance, ce qui aide
le clic.

Ce que l'icône ne reprend JAMAIS (légal et honnête) : les armoiries ou emblèmes d'État
(aigle du Mexique ou de Pologne, emblème de la République italienne, armoiries grecques),
la Marianne et les logos d'administration, ni aucun élément qui ferait croire à un site
officiel. Seules les bandes de couleur du drapeau civil, stylisées, sont utilisées.
"""
import os, sys

# Bandes du drapeau civil, sans emblème : (orientation, couleurs). Couleurs officielles publiées.
FLAGS = {
    'fr': ('v', ['#0055A4', '#FFFFFF', '#EF4135']),
    'it': ('v', ['#009246', '#FFFFFF', '#CE2B37']),
    'mx': ('v', ['#006847', '#FFFFFF', '#CE1126']),        # sans l'aigle
    'be': ('v', ['#000000', '#FDDA24', '#EF3340']),
    'ie': ('v', ['#169B62', '#FFFFFF', '#FF883E']),
    'pl': ('h', ['#FFFFFF', '#DC143C']),                   # sans l'aigle
    'de': ('h', ['#000000', '#DD0000', '#FFCE00']),
    'nl': ('h', ['#AE1C28', '#FFFFFF', '#21468B']),
    'in': ('h', ['#FF9933', '#FFFFFF', '#138808']),        # sans le chakra
    'lu': ('h', ['#EA141D', '#FFFFFF', '#51ADDA']),
    'at': ('h', ['#C8102E', '#FFFFFF', '#C8102E']),
    'es': ('h3', ['#AA151B', '#F1BF00', '#AA151B']),       # sans les armoiries
    'gr': ('gr', ['#0D5EAF', '#FFFFFF']),
    'ch': ('ch', ['#DA291C', '#FFFFFF']),
    'pt': ('pt', ['#046A38', '#DA291C']),                  # sans la sphère armillaire
    'se': ('nordic', ['#006AA7', '#FECC02', None]),
    'dk': ('nordic', ['#C8102E', '#FFFFFF', None]),
    'no': ('nordic', ['#BA0C2F', '#FFFFFF', '#00205B']),
    'fi': ('nordic', ['#FFFFFF', '#002F6C', None]),
    'gb': ('gb', ['#012169', '#FFFFFF', '#C8102E']),
    'us': ('us', ['#B22234', '#FFFFFF', '#3C3B6E']),       # bandes et canton, sans étoiles détaillées
    'ca': ('ca', ['#D80621', '#FFFFFF']),                  # bandes rouges, sans la feuille
    'au': ('stars', ['#012169', '#FFFFFF']),               # fond bleu et Croix du Sud stylisée
    'nz': ('stars', ['#012169', '#CC142B']),
    'sg': ('h', ['#EF3340', '#FFFFFF']),                   # sans croissant ni étoiles
    'ae': ('ae', ['#00732F', '#FFFFFF', '#000000', '#FF0000']),
    'sa': ('h', ['#006C35']),                             # fond vert seul, sans shahada ni sabre
    'br': ('br', ['#009739', '#FEDD00', '#012169']),       # losange et globe, sans devise ni étoiles
    # Turquie : fond rouge seul, sans croissant ni étoile. Pas de bande blanche : rouge sur blanc
    # serait le dessin de l'Indonésie (et de Monaco), le pays ne se lirait plus (2026-10-28).
    'tr': ('h', ['#E30A17']),
    'id': ('h', ['#E70011', '#FFFFFF']),                   # rouge sur blanc (Sang Saka Merah-Putih)
}

HOUSE = '<path d="M16 7.5 7 15h2.6v8.5h4.7v-5.2h3.4v5.2h4.7V15H25z" fill="#fff" stroke="#0B1F33" stroke-width="1.6" stroke-linejoin="round" paint-order="stroke"/>'


def bands(code):
    kind, cols = FLAGS[code]
    if kind == 'v':
        w = 32 / len(cols); return ''.join(f'<rect x="{i*w:.3f}" y="0" width="{w+0.05:.3f}" height="32" fill="{c}"/>' for i, c in enumerate(cols))
    if kind == 'h':
        h = 32 / len(cols); return ''.join(f'<rect x="0" y="{i*h:.3f}" width="32" height="{h+0.05:.3f}" fill="{c}"/>' for i, c in enumerate(cols))
    if kind == 'h3':  # Espagne : 1/4, 1/2, 1/4
        return f'<rect width="32" height="32" fill="{cols[0]}"/><rect y="8" width="32" height="16" fill="{cols[1]}"/>'
    if kind == 'gr':  # 9 bandes et croix blanche dans le canton
        b, w = cols; s = ''.join(f'<rect y="{i*32/9:.3f}" width="32" height="{32/9+0.05:.3f}" fill="{b if i % 2 == 0 else w}"/>' for i in range(9))
        c = 32 / 9 * 5
        return s + f'<rect width="{c:.3f}" height="{c:.3f}" fill="{b}"/><rect x="{c*2/5:.3f}" width="{c/5:.3f}" height="{c:.3f}" fill="{w}"/><rect y="{c*2/5:.3f}" width="{c:.3f}" height="{c/5:.3f}" fill="{w}"/>'
    if kind == 'ch':
        r, w = cols; return f'<rect width="32" height="32" fill="{r}"/><rect x="13" y="6" width="6" height="20" fill="{w}"/><rect x="6" y="13" width="20" height="6" fill="{w}"/>'
    if kind == 'pt':
        g, r = cols; return f'<rect width="32" height="32" fill="{r}"/><rect width="12.8" height="32" fill="{g}"/>'
    if kind == 'nordic':  # croix scandinave décalée vers la hampe
        bg, cr, inner = cols
        out = f'<rect width="32" height="32" fill="{bg}"/><rect x="9" width="7" height="32" fill="{cr}"/><rect y="12.5" width="32" height="7" fill="{cr}"/>'
        if inner: out += f'<rect x="10.75" width="3.5" height="32" fill="{inner}"/><rect y="14.25" width="32" height="3.5" fill="{inner}"/>'
        return out
    if kind == 'gb':
        b, w, r = cols
        return (f'<rect width="32" height="32" fill="{b}"/><path d="M0 0L32 32M32 0L0 32" stroke="{w}" stroke-width="6.4"/>'
                f'<path d="M0 0L32 32M32 0L0 32" stroke="{r}" stroke-width="2.2"/><rect x="12" width="8" height="32" fill="{w}"/>'
                f'<rect y="12" width="32" height="8" fill="{w}"/><rect x="13.6" width="4.8" height="32" fill="{r}"/><rect y="13.6" width="32" height="4.8" fill="{r}"/>')
    if kind == 'us':
        r, w, b = cols; s = ''.join(f'<rect y="{i*32/13:.3f}" width="32" height="{32/13+0.05:.3f}" fill="{r if i % 2 == 0 else w}"/>' for i in range(13))
        return s + f'<rect width="14" height="{32/13*7:.3f}" fill="{b}"/>'
    if kind == 'ca':
        r, w = cols; return f'<rect width="32" height="32" fill="{w}"/><rect width="8" height="32" fill="{r}"/><rect x="24" width="8" height="32" fill="{r}"/>'
    if kind == 'stars':
        b, st = cols
        dots = ''.join(f'<circle cx="{x}" cy="{y}" r="{rr}" fill="{st}" stroke="#FFFFFF" stroke-width="{0.6 if st != "#FFFFFF" else 0}"/>' for x, y, rr in [(25, 6, 1.6), (21, 15, 1.5), (28, 16, 1.5), (25, 26, 1.8)])
        return f'<rect width="32" height="32" fill="{b}"/>' + dots
    if kind == 'ae':
        g, w, k, r = cols
        return f'<rect width="32" height="32" fill="{w}"/><rect width="32" height="10.7" fill="{g}"/><rect y="21.3" width="32" height="10.7" fill="{k}"/><rect width="9" height="32" fill="{r}"/>'
    if kind == 'br':
        g, y, b = cols
        return f'<rect width="32" height="32" fill="{g}"/><path d="M16 4 30 16 16 28 2 16z" fill="{y}"/><circle cx="16" cy="16" r="6.5" fill="{b}"/>'
    raise SystemExit(f'drapeau inconnu : {code}')


# Dent (molaire stylisée) pour les sites de santé bucco-dentaire.
TOOTH = '<path d="M10.2 6.2c-2.6 0-4.4 2.1-4.4 5 0 2.6 1.1 4.3 1.9 6.4.7 1.9.9 4.1 1.4 6.4.4 1.8 1.1 2.8 2.1 2.8 1.3 0 1.6-1.5 1.9-3.4.3-2 .7-3.9 2.9-3.9s2.6 1.9 2.9 3.9c.3 1.9.6 3.4 1.9 3.4 1 0 1.7-1 2.1-2.8.5-2.3.7-4.5 1.4-6.4.8-2.1 1.9-3.8 1.9-6.4 0-2.9-1.8-5-4.4-5-2 0-3.3 1.2-5.8 1.2s-3.8-1.2-5.8-1.2z" fill="#fff" stroke="#0B1F33" stroke-width="1.6" stroke-linejoin="round" paint-order="stroke"/>'

BOLT = '<path d="M19.5 3 7 18h7.5L12 29 25 13.5h-7.5L20.5 3z" fill="#fff" stroke="#0B1F33" stroke-width="1.6" stroke-linejoin="round" paint-order="stroke"/>'


def symbol(sym, code):
    if sym == 'maison':
        return HOUSE
    if sym == 'eclair':
        return BOLT
    if sym == 'dent':
        return TOOTH
    size = 19 if len(sym) == 1 else 14 if len(sym) == 2 else 11
    y = 23 if len(sym) == 1 else 21.5
    # Texte blanc cerné de sombre : lisible sur les bandes claires comme foncées, jusqu'à 16 px.
    return (f'<text x="16" y="{y}" font-size="{size}" font-weight="900" fill="#fff" stroke="#0B1F33" '
            f'stroke-width="2.4" paint-order="stroke" stroke-linejoin="round" '
            f'font-family="Helvetica, Arial, sans-serif" text-anchor="middle">{sym}</text>')


def svg(code, sym):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
            '<defs><clipPath id="r"><rect width="32" height="32" rx="7"/></clipPath></defs>'
            f'<g clip-path="url(#r)">{bands(code)}</g>'
            '<rect x="0.5" y="0.5" width="31" height="31" rx="6.5" fill="none" stroke="#0B1F33" stroke-opacity=".25"/>'
            f'{symbol(sym, code)}</svg>')


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(2)
    code, sym = sys.argv[1].lower(), sys.argv[2]
    site = sys.argv[3] if len(sys.argv) > 3 else '.'
    out = svg(code, sym)
    for f in ('favicon.svg', 'logo.svg'):
        open(os.path.join(site, 'public', f), 'w').write(out)
    print(f'{site}/public : favicon.svg et logo.svg ({code}, « {sym} »)')
