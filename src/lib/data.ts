/** Fund data as filed (src/data/funds.json, built by scripts/build-data.py) and helpers for pages. */
import D from '../data/funds.json';
import H from '../data/history.json';
import TB from '../data/tbills.json';
import P from '../data/params-2026.json';
import { afterTax, type Situation, type Kind } from './engine/tax';
import { displayDate } from './format';

export interface Fund {
  t: string; cid: string; sid: string; name: string; cls: string; reg: string; cat: string; k: Kind; st: string | null;
  min: number; assets: number; fundAssets: number; y: number; yDate: string; g: number | null; wam: number | null; wal: number | null;
  comp: Record<string, number>; usob: number; q: Record<string, number>; rep: string; filed: string; acc: string;
}
export const META = D.meta;
export const FUNDS = D.funds as unknown as Fund[];
export const HISTORY = H as unknown as Record<string, Array<[string, number]>>;
export const TBILLS = TB;
export const PARAMS = P;
export const fund = (t: string): Fund => { const f = FUNDS.find((x) => x.t === t); if (!f) throw new Error(`no fund ${t}`); return f; };
export const lite = (f: Fund) => ({ t: f.t, name: f.name, y: f.y, k: f.k, st: f.st, usob: f.usob, q: f.q, yDate: f.yDate });

export const pct = (x: number, d = 2) => `${(x * 100).toFixed(d)}%`;
export const usd = (x: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(x);
export const bn = (x: number) => (x >= 1e9 ? `$${(x / 1e9).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} billion` : `$${Math.round(x / 1e6)} million`);
export const day = (iso: string) => displayDate(iso, 'en-US');
export const monthName = (ym: string) => new Date(`${ym}-15T00:00:00Z`).toLocaleDateString('en-US', { month: 'long', year: 'numeric', timeZone: 'UTC' });
export { KIND_LABEL, KIND_LEGEND } from './kinds';
/** Latest yield dates in the data: most funds report the last business day of the month, a few the day before. */
const YD = [...new Set(FUNDS.map((f) => f.yDate))].sort();
export const YIELD_DAYS = YD.length > 1 ? `${displayDate(YD[0], 'en-US').replace(/, \d{4}$/, '')} or ${displayDate(YD[YD.length - 1], 'en-US')}` : displayDate(YD[0], 'en-US');

/** Expense drag as filed: series gross 7-day yield minus this class's net 7-day yield, same day. */
export const drag = (f: Fund) => (f.g != null ? Math.max(0, f.g - f.y) : null);
/** Accession number → filing index page on the SEC site. */
export const filingUrl = (f: Fund) => `https://www.sec.gov/Archives/edgar/data/${f.acc.split('-')[0].replace(/^0+/, '')}/${f.acc.replace(/-/g, '')}/${f.acc}-index.htm`;
export const quarterLabel = (ym: string) => `${({ '03': 'March 31', '06': 'June 30', '09': 'September 30', '12': 'December 31' } as Record<string, string>)[ym.slice(5)]}, ${ym.slice(0, 4)}`;

export const COMP_LABEL: Record<string, string> = { tsy: 'Treasury bills and notes', agyExempt: 'Debt of the Federal Home Loan Banks, Farm Credit Banks and Tennessee Valley Authority', agyOther: 'Fannie Mae, Freddie Mac and other agency debt', tsyRepo: 'Repo (short loans to banks and dealers) backed by Treasuries', agyRepo: 'Repo (short loans to banks and dealers) backed by agency securities', otherRepo: 'Other repo (short loans to banks and dealers)', muni: 'Municipal securities', other: 'Company and bank debt (commercial paper, certificates of deposit) and other' };

export function rank(sit: Situation, filter: (f: Fund) => boolean = () => true) {
  return FUNDS.filter(filter).map((f) => ({ f, r: afterTax(f, sit) })).sort((a, b) => b.r.afterTaxYield - a.r.afterTaxYield);
}
/** Average 7-day yield of share classes of a kind (simple mean across classes, as filed). */
export function avgYield(pred: (f: Fund) => boolean) {
  const xs = FUNDS.filter(pred).map((f) => f.y);
  return { n: xs.length, mean: xs.reduce((s, x) => s + x, 0) / Math.max(1, xs.length), min: Math.min(...xs), max: Math.max(...xs) };
}
