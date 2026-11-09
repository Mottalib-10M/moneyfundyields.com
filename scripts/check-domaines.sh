#!/bin/bash
# Lancé par zsh (« zsh check-domaines.sh »), $0 vaut le nom de la fonction : on repasse sous bash (2026-10-24).
[ -z "$BASH_VERSION" ] && exec bash "$0" "$@"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Disponibilité de domaines, interrogée au serveur whois du registre (RECETTE §16.1).
# Usage : check-domaines.sh domaine1.tld domaine2.tld …
# Toujours lancer d'abord sur un domaine connu pris (ex. google.com) : il doit répondre « pris ».
# Règle absolue du 2026-10-16 (RECETTE §16) : un domaine libre qui a déjà vécu (capture Wayback,
# quelle qu'elle soit) sort « REFUSÉ », jamais « LIBRE ». Seul « LIBRE » peut se proposer.
# Registre qui ne répond pas : « INCONNU », jamais « pris » ni « libre » (vérifier sur le site du registre).
chk(){ d=$1; tld=${d##*.}; case $tld in
 sg) s=whois.sgnic.sg;; nz) s=whois.irs.net.nz;; no) s=whois.norid.no;; be) s=whois.dns.be;; dk) s=whois.punktum.dk;; com|net) s=whois.verisign-grs.com;; fr) s=whois.nic.fr;; de) s=whois.denic.de;; ch) s=whois.nic.ch;; nl) s=whois.domain-registry.nl;; ie) s=whois.weare.ie;; pt) s=whois.dns.pt;; es) s=whois.nic.es;; it) s=whois.nic.it;; se) s=whois.iis.se;; pl) s=whois.dns.pl;; ma) s=whois.registre.ma;; ca) s=whois.cira.ca;; mx) s=whois.mx;; us) s=whois.nic.us;; uk) s=whois.nic.uk;; at) s=whois.nic.at;; fi) s=whois.fi;; au) s=whois.auda.org.au;; io) s=whois.nic.io;; *) echo "?      $d (extension non gérée)"; return;; esac
 out=$(perl -e 'alarm 25; exec @ARGV' whois -h $s $d 2>&1); rc=$?
 # Registre muet (délai dépassé, connexion refusée, réponse vide) : on ne conclut rien.
 # Avant le 2026-10-16, ce cas sortait « pris » : tous les .es l'étaient à tort (whois.nic.es ne répond pas).
 # Idem le 2026-10-24 : nic.at « % Quota exceeded » sortait « pris ».
 if [ $rc -ne 0 ] && [ -z "$(echo "$out" | tr -d '[:space:]')" ] || echo "$out" | grep -qiE "timed out|connection refused|connect: |Network is unreachable|getaddrinfo|no whois server|quota exceeded|rate limit|too many requests|exceeded the maximum" || [ -z "$(echo "$out" | tr -d '[:space:]')" ]; then
   case $tld in es) w="https://nic.es/sgnd/dominio/publicBuscarDominios.action?tDominio.nombreDominio=${d%.*}";; *) w="site du registre .$tld";; esac
   echo "INCONNU $d (registre muet : vérifier sur $w ; un témoin pris doit y répondre « Registrado »)"; sleep 1; return; fi
 if echo "$out" | grep -qiE "not found|no match|no entries found|Status:\s*(AVAILABLE|free)|Domain Not Found|No Data Found|no object found|is free|nothing found|Object_Not_Found|No information available about domain name"; then passe=$(python3 -I "$DIR/check-passe-domaine.py" "$d" 2>&1); case $? in 0) echo "LIBRE  $d (passé vierge)";; 1) echo "REFUSÉ $d (libre mais déjà vécu)"; echo "$passe" | sed 's/^/       /';; *) echo "REFUSÉ $d (libre, passé non vérifié)"; echo "$passe" | sed 's/^/       /';; esac; else echo "pris   $d"; fi; sleep 1; }
for d in "$@"; do chk "$d"; done
