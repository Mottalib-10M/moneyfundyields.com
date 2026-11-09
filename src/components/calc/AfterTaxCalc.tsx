/** After-tax yield calculator: one fund, two funds side by side, or a fund against a savings account
 *  or a Treasury bill ETF whose yield the reader types. Engine: lib/engine/tax.ts. First render = build
 *  defaults; the shared link is read after hydration (RECETTE §17.5). */
import { useEffect, useMemo, useState } from 'react';
import NumberField from '../ui/NumberField';
import SelectField from '../ui/SelectField';
import Toggle from '../ui/Toggle';
import StackedBar from '../ui/StackedBar';
import { afterTax, hasSchedule, isNoTax, stateName, stateOptions, stateRule, type Filing, type FundTax, type Result } from '../../lib/engine/tax';
import { formatMoney } from '../../lib/format';
import { readParams, num, str, updateURL } from '../../lib/url-state';
import MentionExemple from './MentionExemple';

export interface FundLite extends FundTax { t: string; name: string; yDate: string }
interface Alt { kind: 'savings' | 'etf' | 'bill'; label: string; defYield: number; help: string }
interface Props {
  funds: FundLite[]; a: string; b?: string; alt?: Alt; pick?: boolean;
  defState?: string; defFiling?: Filing; defIncome?: number; defAmount?: number; methodHref: string; id?: string;
  /** Every share class of the data: when given, a one-fund calculator says where the fund ranks for the reader (test naïf tour 4). */
  rankAll?: FundLite[];
  /** Second calculator of a page: it does not read or write the shared link, which belongs to the first one. */
  noUrl?: boolean;
}

const pct = (x: number, d = 2) => `${(x * 100).toFixed(d)}%`;
const STATES = stateOptions();
/** Where to find the figure (test naïf 2026-11-09: « je ne connais pas mon revenu imposable, je taperai mon brut »). */
export const TAXABLE_HELP = 'Form 1040 “taxable income” line, not salary. Rough is fine';
/** Simple 7-day yield to the yield of a year of daily reinvested dividends, the basis of an APY. */
export const effective = (y: number) => (1 + y / 365) ** 365 - 1;
/** The reverse: an APY back to the simple yearly rate of daily interest, the basis of a 7-day yield. */
export const simpleOfApy = (apy: number) => 365 * ((1 + apy) ** (1 / 365) - 1);
/** Gap in dollars as the reader can check it: difference of the two rounded amounts shown (test naif tour 2: 1,427 − 1,301 = 126, not 125). */
const gapShown = (x: number, y: number) => Math.round(x) - Math.round(y);
const longDate = (iso: string) => new Date(`${iso}T00:00:00Z`).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric', timeZone: 'UTC' });

