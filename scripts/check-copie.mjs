#!/usr/bin/env node
/**
 * check-copie.mjs — aucun passage recopié d'un texte sous droits (RECETTE-SITE.md §12.1, règle 6).
 *
 * Pourquoi ce contrôle existe. Le 2026-10-24, l'audit des droits trouve sur citizenship-tests
 * 42 explications anglaises et 34 françaises qui reprennent dix mots consécutifs ou plus du
 * guide « Discover Canada / Découvrir le Canada » : droit d'auteur de la Couronne, reproduction
 * commerciale interdite. Aucun contrôle ne comparait le site à ses sources.
 *
 * La règle : quand un site s'appuie sur un texte qu'on n'a pas le droit de reproduire (guide
 * officiel sous copyright, manuel commercial, article de presse…), on dépose ce texte en .txt
 * dans data/textes-sources/ (jamais publié : le dossier n'est pas dans public/). Le contrôle
 * échoue dès qu'une suite de 8 mots consécutifs du dist se retrouve dans l'un de ces fichiers.
 * Huit mots : en dessous, les tournures banales (« in the House of Commons of Canada ») se
 * recoupent par hasard ; au-dessus, une phrase recopiée et légèrement retouchée passe.
 *
 * Normalisation des deux côtés : minuscules, accents retirés, apostrophes et ponctuation
 * remplacées par des espaces, chiffres gardés. Le texte du dist comprend le texte visible,
 * les attributs alt/title/aria-label, les meta description et le JSON-LD (FAQ, Quiz).
 * Les écritures sans espaces (chinois, japonais, thaï) sont découpées en caractères, et la
 * fenêtre passe alors à 16 caractères.
 *
 * Écartés : les suites présentes dans au moins 3 fichiers sources (en-têtes, titre de l'ouvrage) et
 * les passages listés dans data/textes-sources/autorises.lst (titre officiel, nom d'une loi).
 *
 * Usage : node scripts/check-copie.mjs <dossier-du-site> [--n=8] [--liste]
 * Sortie : « sans objet » sans data/textes-sources/*.txt ; sinon pages fautives, code 1.
 */
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative, resolve } from 'node:path';

const site = resolve(process.argv[2] || '.');
const N = Number((process.argv.find((a) => a.startsWith('--n=')) || '--n=8').split('=')[1]);
const LISTE = process.argv.includes('--liste');
const NCJK = N * 2;

const srcDir = join(site, 'data', 'textes-sources');
const sources = existsSync(srcDir) ? readdirSync(srcDir).filter((f) => f.toLowerCase().endsWith('.txt')) : [];
if (!sources.length) { console.log('check-copie : sans objet (pas de data/textes-sources/*.txt)'); process.exit(0); }
const dist = ['dist', 'out'].map((d) => join(site, d)).find((d) => existsSync(d));
if (!dist) { console.error(`check-copie : pas de dist/ dans ${site} (lancer le build d'abord)`); process.exit(2); }

