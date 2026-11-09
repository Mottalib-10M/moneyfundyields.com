/** Mini-simulators of the guides (RECETTE §9.3). Pure arithmetic, no fund data: they run in the browser. */
import type { MiniSpec } from './mini-types';

const pct = (x: number, d = 2) => `${(x * 100).toFixed(d)}%`;
const usd = (x: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(x);
const yesNo = [{ value: '1', label: 'Yes' }, { value: '0', label: 'No' }];
const FED = [10, 12, 22, 24, 32, 35, 37].flatMap((r) => (r >= 32 ? [{ value: String(r), label: `${r}%` }, { value: String(r + 3.8), label: `${r}% + 3.8% surtax` }] : [{ value: String(r), label: `${r}%` }]));

const SPECS: Record<string, MiniSpec> = {
  'seven-day': {
    title: 'What a 7-day yield pays on your balance', cta: 'Compare funds after tax',
    inputs: [{ id: 'y', label: '7-day yield', def: 3.88, unit: '%', max: 20, decimals: 2 }, { id: 'a', label: 'Balance', def: 50000, unit: '$', max: 50_000_000 }],
    run: (v) => {
      const y = v.y / 100, a = v.a;
      return { head: ['Dividends over a year at this yield, before tax', usd(a * y)],
        rows: [['A month, before tax', usd((a * y) / 12)], ['A week, before tax', usd((a * y * 7) / 365)], ['Yield if dividends are reinvested every day (effective yield, comparable with a bank APY)', pct((1 + y / 365) ** 365 - 1)]],
        note: 'Only if the yield stayed where it is for a year, which it never does exactly. Tax comes out of these amounts: the full calculator shows what you keep.' };
    },
  },
  fifty: {
    title: 'Does a fund pass the 50% test?', cta: 'See every fund’s quarter-end figures',
    inputs: [{ id: 't', label: 'Treasury bills and notes', def: 40, unit: '%', max: 100, decimals: 1 }, { id: 'g', label: 'Federal Home Loan Bank, Farm Credit and Tennessee Valley Authority debt', def: 15, unit: '%', max: 100, decimals: 1 }],
    run: (v) => {
      const s = Math.min(100, v.t + v.g) / 100, ok = s >= 0.5;
      return { head: ['Share counted for the test', pct(s, 1)],
        rows: [['California, Connecticut, New York', ok ? 'Passes: this share is exempt' : 'Fails: whole dividend taxed'], ['New Jersey, Pennsylvania and Illinois', `${pct(s, 1)} exempt, no threshold`], ['Margin to the 50% line', `${((s - 0.5) * 100).toFixed(1)} points`]],
        note: 'Example figures: each fund page on this site shows its own. Repo (short loans to banks), Fannie Mae and Freddie Mac paper and bank debt count for nothing. The test applies at every quarter end.' };
    },
  },
  letter: {
    title: 'What the tax letter percentage is worth', cta: 'Use your letter in the full calculator',
    inputs: [{ id: 'd', label: 'Dividends from the fund this year', def: 2000, unit: '$', max: 10_000_000 }, { id: 'p', label: 'Share from U.S. obligations', def: 59.87, unit: '%', max: 100, decimals: 2 }, { id: 's', label: 'Your state tax rate', def: 9.3, unit: '%', max: 20, decimals: 2 }],
    run: (v) => {
      const sub = (v.d * v.p) / 100;
      return { head: ['Amount to subtract on your state return', usd(sub)],
        rows: [['State tax saved', usd((sub * v.s) / 100)], ['Dividends still taxed by the state', usd(v.d - sub)]],
        note: 'In California, Connecticut and New York only if the fund met the 50% test for the year; the letter usually says so.' };
    },
  },
  tey: {
    title: 'Tax-equivalent yield of a municipal fund', cta: 'Compare it with a taxable fund',
    inputs: [{ id: 'y', label: 'Municipal fund 7-day yield', def: 2.27, unit: '%', max: 20, decimals: 2 }, { id: 'f', label: 'Federal rate', def: 24, options: FED }, { id: 's', label: 'Your state rate', def: 5, unit: '%', max: 20, decimals: 2 }, { id: 'h', label: 'Fund of your own state?', def: 0, options: yesNo }],
    run: (v) => {
      const y = v.y / 100, f = v.f / 100, s = v.s / 100;
      // Taxable fund keeps Y(1-f-s); national muni keeps y(1-s); own-state muni keeps y.
      const kept = v.h ? y : y * (1 - s);
      const tey = kept / Math.max(0.01, 1 - f - s);
      return { head: ['A fully taxable fund must yield', pct(tey)],
        rows: [['Municipal fund keeps after tax', pct(kept)], ['Taxable fund at the same yield keeps', pct(y * (1 - f - s))]],
        note: 'Taxable fund assumed fully taxed by your state. A Treasury fund keeps more because its state share is exempt.' };
    },
  },
  limits: {
    title: 'Is a portfolio within the rule 2a-7 limits?', cta: 'See each fund’s filed maturities',
    inputs: [{ id: 'm', label: 'Weighted average maturity', def: 35, unit: 'days', max: 400 }, { id: 'l', label: 'Weighted average life', def: 80, unit: 'days', max: 400 }, { id: 'd', label: 'Daily liquid assets', def: 30, unit: '%', max: 100, decimals: 1 }, { id: 'w', label: 'Weekly liquid assets', def: 55, unit: '%', max: 100, decimals: 1 }],
    run: (v) => {
      const ok = [v.m <= 60, v.l <= 120, v.d >= 25, v.w >= 50];
      return { head: ['Within the limits', ok.every(Boolean) ? 'Yes' : 'No'],
        rows: [['Maturity, limit 60 days', ok[0] ? 'Within' : 'Over'], ['Life, limit 120 days', ok[1] ? 'Within' : 'Over'], ['Daily liquid, minimum 25%', ok[2] ? 'Met' : 'Below'], ['Weekly liquid, minimum 50%', ok[3] ? 'Met' : 'Below']],
        note: 'Tax-exempt funds are not held to the daily liquidity minimum.' };
    },
  },
};

export function getSpec(kind: string, _lang = 'en'): MiniSpec {
  const s = SPECS[kind];
  if (!s) throw new Error(`no mini spec ${kind}`);
  return s;
}
