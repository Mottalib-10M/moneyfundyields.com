/** llms.txt (RECETTE §21), generated from the page registry. */
import { PAGES } from '../lib/pages';
import { SITE_URL, LAST_UPDATED, SITE_NAMES } from '../data/site-config';
import { route } from '../i18n/routes';
import { GROUPS } from '../i18n/nav';
import { META } from '../lib/data';
export function GET() {
  const lines = [
    `# ${SITE_NAMES.en}`, '',
    `> What a U.S. money market fund’s yield leaves after federal and state income tax. ${META.classes} retail share classes of ${META.series} funds, with 7-day net yields, holdings and maturities as filed on Form N-MFP with the Securities and Exchange Commission (latest month ending ${META.month}, reports filed ${META.filedFrom} to ${META.filedTo}); the share of income from U.S. obligations estimated from holdings; the 50% quarter-end test of California, Connecticut and New York; 2026 federal brackets and 2025 state schedules. Updated by hand for now, after a new month of reports has been filed; no automatic update. Independent site published by Radif Partners, not an investment adviser; not investment advice. Last updated ${LAST_UPDATED}.`, '',
    `- [All funds ranked after tax](${SITE_URL}${route('home', 'en')})`, '',
    ...GROUPS.flatMap((g) => [`## ${g.label}`, ...PAGES.filter((p) => p.group === g.id).map((p) => `- [${p.nav}](${SITE_URL}${route(p.id, 'en')}): ${p.card}`), '']),
    '## About', `- [Data and method](${SITE_URL}${route('method', 'en')})`, `- [About](${SITE_URL}${route('about', 'en')})`,
  ];
  return new Response(lines.join('\n') + '\n', { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
}
