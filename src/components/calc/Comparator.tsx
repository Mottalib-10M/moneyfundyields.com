/** Home comparator: every share class in funds.json ranked by what it leaves after federal and state
 *  tax for the reader's situation. First render = build defaults (RECETTE §17.5). */
import { useEffect, useMemo, useState } from 'react';
import NumberField from '../ui/NumberField';
import SelectField from '../ui/SelectField';
import Toggle from '../ui/Toggle';
import { afterTax, hasSchedule, isNoTax, stateOptions, stateRule, type Filing } from '../../lib/engine/tax';
import { formatMoney } from '../../lib/format';
import { readParams, num, str, updateURL } from '../../lib/url-state';
import type { FundLite } from './AfterTaxCalc';
import { KIND_LABEL, KIND_LEGEND } from '../../lib/kinds';

export interface Row extends FundLite { name: string; reg: string; assets: number; min: number; g: number | null; href?: string }
interface Props { rows: Row[]; asOf: string; methodHref: string }
const pct = (x: number, d = 2) => `${(x * 100).toFixed(d)}%`;
const STATES = stateOptions();
const TYPES = [
  { value: 'all', label: 'All fund types' }, { value: 'tsy', label: 'Treasury funds' }, { value: 'government', label: 'Government funds' },
  { value: 'prime', label: 'Prime funds' }, { value: 'muni', label: 'Municipal funds' },
];
const match = (k: string, t: string) => t === 'all' || (t === 'tsy' ? k.startsWith('treasury') : t === 'muni' ? k.endsWith('muni') : k === t);

