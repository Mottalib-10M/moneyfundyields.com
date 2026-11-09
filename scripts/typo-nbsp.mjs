#!/usr/bin/env node
/**
 * typo-nbsp.mjs — espaces insécables dans le HTML construit (RECETTE-SITE.md §10.3).
 *
 * Un chiffre ne doit jamais se retrouver en fin de ligne, séparé de son unité ou de ses
 * milliers : « 55 | % », « 20 | 921 $ ». Les textes rédigés à la main utilisent une espace
 * normale ; plutôt que de corriger des milliers de passages, on la remplace après le build.
 *   - toutes langues : chiffre + espace + (%, €, $, CHF, h, milliers) → espace insécable
 *   - français       : espace avant « : ; ? ! » et à l'intérieur de « » → espace insécable
 * Sont laissés intacts : attributs, <script>, <style>, <pre>, <textarea>, et le contenu des
 * <astro-island> (React compare son rendu au HTML servi lors de l'hydratation).
 *
 * En mode --check, signale aussi les décimales écrites avec un point dans une langue à virgule
 * (fr-FR, fr-CA, fr-CH, de-DE, es, nl…) : « 13.18 € », « 18.3 mois », « 0.5 maand » viennent d'un
 * paramètre inséré brut (`{A.x}`) ou d'un `toFixed`, avec ou sans unité derrière. Le point reste correct en anglais et en suisse allemand (de-CH).
 * fr-CH : virgule (décision du 2026-09-18, RECETTE §4).
 * En français, signale aussi les mots écrits sans leurs accents (« fiscalite », « epargne »,
 * « interets », « a partir de ») : trouvé sur 129 guides sur 208 d'epargnemalin.fr le 2026-09-19 ;
 * et les accents ajoutés à tort (« vià », « centrès », « succèssion »).
 *
 * Usage : node scripts/typo-nbsp.mjs [dist]         (appelé par `npm run build`)
 *         node scripts/typo-nbsp.mjs [dist] --check  (compte sans modifier, code 1 si reste)
 */
