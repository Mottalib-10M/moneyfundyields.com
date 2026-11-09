import { SITE_NAMES, SITE_URL, LAST_UPDATED, AUTHOR_NAME, CONTACT_EMAIL, CURRENCY, LANG_TAGS, AUTHOR_DESC, LEGAL, AUTHOR_SAME_AS, SITE_FOUNDED, KNOWS_ABOUT } from '../data/site-config';
import { route, type Locale } from '../i18n/routes';

/** `open` : question ouverte au chargement (la plus demandée), testeurs naïfs du 2026-11-08. */
export interface FAQItem { q: string; a: string; open?: boolean }
const inLang = (l: Locale) => LANG_TAGS[l];
const name = (l: Locale) => SITE_NAMES[l];
const sameAs = () => (AUTHOR_SAME_AS.length ? AUTHOR_SAME_AS : undefined);
const address = () => (LEGAL.city ? { '@type': 'PostalAddress', streetAddress: LEGAL.street, postalCode: LEGAL.postalCode, addressLocality: LEGAL.city, addressCountry: LEGAL.country } : undefined);

/** Nœud auteur réutilisé par tous les schémas : identité, diplôme, domaines d'expertise. */
export function authorNode(lang: Locale) {
  return {
    '@type': 'Organization', name: AUTHOR_NAME, url: `${SITE_URL}${route('about', lang)}`,
    email: CONTACT_EMAIL, description: AUTHOR_DESC[lang],
    // Une Organization citée comme auteur porte son ancienneté et ses principes
    // éditoriaux au même titre que l'éditeur (RECETTE §8.0). Les pages qui
    // n'émettent que ce nœud, FAQ et contact, les perdaient entièrement.
    foundingDate: SITE_FOUNDED, publishingPrinciples: `${SITE_URL}${route('editorial', lang)}`,
    knowsAbout: KNOWS_ABOUT[lang], sameAs: sameAs(),
  };
}
/** Éditeur imbriqué dans Article, WebSite et WebApplication.

Il portait le seul `foundingDate` : `founder` et `publishingPrinciples`
n'existaient que sur la page pilier, qui est la seule à émettre
`organizationSchema`. RECETTE-SITE.md §8.0 les veut sur chaque page. */
const publisherNode = (lang: Locale) => ({ '@type': 'Organization', name: name(lang), url: SITE_URL, foundingDate: SITE_FOUNDED, logo: { '@type': 'ImageObject', url: `${SITE_URL}/og-${lang}.png`, width: 1200, height: 630 }, address: address(),
  founder: authorNode(lang), publishingPrinciples: `${SITE_URL}${route('editorial', lang)}` });

export function webApplicationSchema(o: { name: string; description: string; path: string; lang: Locale }): string {
  return JSON.stringify({ '@context': 'https://schema.org', '@type': 'WebApplication', name: o.name, description: o.description, url: `${SITE_URL}${o.path}`,
    applicationCategory: 'FinanceApplication', operatingSystem: 'All', browserRequirements: 'Requires JavaScript', offers: { '@type': 'Offer', price: '0', priceCurrency: CURRENCY },
    inLanguage: inLang(o.lang), dateModified: LAST_UPDATED, isAccessibleForFree: true, author: authorNode(o.lang), publisher: publisherNode(o.lang) });
}
export function faqSchema(items: FAQItem[], lang: Locale): string {
  return JSON.stringify({ '@context': 'https://schema.org', '@type': 'FAQPage', inLanguage: inLang(lang), mainEntity: items.map((i) => ({ '@type': 'Question', name: i.q, acceptedAnswer: { '@type': 'Answer', text: i.a } })) });
}
export function breadcrumbSchema(items: Array<{ name: string; path: string }>): string {
  return JSON.stringify({ '@context': 'https://schema.org', '@type': 'BreadcrumbList', itemListElement: items.map((it, i) => ({ '@type': 'ListItem', position: i + 1, name: it.name, item: `${SITE_URL}${it.path}` })) });
}
export function organizationSchema(lang: Locale): string {
  return JSON.stringify({ '@context': 'https://schema.org', '@type': 'Organization', name: name(lang), url: SITE_URL, foundingDate: SITE_FOUNDED,
    logo: { '@type': 'ImageObject', url: `${SITE_URL}/og-${lang}.png`, width: 1200, height: 630 }, address: address(),
    telephone: LEGAL.phone || undefined, sameAs: sameAs(),
    contactPoint: { '@type': 'ContactPoint', email: CONTACT_EMAIL, contactType: 'customer support', url: `${SITE_URL}${route('contact', lang)}` },
    founder: authorNode(lang), publishingPrinciples: `${SITE_URL}${route('editorial', lang)}` });
}
export function personSchema(lang: Locale): string {
  return JSON.stringify({ '@context': 'https://schema.org', ...authorNode(lang), worksFor: publisherNode(lang) });
}
export function websiteSchema(lang: Locale): string {
  return JSON.stringify({ '@context': 'https://schema.org', '@type': 'WebSite', name: name(lang), url: `${SITE_URL}${route('home', lang)}`, inLanguage: inLang(lang), publisher: publisherNode(lang) });
}
export function articleSchema(o: { title: string; description: string; path: string; lang: Locale }): string {
  return JSON.stringify({ '@context': 'https://schema.org', '@type': 'Article', headline: o.title, description: o.description, url: `${SITE_URL}${o.path}`,
    datePublished: LAST_UPDATED, dateModified: LAST_UPDATED, inLanguage: inLang(o.lang), image: `${SITE_URL}/og-${o.lang}.png`,
    author: authorNode(o.lang), publisher: publisherNode(o.lang), isAccessibleForFree: true,
    mainEntityOfPage: { '@type': 'WebPage', '@id': `${SITE_URL}${o.path}` } });
}
/** WebPage avec date de dernière revue et relecteur : signal E-E-A-T sur les guides. */
export function webPageSchema(o: { name: string; description: string; path: string; lang: Locale }): string {
  return JSON.stringify({ '@context': 'https://schema.org', '@type': 'WebPage', name: o.name, description: o.description, url: `${SITE_URL}${o.path}`,
    inLanguage: inLang(o.lang), datePublished: LAST_UPDATED, dateModified: LAST_UPDATED, lastReviewed: LAST_UPDATED,
    reviewedBy: authorNode(o.lang), publisher: publisherNode(o.lang), isPartOf: { '@type': 'WebSite', name: name(o.lang), url: SITE_URL } });
}
export function contactPageSchema(o: { name: string; description: string; path: string; lang: Locale }): string {
  return JSON.stringify({ '@context': 'https://schema.org', '@type': 'ContactPage', name: o.name, description: o.description, url: `${SITE_URL}${o.path}`,
    inLanguage: inLang(o.lang), mainEntity: { ...publisherNode(o.lang), email: CONTACT_EMAIL, telephone: LEGAL.phone || undefined, knowsAbout: KNOWS_ABOUT[o.lang] } });
}
/** ProfilePage veut un DateTime complet (Search Console : « Invalid datetime value for dateModified » sur une date seule). */
export function profileDateTime(d: string): string {
  return /T\d/.test(d) ? d : `${d}T12:00:00+00:00`;
}
export function profilePageSchema(o: { path: string; lang: Locale }): string {
  return JSON.stringify({ '@context': 'https://schema.org', '@type': 'ProfilePage', url: `${SITE_URL}${o.path}`, inLanguage: inLang(o.lang), dateModified: profileDateTime(LAST_UPDATED), mainEntity: authorNode(o.lang) });
}
