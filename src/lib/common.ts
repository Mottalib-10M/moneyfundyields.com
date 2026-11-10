/** Shared bits of the content pages: sources by key, related-page cards, fund rows for the islands. */
import { PARAMS, FUNDS, lite, type Fund } from './data';
import { PAGES, FUND_TICKERS, pageById } from './pages';
import { route } from '../i18n/routes';
import { afterTax, stateName } from './engine/tax';
import type { Row } from '../components/calc/Comparator';

type Src = { url: string; label: { en: string } };
const S = PARAMS.sources as unknown as Record<string, Src>;
export const src = (...keys: string[]) => keys.map((k) => { const s = S[k]; if (!s) throw new Error(`no source ${k}`); return { name: s.label.en, url: s.url }; });
export const href = (id: string) => route(id, 'en');
// Cards show the plain name with the ticker (test naïf 2026-11-09: « Other pages » in tickers only).
export const related = (...ids: string[]) => ids.map((id) => { const p = pageById(id)!; return { href: href(id), name: p.menu ?? p.nav, description: p.card }; });
export const METHOD = '/en/method/';
export const fundHref = (t: string) => ((FUND_TICKERS as readonly string[]).includes(t) ? href(`fund-${t.toLowerCase()}`) : undefined);
/** Every share class in the data, as the islands need it (no holdings detail). */
export const LITES = FUNDS.map(lite);
export const ROWS: Row[] = FUNDS.map((f: Fund) => ({ ...lite(f), reg: f.reg, assets: f.assets, min: f.min, g: f.g, href: fundHref(f.t) }));
export const PAGE_FUNDS = LITES.filter((f) => (FUND_TICKERS as readonly string[]).includes(f.t));
export { PAGES };

/** Verdict of the site's one example, in words, for the first screen of a comparison page (testeurs naïfs du
 *  2026-11-10, règle 2 : le résultat annoncé tout de suite). Same example and same rounding as the calculator. */
export function exampleVerdict(a: Fund, b: Fund, st = 'CA'): string {
  const s = { amount: 50000, state: st, filing: 'single' as const, income: 120000 };
  const na = Math.round(afterTax(a, s).net), nb = Math.round(afterTax(b, s).net);
  const usd0 = (n: number) => `$${n.toLocaleString('en-US')}`;
  const who = `In the example below (one person in ${stateName(st)}, $120,000 of taxable income, $50,000)`;
  return na === nb ? `${who}, both leave the same a year.` : na > nb ? `${who}, ${a.t} leaves ${usd0(na - nb)} more a year than ${b.t}.` : `${who}, ${b.t} leaves ${usd0(nb - na)} more a year than ${a.t}.`;
}
