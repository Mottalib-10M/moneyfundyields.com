/** After-tax yield of a money market fund for a US resident. Pure functions, no network.
 *  Parameters: src/data/params-2026.json (federal 2026 brackets, state 2025 schedules, state rules). */
import P from '../../data/params-2026.json';

export type Kind = 'treasury-only' | 'treasury' | 'government' | 'prime' | 'muni' | 'state-muni';
export type Filing = 'single' | 'joint';
export type Rule = 'fifty' | 'prorata' | 'none' | 'unverified';
type Schedule = Array<[number, number]>;
interface StateParams { name: string; rule: string; year: number; source: string; single: Schedule; joint: Schedule; default: number; surtax?: { over: number; rate: number }; nyc?: { single: Schedule; joint: Schedule } }
const STATES = P.states as unknown as Record<string, StateParams>;

export interface FundTax { y: number; k: Kind; st?: string | null; usob: number; q: Record<string, number> }
export interface Situation {
  amount: number; state: string; filing: Filing; income: number;
  /** Rate typed by the reader for a state whose schedule the site does not carry. */
  otherStateRate?: number;
  /** Share of dividends from U.S. obligations, from the fund's year-end tax letter (0..1). Overrides the holdings estimate. */
  exemptOverride?: number | null;
  nyc?: boolean;
}
export interface Result {
  gross: number; fedRate: number; niit: number; fedTax: number;
  stateRate: number; rule: Rule; exemptShare: number; fifty: 'passes' | 'fails' | 'n/a';
  stateTaxable: number; stateTax: number; net: number; afterTaxYield: number; stateLabel: string;
}

export function marginal(s: Schedule, income: number): number {
  let r = s[0][1];
  for (const [from, rate] of s) if (income > from) r = rate;
  return r;
}
/** 2026 standard deduction (Rev. Proc. 2025-32): pay minus this is a fair guess of taxable income. */
export const STANDARD_DEDUCTION = (P.federal as unknown as { standardDeduction: { single: number; joint: number } }).standardDeduction;
export const isNoTax = (st: string) => st in P.noTaxNames;
export const hasSchedule = (st: string) => st in STATES;
export function stateName(st: string): string {
  return STATES[st]?.name ?? (P.noTaxNames as Record<string, string>)[st] ?? (P.otherStates as Record<string, string>)[st] ?? st;
}
export function stateRule(st: string): Rule {
  if (isNoTax(st)) return 'none';
  const s = STATES[st];
  if (!s) return 'unverified';
  return s.rule === 'fifty' ? 'fifty' : 'prorata';
}
export function stateRate(sit: Pick<Situation, 'state' | 'filing' | 'income' | 'otherStateRate' | 'nyc'>): number {
  if (isNoTax(sit.state)) return 0;
  const s = STATES[sit.state];
  if (!s) return Math.max(0, Math.min(0.2, sit.otherStateRate ?? P.otherStateDefaultRate));
  let r = marginal(s[sit.filing], sit.income);
  if (s.surtax && sit.income > s.surtax.over) r += s.surtax.rate;
  if (sit.nyc && s.nyc) r += marginal(s.nyc[sit.filing], sit.income);
  return r;
}
export function federalRate(filing: Filing, income: number): { rate: number; niit: number } {
  const rate = marginal(P.federal[filing] as Schedule, income);
  const niit = income > P.federal.niit[filing] ? P.federal.niit.rate : 0;
  return { rate, niit };
}
/** CA, CT, NY: the fund must hold at least 50% in U.S. obligations at the close of each quarter. */
export function fiftyTest(q: Record<string, number>): 'passes' | 'fails' | 'n/a' {
  const v = Object.values(q);
  if (!v.length) return 'n/a';
  return v.every((x) => x >= 0.5) ? 'passes' : 'fails';
}

export function afterTax(f: FundTax, sit: Situation): Result {
  const amount = Math.max(0, sit.amount);
  const gross = amount * f.y;
  const muni = f.k === 'muni' || f.k === 'state-muni';
  const { rate: fedRate, niit } = federalRate(sit.filing, sit.income);
  const fedTax = muni ? 0 : gross * (fedRate + niit);
  const rule = stateRule(sit.state);
  const sRate = stateRate(sit);
  const fifty = muni ? 'n/a' : fiftyTest(f.q);
  let exemptShare = 0;
  if (rule !== 'none') {
    if (f.k === 'state-muni') exemptShare = f.st === sit.state ? 1 : 0;
    else if (f.k === 'muni') exemptShare = 0;
    else {
      const e = sit.exemptOverride != null ? Math.max(0, Math.min(1, sit.exemptOverride)) : Math.max(0, Math.min(1, f.usob));
      exemptShare = rule === 'fifty' ? (fifty === 'passes' ? e : 0) : e;
    }
  }
  const stateTaxable = rule === 'none' ? 0 : gross * (1 - exemptShare);
  const stateTax = stateTaxable * sRate;
  const net = gross - fedTax - stateTax;
  return { gross, fedRate, niit: muni ? 0 : niit, fedTax, stateRate: sRate, rule, exemptShare, fifty, stateTaxable, stateTax, net,
    afterTaxYield: amount > 0 ? net / amount : f.y * (1 - (muni ? 0 : fedRate + niit)) - f.y * (rule === 'none' ? 0 : (1 - exemptShare) * sRate),
    stateLabel: stateName(sit.state) };
}

/** All states offered in the selectors: name order. */
export function stateOptions(): Array<{ value: string; label: string }> {
  const all: Record<string, string> = { ...(P.otherStates as Record<string, string>), ...(P.noTaxNames as Record<string, string>) };
  for (const [k, v] of Object.entries(STATES)) all[k] = v.name;
  return Object.entries(all).sort((a, b) => a[1].localeCompare(b[1])).map(([value, label]) => ({ value, label }));
}
