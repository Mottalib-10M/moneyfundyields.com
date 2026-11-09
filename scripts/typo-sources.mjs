#!/usr/bin/env node
/**
 * typo-sources.mjs — la typographie du §10.3, appliquée aux sources.
 *
 * `typo-nbsp.mjs` corrige le HTML construit. Sur un site réhydraté par React,
 * c'est impossible : le client reconstruit l'arbre à partir de son propre code,
 * compare le texte servi à celui qu'il produit, et une virgule mise à la place
 * d'un tiret cadratin après le rendu lui suffit pour lever l'erreur #418 et
 * jeter le HTML reçu (dosageguide.com, 2026-09-25 : 639 pages, une erreur par
 * page). Sur ces sites, la correction se fait donc ici, avant le rendu.
 *
 * Deux règles sont portées : le tiret cadratin, qui touche le texte de tous les
 * sites, et, avec --fr, les espaces insécables de la typographie française. Les
 * secondes ne s'appliquent qu'au contenu des chaînes de caractères : une source
 * contient des ternaires (`a ? b : c`) qu'une règle posée sur le fichier entier
 * transformerait en code invalide. Les interpolations `${…}` d'un gabarit sont
 * sautées pour la même raison.
 *
 * Usage : node typo-sources.mjs <racine-du-site> [--check] [--fr]
 * Sortie : nombre de tirets remplacés par fichier, code 1 en --check s'il en reste.
 */
import { readdir, readFile, writeFile } from 'node:fs/promises';
import { join, extname } from 'node:path';

const racine = process.argv[2];
if (!racine) { console.error('usage: node typo-sources.mjs <racine-du-site> [--check]'); process.exit(2); }
const CHECK = process.argv.includes('--check');
const FR = process.argv.includes('--fr');

// Les dossiers construits ou installés ne sont pas des sources : les corriger
// serait sans effet au prochain build, et casserait l'hydratation pour rien.
const IGNORES = new Set(['node_modules', '.git', '.next', 'out', 'dist', 'build', '_archives', 'public']);
const EXTENSIONS = new Set(['.ts', '.tsx', '.js', '.jsx', '.astro', '.md', '.mdx', '.json']);

