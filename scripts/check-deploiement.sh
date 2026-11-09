#!/bin/sh
# check-deploiement.sh — le site en ligne reçoit-il vraiment ce qu'on pousse ? (RECETTE §24)
#
# Deux pannes silencieuses ont figé des sites pendant des semaines sans que rien
# ne le signale : costoflivingusa.com au 29 août, rightetf.com au 4 août.
# Dans les deux cas le workflow tournait, mais `npm ci` refusait de s'exécuter
# (package.json et package-lock.json désynchronisés) et s'arrêtait en 20 secondes.
# Le build ne se lançait jamais, GitHub Pages continuait à servir l'ancienne
# version, et l'onglet Actions affichait des exécutions — juste très courtes.
#
# Deux contrôles, parce qu'aucun ne suffit seul :
#   1. `npm ci --dry-run` avec LES DRAPEAUX DU WORKFLOW : un dépôt qui installe
#      avec --legacy-peer-deps passe en CI même si `npm ci` seul échoue. Tester
#      sans le drapeau donne des faux positifs (4 sur 11 lors de la mise au point).
#   2. l'âge du contenu servi : `last-modified` de la page d'accueil comparé au
#      dernier commit. C'est la seule preuve qu'un déploiement est arrivé à bon
#      port ; lire l'API Actions ne suffit pas, et le jeton n'y a pas toujours accès.
#
# Usage : check-deploiement.sh <dossier-du-site> [domaine]

set -u
d="${1:?dossier du site attendu}"
dom="${2:-$(cat "$d/public/CNAME" "$d/CNAME" 2>/dev/null | head -1 | tr -d ' \r')}"
nom=$(basename "$d")
defauts=0

# ── 1. installation reproductible, avec les drapeaux réellement utilisés en CI
if [ -f "$d/package.json" ] && [ -f "$d/package-lock.json" ]; then
  flags=$(grep -rhoE 'npm ci[^"$]*' "$d"/.github/workflows/*.y*ml 2>/dev/null |
          head -1 | sed 's/^npm ci//')
  if [ -n "$(grep -rl 'npm ci' "$d"/.github/workflows/ 2>/dev/null)" ]; then
    if ! (cd "$d" && npm ci --dry-run $flags >/dev/null 2>&1); then
      echo "!! $nom : npm ci échoue — le déploiement s'arrête avant le build"
      (cd "$d" && npm ci --dry-run $flags 2>&1 |
        grep -E 'Missing:|npm error code' | head -3 | sed 's/^/     /')
      defauts=$((defauts + 1))
    fi
  fi
fi

# ── 2. ce qui est servi est-il plus récent que ce qui est poussé ?
if [ -n "$dom" ]; then
  servi=$(curl -sI -m 20 "https://$dom/" | grep -i '^last-modified:' |
          cut -d' ' -f2- | tr -d '\r')
  if [ -n "$servi" ]; then
    ts_servi=$(date -j -f '%a, %d %b %Y %T %Z' "$servi" '+%s' 2>/dev/null ||
               date -d "$servi" '+%s' 2>/dev/null)
    ts_commit=$(cd "$d" && git log -1 --format=%ct 2>/dev/null)
    if [ -n "$ts_servi" ] && [ -n "$ts_commit" ] &&
       [ "$ts_commit" -gt $((ts_servi + 3600)) ]; then
      jours=$(( (ts_commit - ts_servi) / 86400 ))
      echo "!! $nom : en ligne depuis $jours jour(s) de retard sur le dernier commit"
      echo "     servi le $servi"
      defauts=$((defauts + 1))
    fi
  fi
fi

[ "$defauts" = "0" ] && echo "$nom : déploiement sain"
exit "$defauts"
