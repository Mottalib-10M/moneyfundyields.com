#!/usr/bin/env node
/**
 * check-saisie.mjs — peut-on taper ce qu'on veut dans les champs ? (RECETTE-SITE.md §17.2)
 *
 * Pourquoi ce contrôle existe. Le 2026-09-23, l'utilisateur a signalé trois pannes de
 * saisie sur trois sites différents, toutes invisibles depuis le code :
 *
 *   1. ordenadoliquido.pt : `<input type="number" step={50}>`. Le navigateur refuse
 *      toute valeur qui n'est pas un multiple de 50 et affiche « les deux valeurs
 *      valides les plus proches sont 0 et 50 ». Taper un salaire au hasard est
 *      impossible, et le calcul part sur une valeur fantôme.
 *   2. Un champ où l'on efface tout et où il reste un `0` ou un `1` collé : la valeur
 *      est renvoyée dans le champ à chaque frappe parce que l'état refuse le vide.
 *   3. brutanet.fr : taper « 500 » dans le champ annuel affiche « 5.04 ». Le champ
 *      annuel est calculé depuis le mensuel ; à chaque frappe la valeur est divisée,
 *      arrondie, puis réécrite dans le champ que l'utilisateur est en train de remplir.
 *
 * Aucune de ces trois pannes ne lève d'erreur. Elles ne se voient qu'en tapant.
 *
 * Ce que le script fait, sur chaque champ de saisie visible :
 *   a. Contrôle statique : un `type="number"` dont le `step` dépasse 1 interdit les
 *      valeurs intermédiaires. `step="any"` ou l'absence de `step` sont corrects.
 *   b. Effacement : tout sélectionner puis supprimer doit laisser le champ vide.
 *      Un `0` ou un `1` qui revient tout seul est un défaut.
 *   c. Frappe : taper « 1 » doit afficher « 1 », puis taper « 500 » doit afficher
 *      « 500 ». Toute autre valeur signifie que le champ réécrit ce qu'on tape.
 *
 * Usage : node check-saisie.mjs <dossier-du-site | https://domaine> [--max=20]
 * Sortie : liste des champs fautifs, code 1 s'il y en a.
 * Nécessite Playwright (global : npm i -g playwright && npx playwright install chromium).
 */
import { createServer } from 'node:http';
import { existsSync } from 'node:fs';
import { readFile, stat } from 'node:fs/promises';
import { join, extname, resolve } from 'node:path';
import { createRequire } from 'node:module';
import { execSync } from 'node:child_process';

const require = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = require('playwright')); }
catch { ({ chromium } = require(join(execSync('npm root -g').toString().trim(), 'playwright'))); }

const arg = process.argv[2];
const MAX = Number((process.argv.find((a) => a.startsWith('--max=')) || '--max=20').split('=')[1]);
if (!arg) { console.error('usage: check-saisie.mjs <site-dir | https://domain>'); process.exit(2); }

const TYPES = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.xml': 'application/xml', '.txt': 'text/plain', '.ico': 'image/x-icon', '.woff2': 'font/woff2' };

async function serve(dir) {
  // Astro sort dans `dist/`, Next en export statique dans `out/`. Sans ce choix,
  // un site Next donne « 0 page, 0 defaut » : un echec deguise en succes.
  // Astro sort dans `dist/`, Next dans `out/`, et un site ecrit a la main est servi
  // depuis la racine du depot. Sans ce dernier cas, ces sites rendent « 0 page ».
  const root = ['dist', 'out'].map((d) => resolve(dir, d)).find((d) => existsSync(d))
    || (existsSync(join(resolve(dir), 'index.html')) ? resolve(dir) : resolve(dir, 'dist'));
  const server = createServer(async (req, res) => {
    const p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    let f = join(root, p);
    try { if ((await stat(f)).isDirectory()) f = join(f, 'index.html'); } catch { f = f + '.html'; }
    try { const body = await readFile(f); res.writeHead(200, { 'content-type': TYPES[extname(f)] || 'application/octet-stream' }); res.end(body); }
    catch { res.writeHead(404); res.end('404'); }
  });
  await new Promise((r) => server.listen(0, '127.0.0.1', r));
  return { base: `http://127.0.0.1:${server.address().port}`, server };
}