// Le tiret cadratin en incise est une signature d'écriture automatique. La
// virgule convient aux trois emplois rencontrés : l'incise, l'étiquette suivie
// de son explication et la mention de pied de page. Le demi-cadratin « – »
// reste légitime dans les intervalles et n'est pas touché.
const EM_DASH = /\s*(?:—|&mdash;|&#8212;)\s*/g;
// Un tiret seul n'est pas une incise : valeur vide d'une case (« — »), puce ou
// début de ligne. Le remplacer par une virgule affichait « , » dans les tableaux
// et « , Choisir, » dans les listes (guidevoitureelectrique.fr, 2026-10-12). Seul
// le tiret pris entre deux mots devient une virgule ; les autres deviennent « – ».
const remplaceCadratin = (m, off, str) => {
  const avant = str.slice(Math.max(0, off - 1), off), apres = str.slice(off + m.length, off + m.length + 1);
  const mot = /[\p{L}\p{N})»%€$]/u;
  return mot.test(avant) && /[\p{L}\p{N}(«]/u.test(apres) ? ', ' : m.replace(/\u2014|&mdash;|&#8212;/, '\u2013');
};


// Typographie française : espace insécable avant les deux-points, le point-virgule,
// le point d'interrogation, le point d'exclamation et le guillemet fermant, et
// après le guillemet ouvrant.
const NB = ' ';
const FR_AVANT = / (?=[:;?!»])/g;
const FR_APRES = /« /g;
// Unité collée à son nombre : « 35 % », « 1 200 € ». Dans un gabarit, le nombre
// vient souvent d'une interpolation et l'unité seule reste dans le texte : ce
// cas-là est traité en tête de morceau, juste après un `${…}`.
const UNITE = /(\d) (?=(?:%|€|\$|CHF|Fr\.|h\b|\d{3}(?!\d)))/g;
const UNITE_DEBUT = /^ (?=(?:%|€|\$|CHF|Fr\.))/;

/**
 * Les espaces françaises, posées dans le seul contenu des chaînes et des nœuds
 * JSX. Le texte est parcouru caractère par caractère plutôt qu'avec une
 * expression régulière : un gabarit imbriqué — `${x ? `oui ${y}` : ""}` — fait
 * perdre le fil à toute regex de chaîne, et la moitié d'un fichier passait alors
 * pour du code (brutanet.fr, 2026-09-25).
 */
function espacesFrancaises(source) {
  let poses = 0;
  const applique = (texte, apresInterpolation = false) => {
    let apres = texte.replace(FR_AVANT, NB).replace(FR_APRES, '«' + NB).replace(UNITE, '$1' + NB);
    if (apresInterpolation) apres = apres.replace(UNITE_DEBUT, NB);
    poses += (apres.match(/ /g) || []).length - (texte.match(/ /g) || []).length;
    return apres;
  };

  let out = '';
  let i = 0;
  // Pile des gabarits ouverts : à l'intérieur d'une interpolation `${…}`, on est
  // de nouveau dans du code, et un gabarit peut y être rouvert.
  const pile = [];
  let debutTexte = 0;
  const vider = (jusqua) => { out += source.slice(debutTexte, jusqua); };
  while (i < source.length) {
    const c = source[i];
    const suivant = source[i + 1];
    // Commentaires : ni code ni texte affiché, on les saute tels quels.
    if (c === '/' && suivant === '/' && !pile.length) { const fin = source.indexOf('\n', i); i = fin === -1 ? source.length : fin; continue; }
    if (c === '/' && suivant === '*' && !pile.length) { const fin = source.indexOf('*/', i); i = fin === -1 ? source.length : fin + 2; continue; }
    if (c === "'" || c === '"' || c === '`') {
      vider(i);
      const contenu = lireChaine(source, i, c, applique);
      out += contenu.texte;
      i = contenu.fin;
      debutTexte = i;
      continue;
    }
    i++;
  }
  vider(source.length);

  // Le texte d'un gabarit ne vit pas que dans des chaînes : « <p>Attention : oui</p> »
  // est un nœud JSX. On le traite entre un « > » et un « < », en écartant ce qui
  // contient une accolade, un signe égal ou un point-virgule — du code, pas une phrase.
  return {
    sortie: out
      // Le point-virgule signale du code, sauf dans une entité HTML : « 12,3 %
      // pour les activit&eacute;s » est du texte, et l'exclure laissait passer
      // des pages entières (brutanet.fr, 2026-09-25).
      .replace(/>([^<>{}=]*)</g, (tout, texte) => {
        if (/;/.test(texte.replace(/&[a-zA-Z][a-zA-Z0-9]{1,9};|&#\d{1,5};/g, ''))) return tout;
        if (!/[:;?!«»]|\d /.test(texte)) return tout;
        return '>' + applique(texte) + '<';
      })
      // « {taux} % » : la valeur vient d'une expression, l'unité seule reste dans
      // le texte, et l'espace qui les sépare doit être insécable comme les autres.
      .replace(/\}( (?:%|€|\$|CHF|Fr\.))(?=[<\s])/g, (tout, unite) => {
        poses += 1;
        return '}' + NB + unite.slice(1);
      }),
    poses,
  };
}

/** Lit une chaîne à partir de son guillemet ouvrant, interpolations comprises. */
function lireChaine(source, debut, guillemet, applique) {
  let i = debut + 1;
  let texte = guillemet;
  let morceau = '';
  let vientDInterpolation = false;
  while (i < source.length) {
    const c = source[i];
    if (c === '\\') { morceau += source.slice(i, i + 2); i += 2; continue; }
    if (c === guillemet) { texte += applique(morceau, vientDInterpolation) + guillemet; return { texte, fin: i + 1 }; }
    if (guillemet !== '`' && c === '\n') { texte += applique(morceau, vientDInterpolation); return { texte, fin: i }; }
    if (guillemet === '`' && c === '$' && source[i + 1] === '{') {
      texte += applique(morceau, vientDInterpolation); morceau = ''; vientDInterpolation = true;
      // L'interpolation est du code : on la recopie, en suivant ses accolades et
      // les chaînes qu'elle contient.
      let profondeur = 1; let j = i + 2; let expr = '${';
      while (j < source.length && profondeur) {
        const d = source[j];
        if (d === '{') profondeur++;
        else if (d === '}') { profondeur--; if (!profondeur) { expr += '}'; j++; break; } }
        else if (d === "'" || d === '"' || d === '`') {
          const inner = lireChaine(source, j, d, applique);
          expr += inner.texte; j = inner.fin; continue;
        }
        expr += d; j++;
      }
      texte += expr; i = j; continue;
    }
    morceau += c; i++;
  }
  texte += applique(morceau);
  return { texte, fin: i };
}

async function* parcourir(d) {
  for (const e of await readdir(d, { withFileTypes: true })) {
    if (IGNORES.has(e.name)) continue;
    const p = join(d, e.name);
    if (e.isDirectory()) yield* parcourir(p);
    else if (EXTENSIONS.has(extname(e.name))) yield p;
  }
}

let total = 0, fichiers = 0, insecables = 0;
for await (const f of parcourir(racine)) {
  const source = await readFile(f, 'utf8');
  const n = (source.match(EM_DASH) || []).length;
  let texte = source.replace(EM_DASH, remplaceCadratin);
  let poses = 0;
  if (FR && /\.(ts|tsx|js|jsx|astro)$/.test(f)) ({ sortie: texte, poses } = espacesFrancaises(texte));
  if (!n && !poses) continue;
  total += n; insecables += poses; fichiers++;
  console.log(`  ${f.replace(racine, '').replace(/^\//, '')} : ${n} tiret(s), ${poses} insécable(s)`);
  if (!CHECK) await writeFile(f, texte);
}
console.log(`typo-sources: ${total} tiret(s) cadratin ${CHECK ? 'à remplacer' : 'remplacé(s) par une virgule'} dans ${fichiers} fichier(s)`);
if (FR) console.log(`typo-sources: ${insecables} espace(s) ${CHECK ? 'à rendre insécable(s)' : 'rendue(s) insécable(s)'}`);
if (CHECK && (total || insecables)) process.exit(1);