import { readdir, readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';

const dist = process.argv.find((a, i) => i > 1 && !a.startsWith('--')) || 'dist';
const CHECK = process.argv.includes('--check');
const NB = ' ';

const UNIT = /(\d) (?=(?:%|€|\$|CHF|Fr\.|h\b|\d{3}(?!\d)))/g;
const FR_BEFORE = / (?=[:;?!»])/g;
// « 20 % » est français, allemand ou espagnol ; l'anglais, l'italien, le portugais et les
// langues d'Asie écrivent « 20% ». Les agents rédigeaient « 20 % » partout : 168 occurrences sur les pages
// anglaises de us-medicare-costs le 2026-10-24. On colle le signe dans ces langues.
const PCT_COLLE = /^(en|it|pt|zh|ja|ko|th|ms|id)/i; // néerlandais : « 21 % » et « 21% » sont admis tous deux
const PCT_ESPACE = /(\d)[ \u00a0\u202f](?:&nbsp;)?%|(\d)&nbsp;%/g;
// Le turc place le signe avant le nombre, collé : « %93,4 », « %5 » (TDK). « 93,4 % », « 93,4% »
// et « % 93,4 » deviennent « %93,4 » (tr-bayram, 2026-10-28).
const PCT_AVANT = /^tr/i;
const PCT_TURC = /(?<![%\d.,])(\d+(?:[.,]\d+)?)(?:[ \u00a0\u202f]|&nbsp;)?%/g;
const PCT_TURC_ESPACE = /%(?:[ \u00a0\u202f]|&nbsp;)(?=\d)/g;
const FR_AFTER = /« /g;
// Le tiret cadratin « — » en incise est une signature d'ecriture automatique :
// il abonde dans les textes produits par un modele et presque jamais sous la
// plume d'un redacteur qui compose pour le web. On le remplace donc partout
// dans le texte visible. La virgule convient aux trois emplois rencontres :
// l'incise (« … holidays — typically before … »), l'etiquette suivie de son
// explication (« ANTS — Immatriculation ») et la mention de pied de page
// (« © 2026 Site — Tous droits reserves »). Le tiret demi-cadratin « – », lui,
// reste legitime dans les intervalles (« 2–3 ans ») et n'est pas touche.
// Trois ecritures possibles dans le HTML construit : le caractere lui-meme et
// ses deux entites. Ne traiter que la premiere laissait passer la majorite
// des cas, les gabarits Astro ecrivant volontiers `&mdash;`.
const EM_DASH = /\s*(?:\u2014|&mdash;|&#8212;)\s*/g;
// Un tiret seul n'est pas une incise : valeur vide d'une case (« — »), puce ou
// début de ligne. Le remplacer par une virgule affichait « , » dans les tableaux
// et « , Choisir, » dans les listes (guidevoitureelectrique.fr, 2026-10-12). Seul
// le tiret pris entre deux mots devient une virgule ; les autres deviennent « – ».
const remplaceCadratin = (m, off, str) => {
  const avant = str.slice(Math.max(0, off - 1), off), apres = str.slice(off + m.length, off + m.length + 1);
  const mot = /[\p{L}\p{N})»%€$]/u;
  return mot.test(avant) && /[\p{L}\p{N}(«]/u.test(apres) ? ', ' : m.replace(/\u2014|&mdash;|&#8212;/, '\u2013');
};


// Les dossiers d'archive ne sont pas servis : les corriger reviendrait a
// travailler sur un site fantome.
const ARCHIVES = new Set(['_archives', 'archive', 'archives', 'old', 'backup', 'node_modules']);
// Caches de build : ce qui s'y trouve n'est jamais servi. Les contrôler revenait
// à signaler 166 « fautes d'accent » dans des fichiers intermédiaires de Next
// que personne ne lit (brutanet.fr, 2026-09-26).
const CACHES = new Set(['.next', '.nuxt', '.svelte-kit', '.astro', '.cache', '.vercel', '.turbo']);

async function* walk(d) {
  for (const e of await readdir(d, { withFileTypes: true })) {
    if (e.isDirectory() && ARCHIVES.has(e.name)) continue;
    const p = join(d, e.name);
    // node_modules contient des .html de documentation : ils ne font pas partie du site
    if (e.isDirectory()) { if (e.name !== 'node_modules' && e.name !== '.git' && !CACHES.has(e.name)) yield* walk(p); }
    else if (e.name.endsWith('.html')) yield p;
  }
}

function fix(html) {
  const fr = /<html[^>]*\blang="fr/i.test(html);
  // Langue à virgule décimale : on corrige aussi le séparateur dans le texte visible.
  // Réécrire 106 appels à `toFixed()` site par site ne tenait pas ; la correction se
  // fait donc ici, sur le seul texte que le lecteur voit (rightetf.com, 2026-09-21).
  const { lang } = dotDecimals(html);
  const virgule = lang && !/^(en|ja|ko|zh|th|he|hi|bn|ar|ms)|^de-CH|^it-CH|^es-(MX|US|PR|DO|GT|HN|NI|PA|SV)/i.test(lang);
  const colle = PCT_COLLE.test(lang);
  const avant = PCT_AVANT.test(lang);
  let count = 0, decimales = 0, cadratins = 0;
  // `application/ld+json` n'est pas du code : c'est le même texte que la page,
  // déclaré à Google. Le sauter faisait diverger la réponse déclarée de la
  // réponse affichée, ce que le contrôle §7 signale (2026-09-25).
  const pile = [];
  const out = html.split(/(<[a-zA-Z!\/][^>]*>)/).map((part) => {
    if (part.startsWith('<')) {
      const m = part.match(/^<(\/?)(script|style|pre|textarea|astro-island|code|kbd)\b/i);
      if (m) {
        const fermeture = Boolean(m[1]);
        if (fermeture) pile.pop();
        else if (!part.endsWith('/>')) {
          pile.push(/type=["']application\/ld\+json["']/i.test(part) ? 'ld' : 'saut');
        }
      }
      return part;
    }
    const dedans = pile[pile.length - 1];
    if (dedans === 'saut' || !part.trim()) return part;
    const ldJson = dedans === 'ld' ? 1 : 0;
    const typographie = (texte) => {
      let t = texte.replace(EM_DASH, (m, off, str) => (cadratins++, remplaceCadratin(m, off, str)));
      if (avant) t = t.replace(PCT_TURC, (_, n) => (count++, '%' + n)).replace(PCT_TURC_ESPACE, () => (count++, '%'));
      t = t.replace(UNIT, (_, d) => (count++, d + NB));
      if (colle) t = t.replace(PCT_ESPACE, (_, a, b) => (count++, (a || b) + '%'));
      if (fr) t = t.replace(FR_BEFORE, () => (count++, NB)).replace(FR_AFTER, () => (count++, '«' + NB));
      // Un numéro de version (« ZUGFeRD 1.0 », « XRechnung 3.0 ») garde son point : même règle que --check
      // (de-e-rechnung, 2026-10-25 : la correction mettait « ZUGFeRD 1,0 » alors que --check l'acceptait).
      if (virgule) t = t.replace(DOT_DECIMAL, (m, off, str) => {
        const av = str.slice(Math.max(0, off - 30), off), ap = str.slice(off + m.length, off + m.length + 8);
        return estVersion(av, ap) || estHeure(lang, m, av, ap) ? m : (decimales++, m.replace('.', ','));
      });
      return t;
    };
    // Dans un JSON-LD, seul le contenu des chaînes est du texte : corriger un
    // nombre nu (« "annualPercentageRate": 0.32 ») produirait un JSON invalide,
    // donc un balisage ignoré en entier (rightetf.com, 2026-09-25).
    if (ldJson > 0) {
      return part.replace(/"(?:[^"\\]|\\.)*"/g, (chaine) => {
        const interieur = chaine.slice(1, -1);
        // Une clé JSON n'est pas du texte lisible : on ne touche qu'aux valeurs,
        // reconnaissables à ce qu'elles ne sont pas suivies d'un deux-points.
        return '"' + typographie(interieur) + '"';
      });
    }
    return typographie(part);
  }).join('');
  return { out, count, decimales, cadratins };
}

// Toute décimale à point, unité ou non (« 13.18 € », « 0.5 maand », « divisé par 111.8 »),
// sauf numéros d'articles et de documents (« art. 22.2 », « artikel 11.7a », « Mémento 2.01 »), dates,
// numéros de section (« 8.1 Responsable »), cylindrées (« 1.5 TSI ») et normes (« ECE 22.05 »).
const DOT_DECIMAL = /(?<![\d.,’'\w])(?<!(?:art\.?|artikel|Art\.?|§|Abs\.?|al\.|Form\.?|art[ií]culos?|Art[ií]culos?|articles?|Articles?|artigos?|Artigos?)\s?)(?<!\d\.\d[\d.a-z)]*,?\s(?:y|e|et|and|und|o|ou)\s)(?<!(?:Mémento|Merkblatt|Memento)[^\d]{0,14})(?<!(?:ECE|norme|\^|Ducato|\d\.\d\d ou|version|TLS|ETH|RGAA|WCAG|HTTP|Web)\s?)(?:\d{1,3}(?:['’]\d{3})+|\d+)\.\d{1,2}(?![\d.\w])(?!\s(?:[A-Z][a-zé]|TSI|TDI|TFSI|TCe|PureTech|BlueHDi|dCi|HDi|THP|hybride|essence|diesel|ou\s\d))/g;
/** Texte réellement lu par le visiteur : hors script, style et code. */
function texteVisible(html) {
  // Les blocs script et style partent d'abord, en bloc : un script minifié
  // contient des « i<n » que le découpage en balises prend pour une balise
  // ouvrante, ce qui lui fait avaler le « </script> » fermant. Le compteur
  // passait alors à -1 et tout le CSS et le JavaScript de la suite du document
  // ressortait comme du texte visible (salairebrutonet.com, 2026-09-26).
  html = html.replace(/<(script|style)\b[^>]*>[\s\S]*?<\/\1>/gi, ' ');
  let skip = 0;
  return html.split(/(<[a-zA-Z!\/][^>]*>)/).map((part) => {
    if (part.startsWith('<')) {
      const m = part.match(/^<(\/?)(script|style|pre|textarea|astro-island|code|kbd)\b/i);
      if (m) skip = Math.max(0, skip + (m[1] ? -1 : (part.endsWith('/>') ? 0 : 1)));
      return ' ';
    }
    return skip > 0 ? ' ' : part;
  }).join('');
}

// Numéro de version (« iDrive 8.5 », « Safety Sense 3.0 », « Blade 2.0 », « mise à jour
// logicielle 3.5 », « un 2.0 turbo ») : nom propre ou « version / logicielle / un » juste avant,
// et aucune unité juste après. Une vraie mesure (« Batterie 77.5 kWh ») garde son unité.
function estVersion(before, after) {
  return /(?:\b[A-Za-z]*[A-Z][\w-]*|\b(?:version|logicielle|logiciel|un|une|le|la|PM))(?:\s|&nbsp;|\u00a0)?$/.test(before)
    && !/^(?:\s|&nbsp;|\u00a0)?(?:kWh|kW|km|kg|ch|€|%|L\b|m\b|min|h\b|s\b|ct|mm|cm|t\b|g\b|pouces|ans|mois|euros|fois|x\b)/.test(after);
}

// L'indonésien écrit l'heure avec un point : « pukul 07.30 WIB », « 00.00 » (PUEBI). Une heure n'est
// pas une décimale : deux chiffres d'heure, deux de minutes, ou « pukul / jam » avant, « WIB / WITA / WIT »
// après (id-kalender, 2026-10-28).
function estHeure(lang, m, before, after) {
  if (!/^id/i.test(lang) || !/^(?:[01]?\d|2[0-3])\.[0-5]\d$/.test(m)) return false;
  return /^\d{2}\./.test(m) || /\b(?:pukul|jam)(?:\s|&nbsp;|\u00a0)?$/i.test(before)
    || /^(?:\s|&nbsp;|\u00a0)?WIT/.test(after);
}

function dotDecimals(html) {
  const lang = (html.match(/<html[^>]*\blang="([^"]+)"/i) || [])[1] || '';
  if (/^(en|ja|ko|zh|th|he|hi|bn|ar|ms)|^de-CH|^it-CH|^es-(MX|US|PR|DO|GT|HN|NI|PA|SV)/i.test(lang)) return { lang, hits: [] };   // point décimal : anglais, japonais, coréen, chinois, thaï, hébreu, hindi, bengali, arabe (chiffres latins), malais, suisse allemand et italien (CLDR)
  const text = texteVisible(html);
  // Numéro de version (« iDrive 8.5 », « Safety Sense 3.0 », « Blade 2.0 », « mise à jour
  // logicielle 3.5 », « un 2.0 turbo ») : nom propre ou « version / logicielle / un » juste avant,
  // et aucune unité juste après. Une vraie mesure (« Batterie 77.5 kWh ») garde son unité.
  const hits = [];
  for (const m of text.matchAll(DOT_DECIMAL)) {
    const before = text.slice(Math.max(0, m.index - 30), m.index);
    const after = text.slice(m.index + m[0].length, m.index + m[0].length + 8);
    if (!estVersion(before, after) && !estHeure(lang, m[0], before, after)) hits.push(m[0]);
  }
  return { lang, hits };
}

// « Employee Tax Credit », « Employee PRSI » : noms propres de dispositifs
// étrangers, cités tels quels dans un texte français. Un mot capitalisé suivi
// d'un terme anglais du même nom composé n'est pas un accent oublié.
// Mots qui n'existent pas sans accent en français correct (liste volontairement sûre : pas de
// « a », « ou », « ete », « du » qui ont un sens sans accent).
// Frontières Unicode : avec \b, JavaScript verrait « tres » dans « mètres ». Un nom de domaine
// (« impots.gouv.fr ») n'est pas une faute. Minuscules seulement : l'accent sur une capitale
// (« Epargne ») est recommandé mais toléré.
const NO_ACCENT = /(?<![\p{L}\p{N}])(epargnes?|epargner|fiscalites?|interets?|strategies?|impots?|annees?|periodes?|detaille(?:e|s|es)?|securite|necessaires?|reel(?:le|s|les)?|deja|tres|apres|beneficiaires?|societes?|systemes?|economies?|precaution|electriques?|vehicules?|resume|credit(?:s)? immobiliers?|prelevements?|deduction|remuneration|independants?|debutants?|methodes?|categories?|reduction|generale?s?|necessite|equipe|etape|etapes|criteres?|specifique|scenario|scenarios|numero|zero|a partir|(?<!\b(?:qui|il|elle|on|n'y|y) )a la|(?<!\b(?:qui|il|elle|on) )a l'|au dela|indemnites?|indemnisees?|preavis|conges|payes|anciennete|salaries?|(?<![A-Z])employee?s?(?! (?:Tax|Credit|PRSI|PAYE|Benefit))|economiques?|references?|durees?|prevues?|donnees|liees?|reglements?|calculees?|versees?|percues?)(?![\p{L}\p{N}]|\.[a-z]|-[\p{L}\p{N}-]*\.[a-z]{2,})/gu;
// Accents ajoutés à tort par un vieux script de correction : « vià », « centrès », « Titrès »,
// « succèssion » (1 012 occurrences sur cartegrisesimple.fr, 2026-09-19). Liste blanche des
// vrais mots en consonne + « rès » ; « è » devant une consonne doublée n'existe pas.
const RES_OK = new Set(['très', 'près', 'après', 'auprès', 'exprès', 'progrès', 'congrès', 'cyprès', 'crès', 'grès']);
const WRONG_ACCENT = /(?<![\p{L}])(vià|và|[\p{L}]*è(?:ss|tt|ll|nn|mm|pp|rr)[\p{L}]*|[\p{L}]*[bcdfgmnprtv]rès)(?![\p{L}])/gu;
// Contrôle sur tout le texte visible, composants React compris (ils ne sont pas réécrits après le build).
function pourcentsEspaces(html) {
  const lang = (html.match(/<html[^>]*\blang="([^"]+)"/i) || [])[1] || '';
  if (!PCT_COLLE.test(lang)) return [];
  const titres = [...html.matchAll(/\stitle="([^"]*)"/g)].map((m) => m[1]).join(' ');
  const texte = html.replace(/<(script|style)\b[^>]*>[\s\S]*?<\/\1>/gi, ' ').replace(/<[^>]+>/g, '').replace(/&nbsp;|&#160;/g, '\u00a0') + ' ' + titres;
  return [...texte.matchAll(/[^\n]{0,25}\d[ \u00a0\u202f]%/g)].map((m) => m[0].trim());
}

// Turc : signe placé après le nombre (« 93,4 % », « 93,4% ») ou séparé de lui (« % 93,4 »).
function pourcentsTurcs(html) {
  const lang = (html.match(/<html[^>]*\blang="([^"]+)"/i) || [])[1] || '';
  if (!PCT_AVANT.test(lang)) return [];
  const titres = [...html.matchAll(/\stitle="([^"]*)"/g)].map((m) => m[1]).join(' ');
  // Balise remplacée par un saut de ligne : deux cellules voisines (« %93,4 » puis « %95,1 ») ne se
  // collent pas en « 93,4%95,1 » ; le code d'intégration (« width="100%" ») n'est pas du texte.
  const texte = html.replace(/<(script|style|pre|code|textarea|kbd)\b[^>]*>[\s\S]*?<\/\1>/gi, '\n')
    .replace(/<[^>]+>/g, '\n').replace(/&nbsp;|&#160;/g, '\u00a0') + '\n' + titres;
  return [...texte.matchAll(/[^\n]{0,25}(?:\d[ \u00a0\u202f]?%|%[ \u00a0\u202f]\d)/g)].map((m) => m[0].trim());
}

function wrongAccents(html) {
  if (!/<html[^>]*\blang="fr/i.test(html)) return [];
  const text = texteVisible(html);
  return (text.match(WRONG_ACCENT) || []).filter((w) => !RES_OK.has(w.toLowerCase()));
}

function missingAccents(html) {
  if (!/<html[^>]*\blang="fr/i.test(html)) return [];
  const text = texteVisible(html).replace(/https?:\/\/\S+/g, ' ');
  const hits = text.match(NO_ACCENT) || [];
  // « a la » est ambigu : « Quelle Audi a la meilleure autonomie ? » est correct.
  // On ne le retient donc que sur une page qui perd déjà d'autres accents, signe
  // d'un texte désaccentué (guidevoitureelectrique.fr, 2026-09-21).
  const ambigu = (m) => /^(a la|a l'|au dela)$/i.test(m.trim());
  return hits.some((m) => !ambigu(m)) ? hits : [];
}

// Une page réhydratée par React ne peut pas être retouchée après le rendu :
// le client reconstruit le même arbre à partir de son propre code, compare le
// texte servi au texte qu'il produit, et une virgule mise à la place d'un tiret
// cadratin lui suffit pour lever l'erreur #418 et jeter le HTML reçu. Relevé sur
// dosageguide.com le 2026-09-25 : 639 pages, une erreur d'hydratation sur
// chacune, causée par ce script. Sur ces sites, la typographie se corrige dans
// les sources ; ici on ne touche à rien et on le dit.
const HYDRATE = /self\.__next_f|__NEXT_DATA__|window\.__remixContext|data-reactroot/;

let total = 0, files = 0, dots = 0, corrigees = 0; const dotPages = [];
let accents = 0; const accentPages = [];
let tirets = 0; const tiretPages = [];
let hydratees = 0;
let pourcents = 0; const pctPages = [];
for await (const f of walk(dist)) {
  const html = await readFile(f, 'utf8');
  // Une page réhydratée n'est pas réécrite, mais elle reste contrôlée : taire le
  // défaut reviendrait à supprimer la règle pour les sites Next.
  const hydratee = HYDRATE.test(html);
  if (hydratee) hydratees++;
  const { out, count, decimales, cadratins } = fix(html);
  if (count || decimales || cadratins) { total += count; corrigees += decimales; files++; if (!CHECK && !hydratee) await writeFile(f, out); }
  if (cadratins) { tirets += cadratins; if (tiretPages.length < 10) tiretPages.push(`${f} : ${cadratins}`); }
  if (CHECK) {
    const { lang, hits } = dotDecimals(html);
    if (hits.length) { dots += hits.length; dotPages.push(`${f} : ${hits.slice(0, 3).join(', ')}`); }
    const pct = [...pourcentsEspaces(html), ...pourcentsTurcs(html)];
    if (pct.length) { pourcents += pct.length; pctPages.push(`${f} : ${[...new Set(pct)].slice(0, 3).join(' | ')}`); }
    const wrong = wrongAccents(html);
    if (wrong.length) { accents += wrong.length; accentPages.push(`${f} : accent faux ${[...new Set(wrong)].slice(0, 4).join(', ')}`); }
    const miss = missingAccents(html);
    if (miss.length) { accents += miss.length; accentPages.push(`${f} : ${[...new Set(miss)].slice(0, 4).join(', ')}`); }
  }
}
if (hydratees) {
  console.log(`typo-nbsp: ${hydratees} page(s) réhydratées par React, laissées intactes `
    + `— les retoucher après le rendu casse l'hydratation (React #418). `
    + `Corriger la typographie dans les sources.`);
}
console.log(`typo-nbsp: ${total} espace(s) ${CHECK ? 'à corriger' : 'rendue(s) insécable(s)'} dans ${files} page(s)`);
if (!CHECK && corrigees) console.log(`typo-nbsp: ${corrigees} décimale(s) passée(s) à la virgule`);
if (tirets) console.log(`typo-nbsp: ${tirets} tiret(s) cadratin ${CHECK ? 'à remplacer' : 'remplacé(s) par une virgule'}`);
if (CHECK) tiretPages.forEach((l) => console.log('  ' + l));
if (CHECK) {
  console.log(`typo-nbsp: ${dots} décimale(s) avec un point dans une langue à virgule`);
  dotPages.slice(0, 10).forEach((l) => console.log('  ' + l));
  console.log(`typo-nbsp: ${pourcents} pourcentage(s) écrit(s) mal placé(s) : « 20 % » là où la langue écrit « 20% », ou après le nombre en turc, qui écrit « %20 » (souvent dans un composant React : corriger la source)`);
  pctPages.slice(0, 10).forEach((l) => console.log('  ' + l));
  console.log(`typo-nbsp: ${accents} mot(s) français sans accent ou avec un accent faux`);
  accentPages.slice(0, 10).forEach((l) => console.log('  ' + l));
}
if (CHECK && (total || dots || accents || tirets || pourcents)) process.exit(1);
