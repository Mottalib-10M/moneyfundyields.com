#!/usr/bin/env bash
# Ping IndexNow (Bing, Yandex, Seznam…) avec toutes les URL du sitemap, après déploiement.
# RECETTE §13 et §26 (2026-10-16) : la clé et le site viennent de la configuration DU site
# (src/data/site-config.ts : SITE_URL, INDEXNOW_KEY ; ou variables SITE / INDEXNOW_KEY),
# jamais d'une valeur écrite en dur — la trame portait celle de nettolohn-rechner.ch.
# Usage : scripts/indexnow.sh [https://mon-site.tld]      (depuis la racine du site)
#         scripts/indexnow.sh --dry-run                    (affiche ce qui serait envoyé)
set -euo pipefail
cd "$(dirname "$0")/.."
DRY=0; ARG=""
for a in "$@"; do case "$a" in --dry-run) DRY=1 ;; *) ARG="$a" ;; esac; done
CFG=src/data/site-config.ts
lire() { [ -f "$CFG" ] && sed -nE "s/^export const $1[^=]*= *['\"]([^'\"]+)['\"].*/\1/p" "$CFG" | head -1 || true; }
SITE="${ARG:-${SITE:-$(lire SITE_URL)}}"; SITE="${SITE%/}"
KEY="${INDEXNOW_KEY:-$(lire INDEXNOW_KEY)}"
[ -n "$SITE" ] || { echo "indexnow : SITE_URL introuvable ($CFG) — passer l'URL en argument" >&2; exit 1; }
[[ "$KEY" =~ ^[A-Za-z0-9-]{8,128}$ ]] || { echo "indexnow : INDEXNOW_KEY absente ou invalide dans $CFG" >&2; exit 1; }
[ -f "public/$KEY.txt" ] || { echo "indexnow : public/$KEY.txt manquant (le fichier de clé doit être publié)" >&2; exit 1; }
[ "$(tr -d '[:space:]' < "public/$KEY.txt")" = "$KEY" ] || { echo "indexnow : public/$KEY.txt ne contient pas la clé" >&2; exit 1; }
HOST=$(echo "$SITE" | sed -E 's#https?://##; s#/.*##')
# Le sitemap peut être un index (sitemap-index.xml → sitemap-0.xml…) : on suit les sous-sitemaps.
# En --dry-run, le sitemap est lu dans dist/ quand le site est construit (rien n'est en ligne).
lire_url() { local f="dist/${1#"$SITE"/}"; if [ "$DRY" = 1 ] && [ -f "$f" ]; then cat "$f"; else curl -fsS -m 30 "$1"; fi; }
locs() { lire_url "$1" | grep -oE '<loc>[^<]+</loc>' | sed -E 's#</?loc>##g'; }
URLS=""
for s in $(locs "$SITE/sitemap-index.xml" 2>/dev/null || locs "$SITE/sitemap.xml" 2>/dev/null || true); do
  case "$s" in *.xml) URLS+="$(locs "$s" || true)"$'\n' ;; *) URLS+="$s"$'\n' ;; esac
done
URLS=$(printf '%s' "$URLS" | grep -E "^https?://$HOST(/|$)" | sort -u || true)
N=$(printf '%s' "$URLS" | grep -c . || true)
[ "$N" -gt 0 ] || { echo "indexnow : aucune URL de $HOST dans le sitemap" >&2; exit 1; }
JSON=$(printf '%s\n' "$URLS" | jq -R . | jq -s --arg h "$HOST" --arg k "$KEY" --arg l "$SITE/$KEY.txt" '{host:$h,key:$k,keyLocation:$l,urlList:.}')
if [ "$DRY" = 1 ]; then echo "$JSON" | jq '{host,key,keyLocation,urls:(.urlList|length)}'; exit 0; fi
# IndexNow refuse (403) une clé que le site ne publie pas : on le vérifie avant d'envoyer.
EN_LIGNE=$(curl -fsS -m 15 "$SITE/$KEY.txt" 2>/dev/null | tr -d '[:space:]' || true)
[ "$EN_LIGNE" = "$KEY" ] || { echo "indexnow : $SITE/$KEY.txt n'est pas en ligne — déployer d'abord" >&2; exit 1; }
echo "IndexNow : $N URL de $HOST"
curl -s -X POST "https://api.indexnow.org/indexnow" -H "Content-Type: application/json; charset=utf-8" \
  -d "$JSON" -w "\nHTTP %{http_code}\n"
