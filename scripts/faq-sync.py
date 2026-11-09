"""Aligne le JSON-LD FAQPage sur la FAQ visible de la page.

Règle de recette : une seule source. La FAQ affichée (les <details> dont le
<summary> se termine par « ? ») fait foi ; le balisage est régénéré à partir
d'elle, pour que Google ne se voie jamais promettre une réponse absente.

Usage : faq_sync.py <fichier.html>… ; écrit les fichiers, affiche un compte.
"""
import io, re, sys, json


def texte(t):
    t = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', t, flags=re.S)
    t = re.sub(r'<[^>]+>', ' ', t)
    t = (t.replace('&nbsp;', ' ').replace('&#160;', ' ')
          .replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
          .replace('&eacute;', 'é').replace('&quot;', '"').replace('&#39;', "'")
          .replace(' ', ' ').replace('\xa0', ' '))
    return re.sub(r'\s+', ' ', t).strip()


def paires(doc):
    out = []
    for bloc in re.findall(r'<details\b.*?</details>', doc, re.S):
        s = re.search(r'<summary\b.*?</summary>', bloc, re.S)
        if not s:
            continue
        q = texte(s.group(0)).rstrip(' ▼▲+-').strip()
        if not q.endswith('?'):
            continue                      # accordéon de formulaire, pas une question
        a = texte(bloc.replace(s.group(0), ' '))
        if a:
            out.append((q, extrait(a)))
    return out


def extrait(a, maxi=90):
    """Ce que le balisage déclare : la réponse entière, ou ses premières phrases.

    Une réponse de 140 mots est utile au lecteur mais Google tronque l'extrait
    enrichi bien avant. Plutôt que d'amputer la page, on ne met dans le JSON-LD
    que les premières phrases complètes, dans la limite de 90 mots. Le texte
    déclaré reste alors mot pour mot un début du texte servi : la promesse faite
    au moteur est tenue par la page.
    """
    if len(a.split()) <= maxi:
        return a
    bout, n = [], 0
    # Une fin de phrase est un point suivi d'une espace et d'une majuscule :
    # couper sur tout point cassait « 6.91 % » en deux et fabriquait une phrase
    # absente de la page (calcolalordonetto.it, 2026-09-24).
    for phrase in re.split(r'(?<=[.!?])\s+(?=[A-ZÀ-Ý])', a):
        m = len(phrase.split())
        if n + m > maxi and n >= 40:
            break
        bout.append(phrase); n += m
        if n >= 40 and n <= maxi and len(bout) >= 1 and n + 10 > maxi:
            break
    t = ''.join(bout).strip()
    # Une énumération peut à elle seule dépasser 90 mots : on la coupe alors à la
    # dernière virgule ou au dernier point-virgule utile, plutôt qu'en plein mot.
    mots = t.split()
    if len(mots) > maxi:
        court = ' '.join(mots[:maxi])
        i = max(court.rfind(','), court.rfind(';'), court.rfind(' : '))
        t = (court[:i] if i > 0 else court).rstrip(' ,;') + '.'
    return t


for f in sys.argv[1:]:
    doc = io.open(f, encoding='utf8').read()
    qa = paires(doc)
    if not qa:
        print(f'{f} : aucune FAQ visible'); continue
    schema = {
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        'mainEntity': [{'@type': 'Question', 'name': q,
                        'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in qa],
    }
    bloc = json.dumps(schema, ensure_ascii=False, indent=4)
    nouveau = f'<script type="application/ld+json">\n{bloc}\n    </script>'

    # remplace le FAQPage existant, à défaut l'insère avant </head>
    fait = False
    for m in re.finditer(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', doc, re.S):
        if '"FAQPage"' in m.group(1):
            doc = doc[:m.start()] + nouveau + doc[m.end():]
            fait = True
            break
    if not fait:
        doc = doc.replace('</head>', f'    {nouveau}\n</head>', 1)
    io.open(f, 'w', encoding='utf8').write(doc)
    courtes = [q for q, a in qa if not 40 <= len(a.split()) <= 90]
    print(f'{f} : {len(qa)} question(s){"" if not courtes else "  ⚠ hors bornes : " + "; ".join(q[:45] for q in courtes)}')
