// @ts-check
import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import sitemap from '@astrojs/sitemap';
import tailwindcss from '@tailwindcss/vite';
import { SITE_URL, LAST_UPDATED } from './src/data/site-config.js';
import { ROUTES, NOINDEX_PATHS, LOCALES, DEFAULT_LOCALE } from './src/i18n/routes.js';
export default defineConfig({
  site: SITE_URL, trailingSlash: 'always',
  integrations: [react(), sitemap({
    filter(page) { const p = new URL(page).pathname;
      /* '/' est la page de redirection vers la langue par defaut : elle porte
         un noindex, elle n'a donc rien a faire dans le sitemap. '/embed/' :
         pages d'iframe, hors sitemap pour la meme raison. */
      return p !== '/' && !NOINDEX_PATHS.includes(p) && !p.startsWith('/embed/'); },
    serialize(item) {
      item.lastmod = new Date(LAST_UPDATED);
      const p = new URL(item.url).pathname;
      const pair = ROUTES.find((r) => LOCALES.some((l) => r.paths[l] === p));
      if (pair && LOCALES.length > 1) item.links = [...LOCALES.map((l) => ({ lang: l, url: `${SITE_URL}${pair.paths[l]}` })), { lang: 'x-default', url: `${SITE_URL}${pair.paths[DEFAULT_LOCALE]}` }];
      return item;
    },
  })],
  i18n: { defaultLocale: DEFAULT_LOCALE, locales: [...LOCALES], routing: { prefixDefaultLocale: true, redirectToDefaultLocale: false } },
  // __BUILD_DAY__ : jour du build, identique serveur/navigateur — valeur par défaut des champs date au premier rendu.
  vite: { plugins: [tailwindcss()], define: { __BUILD_DAY__: JSON.stringify(new Date().toISOString().slice(0, 10)) } },
});