async function sitemapUrls(b) {
  const seen = new Set(); const out = new Set();
  const todo = [`${b}/sitemap.xml`, `${b}/sitemap-index.xml`];
  while (todo.length) {
    const u = todo.pop(); if (seen.has(u)) continue; seen.add(u);
    const r = await fetch(u).catch(() => null); if (!r || !r.ok) continue;
    for (const [, loc] of (await r.text()).matchAll(/<loc>([^<]+)<\/loc>/g)) {
      const l = loc.replace(/^https?:\/\/[^/]+/, b);
      if (l.endsWith('.xml')) todo.push(l); else out.add(l);
    }
  }
  return [...out];
}

const live = /^https?:\/\//.test(arg);
let base, server;
if (live) base = arg.replace(/\/$/, ''); else ({ base, server } = await serve(arg));

// On ne teste que les pages qui portent un calculateur, et au plus MAX d'entre elles :
// la saisie se teste frappe par frappe, c'est lent.
const toutes = await sitemapUrls(base);
const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const page = await ctx.newPage();
page.setDefaultTimeout(5000); // une action bloquée ne doit jamais garder le verrou Playwright (2026-10-22)

const pages = [];
for (const u of toutes) {
  if (pages.length >= MAX) break;
  await page.goto(u, { waitUntil: 'domcontentloaded' }).catch(() => {});
  const n = await page.locator('input[type="number"], input[inputmode="decimal"], input[inputmode="numeric"]').count();
  if (n) pages.push(u);
}

const fautes = [];
for (const u of pages) {
      // Pas de `networkidle` : une balise de mesure chargée en différé empêche
      // le réseau de retomber au repos et chaque page consommait alors ses
      // trente secondes de délai (netsalaire.com, 2026-09-24). `load` suffit :
      // les feuilles de style et les images sont là, c'est tout ce qu'il faut.
  await page.goto(u, { waitUntil: 'load' }).catch(() => {});
  await page.waitForTimeout(250);
  const chemin = u.replace(base, '') || '/';

  // a) contrôle statique du pas
  for (const mauvais of await page.evaluate(() => {
    const out = [];
    for (const el of document.querySelectorAll('input[type="number"]')) {
      const r = el.getBoundingClientRect();
      if (r.width < 2 || r.height < 2) continue;
      const s = el.getAttribute('step');
      if (s && s !== 'any' && Number(s) > 1) {
        out.push({ id: el.id || el.name || '(sans id)', step: s });
      }
    }
    return out;
  })) {
    fautes.push(`${chemin} — #${mauvais.id} : step="${mauvais.step}" interdit les valeurs intermédiaires`);
  }

  // b) et c) effacement puis frappe
  const champs = await page.$$('input[type="number"]:visible, input[inputmode="decimal"]:visible, input[inputmode="numeric"]:visible');
  for (const ch of champs.slice(0, 8)) {
    const id = await ch.evaluate((e) => e.id || e.name || e.getAttribute('aria-label') || '(sans id)');
    try {
      // b) effacement. On vide par `fill('')`, qui sélectionne le contenu et émet
      //    l'événement d'entrée comme le ferait un utilisateur. Ne PAS passer par
      //    « Control+A puis Delete » : dans un champ de saisie, Control+A ramène le
      //    curseur en début de ligne au lieu de tout sélectionner, et Delete efface
      //    alors le premier caractère. Le contrôle accusait ainsi les sites d'un
      //    défaut qui n'était que le sien — « 1500 » devenait « 500 », et taper
      //    « 1 » par-dessus donnait « 100 », exactement le symptôme recherché.
      await ch.click();
      await ch.fill('');
      await page.waitForTimeout(120);
      const vide = await ch.inputValue();
      if (vide !== '') fautes.push(`${chemin} — #${id} : ne se vide pas, « ${vide} » reste après effacement`);

      // c) frappe de « 1 » puis de « 500 », caractère par caractère
      for (const attendu of ['1', '500']) {
        await ch.click();
        await ch.fill('');
        await ch.type(attendu, { delay: 60 });
        await page.waitForTimeout(180);
        const v = (await ch.inputValue()).replace(/\s| /g, '');
        if (v !== attendu) fautes.push(`${chemin} — #${id} : « ${attendu} » tapé, « ${v} » affiché`);
      }
    } catch (e) {
      fautes.push(`${chemin} — #${id} : champ inutilisable (${e.constructor.name})`);
    }
  }
}
await ctx.close();
await browser.close();
server?.close();

console.log(`check-saisie: ${pages.length} page(s) à calculateur, ${fautes.length} défaut(s)`);
for (const f of fautes.slice(0, 50)) console.log('  ' + f);
if (fautes.length > 50) console.log(`  … et ${fautes.length - 50} de plus`);
process.exit(fautes.length ? 1 : 0);
