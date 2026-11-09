import { route, type Locale } from './routes';
import { PAGES, pageById, type Group } from '../lib/pages';
export interface NavLink { href: string; label: string } export interface NavCategory { label: string; links: NavLink[] }
const CORE: Record<string, string> = { home: 'All money fund yields', method: 'Data and method', about: 'About', widget: 'Embed the calculator', contact: 'Contact', editorial: 'Editorial policy', privacy: 'Privacy', terms: 'Legal notice', cookies: 'Cookies' };
export const GROUPS: Array<{ id: Group; label: string }> = [
  { id: 'funds', label: 'Funds' },
  { id: 'compare', label: 'Compare' },
  { id: 'states', label: 'By state' },
  { id: 'guides', label: 'Guides' },
];
export const label = (id: string) => CORE[id] ?? pageById(id)?.nav ?? id;
const link = (id: string, lang: Locale): NavLink => ({ href: route(id, lang), label: label(id) });
const inGroup = (g: Group, lang: Locale): NavLink[] => PAGES.filter((p) => p.group === g).map((p) => ({ href: route(p.id, lang), label: p.menu ?? p.nav }));
/** First entry of the menu, for a reader who does not know where to start (test naïf tour 4). */
const START: Array<[string, string]> = [['home', 'Rank all funds after tax (find yours)'], ['money-market-vs-high-yield-savings', 'Bank savings vs a money fund'], ['money-market-fund-rules', 'Is a money fund safe? The rules'], ['seven-day-yield', 'What the 7-day yield means']];
export function navCategories(lang: Locale): NavCategory[] {
  return [{ label: 'Start here', links: START.map(([id, l]) => ({ href: route(id, lang), label: l })) }, ...GROUPS.map((g) => ({ label: g.label, links: inGroup(g.id, lang) }))];
}
export const navDirect = (_lang: Locale): NavLink[] => [];
export const footerColumns = (lang: Locale): NavCategory[] => [
  { label: 'Funds', links: inGroup('funds', lang) },
  { label: 'Compare and states', links: [...inGroup('compare', lang), ...inGroup('states', lang)] },
  { label: 'Guides', links: inGroup('guides', lang) },
  { label: 'This site', links: ['home', 'method', 'about', 'contact', 'editorial', 'widget', 'terms', 'privacy', 'cookies'].map((i) => link(i, lang)) },
];
export const popularLinks = (_lang: Locale): NavLink[] => [];
