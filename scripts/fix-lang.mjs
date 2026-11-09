#!/usr/bin/env node
/**
 * fix-lang.mjs — aligne l'attribut `lang` du <html> sur la langue de l'URL (RECETTE §6).
 *
 * Les applications Next dont le <html> vit dans le layout racine ne peuvent pas
 * connaître la locale : elles servent la langue par défaut à toutes les pages.
 * rightetf.com annonçait ainsi `lang="fr"` sur ses 1 108 pages allemandes et
 * anglaises, et gfp `lang="fr"` sur ses pages arabes (2026-09-21).
 *
 * Usage : node scripts/fix-lang.mjs <dossier construit> [--check]
 */
import { readdir, readFile, writeFile } from 'node:fs/promises';
import { join, sep } from 'node:path';

const racine = process.argv.find((a, i) => i > 1 && !a.startsWith('--')) || 'dist';
const CHECK = process.argv.includes('--check');
const LANGUES = /^(fr|en|de|es|it|nl|pt|sv|da|no|fi|pl|ar|zh|ja|ko|hi|bn|ru|tr|id|ms|th|he|cs|ro|uk|el|hu|vi)$/;

async function* pages(d) {
  for (const e of await readdir(d, { withFileTypes: true })) {
    const p = join(d, e.name);
    if (e.isDirectory()) { if (e.name !== 'node_modules' && e.name !== '_next') yield* pages(p); }
    else if (e.name.endsWith('.html')) yield p;
  }
}

let corrigees = 0, vues = 0;
for await (const f of pages(racine)) {
  const parts = f.split(sep);
  const i = parts.indexOf(racine.split(sep).pop());
  const seg = parts[i + 1];
  if (!seg || !LANGUES.test(seg)) continue;      // page hors arborescence de langue
  const html = await readFile(f, 'utf8');
  const m = html.match(/<html[^>]*\blang="([^"]+)"/i);
  if (!m) continue;
  vues++;
  if (m[1].toLowerCase().startsWith(seg)) continue;
  corrigees++;
  if (!CHECK) {
    await writeFile(f, html.replace(/(<html[^>]*\blang=")[^"]+(")/i, `$1${seg}$2`));
  }
}
console.log(`fix-lang: ${corrigees} page(s) ${CHECK ? 'à corriger' : 'réalignées'} sur ${vues} page(s) de langue`);
if (CHECK && corrigees) process.exit(1);
