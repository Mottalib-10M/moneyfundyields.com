/** One set of fund-type labels for every page and island (test naif 2026-11-08: "Treasury only", "Treasury-only",
 *  "government" and "Government" sat side by side). Definitions follow the classification of scripts/build-data.py. */
export const KIND_LABEL: Record<string, string> = {
  'treasury-only': 'Treasury only', treasury: 'Treasury', government: 'Government', prime: 'Prime',
  muni: 'Municipal', 'state-muni': 'Single-state municipal',
};
/** One-line plain definition of each type, for the legend under the tables. */
export const KIND_LEGEND = 'Treasury only: holds only U.S. Treasury bills and notes. Treasury: Treasuries plus short loans to banks backed by Treasuries (called repo). Government: also holds debt of U.S. agencies and repo backed by it. Prime: also lends to banks and companies. Municipal: lends to states and cities, free of federal tax; a single-state municipal fund is also free of tax in its own state.';
