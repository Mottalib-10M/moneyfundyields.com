/** 50% test, fund by fund: the reader picks a fund and sees its quarter-end figures and the verdict (test naïf tour 4:
 *  « personne ne connaît ces pourcentages »). Figures as filed, from the build; the typed-figures version stays below. */
import { useState } from 'react';
import SelectField from '../ui/SelectField';
import MentionExemple from './MentionExemple';
import { optionLabel } from './AfterTaxCalc';

interface F { t: string; name: string; q: Record<string, number>; href?: string }
interface Props { funds: F[]; quarters: Array<[string, string]>; def: string }
const pct = (x: number) => `${(x * 100).toFixed(1)}%`;

export default function FiftyPicker({ funds, quarters, def }: Props) {
  const [t, setT] = useState(def);
  const [touched, setTouched] = useState(false);
  const f = funds.find((x) => x.t === t) ?? funds[0];
  const vals = quarters.map(([k, label]) => ({ label, v: f.q[k] }));
  const ok = vals.every((x) => x.v != null && x.v >= 0.5);
  return (
    <div data-chrome data-outil className="not-prose my-8 rounded-xl border border-accent-200 bg-white p-4 shadow-sm sm:p-5">
      <p className="text-base font-semibold text-navy-900">Pick your fund to see if it passed</p>
      <div className="mt-3 grid gap-5 sm:grid-cols-2">
        <form onSubmit={(e) => e.preventDefault()}>
          <SelectField id="fifty-fund" label="Fund" value={f.t} onChange={(v) => { setTouched(true); setT(v); }} options={funds.map((x) => ({ value: x.t, label: optionLabel(x.t, x.name) }))} help="Government and Treasury funds in the data, largest first" />
        </form>
        <div data-resultat aria-live="polite" className="rounded-lg bg-navy-50 p-4">
          <MentionExemple lang="en" touched={touched ? { f: true } : {}} />
          <p className="text-sm font-medium text-navy-600">{f.t} in California, Connecticut and New York</p>
          <p className="mt-1 text-2xl font-bold text-navy-900">{ok ? 'Passes' : 'Fails: whole dividend taxed'}</p>
          <table className="mt-3 w-full text-sm"><tbody className="divide-y divide-navy-200">
            {vals.map((x) => <tr key={x.label}><td className="py-1.5 pr-3 text-navy-600">U.S. government debt on {x.label}</td><td className="tabular-nums py-1.5 text-right text-navy-900">{x.v != null ? pct(x.v) : 'n/a'}</td></tr>)}
          </tbody></table>
          <p className="mt-2 text-xs text-navy-500">The fund needs at least 50% at every quarter end. From its own reports to the SEC; its year-end tax letter gives the official answer. {f.href && <a className="underline" href={f.href}>{f.t} in detail</a>}</p>
        </div>
      </div>
    </div>
  );
}
