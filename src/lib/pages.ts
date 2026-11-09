/** Page registry: every indexable content page of the site, in menu order. */
export type Group = 'funds' | 'compare' | 'states' | 'guides';
export interface PageDef { id: string; slug: string; group: Group; nav: string; card: string; menu?: string }

export const FUND_TICKERS = ['VMFXX', 'VUSXX', 'VMRXX', 'VMSXX', 'VCTXX', 'VYFXX', 'SPAXX', 'FDRXX', 'FZFXX', 'FDLXX', 'SPRXX', 'FZDXX', 'FTEXX', 'SWVXX', 'SNSXX', 'SNOXX', 'SNVXX', 'SWTXX'] as const;

/** Plain name of each fund page, shown on its card (test naif 2026-11-08: 18 cards with the same line and no name). */
const FUND_CARD: Record<string, string> = {
  VMFXX: 'Vanguard Federal Money Market: where Vanguard keeps uninvested cash', VUSXX: 'Vanguard Treasury Money Market: Treasuries only',
  VMRXX: 'Vanguard Cash Reserves Federal Money Market', VMSXX: 'Vanguard Municipal Money Market: free of federal tax',
  VCTXX: 'Vanguard California Municipal Money Market', VYFXX: 'Vanguard New York Municipal Money Market',
  SPAXX: 'Fidelity Government Money Market: where Fidelity keeps uninvested cash', FDRXX: 'Fidelity Government Cash Reserves',
  FZFXX: 'Fidelity Treasury Money Market', FDLXX: 'Fidelity Treasury Only Money Market', SPRXX: 'Fidelity Money Market: a prime fund',
  FZDXX: 'Fidelity Money Market, Premium class: a prime fund', FTEXX: 'Fidelity Municipal Money Market: free of federal tax',
  SWVXX: 'Schwab Prime Advantage Money Fund', SNSXX: 'Schwab U.S. Treasury Money Fund', SNOXX: 'Schwab Treasury Obligations Money Fund',
  SNVXX: 'Schwab Government Money Fund', SWTXX: 'Schwab Municipal Money Fund: free of federal tax',
};
/** Ticker and a short name in the menu (test naïf tour 4: « 18 codes nus, des plaques d'immatriculation »). */
const FUND_MENU: Record<string, string> = {
  VMFXX: 'Vanguard default cash fund', VUSXX: 'Vanguard Treasury', VMRXX: 'Vanguard Cash Reserves', VMSXX: 'Vanguard Municipal',
  VCTXX: 'Vanguard California Municipal', VYFXX: 'Vanguard New York Municipal', SPAXX: 'Fidelity default cash fund', FDRXX: 'Fidelity Government Cash Reserves',
  FZFXX: 'Fidelity Treasury', FDLXX: 'Fidelity Treasury Only', SPRXX: 'Fidelity Money Market (prime)', FZDXX: 'Fidelity Money Market, Premium',
  FTEXX: 'Fidelity Municipal', SWVXX: 'Schwab Prime Advantage', SNSXX: 'Schwab U.S. Treasury', SNOXX: 'Schwab Treasury Obligations',
  SNVXX: 'Schwab Government', SWTXX: 'Schwab Municipal',
};
const fundPages: PageDef[] = FUND_TICKERS.map((t) => ({ id: `fund-${t.toLowerCase()}`, slug: t.toLowerCase(), group: 'funds', nav: t, card: FUND_CARD[t], menu: `${t} · ${FUND_MENU[t]}` }));

