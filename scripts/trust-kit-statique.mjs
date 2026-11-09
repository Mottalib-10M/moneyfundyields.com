#!/usr/bin/env node
/**
 * trust-kit-statique.mjs — la trame de confiance sur un site écrit à la main (§8).
 *
 * `trust-kit.mjs` est une intégration Astro : il s'accroche aux hooks du build et
 * ne sait rien faire d'un site sans générateur. netsalaire.com en est un — 33
 * fichiers HTML servis depuis la racine du dépôt — et il lui manquait, sur 29
 * pages, la date de mise à jour en haut et en bas, l'encart auteur, le lien vers
 * la méthodologie, et les champs `foundingDate` et `publishingPrinciples` de
 * l'Organization.
 *
 * Ce script produit exactement la même sortie, sur les fichiers eux-mêmes.
 *
 * La date vient du **dernier commit qui a touché le fichier**, jamais du dernier
 * commit du dépôt : une date globale ferait changer toutes les pages à chaque
 * déploiement, et Google traite alors la date comme non fiable sur tout le site.
 * Une fausse fraîcheur est pire que pas de date (§8.4).
 *
 * Usage : node trust-kit-statique.mjs <dossier> [--lang fr] [--about /fr/a-propos/]
 *                                     [--method /fr/methodologie/] [--auteur "Nom"]
 */
import { readFile, writeFile } from 'node:fs/promises';
import { readdirSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';
import { execFileSync } from 'node:child_process';

const arg = (nom, defaut) => {
  const i = process.argv.indexOf('--' + nom);
  return i > 0 ? process.argv[i + 1] : defaut;
};
const racine = process.argv[2];
if (!racine) { console.error('usage: trust-kit-statique.mjs <dossier> [--lang fr] …'); process.exit(2); }
const LANG = arg('lang', 'fr');
const ABOUT = arg('about', '/fr/a-propos/');
const METHOD = arg('method', '/fr/methodologie/');
const AUTEUR = arg('auteur', 'Radif Partners');
const FONDATION = arg('fondation', '2025-01-01');

const TEXTES = {
  fr: { maj: 'Mis à jour le', par: 'Publié par', methode: 'Méthode de calcul',
        avert: 'Estimation indicative : ce site ne remplace ni une décision de l’administration ni l’avis d’un professionnel.' },
  en: { maj: 'Updated', par: 'Published by', methode: 'How we calculate',
        avert: 'Indicative estimate: this site replaces neither an official decision nor professional advice.' },
};
const T = TEXTES[LANG] || TEXTES.en;

// Date lisible dans la langue de la page, en UTC : sans le fuseau force, une date
// construite à minuit recule d'un jour sur une machine à l'ouest de Greenwich.
const dateLisible = (iso) => {
  const d = new Date(`${iso}T12:00:00Z`);
  const s = new Intl.DateTimeFormat(LANG === 'fr' ? 'fr-FR' : 'en-GB',
    { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' }).format(d);
  // Français : « 1er octobre », jamais « 1 octobre ».
  return LANG === 'fr' ? s.replace(/^1 /, '1er ') : s;
};

const dateDuFichier = (f) => {
  try {
    const d = execFileSync('git', ['log', '-1', '--format=%cs', '--', relative(racine, f)],
      { cwd: racine, encoding: 'utf8' }).trim();
    if (d) return d;
  } catch { /* fichier non suivi */ }
  return new Date().toISOString().slice(0, 10);
};

const pages = [];
(function parcours(d) {
  for (const e of readdirSync(d)) {
    if (['_archives', '.git', 'node_modules', '__pycache__'].includes(e)) continue;
    const p = join(d, e);
    if (statSync(p).isDirectory()) parcours(p);
    else if (e === 'index.html' || e.endsWith('.html')) pages.push(p);
  }
})(racine);

let faits = 0, sautees = 0;
for (const f of pages) {
  let html = await readFile(f, 'utf8');
  // On ne touche ni aux pages non indexables, ni à celles déjà traitées.
  if (/<meta[^>]+robots[^>]+noindex/i.test(html) || html.includes('data-trust-kit')) { sautees++; continue; }
  if (!/<\/main>/i.test(html)) { sautees++; continue; }

  const date = dateDuFichier(f);
  const lisible = dateLisible(date);

  // Haut de page : juste après l'ouverture du <main>.
  const haut = `<p data-trust-kit class="trust-top" style="margin:0 0 .75rem;font-size:.8125rem;opacity:.75">`
    + `${T.maj} <time datetime="${date}">${lisible}</time></p>`;
  // Seulement sur une page de lecture (Article déclaré) : sur un simulateur ou un
  // accueil, la date reste en bas (RECETTE §8.4, 2026-10-15).
  if (/"@type"\s*:\s*"(?:Article|BlogPosting|NewsArticle)"/.test(html)) html = html.replace(/(<main\b[^>]*>)/i, `$1\n        ${haut}`);

  // Bas de page : dans le <footer>, car c'est là que le lecteur — et le contrôle —
  // cherchent la date, l'auteur et le lien vers la méthode.
  const bas = `\n      <div data-trust-kit class="trust-bottom" style="margin-top:1.5rem;padding-top:1rem;`
    + `border-top:1px solid #e2e8f0;font-size:.8125rem;opacity:.8">`
    + `<p>${T.avert}</p>`
    + `<p>${T.maj} <time datetime="${date}">${lisible}</time> · `
    + `<a href="${METHOD}">${T.methode}</a> · `
    + `${T.par} <a rel="author" href="${ABOUT}">${AUTEUR}</a></p></div>\n    `;
  if (/<\/footer>/i.test(html)) {
    const i = html.lastIndexOf('</footer>');
    html = html.slice(0, i) + bas + html.slice(i);
  } else {
    html = html.replace(/(<\/main>)/i, `${bas}$1`);
  }

  // Organization : compléter foundingDate et publishingPrinciples. On analyse le
  // JSON plutôt que de le tailler à l'expression régulière : l'objet contient des
  // accolades imbriquées, qu'un motif plat ne sait pas franchir.
  html = html.replace(/(<script[^>]*application\/ld\+json[^>]*>)([\s\S]*?)(<\/script>)/gi,
    (tout, ouvre, corps, ferme) => {
      let data;
      try { data = JSON.parse(corps); } catch { return tout; }
      let touche = false;
      const visite = (n) => {
        if (Array.isArray(n)) return n.forEach(visite);
        if (!n || typeof n !== 'object') return;
        if (n['@type'] === 'Organization') {
          if (!n.foundingDate) { n.foundingDate = FONDATION; touche = true; }
          if (!n.publishingPrinciples) { n.publishingPrinciples = METHOD; touche = true; }
        }
        Object.values(n).forEach(visite);
      };
      visite(data);
      return touche ? ouvre + JSON.stringify(data) + ferme : tout;
    });

  await writeFile(f, html);
  faits++;
}
console.log(`  trust-kit statique : ${faits} page(s) complétée(s), ${sautees} sautée(s)`);
