/** Shared bits of the content pages: sources by key, related-page cards, fund rows for the islands. */
import { PARAMS, FUNDS, lite, type Fund } from './data';
import { PAGES, FUND_TICKERS, pageById } from './pages';
import { route } from '../i18n/routes';
import type { Row } from '../components/calc/Comparator';

type Src = { url: string; label: { en: string } };
const S = PARAMS.sources as unknown as Record<string, Src>;
export const src = (...keys: string[]) => keys.map((k) => { const s = S[k]; if (!s) throw new Error(`no source ${k}`); return { name: s.label.en, url: s.url }; });
export const href = (id: string) => route(id, 'en');
export const related = (...ids: string[]) => ids.map((id) => { const p = pageById(id)!; return { href: href(id), name: p.nav, description: p.card }; });
export const METHOD = '/en/method/';
export const fundHref = (t: string) => ((FUND_TICKERS as readonly string[]).includes(t) ? href(`fund-${t.toLowerCase()}`) : undefined);
/** Every share class in the data, as the islands need it (no holdings detail). */
export const LITES = FUNDS.map(lite);
export const ROWS: Row[] = FUNDS.map((f: Fund) => ({ ...lite(f), reg: f.reg, assets: f.assets, min: f.min, g: f.g, href: fundHref(f.t) }));
export const PAGE_FUNDS = LITES.filter((f) => (FUND_TICKERS as readonly string[]).includes(f.t));
export { PAGES };