export const PAGES: PageDef[] = [
  ...fundPages,
  { id: 'vmfxx-vs-vusxx', slug: 'vmfxx-vs-vusxx', group: 'compare', nav: 'VMFXX vs VUSXX', menu: 'Vanguard Federal vs Vanguard Treasury (VMFXX vs VUSXX)', card: 'Vanguard Federal against Vanguard Treasury, after state tax' },
  { id: 'spaxx-vs-fdrxx', slug: 'spaxx-vs-fdrxx', group: 'compare', nav: 'SPAXX vs FDRXX', menu: 'Two Fidelity government funds (SPAXX vs FDRXX)', card: 'Two Fidelity government funds, two expense levels' },
  { id: 'spaxx-vs-vmfxx', slug: 'spaxx-vs-vmfxx', group: 'compare', nav: 'SPAXX vs VMFXX', menu: 'Fidelity’s cash fund vs Vanguard’s (SPAXX vs VMFXX)', card: 'The default cash funds of Fidelity and Vanguard, after tax' },
  { id: 'swvxx-vs-snsxx', slug: 'swvxx-vs-snsxx', group: 'compare', nav: 'SWVXX vs SNSXX', menu: 'Schwab prime vs Schwab Treasury (SWVXX vs SNSXX)', card: 'Schwab prime against Schwab Treasury, by state' },
  { id: 'treasury-bills-vs-money-market-funds', slug: 'treasury-bills-vs-money-market-funds', group: 'compare', nav: 'T-bills, SGOV vs money funds', menu: 'Treasury bills and T-bill ETFs vs money funds', card: 'Bills bought yourself or a T-bill ETF (SGOV, BIL) against a money fund' },
  { id: 'money-market-vs-high-yield-savings', slug: 'money-market-vs-high-yield-savings', group: 'compare', nav: 'Money fund vs savings', card: 'Cash in a savings account? Compare it with a money fund after tax' },
  { id: 'prime-vs-government-money-market-funds', slug: 'prime-vs-government-money-market-funds', group: 'compare', nav: 'Prime vs government', menu: 'Prime vs government funds', card: 'Yield gap between prime, government and Treasury funds' },
  { id: 'california', slug: 'california', group: 'states', nav: 'California', card: 'The 50% rule and the funds that pass it' },
  { id: 'new-york', slug: 'new-york', group: 'states', nav: 'New York', card: 'State and New York City tax on fund dividends' },
  { id: 'connecticut', slug: 'connecticut', group: 'states', nav: 'Connecticut', card: 'Quarter-end test and 2025 brackets' },
  { id: 'new-jersey', slug: 'new-jersey', group: 'states', nav: 'New Jersey', card: 'Federal-debt share exempt with no threshold' },
  { id: 'pennsylvania', slug: 'pennsylvania', group: 'states', nav: 'Pennsylvania', card: 'Flat 3.07% and the exempt federal share' },
  { id: 'illinois', slug: 'illinois', group: 'states', nav: 'Illinois', card: 'Flat 4.95%, repo income taxed' },
  { id: 'no-income-tax-states', slug: 'no-income-tax-states', group: 'states', nav: 'No income tax states', card: 'Texas, Florida and seven others: only federal tax' },
  { id: 'seven-day-yield', slug: 'seven-day-yield', group: 'guides', nav: '7-day yield', card: 'What the 7-day yield measures and what it pays' },
  { id: 'fifty-percent-rule', slug: 'fifty-percent-rule', group: 'guides', nav: '50% rule', menu: 'The 50% state-tax rule', card: 'The quarter-end test of California, Connecticut and New York' },
  { id: 'us-government-obligations-percentage', slug: 'us-government-obligations-percentage', group: 'guides', nav: 'Tax letter %', menu: 'Your fund’s tax letter: the % to use', card: 'Using the fund’s year-end percentage on your state return' },
  { id: 'municipal-money-market-funds', slug: 'municipal-money-market-funds', group: 'guides', nav: 'Municipal funds', menu: 'Municipal funds (free of federal tax)', card: 'Tax-exempt and single-state funds, tax-equivalent yield' },
  { id: 'money-market-fund-rules', slug: 'money-market-fund-rules', group: 'guides', nav: 'Fund rules', card: 'Rule 2a-7: maturity limits, liquidity and fees' },
];
export const pageById = (id: string) => PAGES.find((p) => p.id === id);
