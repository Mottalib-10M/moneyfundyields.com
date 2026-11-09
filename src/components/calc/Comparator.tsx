/** Home comparator: every share class in funds.json ranked by what it leaves after federal and state
 *  tax for the reader's situation. First render = build defaults (RECETTE §17.5). */
import { useEffect, useMemo, useState } from 'react';
import NumberField from '../ui/NumberField';
import SelectField from '../ui/SelectField';
import Toggle from '../ui/Toggle';
import { afterTax, hasSchedule, isNoTax, stateName, stateOptions, stateRule, type Filing } from '../../lib/engine/tax';
import { formatMoney } from '../../lib/format';
import { readParams, num, str, updateURL } from '../../lib/url-state';
import { TAXABLE_HELP, type FundLite } from './AfterTaxCalc';
import { KIND_LABEL, KIND_LEGEND } from '../../lib/kinds';
import MentionExemple from './MentionExemple';

export interface Row extends FundLite { name: string; reg: string; assets: number; min: number; g: number | null; href?: string }
interface Props { rows: Row[]; asOf: string; methodHref: string; series?: number; yieldDays?: string }
const pct = (x: number, d = 2) => `${(x * 100).toFixed(d)}%`;
const STATES = stateOptions();
const TYPES = [
  { value: 'all', label: 'All fund types' }, { value: 'tsy', label: 'Treasury funds' }, { value: 'government', label: 'Government funds' },
  { value: 'prime', label: 'Prime funds' }, { value: 'muni', label: 'Municipal funds' },
];
/** The reader's fund from what they type: a ticker (SPAXX), or a few letters of the name (test naïf tour 4: « où est mon fonds ? »). */
export function findFund(rows: Row[], q: string): Row | undefined {
  const x = q.trim().toLowerCase();
  if (x.length < 2) return undefined;
  return rows.find((r) => r.t.toLowerCase() === x) ?? (x.length >= 3 ? rows.find((r) => r.name.toLowerCase().includes(x)) ?? rows.find((r) => r.t.toLowerCase().startsWith(x)) : undefined);
}
const isEtf = (r: Row) => /\bETF\b/.test(r.name);
const match = (k: string, t: string) => t === 'all' || (t === 'tsy' ? k.startsWith('treasury') : t === 'muni' ? k.endsWith('muni') : k === t);

