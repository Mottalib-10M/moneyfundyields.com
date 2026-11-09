#!/usr/bin/env node
/**
 * check-nombres.mjs — les montants sont-ils lisibles ? (RECETTE-SITE.md §4.1)
 *
 * Signale les champs de saisie qui affichent un nombre brut : cinq chiffres ou plus
 * sans separateur de milliers, ou trois decimales et plus apres la virgule.
 *
 * Deux pieges, tous deux rencontres en ecrivant ce script :
 *
 *   - **Le point est le separateur de milliers en espagnol**, pas une virgule
 *     decimale. « 30.000 » est correct ; une premiere version le signalait a tort.
 *   - **Le portugais et l'espagnol ne groupent pas sous dix mille.** « 1500 » y est
 *     la bonne ecriture, d'ou le seuil a cinq chiffres et non quatre.
 *
 * Un curseur, une case a cocher ou un bouton radio n'affiche pas sa valeur : ils
 * sont ecartes, et le curseur refuserait de toute facon un separateur.
 *
 * Usage : node check-nombres.mjs <dossier-du-site>
 * Necessite Playwright.
 */
import { createServer } from 'node:http';
import { readFileSync, statSync, existsSync, readdirSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { createRequire } from 'node:module';
import { execSync } from 'node:child_process';
const require = createRequire(import.meta.url);
const { chromium } = require(join(execSync('npm root -g').toString().trim(), 'playwright'));
// Corps de la fonction estCode(i), partagé avec le test (node check-nombres.mjs --test).
const EST_CODE = `
  const ac = (i.getAttribute('autocomplete') || '').toLowerCase();
  if (/(^|\\s)(postal-code|tel|tel-national|cc-number|cc-csc|one-time-code|bday-year)(\\s|$)/.test(ac)) return true;
  if (/^(cp|cap)$/i.test(i.id || '') || /^(cp|cap)$/i.test(i.name || '')) return true;   // CP, CAP italien : seulement en identifiant
  const lab = i.id && document.querySelector('label[for="' + CSS.escape(i.id) + '"]');
  const nom = [i.id, i.name, i.getAttribute('aria-label'), i.placeholder, lab && lab.textContent].join(' ').toLowerCase();
  return /\\b(plz|postleitzahl|postal|postcode|post code|zip|zipcode|code postal|codepostal|código postal|codigo postal|postinumero|postnummer|postnr)\\b/.test(nom);
`;
const dir = process.argv[2];
if (dir === '--test') {   // non-régression : node check-nombres.mjs --test
  const br = await chromium.launch(); const pg = await br.newPage();
  await pg.setContent(`<html lang="de"><body>
    <input id="a" autocomplete="postal-code" value="10115"><label for="b">PLZ</label><input id="b" value="80331">
    <input name="zip" value="90210"><input id="brutto" value="45000"><input id="c" value="1.500,125">
    <input id="d" inputmode="numeric" value="12.000"></body></html>`);
  const fautes = await pg.evaluate((src) => { const estCode = new Function('i', src);
    return [...document.querySelectorAll('input')].filter((i) => !estCode(i) && (/^\d{5,}$/.test(i.value) || /,\d{3,}/.test(i.value))).map((i) => i.id || i.name); }, EST_CODE);
  await br.close();
  const ok = JSON.stringify(fautes) === JSON.stringify(['brutto', 'c']);
  console.log('check-nombres --test :', ok ? 'OK' : 'ÉCHEC ' + JSON.stringify(fautes)); process.exit(ok ? 0 : 1);
}
// Astro sort dans `dist/`, Next dans `out/`, et un site ecrit a la main est servi
// depuis la racine du depot.
const root = ['dist', 'out'].map((d) => resolve(dir, d)).find(existsSync)
  || (existsSync(join(resolve(dir), 'index.html')) ? resolve(dir) : null);
if (!root) { console.error('aucune sortie trouvée : ni dist/, ni out/, ni index.html à la racine'); process.exit(2); }
const srv = createServer((q, r) => {
  let f = join(root, decodeURIComponent(new URL(q.url, 'http://x').pathname));
  try { if (statSync(f).isDirectory()) f = join(f, 'index.html'); } catch { f += '.html'; }
  // Lire le fichier AVANT d'ecrire l'en-tete : sinon une lecture qui echoue laisse
  // l'en-tete 200 deja envoye et le serveur lance ERR_HTTP_HEADERS_SENT.
  let corps = null;
  try { corps = readFileSync(f); } catch { /* fichier absent */ }
  if (corps === null) { r.writeHead(404); r.end(); return; }
  r.writeHead(200, { 'content-type': f.endsWith('.css') ? 'text/css' : f.endsWith('.js') ? 'text/javascript' : 'text/html' });
  r.end(corps);
});
await new Promise((r) => srv.listen(0, '127.0.0.1', r));
const base = 'http://127.0.0.1:' + srv.address().port;
// Pages a calculateur : celles du sitemap qui portent un champ de saisie.
const urls = new Set();
for (const f of ['sitemap.xml', 'sitemap-index.xml', 'sitemap-0.xml']) {
  const r = await fetch(`${base}/${f}`).catch(() => null);
  if (!r || !r.ok) continue;
  for (const [, loc] of (await r.text()).matchAll(/<loc>([^<]+)<\/loc>/g)) {
    const u = loc.replace(/^https?:\/\/[^/]+/, base);
    if (!u.endsWith('.xml')) urls.add(u);
  }
}
const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1440, height: 900 } });
const fautes = [];
let vues = 0;
for (const u of [...urls].slice(0, 40)) {
      // Pas de `networkidle` : une balise de mesure chargée en différé empêche
      // le réseau de retomber au repos et chaque page consommait alors ses
      // trente secondes de délai (netsalaire.com, 2026-09-24). `load` suffit :
      // les feuilles de style et les images sont là, c'est tout ce qu'il faut.
  await p.goto(u, { waitUntil: 'load' }).catch(() => {});
  await p.waitForTimeout(200);
  const r = await p.evaluate((src) => {
    const estCode = new Function('i', src);
    const out = [];
    for (const i of document.querySelectorAll('input')) {
      // Un curseur, une case ou un bouton radio n'affiche pas sa valeur : la
      // mettre en forme n'aurait aucun sens, et le curseur la refuserait.
      if (!i.offsetWidth || i.readOnly) continue;
      if (['range', 'checkbox', 'radio', 'hidden', 'submit', 'button'].includes(i.type)) continue;
      // Un code n'est pas un montant : code postal (PLZ, CP, ZIP), téléphone, carte, code reçu.
      // « 10115 » dans un champ autocomplete="postal-code" était signalé (2026-10-16, RECETTE §26).
      if (estCode(i)) continue;
      const v = i.value;
      // Un montant de quatre chiffres ou plus sans separateur, ou avec decimales.
      // Le portugais et l'espagnol ne groupent pas sous dix mille : « 1500 » y est
      // correct. On ne signale donc qu'a partir de cinq chiffres.
      // Attention : le point est le separateur de MILLIERS en espagnol, pas une
      // virgule decimale. « 30.000 » est correct ; seules trois decimales ou plus
      // apres une virgule trahissent un arrondi manquant.
      // La virgule groupe les milliers en anglais : « 10,000 » y est correct,
      // et le signaler accusait à tort les pages anglaises d'un site bilingue
      // (calcolalordonetto.it, 2026-09-24). On ne retient donc la règle de la
      // virgule que dans les langues où elle sépare les décimales.
      const langue = (document.documentElement.lang || '').slice(0, 2).toLowerCase();
      // es-MX (et l'espagnol d'Amérique du Nord et centrale) écrit 15,000.50 comme l'anglais (CLDR).
      const pointDecimal = /^es-(MX|US|PR|DO|GT|HN|NI|PA|SV)/i.test(document.documentElement.lang || '');
      const virguleDecimale = !pointDecimal && !['en', 'ja', 'zh', 'ko', 'ar', 'hi', 'he', 'th'].includes(langue);
      if (/^\d{5,}$/.test(v) || (virguleDecimale && /,\d{3,}/.test(v))) {
        out.push(`${i.id || i.name || '(sans id)'} = « ${v} »`);
      }
    }
    return out;
  }, EST_CODE);
  vues++;
  for (const m of r) fautes.push(`${u.replace(base, '') || '/'} — ${m}`);
}
await b.close(); srv.close();
console.log(`  ${vues} page(s), ${fautes.length} champ(s) mal formaté(s)`);
[...new Set(fautes)].slice(0, 12).forEach((f) => console.log('    ' + f));
