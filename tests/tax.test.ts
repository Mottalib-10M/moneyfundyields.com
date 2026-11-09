import { describe, it, expect } from 'vitest';
import { afterTax, marginal, federalRate, stateRate, fiftyTest } from '../src/lib/engine/tax';
import P from '../src/data/params-2026.json';

const govt = { y: 0.04, k: 'government' as const, usob: 0.7, q: { '2026-06': 0.62, '2026-09': 0.68 } };
const thin = { y: 0.04, k: 'treasury' as const, usob: 0.43, q: { '2026-06': 0.37, '2026-09': 0.36 } };
const caMuni = { y: 0.02, k: 'state-muni' as const, st: 'CA', usob: 0, q: {} };

describe('brackets (IRS Rev. Proc. 2025-32, 2026)', () => {
  it('single filer at 105,700 is still in the 22% bracket, 105,701 in 24%', () => {
    expect(federalRate('single', 105700).rate).toBe(0.22);
    expect(federalRate('single', 105701).rate).toBe(0.24);
  });
  it('joint filer at 400,000 is still at 24%', () => expect(federalRate('joint', 400000).rate).toBe(0.24) );
  it('NIIT starts above 200,000 single / 250,000 joint (IRC 1411)', () => {
    expect(federalRate('single', 200000).niit).toBe(0);
    expect(federalRate('single', 200001).niit).toBe(0.038);
    expect(federalRate('joint', 250001).niit).toBe(0.038);
  });
  it('California 2025: 9.3% from 72,724 single, plus 1% over $1M', () => {
    expect(stateRate({ state: 'CA', filing: 'single', income: 80000 })).toBe(0.093);
    expect(stateRate({ state: 'CA', filing: 'single', income: 1_200_000 })).toBeCloseTo(0.133, 10);
  });
  it('New York City adds 3.876% to a single filer above 50,000', () => {
    expect(stateRate({ state: 'NY', filing: 'single', income: 100000, nyc: true })).toBeCloseTo(0.06 + 0.03876, 10);
  });
  it('no-tax state and unknown state', () => {
    expect(stateRate({ state: 'TX', filing: 'single', income: 100000 })).toBe(0);
    expect(stateRate({ state: 'OH', filing: 'single', income: 100000, otherStateRate: 0.035 })).toBe(0.035);
    expect(marginal(P.states.PA.single as [number, number][], 1)).toBe(0.0307);
  });
});

describe('state exemption rules', () => {
  it('fund at 62% and 68% passes the CA/CT/NY 50% test; 37% and 36% fails', () => {
    expect(fiftyTest(govt.q)).toBe('passes');
    expect(fiftyTest(thin.q)).toBe('fails');
  });
  it('California resident, $100,000 at 4%, $90,000 income: fed 24%, CA 9.3% on the 30% not exempt', () => {
    const r = afterTax(govt, { amount: 100000, state: 'CA', filing: 'single', income: 90000 });
    expect(r.gross).toBeCloseTo(4000, 6);
    expect(r.fedTax).toBeCloseTo(880, 6); // 22% bracket at 90,000 single
    expect(r.stateTax).toBeCloseTo(4000 * 0.3 * 0.093, 6);
    expect(r.net).toBeCloseTo(4000 - 880 - 111.6, 6);
  });
  it('a fund under 50% loses the whole California exemption but keeps the pro rata share in New Jersey', () => {
    const ca = afterTax(thin, { amount: 100000, state: 'CA', filing: 'single', income: 90000 });
    expect(ca.exemptShare).toBe(0);
    const nj = afterTax(thin, { amount: 100000, state: 'NJ', filing: 'single', income: 90000 });
    expect(nj.exemptShare).toBeCloseTo(0.43, 10);
    expect(nj.stateTax).toBeCloseTo(4000 * 0.57 * 0.0637, 6);
  });
  it('tax letter percentage overrides the holdings estimate', () => {
    const r = afterTax(govt, { amount: 10000, state: 'IL', filing: 'single', income: 60000, exemptOverride: 0.5987 });
    expect(r.exemptShare).toBeCloseTo(0.5987, 10);
  });
  it('California municipal fund: free of federal tax, free of CA tax for a Californian, taxed in New York', () => {
    const ca = afterTax(caMuni, { amount: 50000, state: 'CA', filing: 'joint', income: 200000 });
    expect(ca.fedTax).toBe(0); expect(ca.stateTax).toBe(0); expect(ca.net).toBeCloseTo(1000, 6);
    const ny = afterTax(caMuni, { amount: 50000, state: 'NY', filing: 'joint', income: 200000 });
    expect(ny.stateTax).toBeCloseTo(1000 * 0.06, 6);
  });
  it('Texas resident pays federal tax only', () => {
    const r = afterTax(govt, { amount: 100000, state: 'TX', filing: 'single', income: 300000 });
    expect(r.stateTax).toBe(0);
    expect(r.fedTax).toBeCloseTo(4000 * (0.35 + 0.038), 6);
  });
  it('empty amount gives zero income but still an after-tax yield', () => {
    const r = afterTax(govt, { amount: 0, state: 'TX', filing: 'single', income: 50000 });
    expect(r.net).toBe(0); expect(r.afterTaxYield).toBeCloseTo(0.04 * 0.88, 10);
  });
});
