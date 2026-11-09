#!/usr/bin/env node
/**
 * check-contraste.mjs — le texte est-il lisible sur son fond ? (RECETTE-SITE.md §10.3)
 *
 * Pourquoi ce contrôle existe. Le 2026-09-23, l'utilisateur a envoyé une capture de
 * indemnitelicenciement.fr : le titre « Calculateur d'indemnité de licenciement 2026 »
 * était invisible. Mesure : texte rgb(20, 23, 29) sur un dégradé rgb(0, 0, 119), soit
 * 1,08:1 là où il en faut 4,5. La cause est systématique et ne produit aucune erreur :
 * le conteneur porte `text-white`, mais la feuille du site pose une règle de base
 * `h1, h2, h3 { color: <gris très foncé> }`. Une règle qui vise l'élément l'emporte
 * toujours sur une couleur simplement héritée du parent, quelle que soit la
 * spécificité du parent. Le titre reprend donc le gris foncé, sur fond bleu nuit.
 *
 * Le même défaut avait déjà été trouvé à la main sur salarioliquido.pt. Le trouver
 * deux fois à l'œil sur deux sites signifie qu'il est sur tous les autres : d'où ce
 * contrôle, qui le cherche partout et sans exception.
 *
 * Ce que le script mesure, et les pièges qu'il évite :
 *
 *   1. La couleur est lue après rendu, puis convertie par un canvas. Sans cela,
 *      `oklch()` et `color()` — que Tailwind v4 produit — ne se parsent pas : un fond
 *      déclaré en oklch passait pour illisible ou, pire, pour parfait.
 *   2. Le fond effectif se calcule en remontant les ancêtres et en **composant** les
 *      couches translucides. Un `bg-white/10` sur un héros sombre n'est pas blanc.
 *   3. Les dégradés sont examinés stop par stop : un texte peut être lisible à gauche
 *      et illisible à droite du même bloc.
 *   4. Le seuil suit WCAG 2.1 AA : 4,5:1, ramené à 3:1 pour le grand texte (≥ 24 px,
 *      ou ≥ 18,66 px en gras), parce qu'un caractère épais se lit à moindre contraste.
 *
 * Usage : node check-contraste.mjs <dossier-du-site | https://domaine> [--max=400]
 *   - un dossier : sert <dossier>/dist en local (build frais obligatoire)
 *   - une URL    : lit le sitemap du site en ligne
 * Sortie : liste des textes fautifs, code 1 s'il y en a.
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
const MAX = Number((process.argv.find((a) => a.startsWith('--max=')) || '--max=400').split('=')[1]);
if (!arg) { console.error('usage: check-contraste.mjs <site-dir | https://domain>'); process.exit(2); }

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

// ── Exécuté dans la page ────────────────────────────────────────────────────
function inspecter() {
  const cv = document.createElement('canvas');
  cv.width = cv.height = 1;
  const cx = cv.getContext('2d', { willReadFrequently: true });

  /** Toute couleur CSS -> [r, g, b, a]. Le canvas fait le travail que `parseInt`
   *  ne peut pas faire sur `oklch()`, `color()` ou un nom de couleur. */
  const rgba = (c) => {
    if (!c) return null;
    cx.clearRect(0, 0, 1, 1);
    try { cx.fillStyle = '#000'; cx.fillStyle = c; } catch { return null; }
    cx.fillRect(0, 0, 1, 1);
    const d = cx.getImageData(0, 0, 1, 1).data;
    return [d[0], d[1], d[2], d[3] / 255];
  };

  /** Couche du dessus posée sur la couche du dessous. */
  const poser = (haut, bas) => {
    const a = haut[3];
    return [
      Math.round(haut[0] * a + bas[0] * (1 - a)),
      Math.round(haut[1] * a + bas[1] * (1 - a)),
      Math.round(haut[2] * a + bas[2] * (1 - a)),
      1,
    ];
  };

  const lum = ([r, g, b]) => {
    const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
  };
  const ratio = (x, y) => {
    const a = lum(x), b = lum(y);
    return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
  };

  /** Fonds effectifs sous un élément. Plusieurs valeurs quand un dégradé est
   *  rencontré : on rendra le verdict sur le pire de ses arrêts de couleur.
   *
   *  Un fond d'ancêtre n'est pris en compte que s'il **couvre réellement** la
   *  boîte du texte : le fond d'un élément ne se peint que dans sa propre boîte,
   *  et un enfant qui déborde se retrouve sur le fond du grand-parent. Sans cette
   *  vérification, le filet décoratif de 4 px du pied de page portugais — un
   *  dégradé aux couleurs du drapeau, ancêtre d'un bloc de 63 px qui le déborde —
   *  faisait passer 165 textes parfaitement lisibles pour illisibles sur rouge. */
  const couvre = (a, b) => {
    const A = a.getBoundingClientRect(), B = b.getBoundingClientRect();
    return A.top <= B.top + 1 && A.bottom >= B.bottom - 1
        && A.left <= B.left + 1 && A.right >= B.right - 1;
  };

  const fonds = (el) => {
    const couches = [];
    let n = el;
    while (n && n.nodeType === 1) {
      if (n !== el && !couvre(n, el)) { n = n.parentElement; continue; }
      const s = getComputedStyle(n);
      const img = s.backgroundImage;
      if (img && img !== 'none') {
        const stops = [...img.matchAll(/rgba?\([^)]+\)/g)].map((m) => rgba(m[0])).filter(Boolean);
        if (stops.length) { couches.push({ degrade: stops }); break; }
      }
      const bg = rgba(s.backgroundColor);
      if (bg && bg[3] > 0) {
        couches.push({ uni: bg });
        if (bg[3] >= 0.999) break;
      }
      n = n.parentElement;
    }
    // Sous tout cela, le blanc du navigateur.
    const base = [255, 255, 255, 1];
    const derniere = couches[couches.length - 1];
    const departs = derniere && derniere.degrade ? derniere.degrade : [derniere ? derniere.uni : base];
    return departs.map((dep) => {
      let fond = dep[3] >= 0.999 ? dep : poser(dep, base);
      for (let i = couches.length - 2; i >= 0; i--) {
        const c = couches[i];
        fond = poser(c.uni || c.degrade[0], fond);
      }
      return fond;
    });
  };

  const visible = (el) => {
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    return r.width > 1 && r.height > 1 && s.visibility !== 'hidden' && s.display !== 'none'
      && Number(s.opacity) > 0.05;
  };

  const out = [];
  const vus = new Set();
  for (const el of document.querySelectorAll('body *')) {
    // Seuls les éléments qui portent eux-mêmes du texte : sinon on juge un
    // conteneur sur la couleur d'un enfant qui n'est pas la sienne.
    const propre = [...el.childNodes]
      .filter((n) => n.nodeType === 3).map((n) => n.textContent.trim()).join(' ').trim();
    if (propre.length < 2) continue;
    if (!visible(el)) continue;
    const s = getComputedStyle(el);
    const txt = rgba(s.color);
    if (!txt || txt[3] < 0.05) continue;
    const taille = parseFloat(s.fontSize);
    const gras = Number(s.fontWeight) >= 700 || ['bold', 'bolder'].includes(s.fontWeight);
    const grand = taille >= 24 || (taille >= 18.66 && gras);
    const seuil = grand ? 3 : 4.5;

    let pire = Infinity, pireFond = null;
    for (const f of fonds(el)) {
      const t = txt[3] >= 0.999 ? txt : poser(txt, f);
      const r = ratio(t, f);
      if (r < pire) { pire = r; pireFond = f; }
    }
    if (pire >= seuil) continue;
    const cle = `${el.tagName}|${s.color}|${propre.slice(0, 40)}`;
    if (vus.has(cle)) continue;
    vus.add(cle);
    out.push({
      texte: propre.slice(0, 60),
      balise: el.tagName.toLowerCase(),
      classe: (el.className && String(el.className).slice(0, 60)) || '',
      couleur: s.color,
      fond: `rgb(${pireFond[0]}, ${pireFond[1]}, ${pireFond[2]})`,
      ratio: Math.round(pire * 100) / 100,
      seuil,
      taille: Math.round(taille),
    });
  }
  return out;
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
  return [...out].slice(0, MAX);
}

