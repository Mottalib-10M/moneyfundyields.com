// Fabrique les icônes que toute page déclare (RECETTE §13) à partir de public/favicon.svg :
// favicon.ico (PNG 16/32/48 dans un conteneur ICO), apple-touch-icon.png (180),
// icon-192.png et icon-512.png du manifeste. Sans elles, check-trame signale
// « favicon déclarée mais absente du build » sur chaque page.
// Usage : node scripts/gen-icons.mjs   (dans le dossier du site, sharp installé)
import sharp from 'sharp';
import { readFileSync, writeFileSync, readdirSync } from 'node:fs';
const svg = readFileSync('public/favicon.svg');
const png = (size) => sharp(svg, { density: 384 }).resize(size, size).png().toBuffer();
const sizes = [16, 32, 48];
const bufs = await Promise.all(sizes.map(png));
// Conteneur ICO : en-tête 6 octets, 16 octets par image, puis les PNG.
const head = Buffer.alloc(6); head.writeUInt16LE(0, 0); head.writeUInt16LE(1, 2); head.writeUInt16LE(sizes.length, 4);
let offset = 6 + 16 * sizes.length; const dir = [];
sizes.forEach((s, i) => { const e = Buffer.alloc(16); e.writeUInt8(s, 0); e.writeUInt8(s, 1); e.writeUInt8(0, 2); e.writeUInt8(0, 3); e.writeUInt16LE(1, 4); e.writeUInt16LE(32, 6); e.writeUInt32LE(bufs[i].length, 8); e.writeUInt32LE(offset, 12); offset += bufs[i].length; dir.push(e); });
writeFileSync('public/favicon.ico', Buffer.concat([head, ...dir, ...bufs]));
writeFileSync('public/apple-touch-icon.png', await png(180));
writeFileSync('public/icon-192.png', await png(192));
writeFileSync('public/icon-512.png', await png(512));
// Sites plus anciens : toute autre icône PNG déjà présente (favicon-16x16.png, favicon-192.png,
// android-chrome-512x512.png…) est redessinée à sa taille, lue dans son nom, pour qu'aucune ne garde l'ancien dessin.
const extra = readdirSync('public').filter((f) => /^(favicon|icon|android-chrome|apple-touch-icon)-?.*?(\d+)(x\d+)?\.png$/.test(f) && !['icon-192.png', 'icon-512.png'].includes(f));
for (const f of extra) { const n = +f.match(/(\d+)(?:x\d+)?\.png$/)[1]; if (n >= 16 && n <= 1024) writeFileSync(`public/${f}`, await png(n)); }
console.log('icônes : favicon.ico, apple-touch-icon.png, icon-192.png, icon-512.png' + (extra.length ? ', ' + extra.join(', ') : ''));
