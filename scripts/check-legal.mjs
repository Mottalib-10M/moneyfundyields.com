// Contrôle avant mise en ligne : l'identité légale est-elle complète, et les pages
// légales sont-elles exemptes de mentions provisoires ?
// Usage : npm run check:legal
import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';

// Sans argument : le gabarit lui-même. Avec un argument : le site à contrôler
// (les sites en ligne n'embarquent pas ce script, on l'appelle depuis la factory).
const root = process.argv[2] ? resolve(process.argv[2]) + '/' : new URL('..', import.meta.url).pathname;
const errors = [];

/* 1. Identité légale ------------------------------------------------------- */
// Un site ecrit a la main n'a pas de fiche d'identite : on le dit, au lieu de
// planter sur ENOENT. Un controle qui s'arrete ne controle pas.
const ficheLegale = join(root, 'src/data/site-config.ts');
if (!existsSync(ficheLegale)) {
  // Un site écrit à la main n'a pas de fiche : son identité légale vit dans la
  // page de mentions elle-même. Dire « aucune fiche » et sortir revenait à ne
  // rien contrôler sur ces sites (netsalaire.com, 2026-09-24). On lit donc la
  // page servie et on y cherche les mentions exigées par la LCEN art. 6-III.
  const pages = ['fr/mentions-legales', 'mentions-legales', 'fr/impressum', 'impressum',
                 'fr/aviso-legal', 'aviso-legal', 'legal-notice', 'fr/legal-notice',
                 'colofon', 'note-legali', 'legal', 'fr/legal', 'tr/yasal-bilgiler', 'yasal-bilgiler', 'id/legal', 'id/ketentuan']
    // Le dossier servi ne s'appelle pas toujours dist : salaryafter.com publie
    // depuis docs/ et calorierule.com depuis output/. Ne chercher que dist et out
    // faisait déclarer « aucune page de mentions légales » sur des sites qui en
    // avaient une (2026-09-26).
    .flatMap((d) => ['', 'dist/', 'out/', 'build/', 'docs/', 'output/', '_site/', 'www/']
      .map((s) => join(root, s + d, 'index.html')))
    .filter(existsSync);
  if (!pages.length) {
    console.log('\n  Aucune page de mentions légales trouvée, et pas de fiche src/data/site-config.ts.');
    console.log('  Sans elle, ni la LCEN art. 6-III ni le RGPD ne peuvent être satisfaits.');
    console.log('\n  À corriger avant la mise en ligne.\n');
    process.exit(1);
  }
  const texte = readFileSync(pages[0], 'utf8')
    .replace(/<script[\s\S]*?<\/script>/g, ' ')
    .replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ');
  // Les sites du portefeuille ne sont pas tous en français : un contrôle qui
  // ne cherche que « éditeur » et « hébergeur » déclare non conforme un site
  // anglais parfaitement en règle (costoflivingusa.com, 2026-09-24).
  const exige = {
    'éditeur nommé': /(éditeur|editeur|publié par|edité par|published by|publisher|editor|herausgeber|uitgever|editado por|yayıncı|yayımlayan|penerbit|pengelola)/i,
    'adresse postale': /\b\d{4,5}\s+[A-ZÀ-Ý][\wÀ-ÿ'-]+|\b[A-Z][a-z]+,?\s+[A-Z]{2}\s+\d{5}\b/,
    'contact': /[\w.+-]+@[\w-]+\.[a-z]{2,}|formulaire de contact|contact form/i,
    'hébergeur': /(hébergeur|hebergeur|hébergé par|hosting|hosted by|host:|provider|barındırma|yer sağlayıcı)/i,
    'directeur de la publication ou responsable': /(directeur de la publication|responsable de la publication|représentant légal|société|managing director|responsible for content|legal representative|company|LLC|Ltd|Inc\.)/i,
  };
  const absents = Object.entries(exige).filter(([, re]) => !re.test(texte)).map(([k]) => k);
  console.log(`\n  Site sans fiche d'identité : contrôle sur ${pages[0].replace(root, '')}`);
  if (absents.length) {
    console.log('  Mentions absentes de la page :');
    absents.forEach((k) => console.log(`   - ${k}`));
    console.log('\n  À corriger avant la mise en ligne.\n');
    process.exit(1);
  }
  console.log('  Mentions légales complètes.\n');
  process.exit(0);
}
const src = readFileSync(ficheLegale, 'utf8');
const block = src.slice(src.indexOf('export const LEGAL: LegalIdentity'));
const value = (key) => {
  const m = block.match(new RegExp(`${key}:\\s*['"\`]([^'"\`]*)['"\`]`));
  return m ? m[1] : '';
};
// Les champs obligatoires sont ceux que le site declare lui-meme dans
// LEGAL_REQUIRED : d'un pays a l'autre, et selon que l'editeur est une societe ou
// une personne physique, la liste n'est pas la meme. La liste en dur exigeait
// `legalForm`, qui est vide a dessein sur les vingt-six sites du portefeuille --
// une personne physique n'a pas de forme juridique -- si bien que le controle
// echouait partout et ne signalait plus rien d'utile.
const declaree = src.match(/LEGAL_REQUIRED[^=]*=\s*\[([^\]]*)\]/);
const requis = declaree
  ? [...declaree[1].matchAll(/['"`]([^'"`]+)['"`]/g)].map((m) => m[1])
  : ['entityName', 'street', 'postalCode', 'city'];
const missing = requis.filter((k) => !value(k));
const hostingBlock = block.match(/hosting:\s*\{([^}]*)\}/);
const hostingName = hostingBlock ? (hostingBlock[1].match(/name:\s*['"`]([^'"`]*)['"`]/) || [, ''])[1] : '';
if (!hostingName) missing.push('hosting.name');
if (missing.length) {
  errors.push('Identité légale incomplète dans src/data/site-config.ts :');
  missing.forEach((k) => errors.push(`   - ${k}`));
}

/* 2. Mentions provisoires dans les pages ----------------------------------- */
// Un crochet contenant une formule d'attente : « [à compléter] », « [Si activé :] »,
// « [… vor Inbetriebnahme ergänzen] ». Les apostrophes sont exclues du motif pour ne pas
// confondre un placeholder avec un tableau JSX (`rows={[['…', '…']]}`).
const PLACEHOLDER = /\[[^\]{}<>'"\n]{0,140}(?:à compléter|a compléter|à définir|si activé|sofern aktiviert|falls vorhanden|vor Inbetriebnahme|zu ergänzen|nog invullen|por completar|to be added|\bTODO\b|\bXXX\b)[^\]\n]{0,140}\]/i;
const walk = (dir) => readdirSync(dir).flatMap((e) => {
  const p = join(dir, e);
  return statSync(p).isDirectory() ? walk(p) : /\.(astro|tsx|jsx)$/.test(p) ? [p] : [];
});
// Astro range ses pages dans `src/pages`, Next dans `src/app`. Le script plantait
// sur `ENOENT src/pages` pour les cinq sites Next du portefeuille, qui n'etaient
// donc jamais controles.
const dossiers = ['src/pages', 'src/app'].map((d) => join(root, d)).filter(existsSync);
for (const file of dossiers.flatMap(walk)) {
  readFileSync(file, 'utf8').split('\n').forEach((line, i) => {
    if (PLACEHOLDER.test(line)) errors.push(`Mention provisoire : ${file.slice(root.length)}:${i + 1}`);
  });
}

if (errors.length) {
  console.error('');
  errors.forEach((e) => console.error(`  ${e}`));
  console.error('\n  À corriger avant la mise en ligne.\n');
  process.exit(1);
}
console.log('Identité légale complète, aucune mention provisoire.');