const live = /^https?:\/\//.test(arg);
let base, server;
if (live) base = arg.replace(/\/$/, ''); else ({ base, server } = await serve(arg));
const pages = await sitemapUrls(base);

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const page = await ctx.newPage();
const fautes = [];
for (const u of pages) {
      // Pas de `networkidle` : une balise de mesure chargée en différé empêche
      // le réseau de retomber au repos et chaque page consommait alors ses
      // trente secondes de délai (netsalaire.com, 2026-09-24). `load` suffit :
      // les feuilles de style et les images sont là, c'est tout ce qu'il faut.
  await page.goto(u, { waitUntil: 'load' }).catch(() => {});
  await page.waitForTimeout(120);
  const mauvais = await page.evaluate(inspecter);
  const chemin = u.replace(base, '') || '/';
  for (const m of mauvais) {
    fautes.push(`${chemin} — ${m.balise} « ${m.texte} » : ${m.ratio}:1 < ${m.seuil} `
      + `(${m.couleur} sur ${m.fond}, ${m.taille} px)${m.classe ? ` [${m.classe}]` : ''}`);
  }
}
await ctx.close();
await browser.close();
server?.close();

console.log(`check-contraste: ${pages.length} page(s), ${fautes.length} texte(s) sous le seuil`);
// `--tout` : tout lister, pour corriger en masse sans deviner ce que cache
// le « … et N de plus » (netsalaire.com, 2026-09-24).
const limite = process.argv.includes('--tout') ? fautes.length : 60;
for (const f of fautes.slice(0, limite)) console.log('  ' + f);
if (fautes.length > limite) console.log(`  … et ${fautes.length - limite} de plus`);
process.exit(fautes.length ? 1 : 0);
