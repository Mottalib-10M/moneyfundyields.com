/** Génère og-<lang>.png (1200×630) + icônes. Lit OG_VARIANTS et THEME_COLOR depuis src/data/og.json */
import sharp from 'sharp';
import { readFileSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
const __dirname = dirname(fileURLToPath(import.meta.url));
const PUBLIC = join(__dirname, '..', 'public');
const cfg = JSON.parse(readFileSync(join(__dirname, '..', 'src', 'data', 'og.json'), 'utf8'));
const ACCENT = cfg.accent; const SYM = cfg.symbol;
// Logo drapeau (RECETTE §19.1) : quand public/logo.svg existe, l'image OG reprend ce dessin au lieu
// d'écrire le symbole en texte (un pictogramme « dent » ou « maison » s'écrivait en toutes lettres),
// et les icônes PNG restent celles de gen-icons.mjs, qu'on n'écrase pas.
const LOGO = existsSync(join(PUBLIC, 'logo.svg')) ? readFileSync(join(PUBLIC, 'logo.svg'), 'utf8').replace('<svg ', '<svg x="80" y="70" width="72" height="72" ') : '';
const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
function og({ title, subtitle, badge, brand }) {
  const lines = title.split('\n');
  return `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630"><rect width="1200" height="630" fill="#fff"/><rect width="1200" height="14" fill="${ACCENT}"/>
  ${LOGO || `<rect x="80" y="70" width="72" height="72" rx="16" fill="${ACCENT}"/><text x="116" y="${SYM.length > 1 ? 116 : 122}" font-family="Helvetica, Arial, sans-serif" font-size="${SYM.length > 1 ? 26 : 40}" font-weight="800" fill="#fff" text-anchor="middle">${esc(SYM)}</text>`}
  <text x="172" y="116" font-family="Helvetica, Arial, sans-serif" font-size="34" font-weight="700" fill="#0f172a">${esc(brand)}</text>
  ${lines.map((l, i) => `<text x="80" y="${260 + i * 78}" font-family="Helvetica, Arial, sans-serif" font-size="62" font-weight="800" fill="#0f172a">${esc(l)}</text>`).join('')}
  <text x="80" y="${260 + lines.length * 78 + 10}" font-family="Helvetica, Arial, sans-serif" font-size="30" fill="#475569">${esc(subtitle)}</text>
  <rect x="80" y="540" width="${badge.length * 14 + 40}" height="44" rx="22" fill="#f8fafc" stroke="${ACCENT}"/><text x="${100 + badge.length * 7}" y="569" font-family="Helvetica, Arial, sans-serif" font-size="22" font-weight="600" fill="${ACCENT}" text-anchor="middle">${esc(badge)}</text></svg>`;
}
for (const v of cfg.variants) { await sharp(Buffer.from(og(v))).png().toFile(join(PUBLIC, v.file)); console.log('✓', v.file); }
const icon = (size) => `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 32 32"><rect width="32" height="32" rx="7" fill="${ACCENT}"/><text x="16" y="${SYM.length > 1 ? 20 : 23}" font-size="${SYM.length > 1 ? 10 : 19}" font-weight="800" fill="#fff" font-family="Helvetica, Arial, sans-serif" text-anchor="middle">${esc(SYM)}</text></svg>`;
if (!LOGO) for (const [n, s] of [['icon-192.png', 192], ['icon-512.png', 512], ['apple-touch-icon.png', 180]]) { await sharp(Buffer.from(icon(s))).png().toFile(join(PUBLIC, n)); console.log('✓', n); }