export default function Comparator({ rows, asOf, methodHref, series, yieldDays = '' }: Props) {
  const [state, setState] = useState('CA');
  const [filing, setFiling] = useState<Filing>('single');
  const [income, setIncome] = useState(120000);
  const [amount, setAmount] = useState(50000);
  const [other, setOther] = useState(5);
  const [type, setType] = useState('all');
  const [all, setAll] = useState(false);
  // Example fund shown until the reader types theirs: the default cash fund of the largest brokerage (test naïf tour 4).
  const [mineQ, setMineQ] = useState('SPAXX');
  const [myTouched, setMyTouched] = useState(false);
  // Example until the reader changes a box (test naif tour 2: "Highest yield after tax for you" before anything was typed).
  const [touched, setTouched] = useState(false);
  const mine = <T,>(f: (v: T) => void) => (v: T) => { setTouched(true); f(v); };
  useEffect(() => {
    const u = readParams(window.location.search);
    if (u.toString() === '') return;
    setState(str(u, 'st', 'CA')); setFiling(str(u, 'fs', 'single') === 'joint' ? 'joint' : 'single'); setIncome(num(u, 'inc', 120000));
    setAmount(num(u, 'amt', 50000)); setOther(num(u, 'sr', 5)); setType(str(u, 'type', 'all')); setMineQ(str(u, 'my', 'SPAXX'));
  }, []);
  useEffect(() => { updateURL({ st: state, fs: filing, inc: income, amt: amount, sr: hasSchedule(state) || isNoTax(state) ? undefined : other, type: type === 'all' ? undefined : type, my: mineQ === 'SPAXX' ? undefined : mineQ }); }, [state, filing, income, amount, other, type, mineQ]);
  const sit = { amount, state, filing, income, otherStateRate: other / 100 };
  const ranked = useMemo(() => rows.filter((r) => match(r.k, type)).map((r) => ({ r, x: afterTax(r, sit) })).sort((p, q) => q.x.afterTaxYield - p.x.afterTaxYield),
    [rows, state, filing, income, amount, other, type]);
  const shown = all ? ranked : ranked.slice(0, 20);
  const best = ranked[0];
  const myRow = findFund(rows, mineQ);
  const allRanked = useMemo(() => (type === 'all' ? ranked : rows.map((r) => ({ r, x: afterTax(r, sit) })).sort((p, q) => q.x.afterTaxYield - p.x.afterTaxYield)), [ranked, rows, type]);
  const myPos = myRow ? allRanked.findIndex((z) => z.r.t === myRow.t) : -1;
  const my = myPos >= 0 ? allRanked[myPos] : undefined;
  const top = allRanked[0];
  const myShownIdx = my ? shown.findIndex((z) => z.r.t === my.r.t) : -1;
  const rule = stateRule(state);
  const example = !touched && state === 'CA' && filing === 'single' && income === 120000 && amount === 50000;
  return (
    <div data-chrome data-outil className="not-prose">
      <div className="grid gap-6 rounded-xl border border-navy-200 bg-white p-4 sm:p-6 lg:grid-cols-[minmax(0,1fr)_340px]">
        <form className="grid content-start gap-x-4 gap-y-3 sm:grid-cols-2" onSubmit={(e) => e.preventDefault()} aria-label="Your tax situation">
          {example && <p className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-navy-800 sm:col-span-2"><strong>Example:</strong> single, California, $120,000 taxable income, $50,000 cash. Change the boxes to yours; every page starts from this example.</p>}
          <SelectField id="cmp-st" label="State you live in" value={state} onChange={mine(setState)} options={STATES} />
          <NumberField id="cmp-inc" label="Taxable income" value={income} onChange={mine(setIncome)} unit="$" max={10_000_000} help={TAXABLE_HELP} />
          <Toggle id="cmp-fs" label="Filing status" value={filing} onChange={mine((v: string) => setFiling(v === 'joint' ? 'joint' : 'single'))} options={[{ value: 'single', label: 'Single' }, { value: 'joint', label: 'Married, joint' }]} />
          <NumberField id="cmp-amt" label="Amount of cash" value={amount} onChange={mine(setAmount)} unit="$" max={50_000_000} />
          {!hasSchedule(state) && !isNoTax(state) && <NumberField id="cmp-sr" label="Your state tax rate" value={other} onChange={setOther} unit="%" max={20} decimals={2} help="Rate on your last dollar of income" />}
          <SelectField id="cmp-type" label="Show only one type of fund (optional)" value={type} onChange={setType} options={TYPES} />
          <div id="find-fund" className="grid grid-rows-subgrid row-span-3 content-start gap-y-0 sm:col-span-2 scroll-mt-24">
            <label htmlFor="cmp-my" className="mb-1 block text-sm font-medium text-navy-700">Your fund, to see where it ranks</label>
            <input id="cmp-my" type="search" list="cmp-my-list" value={mineQ} onChange={(e) => { setMyTouched(true); setMineQ(e.target.value); }} placeholder="Ticker or name, e.g. SPAXX" autoComplete="off"
              className="h-12 w-full rounded-lg border border-navy-300 bg-white px-4 text-lg text-navy-900 focus:border-accent-500 focus:outline-none focus:ring-2 focus:ring-accent-500/20" />
            <datalist id="cmp-my-list">{rows.map((r) => <option key={r.t} value={r.t}>{r.name}</option>)}</datalist>
            <p className="mt-1 text-xs text-navy-500">{myRow ? (!myTouched && mineQ === 'SPAXX' ? `Example: ${myRow.t} · ${myRow.name}. Type the ticker or name of yours` : `Found: ${myRow.t} · ${myRow.name}`) : mineQ.trim() ? 'No fund in the data matches; try the ticker shown in your account' : 'The short code in your brokerage account, like SPAXX or VMFXX'}</p>
          </div>
        </form>
        <div data-resultat aria-live="polite" className="rounded-xl bg-accent-50 p-4 sm:p-5">
          {best ? <>
            <MentionExemple lang="en" touched={example ? {} : { any: true }} />
            {my && top && <div data-mon-fonds className="mb-4 rounded-lg border border-accent-200 bg-white p-3">
              <p className="text-sm font-medium text-navy-700">{my.r.t}{!myTouched && mineQ === 'SPAXX' ? ' (example fund: type yours in the box)' : ''}: rank <strong className="tabular-nums">{myPos + 1} of {allRanked.length}</strong> after tax</p>
              <p className="tabular-nums text-2xl font-bold text-navy-900">{pct(my.x.afterTaxYield)} <span className="text-base font-medium text-navy-700">· {formatMoney(my.x.net)} a year kept</span></p>
              <p className="tabular-nums mt-1 text-sm text-navy-800">{myPos === 0 ? 'No fund in the data keeps more.' : <>The top fund keeps <strong>{formatMoney(Math.round(top.x.net) - Math.round(my.x.net))} more a year</strong> on {formatMoney(amount)}.</>}{my.r.href && <> <a className="font-medium text-accent-700 underline" href={my.r.href}>{my.r.t} in detail</a></>}</p>
            </div>}
            <p className="text-sm font-medium text-navy-700">Top fund after tax {example ? 'in this example' : 'for you'}, from the funds’ {asOf} reports to the SEC ({yieldDays})</p>
            <p className="tabular-nums text-4xl font-bold text-navy-900">{pct(best.x.afterTaxYield)}</p>
            <p className="text-sm text-navy-800"><strong>{best.r.name}</strong> ({best.r.t})</p>
            <p className="tabular-nums mt-2 text-sm text-navy-700">{formatMoney(best.x.net)} a year kept on {formatMoney(amount)}. Before tax this fund pays {pct(best.r.y)}; tax takes the difference.</p>
            <p className="mt-2 text-xs text-navy-700">Your brokerage decides which funds you can buy there, with what minimum and fee: check its list before moving cash. Not a bank account: a money fund is not FDIC-insured.</p>
            <p className="mt-2 text-xs text-navy-600">{rule === 'fifty' ? `${stateName(state)} taxes the whole dividend of a fund that kept less than half its money in U.S. government debt at a quarter end (the 50% rule). The ranking applies it.` : rule === 'none' ? 'No state income tax: only federal tax is taken.' : rule === 'unverified' ? 'This site has not checked your state’s rule: it assumes the part earned on U.S. government debt is free of state tax.' : 'Your state does not tax the part of a dividend earned on U.S. government debt.'} Ranking of past yields, not a recommendation. Nothing you type leaves your browser. <a className="underline" href={methodHref}>Method</a></p>
          </> : <p className="text-sm text-navy-700">No fund of this type in the data.</p>}
        </div>
      </div>
      <p className="mt-6 text-sm font-medium text-navy-800">{rows.length} versions (share classes){series ? ` of ${series} funds` : ''}, ranked by what you keep after federal and state tax, not by the yield before tax. A fund can come in several versions (share classes) with different fees; each one is a row.</p>
      <p className="mt-1 text-xs text-navy-600">Each fund is shown by name, then its ticker (like VMFXX), the short code your brokerage account shows. Underlined names have their own page on this site. Not every fund is open to you: the minimum shown is the one the fund reported to the SEC, and your brokerage decides whether it offers the fund.</p>
      {/* Repère pour lire le tableau : ouvert (testeurs naïfs du 2026-11-09, « Treasury only / Government : je ne sais pas ce que ça change »). */}
      <p className="mt-1 text-xs text-navy-700"><strong>Fund types.</strong> {KIND_LEGEND} The type comes from what the fund held, not from its name.</p>
      <div className="mt-2 overflow-x-auto">
        <table className="journal w-full text-sm">
          <thead><tr><th className="py-2 pr-3 text-left">Rank</th><th className="py-2 pr-3 text-left">Fund</th><th className="py-2 pr-3 text-right">You keep (after tax)</th><th className="hidden py-2 pr-3 text-right sm:table-cell">Kept a year</th><th className="py-2 pr-3 text-right">Before tax</th><th className="hidden py-2 pr-3 text-left sm:table-cell">Type</th><th className="hidden py-2 text-right md:table-cell">State-tax-free part</th></tr></thead>
          <tbody className="divide-y divide-navy-100">
            {shown.map(({ r, x }, i) => (
              <tr key={r.t} className={my && r.t === my.r.t ? 'bg-amber-50' : undefined}>
                <td className="tabular-nums py-2 pr-3 text-navy-500">{i + 1}</td>
                <td className="py-2 pr-3">{r.href ? <a href={r.href} className="font-medium text-accent-700 underline">{r.name}</a> : <span className="font-medium text-navy-900">{r.name}</span>} <span className="block text-xs text-navy-600">{r.t}{isEtf(r) && <span className="ml-1 rounded bg-navy-100 px-1 text-navy-700">ETF (exchange-traded fund), trades like a stock</span>}{r.min >= 1 && <span> · minimum {formatMoney(r.min)}</span>}<span className="sm:hidden"> · {KIND_LABEL[r.k]}{r.st ? ` (${r.st})` : ''}</span></span></td>
                <td className="tabular-nums py-2 pr-3 text-right font-semibold">{pct(x.afterTaxYield)}</td>
                <td className="tabular-nums hidden py-2 pr-3 text-right sm:table-cell">{formatMoney(x.net)}</td>
                <td className="tabular-nums py-2 pr-3 text-right text-navy-600">{pct(r.y)}</td>
                <td className="hidden py-2 pr-3 text-navy-700 sm:table-cell">{KIND_LABEL[r.k]}{r.st ? ` (${r.st})` : ''}</td>
                <td className="tabular-nums hidden py-2 text-right md:table-cell">{r.k.endsWith('muni') ? 'n/a' : pct(r.usob, 0)}</td>
              </tr>))}
            {my && myShownIdx < 0 && <tr data-mon-fonds-ligne className="bg-amber-50">
              <td className="tabular-nums py-2 pr-3 text-navy-500">{myPos + 1}</td>
              <td className="py-2 pr-3">{my.r.href ? <a href={my.r.href} className="font-medium text-accent-700 underline">{my.r.name}</a> : <span className="font-medium text-navy-900">{my.r.name}</span>} <span className="block text-xs text-navy-600">{my.r.t} · your fund{type !== 'all' ? ', rank among all types' : ''}</span></td>
              <td className="tabular-nums py-2 pr-3 text-right font-semibold">{pct(my.x.afterTaxYield)}</td>
              <td className="tabular-nums hidden py-2 pr-3 text-right sm:table-cell">{formatMoney(my.x.net)}</td>
              <td className="tabular-nums py-2 pr-3 text-right text-navy-600">{pct(my.r.y)}</td>
              <td className="hidden py-2 pr-3 text-navy-700 sm:table-cell">{KIND_LABEL[my.r.k]}{my.r.st ? ` (${my.r.st})` : ''}</td>
              <td className="tabular-nums hidden py-2 text-right md:table-cell">{my.r.k.endsWith('muni') ? 'n/a' : pct(my.r.usob, 0)}</td>
            </tr>}
          </tbody>
        </table>
      </div>
      {ranked.length > 20 && <button type="button" onClick={() => setAll(!all)} className="mt-3 rounded-lg border border-navy-300 px-4 py-2 text-sm font-medium text-navy-800 hover:bg-navy-50">{all ? 'Show the top 20' : `Show all ${ranked.length} funds`}</button>}
    </div>
  );
}
