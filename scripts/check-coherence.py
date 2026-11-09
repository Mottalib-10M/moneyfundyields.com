# -*- coding: utf-8 -*-
"""Les champs du formulaire et la fonction de calcul parlent-ils de la meme chose ?

Le simulateur d'indemnite de licenciement rendait toujours zero parce que son
formulaire posait deux champs d'anciennete -- annees et mois -- quand sa fonction
n'en lisait qu'un, qu'elle prenait pour le total. Rien dans le code ne le
signalait : les deux cotes compilent, le site se construit, et le resultat est
faux en silence.

Ce controle compare, pour chaque simulateur :
  - les `name` des champs declares dans le formulaire, contre les `inputs.X` que
    la fonction lit reellement. Un champ declare et jamais lu est inerte ; une
    lecture sans champ correspondant vaut toujours zero ;
  - les `key` des resultats affiches, contre les cles que la fonction renvoie.
    Un resultat affiche mais jamais produit laisse une ligne vide.

Usage : python3 check-coherence.py [dossier-du-site]   (defaut : dossier courant)

Le controle vise la structure Next.js des anciens sites (configuration centrale des
simulateurs dans SimulatorClient.tsx + calculations.ts). Un site Astro de la trame n'a pas
cette configuration : chaque simulateur est un composant qui lit ses propres champs, et la
coherence champs/calcul y est couverte par les tests vitest et par check-saisie.mjs. Sur
Astro le controle sort donc « sans objet » (code 0) au lieu de planter (RECETTE §26, 2026-10-16).
"""
import io, os, re, sys

CLIENT = 'src/app/simulateurs/[slug]/SimulatorClient.tsx'
CALCULS = 'src/lib/calculations.ts'

site = sys.argv[1] if len(sys.argv) > 1 else '.'
CLIENT, CALCULS = os.path.join(site, CLIENT), os.path.join(site, CALCULS)
if not (os.path.isfile(CLIENT) and os.path.isfile(CALCULS)):
    astro = any(os.path.isfile(os.path.join(site, f)) for f in ('astro.config.mjs', 'astro.config.ts', 'astro.config.js'))
    print(f"check-coherence : sans objet — {'site Astro' if astro else 'structure non Next.js'} "
          f"(ni {os.path.relpath(CLIENT, site)} ni configuration centrale des simulateurs ; "
          "cohérence couverte par vitest et check-saisie.mjs)")
    sys.exit(0)
client = io.open(CLIENT, encoding='utf8').read()
calculs = io.open(CALCULS, encoding='utf8').read()

# Decoupe des configurations de simulateur : "slug": { ... calculate: fn },
config = re.compile(r'"([a-z0-9-]+)":\s*\{\s*\n\s*fields:(.*?)calculate:\s*(\w+),', re.S)
fonction = re.compile(r'export function (\w+)\(\s*inputs[^)]*\)[^{]*\{(.*?)\n\}', re.S)
corps = {m.group(1): m.group(2) for m in fonction.finditer(calculs)}

soucis = []
for m in config.finditer(client):
    slug, bloc, nom_fn = m.group(1), m.group(2), m.group(3)
    if nom_fn not in corps:
        soucis.append(f'{slug} : fonction {nom_fn} introuvable')
        continue
    src = corps[nom_fn]
    champs = set(re.findall(r'name:\s*"(\w+)"', bloc))
    lus = set(re.findall(r'inputs\.(\w+)', src)) | set(re.findall(r'inputs\["(\w+)"\]', src))
    resultats = set(re.findall(r'\{\s*key:\s*"(\w+)"', bloc))
    # Cles renvoyees : le dernier objet `return { ... }` de la fonction.
    rendus = set()
    for ret in re.findall(r'return\s*\{(.*?)\n\s*\};', src, re.S):
        rendus |= set(re.findall(r'^\s*(\w+):', ret, re.M))

    inertes = champs - lus
    fantomes = lus - champs
    vides = resultats - rendus
    if inertes:
        soucis.append(f'{slug} : champ(s) saisi(s) mais jamais lu(s) par le calcul → {sorted(inertes)}')
    if fantomes:
        soucis.append(f'{slug} : le calcul lit des entrées absentes du formulaire (valent 0) → {sorted(fantomes)}')
    if vides:
        soucis.append(f'{slug} : résultat(s) affiché(s) mais jamais produit(s) → {sorted(vides)}')

print(f'{len(list(config.finditer(client)))} simulateur(s) examiné(s), {len(soucis)} incohérence(s)')
for s in soucis:
    print('  ' + s)
sys.exit(1 if soucis else 0)