export default function AfterTaxCalc({ funds, a, b, alt, pick = true, defState = 'CA', defFiling = 'single', defIncome = 120000, defAmount = 50000, methodHref, id = 'calc', rankAll, noUrl = false }: Props) {
  const [fa, setFa] = useState(a);
  const [fb, setFb] = useState(b ?? '');
  const [amount, setAmount] = useState(defAmount);
  const [state, setState] = useState(defState);
  const [filing, setFiling] = useState<Filing>(defFiling);
  const [income, setIncome] = useState(defIncome);
  const [other, setOther] = useState(5);
  const [nyc, setNyc] = useState('no');
  const [letter, setLetter] = useState(0);
  const [altYield, setAltYield] = useState(alt ? +(alt.defYield * 100).toFixed(2) : 0);
  const [altShare, setAltShare] = useState(100);
  // Until the reader changes a box, the figures are an example, and the calculator says so (test naif tour 2:
  // "California, $120,000, c'est moi ?" and "Highest yield for you" before anything was typed).
  const [touched, setTouched] = useState(false);
  const mine = <T,>(f: (v: T) => void) => (v: T) => { setTouched(true); f(v); };

  useEffect(() => {
    if (noUrl) return;
    const u = readParams(window.location.search);
    if (u.toString() === '') return;
    setFa(str(u, 'fund', a)); if (b) setFb(str(u, 'vs', b));
    setAmount(num(u, 'amt', defAmount)); setState(str(u, 'st', defState)); setFiling(str(u, 'fs', defFiling) === 'joint' ? 'joint' : 'single');
    setIncome(num(u, 'inc', defIncome)); setOther(num(u, 'sr', 5)); setNyc(str(u, 'nyc', 'no')); setLetter(num(u, 'tl', 0));
    if (alt) { setAltYield(num(u, 'ay', +(alt.defYield * 100).toFixed(2))); setAltShare(num(u, 'as', 100)); }
  }, []);
  useEffect(() => {
    if (noUrl) return;
    updateURL({ fund: fa, vs: b ? fb : undefined, amt: amount, st: state, fs: filing, inc: income, sr: hasSchedule(state) || isNoTax(state) ? undefined : other,
      nyc: state === 'NY' ? nyc : undefined, tl: letter || undefined, ay: alt ? altYield : undefined, as: alt?.kind === 'etf' ? altShare : undefined });
  }, [fa, fb, amount, state, filing, income, other, nyc, letter, altYield, altShare]);

  const sit = { amount, state, filing, income, otherStateRate: other / 100, nyc: nyc === 'yes', exemptOverride: letter > 0 ? letter / 100 : null };
  const fundA = funds.find((f) => f.t === fa) ?? funds[0];
  const fundB = b ? funds.find((f) => f.t === fb) ?? funds[1] : undefined;
  // Against a savings APY, both are put on the same footing. Tour 1 compounded the fund's yield, so VUSXX showed 3.01%
  // here and 2.96% in every ranking (test naif tour 2). Now the fund keeps the figure of every other page and the APY
  // the reader types is turned back into the simple yearly rate that a 7-day yield is quoted on.
  const vsApy = alt?.kind === 'savings';
  // A bill pays interest, not dividends (test naïf 2026-11-09: « $1,975 of dividends » pour un bon du Trésor).
  const altPaid = alt?.kind === 'savings' || alt?.kind === 'bill' ? 'interest' : 'dividends';
  const ra = useMemo(() => afterTax(fundA, sit), [fundA, amount, state, filing, income, other, nyc, letter]);
  const rb = useMemo(() => (fundB ? afterTax(fundB, { ...sit, exemptOverride: null }) : undefined), [fundB, amount, state, filing, income, other, nyc]);
  const altFund: FundTax | undefined = alt ? (alt.kind === 'savings'
    ? { y: simpleOfApy(altYield / 100), k: 'prime', usob: 0, q: { x: 0 } }
    : { y: altYield / 100, k: 'treasury-only', usob: altShare / 100, q: { x: altShare / 100 } }) : undefined;
  const rAlt = useMemo(() => (altFund ? afterTax(altFund, { ...sit, exemptOverride: null }) : undefined), [altYield, altShare, amount, state, filing, income, other, nyc, alt?.kind]);
  const second = rb ?? rAlt;
  // Where the fund ranks for the reader, and what the top fund keeps more (test naïf tour 4: the decisive figure was six screens down).
  const ranking = useMemo(() => {
    if (!rankAll || second) return undefined;
    const sitNoLetter = { ...sit, exemptOverride: null };
    const all = rankAll.map((f) => ({ f, r: f.t === fundA.t ? ra : afterTax(f, sitNoLetter) })).sort((p, q) => q.r.afterTaxYield - p.r.afterTaxYield);
    const pos = all.findIndex((x) => x.f.t === fundA.t);
    return { pos: pos + 1, n: all.length, top: all[0] };
  }, [rankAll, ra, fundA, amount, state, filing, income, other, nyc]);
  const secondName = fundB?.t ?? alt?.label ?? '';
  const secondInText = fundB?.t ?? (alt ? `a ${alt.kind === 'savings' ? alt.label.toLowerCase() : alt.label}` : '');
  const dates = [...new Set([fundA.yDate, ...(fundB ? [fundB.yDate] : [])])];
  // Libellé du choix : la liste de la trame l'affiche maintenant en entier (report du 2026-11-08) ; au-delà de
  // deux lignes sur un téléphone de 320 px le champ grandissait (check-layout). Le ticker vient d'abord et
  // identifie le fonds ; « Money Market Fund », commun à tous, est retiré, et un nom encore long est coupé
  // à un mot entier. Le nom complet reste dans le résultat.
  const opts = funds.map((f) => ({ value: f.t, label: optionLabel(f.t, f.name) }));
  const rule = stateRule(state);
  const example = !touched && state === defState && filing === defFiling && income === defIncome && amount === defAmount;
  const who = `${defFiling === 'joint' ? 'a married couple filing jointly' : 'a single filer'} in ${stateName(defState)}, ${formatMoney(defIncome)} of taxable income, ${formatMoney(defAmount)} of cash`;

  return (
    <div data-chrome data-outil className="not-prose grid gap-6 rounded-xl border border-navy-200 bg-white p-4 sm:p-6 lg:grid-cols-[minmax(0,1fr)_380px]">
      <form className="grid content-start gap-x-4 gap-y-3 sm:grid-cols-2" onSubmit={(e) => e.preventDefault()} aria-label="Your tax situation">
        {example && <p className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-navy-800 sm:col-span-2"><strong>Example:</strong> {who}. Change the boxes to your own numbers (every page starts from this example).</p>}
        {pick && <SelectField id={`${id}-fund`} label={b ? 'First fund' : 'Fund'} value={fundA.t} onChange={setFa} options={opts} className="sm:col-span-2" />}
        {!pick && b && <p className="text-sm text-navy-700 sm:col-span-2"><span className="font-medium">First fund:</span> {fundA.t} · {fundA.name}</p>}
        {b && <SelectField id={`${id}-vs`} label="Second fund" value={fundB?.t ?? ''} onChange={setFb} options={opts} className="sm:col-span-2" />}
        {alt && <NumberField id={`${id}-alt`} label={alt.kind === 'savings' ? 'Savings account rate (APY)' : `${alt.label} yield you see`} value={altYield} onChange={mine(setAltYield)} unit="%" max={20} decimals={2} help={alt.help} />}
        {alt?.kind === 'etf' && <NumberField id={`${id}-alts`} label="Share from Treasuries" value={altShare} onChange={setAltShare} unit="%" max={100} help="Leave 100% for an ETF that holds only Treasuries; its year-end tax letter gives the exact share" />}
        <SelectField id={`${id}-st`} label="State you live in" value={state} onChange={mine(setState)} options={STATES} />
        <NumberField id={`${id}-inc`} label="Taxable income" value={income} onChange={mine(setIncome)} unit="$" max={10_000_000} help={TAXABLE_HELP} />
        <Toggle id={`${id}-fs`} label="Filing status" value={filing} onChange={mine((v: string) => setFiling(v === 'joint' ? 'joint' : 'single'))} options={[{ value: 'single', label: 'Single' }, { value: 'joint', label: 'Married, joint' }]} />
        <NumberField id={`${id}-amt`} label="Amount of cash" value={amount} onChange={mine(setAmount)} unit="$" max={50_000_000} />
        {!hasSchedule(state) && !isNoTax(state) && <NumberField id={`${id}-sr`} label="Your state tax rate" value={other} onChange={setOther} unit="%" max={20} decimals={2} help="Top rate that applies to your last dollar" />}
        {state === 'NY' && <Toggle id={`${id}-nyc`} label="New York City resident" value={nyc} onChange={setNyc} options={[{ value: 'no', label: 'No' }, { value: 'yes', label: 'Yes' }]} />}
        <details className="sm:col-span-2 rounded-lg border border-navy-200 px-3 py-2">
          <summary className="cursor-pointer text-sm font-medium text-navy-700">Optional: the fund’s year-end tax letter, if you have it
            {/* Valeur actuelle du champ replié, lisible sans ouvrir. Phrase entière plutôt que « Now: » de la trame (testeurs naïfs du 2026-11-09). */}
            <span data-actuellement className="mt-0.5 block text-xs font-normal text-navy-600">{letter > 0 ? `In use: ${new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(letter)}% from your letter` : 'Nothing to do without it: this site estimates the share from the fund’s holdings'}</span></summary>
          <div className="mt-3 grid gap-x-4 sm:grid-cols-2">
            <NumberField id={`${id}-tl`} label={`${fundA.t}: share of dividends from U.S. government debt`} value={letter} onChange={setLetter} unit="%" max={100} decimals={2} help="Empty: the site’s holdings estimate is used" />
          </div>
        </details>
      </form>
      <div data-resultat aria-live="polite" className="rounded-xl bg-accent-50 p-4 sm:p-5">
        <MentionExemple lang="en" touched={example ? {} : { any: true }} />
        <ResultHead r={ra} name={fundA.t} />
        <Lines r={ra} rule={rule} name={fundA.t} />
        {ranking && <div data-rang className="mt-4 rounded-lg border border-accent-200 bg-white p-3 text-sm text-navy-800">
          <p>Rank <strong className="tabular-nums">{ranking.pos} of {ranking.n}</strong> after tax {example ? 'in this example' : 'for you'}.</p>
          <p className="tabular-nums mt-1">{ranking.pos === 1 ? `No fund in the data keeps more.` : <>The top fund, {ranking.top.f.name} ({ranking.top.f.t}), keeps <strong>{formatMoney(gapShown(ranking.top.r.net, ra.net))} more a year</strong> on {formatMoney(amount)}.</>}</p>
          <p className="mt-1 text-xs text-navy-600">{fundA.t} may be just your brokerage’s default. Your brokerage decides which other funds you can buy there, with what minimum and fee: check its list before moving cash. Not a bank account: not FDIC-insured.</p>
        </div>}
        {second && <div className="mt-4 border-t border-accent-200 pt-3">
          {/* The answer first, then the detail of the second fund (test naïf 2026-11-09: the conclusion came after two blocks). */}
          <p data-ecart className="mb-3 rounded-lg bg-white px-3 py-2 text-base text-navy-900">{gapShown(ra.net, second.net) >= 0
            ? <>{fundA.t} leaves <strong>{formatMoney(gapShown(ra.net, second.net))}</strong> more a year than {secondInText}.</>
            : <>{secondName} leaves <strong>{formatMoney(gapShown(second.net, ra.net))}</strong> more a year than {fundA.t}.</>}</p>
          {vsApy && <p className="mb-2 text-xs text-navy-700">Your bank’s {pct(altYield / 100)} APY pays about <strong>{formatMoney(amount * altYield / 100)}</strong> a year on {formatMoney(amount)}, interest on interest included. Fund yields leave that out, so the bank is counted the same way here: {pct(simpleOfApy(altYield / 100))}, {formatMoney(second.gross)} a year. Reinvested, both earn a little more.</p>}
          <ResultHead r={second} name={secondName} small paid={altPaid} />
          <Lines r={second} rule={rule} name={secondName} paid={altPaid === 'interest' ? 'Interest' : 'Dividends'} bank={vsApy} small />
          {vsApy && <p className="mt-2 text-xs text-navy-700">No brokerage account? A money fund is bought through one, opened with a fund company or a broker, which sets the funds offered, the minimum and fees. A bank’s money market <em>account</em> is not a fund.</p>}
        </div>}
        <p className="mt-3 text-xs text-navy-600">{dates.length > 1 ? `Yields reported by the funds for ${fundA.t} ${longDate(fundA.yDate)}, ${fundB!.t} ${longDate(fundB!.yDate)}` : `Yield reported by the fund for ${longDate(fundA.yDate)}`}; yields change daily. Estimate, not tax or investment advice. Nothing you type leaves your browser. <a href={methodHref} className="underline">How it is computed</a></p>
      </div>
    </div>
  );
}

function ResultHead({ r, name, small = false, paid = 'dividends' }: { r: Result; name: string; small?: boolean; paid?: string }) {
  return (<div>
    <p className="text-sm font-medium text-navy-700">{name} after federal and {r.rule === 'none' ? 'no state' : r.stateLabel} tax</p>
    <p className={`tabular-nums font-bold text-navy-900 ${small ? 'text-2xl' : 'text-4xl'}`}>{pct(r.afterTaxYield)}</p>
    <p className="tabular-nums text-sm text-navy-700">{formatMoney(r.net)} a year kept on {formatMoney(r.gross)} of {paid}</p>
  </div>);
}

function Lines({ r, rule, name, paid = 'Dividends', small = false, bank = false }: { r: Result; rule: string; name: string; paid?: string; small?: boolean; bank?: boolean }) {
  // In dollars, not as a share: "71% state-tax-free" sat next to "Kept 73%" and the two were read as one (test naif tour 2).
  // The rate applies to the taxed part only, and the line says so (test naïf 2026-11-09: « 9,3 % de 1 775 $, ça ne fait pas 48 $ »).
  const freeAmt = formatMoney(r.gross * r.exemptShare);
  const taxed = `${pct(r.stateRate, 2)} on the ${formatMoney(r.stateTaxable)} ${rule === 'unverified' ? 'the state' : r.stateLabel} taxes`;
  const free = r.stateTaxable <= 0.5 ? `none: all ${formatMoney(r.gross)} is free of ${r.stateLabel} tax` : `${taxed}; the other ${freeAmt} is free of it`;
  const note = rule === 'none' ? 'none: no state income tax' : bank ? `${taxed}: bank interest is taxed in full`
    : rule === 'fifty' ? (r.fifty === 'fails' ? `${taxed}: the fund missed the 50% rule, so all of it is taxed` : free)
    : rule === 'unverified' ? (r.stateTaxable <= 0.5 ? `none: all ${formatMoney(r.gross)} assumed free of state tax` : `${taxed}; the other ${freeAmt} assumed free of it`) : free;
  return (<>
    <table className="mt-3 w-full text-sm"><tbody className="divide-y divide-accent-200">
      <tr><td className="py-1.5 pr-2 text-navy-700">{paid} before tax</td><td className="tabular-nums py-1.5 text-right text-navy-900">{formatMoney(r.gross)}</td></tr>
      <tr><td className="py-1.5 pr-2 text-navy-700">{r.fedTax === 0 && r.gross > 0 ? <>Federal tax <span className="block text-xs text-navy-600">none: a municipal fund’s dividends are free of federal tax</span></> : `Federal tax at ${pct(r.fedRate + r.niit, 1)}`}</td><td className="tabular-nums py-1.5 text-right text-navy-900">−{formatMoney(r.fedTax)}</td></tr>
      <tr><td className="py-1.5 pr-2 text-navy-700">{rule === 'none' || rule === 'unverified' ? 'State tax' : `${r.stateLabel} tax`} <span className="block text-xs text-navy-600">{note}</span></td><td className="tabular-nums py-1.5 text-right text-navy-900">−{formatMoney(r.stateTax)}</td></tr>
    </tbody></table>
    {<div className="mt-3"><StackedBar ariaPrefix={`${name} dividends`} total={r.gross} segments={[{ label: 'Kept', value: Math.max(0, r.net), color: '#1F5C4A' }, { label: 'Federal', value: r.fedTax, color: '#94a3b8' }, { label: 'State', value: r.stateTax, color: '#cbd5e1' }]} /></div>}
  </>);
}

/** « VCTXX · Vanguard California Municipal » : ticker, puis le nom sans le suffixe commun, 38 caractères au plus. */
export function optionLabel(t: string, name: string): string {
  // Share class added to tell two rows apart (« · Investor Shares ») is left out: the ticker already does it.
  const court = name.split(' · ')[0].replace(/\s+money\s+(market\s+)?(fund|portfolio|account)s?\s*$/i, '').trim() || name;
  const s = `${t} · ${court}`;
  if (s.length <= 38) return s;
  const cut = s.slice(0, 37);
  return `${cut.slice(0, cut.lastIndexOf(' ') > t.length + 3 ? cut.lastIndexOf(' ') : 37).replace(/[\s,·-]+$/, '')}…`;
}
