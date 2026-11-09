/**
 * Libellés du bandeau de consentement, partagés par ConsentBanner et par le bouton
 * « gérer les cookies » du pied de page (BaseLayout) : les deux doivent toujours
 * parler la langue de la page, y compris sur les sites bilingues.
 */
export interface ConsentStrings {
  title: string; body: string; accept: string; reject: string; more: string; manage: string;
}

export const CONSENT_STRINGS: Record<string, ConsentStrings> = {
  fr: {
    title: 'Cookies et mesure d’audience',
    body: 'Le calculateur fonctionne entièrement dans votre navigateur et n’a besoin d’aucun cookie. Nous souhaitons seulement mesurer l’audience du site pour savoir quelles pages sont utiles. Rien n’est déposé sans votre accord.',
    accept: 'Accepter', reject: 'Continuer sans accepter', more: 'En savoir plus',
    manage: 'Gérer les cookies',
  },
  de: {
    title: 'Cookies und Reichweitenmessung',
    body: 'Der Rechner läuft vollständig in Ihrem Browser und braucht keine Cookies. Wir möchten lediglich messen, welche Seiten genutzt werden. Ohne Ihre Einwilligung wird nichts gespeichert.',
    accept: 'Einverstanden', reject: 'Ohne Einwilligung fortfahren', more: 'Mehr erfahren',
    manage: 'Cookie-Einstellungen',
  },
  nl: {
    title: 'Cookies en bezoekstatistieken',
    body: 'De rekenhulp werkt volledig in uw browser en heeft geen cookies nodig. We willen alleen meten welke pagina’s worden gebruikt. Zonder uw toestemming wordt er niets geplaatst.',
    accept: 'Akkoord', reject: 'Doorgaan zonder toestemming', more: 'Meer informatie',
    manage: 'Cookie-instellingen',
  },
  es: {
    title: 'Cookies y medición de audiencia',
    body: 'La calculadora funciona por completo en su navegador y no necesita cookies. Solo queremos saber qué páginas se utilizan. Sin su consentimiento no se instala nada.',
    accept: 'Aceptar', reject: 'Continuar sin aceptar', more: 'Más información',
    manage: 'Configurar cookies',
  },
  nb: {
    title: 'Informasjonskapsler og besøksstatistikk',
    body: 'Kalkulatoren kjører helt i nettleseren din og trenger ingen informasjonskapsler. Vi ønsker bare å måle hvilke sider som blir brukt. Ingenting lagres uten ditt samtykke.',
    accept: 'Godta', reject: 'Fortsett uten å godta', more: 'Les mer',
    manage: 'Innstillinger for informasjonskapsler',
  },
  da: {
    title: 'Cookies og besøgsstatistik',
    body: 'Beregneren kører helt i din browser og har ikke brug for cookies. Vi vil kun måle, hvilke sider der bliver brugt. Intet gemmes uden dit samtykke.',
    accept: 'Accepter', reject: 'Fortsæt uden at acceptere', more: 'Læs mere',
    manage: 'Cookie-indstillinger',
  },
  en: {
    title: 'Cookies and analytics',
    body: 'The calculator runs entirely in your browser and needs no cookies. We use analytics only to see which pages are useful. You can change your choice at any time.',
    accept: 'Accept', reject: 'Opt out', more: 'Learn more',
    manage: 'Cookie settings',
  },
};

export const consentStrings = (lang: string): ConsentStrings => CONSENT_STRINGS[lang] ?? CONSENT_STRINGS.en;