const CJK = /[぀-ヿ㐀-鿿豈-﫿가-힯฀-๿]/u;
function mots(s) {
  const t = s.normalize('NFKD').replace(/\p{M}+/gu, '').toLowerCase()
    .replace(/[’'`´]/g, ' ').replace(/[^\p{L}\p{N}]+/gu, ' ');
  const out = [];
  for (const w of t.split(' ')) {
    if (!w) continue;
    if (CJK.test(w)) for (const c of w) out.push(c); else out.push(w);
  }
  return out;
}
const fenetre = (toks, i) => (CJK.test(toks[i]) ? NCJK : N);

// Index des n-grammes des textes sources (mots latins : N ; caractères CJK : 2N).
const index = new Map(); // gramme → fichier source
const fichiers = new Map(); // gramme → nombre de fichiers où il apparaît
let nbMots = 0;
for (const f of sources) {
  const toks = mots(readFileSync(join(srcDir, f), 'utf8'));
  nbMots += toks.length;
  const vus = new Set();
  for (let i = 0; i < toks.length; i++) {
    const n = fenetre(toks, i);
    if (i + n > toks.length) continue;
    const g = toks.slice(i, i + n).join(' ');
    if (!index.has(g)) index.set(g, f);
    if (!vus.has(g)) { vus.add(g); fichiers.set(g, (fichiers.get(g) || 0) + 1); }
  }
}
// En-têtes courants et titre de l'ouvrage (« Discover Canada: The Rights and Responsibilities of
// Citizenship » en tête de chaque chapitre) : présents dans au moins 3 fichiers, ce ne sont pas du
// contenu. Citer le titre d'un guide reste permis.
let communs = 0;
const commun = new Set();
if (sources.length >= 3) for (const [g, k] of fichiers) if (k >= 3) { index.delete(g); commun.add(g); communs++; }
// Passages admis à la main (titre officiel, nom d'une loi, d'une institution) : une ligne par passage,
// dans data/textes-sources/autorises.lst (pas en .txt : ce n'est pas un texte sous droits).
const admis = existsSync(join(srcDir, 'autorises.lst'))
  ? readFileSync(join(srcDir, 'autorises.lst'), 'utf8').split('\n').map((l) => mots(l.replace(/#.*/, '')).join(' ')).filter(Boolean)
  : [];

const ENT = { amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ', rsquo: '’', lsquo: '‘', laquo: '«', raquo: '»', ndash: '–', mdash: '—', hellip: '…' };
const decode = (s) => s
  .replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16)))
  .replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(Number(d)))
  .replace(/&([a-z]+);/gi, (m, n) => ENT[n.toLowerCase()] ?? m);

function blocs(h) {
  const out = [];
  for (const m of h.matchAll(/<script[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi)) {
    try { (function walk(v) { if (typeof v === 'string') out.push(v); else if (v && typeof v === 'object') Object.values(v).forEach(walk); })(JSON.parse(m[1])); }
    catch { out.push(m[1]); }
  }
  for (const m of h.matchAll(/<meta[^>]+(?:name|property)=["'](?:description|og:description|twitter:description)["'][^>]*content=["']([^"']*)["']/gi)) out.push(decode(m[1]));
  for (const m of h.matchAll(/\s(?:alt|title|aria-label)=["']([^"']{20,})["']/gi)) out.push(decode(m[1]));
  // Le texte visible, bloc par bloc : une suite de mots ne doit pas enjamber deux paragraphes.
  const corps = h.replace(/<!--[\s\S]*?-->/g, ' ').replace(/<(script|style|noscript|template|svg)\b[\s\S]*?<\/\1>/gi, ' ');
  for (const b of corps.split(/<\/?(?:p|li|h[1-6]|td|th|dt|dd|div|section|article|header|footer|nav|main|blockquote|figcaption|summary|details|tr|br|option|label|button)\b[^>]*>/i)) {
    const t = decode(b.replace(/<[^>]+>/g, ' ')).trim();
    if (t) out.push(t);
  }
  return out;
}

function* html(dir) {
  for (const e of readdirSync(dir)) {
    const p = join(dir, e);
    if (statSync(p).isDirectory()) yield* html(p);
    else if (e.endsWith('.html')) yield p;
  }
}

const fautes = [];
let pagesLues = 0;
for (const f of html(dist)) {
  const h = readFileSync(f, 'utf8');
  if (/<meta[^>]+http-equiv=["']?refresh/i.test(h)) continue;
  pagesLues++;
  const passages = new Map(); // passage recopié → source
  for (const b of blocs(h)) {
    const toks = mots(b);
    // Suites maximales de n-grammes communs : un seul passage par phrase recopiée.
    let i = 0;
    while (i < toks.length) {
      const n = fenetre(toks, i);
      const g = i + n <= toks.length ? toks.slice(i, i + n).join(' ') : null;
      if (!g || !index.has(g)) { i++; continue; }
      let j = i + 1;
      while (j + fenetre(toks, j) <= toks.length && index.has(toks.slice(j, j + fenetre(toks, j)).join(' '))) j++;
      const fin = j - 1 + fenetre(toks, j - 1);
      const sep = CJK.test(toks[i]) ? '' : ' ';
      const passage = toks.slice(i, fin).join(sep);
      // Titre suivi d'un ou deux mots (« … of Citizenship The ») : on compte les mots du passage
      // qui ne sont pas couverts par un en-tête commun ; moins de 3, ce n'est pas du contenu.
      const couvert = new Set();
      for (let k = Math.max(0, i - NCJK); k < fin; k++) {
        const n2 = fenetre(toks, k);
        if (k + n2 <= toks.length && commun.has(toks.slice(k, k + n2).join(' '))) for (let q = k; q < k + n2; q++) couvert.add(q);
      }
      let neufs = 0; for (let q = i; q < fin; q++) if (!couvert.has(q)) neufs++;
      if (neufs < 3) { i = fin; continue; }
      if (!admis.some((a) => (' ' + a + ' ').includes(' ' + passage + ' ') || a === passage)) passages.set(passage, index.get(g));
      i = fin;
    }
  }
  if (passages.size) fautes.push({ rel: '/' + relative(dist, f), passages: [...passages].sort((a, b) => b[0].length - a[0].length) });
}

console.log(`check-copie : ${pagesLues} page(s) comparées à ${sources.length} texte(s) sous droits (${nbMots} mots, ${index.size} suites de ${N} mots${communs ? `, ${communs} en-têtes communs à 3 fichiers écartés` : ''}${admis.length ? `, ${admis.length} passage(s) admis` : ''})`);
const total = fautes.reduce((s, x) => s + x.passages.length, 0);
for (const { rel, passages } of (LISTE ? fautes : fautes.slice(0, 15))) {
  console.log(`  ${rel} : ${passages.length} passage(s) recopié(s)`);
  for (const [p, src] of passages.slice(0, LISTE ? 50 : 2)) {
    const w = p.split(' ');
    console.log(`      « ${w.length > 30 ? w.slice(0, 30).join(' ') + ' …' : p} » (${w.length > 1 ? w.length + ' mots' : p.length + ' caractères'}, ${src})`);
  }
}
if (!LISTE && fautes.length > 15) console.log(`  … ${fautes.length - 15} page(s) de plus (--liste pour tout voir)`);
if (total) {
  console.log(`check-copie : ${total} passage(s) d'au moins ${N} mots recopié(s) sur ${fautes.length} page(s) — réécrire avec nos mots (citer la source ne suffit pas)`);
  process.exit(1);
}
console.log('check-copie : 0 passage recopié');