export default function Comparator({ rows, asOf, methodHref }: Props) {
  const [state, setState] = useState('CA');
  const [filing, setFiling] = useState<Filing>('single');
  const [income, setIncome] = useState(120000);
  const [amount, setAmount] = useState(50000);
  const [other, setOther] = useState(5);
  const [type, setType] = useState('all');
  const [all, setAll] = useState(false);
  // Example until the reader changes a box (test naif tour 2: "Highest yield after tax for you" before anything was typed).
  const [touched, setTouched] = useState(false);
  const mine = <T,>(f: (v: T) => void) => (v: T) => { setTouched(true); f(v); };
  useEffect(() => {
    const u = readParams(window.location.search);
    if (u.toString() === '') return;
    setState(str(u, 'st', 'CA')); setFiling(str(u, 'fs', 'single') === 'joint' ? 'joint' : 'single'); setIncome(num(u, 'inc', 120000));
    setAmount(num(u, 'amt', 50000)); setOther(num(u, 'sr', 5)); setType(str(u, 'type', 'all'));
  }, []);
  useEffect(() => { updateURL({ st: state, fs: filing, inc: income, amt: amount, sr: hasSchedule(state) || isNoTax(state) ? undefined : other, type: type === 'all' ? undefined : type }); }, [state, filing, income, amount, other, type]);
  const sit = { amount, state, filing, income, otherStateRate: other / 100 };
  const ranked = useMemo(() => rows.filter((r) => match(r.k, type)).map((r) => ({ r, x: afterTax(r, sit) })).sort((p, q) => q.x.afterTaxYield - p.x.afterTaxYield),
    [rows, state, filing, income, amount, other, type]);
  const shown = all ? ranked : ranked.slice(0, 20);
  const best = ranked[0];
  const rule = stateRule(state);
  const example = !touched && state === 'CA' && filing === 'single' && income === 120000 && amount === 50000;
  return (
    <div data-chrome data-outil className="not-prose">
      <div className="grid gap-6 rounded-xl border border-navy-200 bg-white p-4 sm:p-6 lg:grid-cols-[minmax(0,1fr)_340px]">
        <form className="grid content-start gap-x-4 gap-y-3 sm:grid-cols-2" onSubmit={(e) => e.preventDefault()} aria-label="Your tax situation">
          {example && <p className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-navy-800 sm:col-span-2"><strong>Example:</strong> a single filer in California, $120,000 of taxable income, $50,000 of cash. Change the boxes to your own numbers.</p>}
          <SelectField id="cmp-st" label="State you live in" value={state} onChange={mine(setState)} options={STATES} />
          <NumberField id="cmp-inc" label="Taxable income" value={income} onChange={mine(setIncome)} unit="$" max={10_000_000} help="After deductions, pensions included; a rough figure is fine" />
          <Toggle id="cmp-fs" label="Filing status" value={filing} onChange={mine((v: string) => setFiling(v === 'joint' ? 'joint' : 'single'))} options={[{ value: 'single', label: 'Single' }, { value: 'joint', label: 'Married, joint' }]} />
          <NumberField id="cmp-amt" label="Amount of cash" value={amount} onChange={mine(setAmount)} unit="$" max={50_000_000} />
          {!hasSchedule(state) && !isNoTax(state) && <NumberField id="cmp-sr" label="Your state tax rate" value={other} onChange={setOther} unit="%" max={20} decimals={2} help="Rate on your last dollar of income" />}
          <SelectField id="cmp-type" label="Show" value={type} onChange={setType} options={TYPES} />
        </form>
        <div data-resultat aria-live="polite" className="rounded-xl bg-accent-50 p-4 sm:p-5">
          {best ? <>
            {example && <p data-exemple className="mb-1 text-xs font-semibold uppercase tracking-wide text-amber-800">Example result</p>}
            <p className="text-sm font-medium text-navy-700">Highest yield after tax {example ? 'in this example' : 'for you'}, from the {asOf} reports</p>
            <p className="tabular-nums text-4xl font-bold text-navy-900">{pct(best.x.afterTaxYield)}</p>
            <p className="text-sm text-navy-800"><strong>{best.r.name}</strong> ({best.r.t})</p>
            <p className="tabular-nums mt-2 text-sm text-navy-700">{formatMoney(best.x.net)} a year kept on {formatMoney(amount)}. Before tax this fund pays {pct(best.r.y)}; tax takes the difference.</p>
            <p className="mt-2 text-xs text-navy-600">{rule === 'fifty' ? 'In your state, the part of a dividend earned on U.S. government debt is free of state tax only if the fund kept at least half its money in that debt at every quarter end. The ranking applies this.' : rule === 'none' ? 'No state income tax: only federal tax is taken.' : rule === 'unverified' ? 'This site has not checked your state’s rule: it assumes the part earned on U.S. government debt is free of state tax.' : 'Your state does not tax the part of a dividend earned on U.S. government debt.'} Ranking of past yields, not a recommendation. Nothing you type leaves your browser. <a className="underline" href={methodHref}>Method</a></p>
          </> : <p className="text-sm text-navy-700">No fund of this type in the data.</p>}
        </div>
      </div>
      <p className="mt-6 text-sm font-medium text-navy-800">Ranked by what you keep after federal and state tax, not by the yield before tax.</p>
      <p className="mt-1 text-xs text-navy-600">Each fund is shown by name, then its ticker (like VMFXX), the short code your brokerage account shows. Underlined names have their own page on this site. {KIND_LEGEND}</p>
      <div className="mt-2 overflow-x-auto">
        <table className="journal w-full text-sm">
          <thead><tr><th className="py-2 pr-3 text-left">#</th><th className="py-2 pr-3 text-left">Fund</th><th className="py-2 pr-3 text-right">You keep (after tax)</th><th className="hidden py-2 pr-3 text-right sm:table-cell">Kept a year</th><th className="py-2 pr-3 text-right">Before tax</th><th className="hidden py-2 pr-3 text-left sm:table-cell">Type</th><th className="hidden py-2 text-right md:table-cell">State-tax-free part</th></tr></thead>
          <tbody className="divide-y divide-navy-100">
            {shown.map(({ r, x }, i) => (
              <tr key={r.t}>
                <td className="tabular-nums py-2 pr-3 text-navy-500">{i + 1}</td>
                <td className="py-2 pr-3">{r.href ? <a href={r.href} className="font-medium text-accent-700 underline">{r.name}</a> : <span className="font-medium text-navy-900">{r.name}</span>} <span className="block text-xs text-navy-600">{r.t}<span className="sm:hidden"> · {KIND_LABEL[r.k]}{r.st ? ` (${r.st})` : ''}</span></span></td>
                <td className="tabular-nums py-2 pr-3 text-right font-semibold">{pct(x.afterTaxYield)}</td>
                <td className="tabular-nums hidden py-2 pr-3 text-right sm:table-cell">{formatMoney(x.net)}</td>
                <td className="tabular-nums py-2 pr-3 text-right text-navy-600">{pct(r.y)}</td>
                <td className="hidden py-2 pr-3 text-navy-700 sm:table-cell">{KIND_LABEL[r.k]}{r.st ? ` (${r.st})` : ''}</td>
                <td className="tabular-nums hidden py-2 text-right md:table-cell">{r.k.endsWith('muni') ? 'n/a' : pct(r.usob, 0)}</td>
              </tr>))}
          </tbody>
        </table>
      </div>
      {ranked.length > 20 && <button type="button" onClick={() => setAll(!all)} className="mt-3 rounded-lg border border-navy-300 px-4 py-2 text-sm font-medium text-navy-800 hover:bg-navy-50">{all ? 'Show the top 20' : `Show all ${ranked.length} funds`}</button>}
      <p className="mt-3 text-xs text-navy-600">A fund can come in several versions (share classes) with different fees; each one is a row.</p>
    </div>
  );
}
