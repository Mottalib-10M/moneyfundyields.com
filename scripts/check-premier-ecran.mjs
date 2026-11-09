#!/usr/bin/env node
/**
 * check-premier-ecran.mjs — le simulateur se voit sans défiler (RECETTE-SITE.md §5, règle du 2026-10-11).
 *
 * Remarque de l'éditeur (2026-10-11) : « il faut que je déroule pour voir le simulateur, je ne le
 * vois pas sur mon premier écran ». Le comptage de mots dans le HTML ne le voyait pas : un tableau,
 * une grille d'États ou un chapeau déplié repoussaient le formulaire sous la ligne de flottaison.
 * Seul le navigateur sait ce qui est dessiné : ce contrôle mesure la page rendue.
 *
 * Sur chaque page qui porte un simulateur (premier `main form` avec un champ visible) :
 *   1. Ordinateur (1366 × 768) : le premier champ du simulateur commence dans les 60 % du haut
 *      de l'écran, ET le résultat (`[data-resultat]`, sinon le premier `[aria-live]` de main)
 *      commence dans l'écran : on voit la question et la réponse sans toucher la molette.
 *   2. Téléphone (390 × 844) : le premier champ commence dans l'écran.
 *   3. Rien de lourd avant le simulateur : aucun tableau ni grille de plus de 6 lignes au-dessus.
 * Un mini-simulateur placé dans le corps d'un guide (RECETTE §9.3) porte
 * `data-simulateur-secondaire` sur son formulaire : il n'est alors pas contrôlé.
 *
 * Usage : node check-premier-ecran.mjs <dossier-du-site | https://domaine> [--max=400]
 * Sortie : pages fautives, code 1 s'il y en a. Nécessite Playwright (comme check-layout.mjs).
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
const MAX = Number((process.argv.find((a) => a.startsWith('--max=')) || '--max=400').split('=')[1]);
if (!arg) { console.error('usage: check-premier-ecran.mjs <site-dir | https://domain>'); process.exit(2); }

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
  return { base: `http://127.0.0.1:${server.address().port}`, server, root };
}

async function pagesFrom(base, root) {
  // Pages du sitemap (indexables) ; sinon parcours de dist.
  const urls = [];
  const get = async (u) => { try { const r = await fetch(u); return r.ok ? await r.text() : ''; } catch { return ''; } };
  const idx = await get(`${base}/sitemap-index.xml`) || await get(`${base}/sitemap.xml`);
  const locs = [...idx.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1]);
  for (const l of locs) {
    if (l.endsWith('.xml')) {
      const sub = await get(base + new URL(l).pathname);
      urls.push(...[...sub.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => base + new URL(m[1]).pathname));
    } else urls.push(base + new URL(l).pathname);
  }
  return [...new Set(urls)].slice(0, MAX);
}

function mesure() {
  const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
  // Curseurs ARIA compris (globalfinancepro.com, 2026-10-12 : les sliders n'étaient pas vus).
  // Champs désactivés exclus : une liste à cocher Markdown (cases disabled) n'est pas un simulateur (cartegrisesimple.fr, 2026-10-12).
  const ctrlSel = 'input:not([type=hidden]):not([type=search]):not([disabled]), select:not([disabled]), textarea:not([disabled]), button[aria-pressed], [role=slider], [role=spinbutton]';
  const inMain = ctrlSel.split(',').map((x) => `main ${x.trim()}`).join(', ');
  // Un formulaire de contact ou de lettre d'information (e-mail, zone de texte) n'est pas un simulateur :
  // sans cette exclusion, les pages sans calculateur de netsalaire.com étaient signalées (2026-10-12).
  const contact = (f) => !!f.querySelector('input[type=email], textarea') || /contact|newsletter|subscribe|mailto:/i.test((f.getAttribute('action') || '') + ' ' + (f.id || '') + ' ' + (f.className || ''));
  const forms = [...document.querySelectorAll('main form')].filter((f) => !contact(f) && !f.closest('[data-simulateur-secondaire]') && !f.hasAttribute('data-simulateur-secondaire') && [...f.querySelectorAll(ctrlSel)].some(vis));
  // Un simulateur sans <form> (boutons et champs dans un bloc) : premier bloc de main qui a un champ.
  let calc = forms[0];
  if (!calc) {
    const c = [...document.querySelectorAll(inMain)].find((e) => vis(e) && !e.closest('[data-simulateur-secondaire], nav, header, footer, details') && !(e.closest('form') && contact(e.closest('form'))) && e.type !== 'email' && e.tagName !== 'TEXTAREA');
    if (!c) return null;
    calc = c.closest('section, [class*=calc], [class*=rechner], [class*=simul], div') || c;
  }
  const first = [...calc.querySelectorAll(ctrlSel)].find(vis) || calc;
  const top = first.getBoundingClientRect().top + scrollY;
  const res = document.querySelector('main [data-resultat]') || [...document.querySelectorAll('main [aria-live]')].find((e) => vis(e) && !e.closest('[data-simulateur-secondaire]'));
  const resTop = res ? res.getBoundingClientRect().top + scrollY : null;
  // Blocs lourds au-dessus du simulateur
  const lourds = [...document.querySelectorAll('main table, main [role=table], main ul, main ol, main [class*=grid]')].filter((e) => {
    if (!vis(e) || e.closest('form, nav, header, footer, details, [data-chrome]') || calc.contains(e) || e.contains(calc)) return false;
    if (e.getBoundingClientRect().top + scrollY >= top) return false;
    const n = e.matches('table, [role=table]') ? e.querySelectorAll('tr, [role=row]').length : e.children.length;
    return n > 6;
  }).map((e) => `${e.tagName.toLowerCase()}(${e.matches('table') ? e.querySelectorAll('tr').length : e.children.length})`);
  return { top: Math.round(top), resTop: resTop == null ? null : Math.round(resTop), lourds, h: innerHeight };
}

const local = !/^https?:\/\//.test(arg);
const srv = local ? await serve(arg) : { base: arg.replace(/\/$/, '') };
const urls = await pagesFrom(srv.base, srv.root);
const browser = await chromium.launch();
const desk = await browser.newPage({ viewport: { width: 1366, height: 768 } });
const phone = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
let fautes = 0, avecSimu = 0;
// Une mesure qui ne rend jamais la main ne doit pas garder le verrou Playwright (25 min bloquées
// sur us-heating-oil-propane, 2026-10-22) : 15 s par mesure, 20 min pour tout le contrôle.
const borne = (p, ms = 15000) => Promise.race([p, new Promise((r) => setTimeout(() => r(null), ms))]);
setTimeout(() => { console.log('check-premier-ecran : délai global de 20 min dépassé'); process.exit(2); }, 20 * 60 * 1000).unref();
for (const u of urls) {
  const errs = [];
  // Une page qui ne charge pas est une faute, pas une page « sans simulateur » : sous une
  // machine chargée, l'échec silencieux faisait passer 26 pages sur 46 (2026-10-11).
  const ok = await desk.goto(u, { waitUntil: 'networkidle', timeout: 60000 }).then((r) => !r || r.ok()).catch(() => false);
  if (!ok) { fautes++; console.log(`✗ ${new URL(u).pathname}\n   - page non chargée (délai ou erreur) : relancer`); continue; }
  // Chapeau replié (RECETTE §26, 2026-10-02) : sans sa feuille de style, la case à cocher s'affiche
  // brute et le texte reste déplié. Cinq sites sur douze l'avaient ainsi le 2026-10-24 (composant
  // Clamp.astro recopié sans ses règles .clamp-*), et aucun contrôle ne le voyait.
  const replie = await borne(desk.evaluate(() => [...document.querySelectorAll('.clamp-toggle, .clamp-rest')].filter((e) => {
    const s = getComputedStyle(e), r = e.getBoundingClientRect();
    return e.matches('.clamp-rest') ? s.display !== 'none' : s.opacity !== '0' && s.display !== 'none' && r.width > 1;
  }).length).catch(() => 0));
  if (replie) { fautes++; console.log(`✗ ${new URL(u).pathname}\n   - texte replié affiché en entier (case à cocher visible ou .clamp-rest affiché) : règles .clamp-* absentes de la feuille de style`); }
  // Début visible réduit à un fragment : « Seit 1. » puis « Weiterlesen » (eu-rent-indexation, 2026-10-24),
  // le découpage avait pris l'ordinal de « 1. April » pour une fin de phrase.
  const court = await borne(desk.evaluate(() => [...document.querySelectorAll('.clamp p')].filter((p) => p.querySelector('.clamp-rest'))
    .map((p) => [...p.childNodes].filter((n) => !(n.classList && n.classList.contains('clamp-rest'))).map((n) => n.textContent).join('').trim())
    .filter((t) => (/[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]/.test(t) ? t.length < 8 : t.split(/\s+/).length < 4))).catch(() => []));  // une vraie phrase courte (« Morocco has a short CDC list. ») passe ; chinois, japonais, coréen : sans espaces, on compte les caractères
  if (court?.length) { fautes++; console.log(`✗ ${new URL(u).pathname}\n   - texte replié coupé trop tôt : « ${court[0]} » (découpage des phrases dans Clamp.astro)`); }
  const d = await borne(desk.evaluate(mesure).catch(() => null));
  if (!d) continue;
  avecSimu++;
  if (d.top > d.h * 0.6) errs.push(`ordinateur : premier champ à ${d.top} px (limite ${Math.round(d.h * 0.6)})`);
  if (d.resTop == null) errs.push('résultat introuvable : marquer le bloc du résultat avec data-resultat');
  else if (d.resTop > d.h - 40) errs.push(`ordinateur : résultat à ${d.resTop} px, hors du premier écran (${d.h})`);
  if (d.lourds.length) errs.push(`bloc lourd au-dessus du simulateur : ${d.lourds.join(', ')}`);
  await phone.goto(u, { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
  const m = await borne(phone.evaluate(mesure).catch(() => null));
  if (m && m.top > m.h - 60) errs.push(`téléphone : premier champ à ${m.top} px, hors du premier écran (${m.h})`);
  // Liste coupée parce qu'elle partage sa ligne : « United St… », « Mainland … » (eta et eu-rent, 2026-10-24).
  const coupees = await borne(phone.evaluate(() => {
    const ctx = document.createElement('canvas').getContext('2d');
    return [...document.querySelectorAll('main select')].filter((s) => {
      const r = s.getBoundingClientRect(); if (!r.width || r.width >= innerWidth * 0.6) return false;
      const cs = getComputedStyle(s); ctx.font = `${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
      const txt = s.options[s.selectedIndex]?.text || '';
      return ctx.measureText(txt).width > s.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight) + 2;
    }).map((s) => s.options[s.selectedIndex]?.text);
  }).catch(() => []));
  if (coupees?.length) errs.push(`téléphone : liste tronquée sur une demi-largeur (« ${coupees[0]} ») : un champ par ligne sous 640 px`);
  if (errs.length) { fautes++; console.log(`✗ ${new URL(u).pathname}\n   - ${errs.join('\n   - ')}`); }
}
await browser.close();
srv.server?.close();
console.log(`check-premier-ecran : ${fautes} page(s) fautive(s) sur ${avecSimu} page(s) à simulateur (${urls.length} pages lues)`);
process.exit(fautes ? 1 : 0);
