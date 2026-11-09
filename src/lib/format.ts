/** Formatage monétaire/numérique localisé (configuré par site via site-config). */
import { LOCALE_TAG, CURRENCY } from '../data/site-config';

const cache = new Map<string, Intl.NumberFormat>();
function nf(opts: Intl.NumberFormatOptions): Intl.NumberFormat {
  const k = JSON.stringify(opts);
  if (!cache.has(k)) cache.set(k, new Intl.NumberFormat(LOCALE_TAG, opts));
  return cache.get(k)!;
}
export function formatMoney(value: number, decimals = 0): string {
  return nf({ style: 'currency', currency: CURRENCY, minimumFractionDigits: decimals, maximumFractionDigits: decimals }).format(value);
}
export function formatNumber(value: number, decimals = 0): string {
  return nf({ minimumFractionDigits: decimals, maximumFractionDigits: decimals }).format(value);
}
/** Nombre tiré des paramètres et inséré dans un texte : décimales utiles seulement (13,18 · 111,8 · 548),
 *  toujours au format de la locale. Jamais `{P.x}` ni `toFixed` dans une page (RECETTE §4, §17.4). */
export function formatDecimal(value: number, max = 2): string {
  return nf({ maximumFractionDigits: max }).format(value);
}
export function formatPercent(value: number, decimals = 1): string {
  // Le format d'Intl fait foi : « 3.5% » en anglais, « 3,5 % » en français ; l'espace qu'il pose devient insécable (RECETTE §10.3, 2026-10-24).
  return nf({ style: 'percent', minimumFractionDigits: decimals, maximumFractionDigits: decimals }).format(value).replace(/(\d)\s%/, '$1\u00a0%');
}
export function parseLocaleNumber(input: string): number {
  const cleaned = input.replace(/[^\d.,-]/g, '');
  // Détecte le séparateur décimal : le dernier des deux symboles
  const lastComma = cleaned.lastIndexOf(','), lastDot = cleaned.lastIndexOf('.');
  let s = cleaned;
  if (lastComma > lastDot) s = cleaned.replace(/\./g, '').replace(',', '.');
  // « 35.000 » en danois, néerlandais ou allemand : point séparateur de milliers, pas décimal.
  else if (/^-?\d{1,3}(\.\d{3})+$/.test(cleaned)) s = cleaned.replace(/\./g, '');
  else s = cleaned.replace(/,/g, '');
  const n = parseFloat(s);
  return isNaN(n) ? 0 : n;
}

/** Date de mise à jour écrite dans la langue de la page (registre 2026-09-21) : « 27 September 2026 »,
 *  jamais le format machine. Fuseau UTC forcé, sinon la date recule d'un jour à l'ouest de Greenwich.
 *  Le format ISO reste dans l'attribut `datetime` de la balise <time>. */
export function displayDate(iso: string, langTag: string): string {
  const s = new Date(`${iso}T00:00:00Z`).toLocaleDateString(langTag, { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' });
  // Français : « 1er novembre », jamais « 1 novembre » (ordinal du premier jour du mois).
  return langTag.startsWith('fr') ? s.replace(/^1 /, '1er ') : s;
}
