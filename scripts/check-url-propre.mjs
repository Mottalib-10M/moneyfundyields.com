#!/usr/bin/env node
/**
 * check-url-propre.mjs — une page = une seule URL, identique partout (RECETTE-SITE.md §18).
 *
 * Pourquoi ce contrôle existe. Le 2026-10-10, l'éditeur ouvre
 * https://realsalary.co.uk/hourly-rate/ et la barre d'adresse devient aussitôt
 * https://realsalary.co.uk/hourly-rate/#salary=30000, sans qu'il ait rien touché.
 * Chaque calculateur écrivait son état dans l'URL depuis un `useEffect` exécuté au
 * montage : la valeur par défaut partait dans l'adresse dès le chargement. La règle
 * existait déjà (« après une interaction, et seulement après », §18), mais aucun
 * contrôle ne la vérifiait : le build était propre, le HTML aussi, le défaut ne se
 * voyait qu'en ouvrant la page dans un navigateur.
 *
 * La règle de l'éditeur : l'URL d'une page est la même, au caractère près (barre
 * finale comprise), dans le sitemap, dans la balise canonical, dans les liens, et
 * dans la barre d'adresse à l'ouverture. L'état du calculateur ne s'écrit dans
 * l'adresse qu'après une action de l'utilisateur.
 *
 * Ce que le script vérifie, pour chaque URL du sitemap :
 *   a. La page répond 200 à cette adresse exacte, sans aucune redirection.
 *   b. Sa balise canonical désigne exactement cette adresse (même chemin, même barre finale).
 *   c. Après chargement complet et hydratation, sans aucun clic ni frappe, la barre
 *      d'adresse n'a pas changé : ni fragment `#…`, ni paramètre `?…`, ni chemin modifié.
 *
 * Usage : node check-url-propre.mjs <dossier-du-site | https://domaine> [--attente=2500] [--max=N]
 * Sortie : liste des pages fautives, code 1 s'il y en a.
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
// L'hydratation `client:idle` et l'écriture différée (300 ms) se terminent bien avant
// 2,5 s ; en dessous, un défaut pourrait passer inaperçu.
const MAX = Number((process.argv.find((a) => a.startsWith('--max=')) || '--max=100000').split('=')[1]);
const ATTENTE = Number((process.argv.find((a) => a.startsWith('--attente=')) || '--attente=2500').split('=')[1]);
if (!arg) { console.error('usage: check-url-propre.mjs <site-dir | https://domain>'); process.exit(2); }

const TYPES = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.xml': 'application/xml', '.txt': 'text/plain', '.ico': 'image/x-icon', '.woff2': 'font/woff2' };

async function serve(dir) {
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
      const l = loc.trim().replace(/^https?:\/\/[^/]+/, b);
      if (l.endsWith('.xml')) todo.push(l); else out.add(l);
    }
  }
  return [...out];
}

const live = /^https?:\/\//.test(arg);
let base, server;
if (live) base = arg.replace(/\/$/, ''); else ({ base, server } = await serve(arg));

const urls = (await sitemapUrls(base)).slice(0, MAX);
const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
const page = await ctx.newPage();
const chemin = (u) => { const x = new URL(u); return x.pathname + x.search + x.hash; };

const fautes = [];
for (const u of urls) {
  const c = chemin(u);
  // a) réponse directe, sans redirection
  const redirs = [];
  const onResp = (r) => { if (r.request().isNavigationRequest() && r.status() >= 300 && r.status() < 400) redirs.push(`${r.status()} ${chemin(r.url())}`); };
  page.on('response', onResp);
  const resp = await page.goto(u, { waitUntil: 'load' }).catch(() => null);
  page.off('response', onResp);
  if (!resp) { fautes.push(`${c} — ne charge pas`); continue; }
  if (redirs.length) fautes.push(`${c} — redirection depuis l'URL du sitemap (${redirs.join(', ')})`);
  if (resp.status() !== 200) fautes.push(`${c} — répond ${resp.status()}`);

  // b) canonical identique à l'URL du sitemap, barre finale comprise
  const canon = await page.evaluate(() => document.querySelector('link[rel="canonical"]')?.getAttribute('href') || '');
  if (!canon) fautes.push(`${c} — pas de balise canonical`);
  else {
    let cc; try { cc = new URL(canon, u).pathname; } catch { cc = canon; }
    if (cc !== new URL(u).pathname) fautes.push(`${c} — canonical différente : ${cc}`);
  }

  // c) aucune réécriture de l'adresse sans interaction
  await page.waitForTimeout(ATTENTE);
  const apres = page.url();
  if (apres !== u) fautes.push(`${c} — l'adresse devient ${chemin(apres)} sans aucune interaction`);
}
await ctx.close();
await browser.close();
server?.close();

console.log(`check-url-propre: ${urls.length} page(s) du sitemap, ${fautes.length} défaut(s)`);
for (const f of fautes.slice(0, 60)) console.log('  ' + f);
if (fautes.length > 60) console.log(`  … et ${fautes.length - 60} de plus`);
process.exit(fautes.length ? 1 : 0);
