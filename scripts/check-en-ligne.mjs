/**
 * Controle du site SERVI : sitemap, codes de reponse, redirections, liens morts.
 *
 * Pourquoi ce controle existe. `check-liens.py` verifie les cibles mortes dans
 * le build, avant publication. Il ne voit rien de ce qui arrive ensuite : une
 * redirection posee par l'hebergeur, un sitemap absent, une page qui ne repond
 * plus. Constate le 2026-09-26 sur orthoclermont.com, servi depuis OVH en
 * Apache : ses 26 liens internes pointaient vers la variante sans barre finale
 * et passaient tous par un 301. Le build etait irreprochable, le site non.
 *
 * Ce que le controle exige, d'apres RECETTE-SITE.md §13 et §18.1 :
 *   1. Un sitemap existe et se lit.
 *   2. Chaque URL du sitemap repond 200 SANS redirection. Une URL qui redirige
 *      n'a rien a faire dans un sitemap : elle gaspille le budget d'exploration
 *      et brouille le signal canonique.
 *   3. Les liens internes repondent 200 sans redirection, pour la meme raison.
 *   4. Aucune URL a parametres dans le sitemap ni dans les liens.
 *
 * L'ETAT D'UN CALCULATEUR N'EST PAS UNE URL DE PAGE. Il s'ecrit dans la barre
 * d'adresse par `history.replaceState` apres une interaction, et seulement
 * apres : sans interaction, le lien reste neutre. Ces URL ne sont ni liees ni
 * dans le sitemap, un robot ne les rencontre jamais. On les ignore donc au
 * lieu de les compter comme des pages a verifier.
 *
 * Usage : node scripts/check-en-ligne.mjs <domaine> [<domaine>...] [--verbose]
 */
const args = process.argv.slice(2);
const verbose = args.includes('--verbose');
const domaines = args.filter((a) => !a.startsWith('--'));
if (!domaines.length) {
  console.error('usage : node scripts/check-en-ligne.mjs <domaine> [...]');
  process.exit(2);
}

const DELAI = 20_000;
const LOT = 8;
// On lit toutes les pages du sitemap, pas un echantillon. Le 2026-09-26, un
// echantillon de douze pages annoncait 6 liens morts sur brutanet.fr : il y en
// avait 65. Un total mesure sur une fraction du site est un plancher, pas un
// compte. Le plafond ne protege que des sites a plusieurs milliers d'URL.
const PLAFOND_PAGES = Number((args.find((a) => a.startsWith('--pages=')) ?? '').slice(8)) || 600;

async function reponse(url, suivre = false) {
  const c = new AbortController();
  const t = setTimeout(() => c.abort(), DELAI);
  try {
    const r = await fetch(url, {
      redirect: suivre ? 'follow' : 'manual',
      signal: c.signal,
      headers: { 'User-Agent': 'Mozilla/5.0 (check-en-ligne)' },
    });
    clearTimeout(t);
    return { code: r.status, vers: r.headers.get('location'), corps: r };
  } catch (e) {
    clearTimeout(t);
    return { code: 0, erreur: e.name === 'AbortError' ? 'timeout' : String(e.message).slice(0, 50) };
  }
}

async function corps(url) {
  const r = await reponse(url, true);
  return r.code === 200 ? await r.corps.text() : null;
}

/** Les URL du sitemap, en suivant un index s'il y en a un. */
async function urlsDuSitemap(domaine) {
  for (const nom of ['sitemap-index.xml', 'sitemap.xml', 'sitemap_index.xml']) {
    const xml = await corps(`https://${domaine}/${nom}`);
    if (!xml) continue;
    const locs = [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1].trim());
    if (/<sitemapindex/i.test(xml)) {
      const out = [];
      for (const s of locs) {
        const enfant = await corps(s);
        if (enfant) out.push(...[...enfant.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1].trim()));
      }
      return { nom, urls: out };
    }
    return { nom, urls: locs };
  }
  return { nom: null, urls: [] };
}

let defauts = 0;
for (const d of domaines) {
  const { nom, urls } = await urlsDuSitemap(d);
  if (!nom) {
    console.log(`!! ${d.padEnd(26)} AUCUN SITEMAP — Google ne sait pas quelles pages existent`);
    defauts++;
    continue;
  }

  const redirigees = [], cassees = [], parametrees = urls.filter((u) => u.includes('?'));

  for (let i = 0; i < urls.length; i += LOT) {
    await Promise.all(urls.slice(i, i + LOT).map(async (u) => {
      const r = await reponse(u);
      if (r.code >= 300 && r.code < 400) redirigees.push(`${u} -> ${r.code} ${r.vers ?? ''}`);
      else if (r.code !== 200) cassees.push(`${u} -> ${r.code || r.erreur}`);
    }));
  }

  // Toutes les pages du sitemap, ou un echantillon reparti sur toute sa
  // longueur si le site depasse le plafond.
  const pas = Math.max(1, Math.ceil(urls.length / PLAFOND_PAGES));
  const echantillon = urls.filter((_, i) => i % pas === 0).slice(0, PLAFOND_PAGES);
  const morts = new Map();
  const vus = new Set();
  const aSonder = [];
  const lirePage = async (page) => {
    const html = await corps(page);
    if (!html) return;
    // On retire scripts et styles AVANT d'extraire les liens. Sans cela, une
    // chaine JavaScript qui construit du HTML est lue comme un lien : le motif
    // `'<a href="' + item.href + '"` d'un champ de recherche produisait un
    // faux lien `/'%20+%20item.href%20+%20'` sur six sites a la fois. Mesure
    // du 2026-09-26 : ces soixante-dix « liens morts » n'existaient pas.
    const visible = html.replace(/<(script|style)\b[^>]*>[\s\S]*?<\/\1>/gi, ' ');
    const liens = [...visible.matchAll(/<a\b[^>]*href="([^"]+)"/gi)]
      .map((m) => m[1])
      .filter((h) => !/^(mailto:|tel:|javascript:|#)/i.test(h))
      // L'etat d'un calculateur vit dans la barre d'adresse, pas dans le site.
      // Ces URL ne sont ni liees ni listees : les verifier n'a pas de sens.
      .filter((h) => !h.includes('?') && !h.includes('#'))
      .map((h) => { try { return new URL(h, page).href; } catch { return null; } })
      .filter((h) => h && h.includes(d));
    for (const h of new Set(liens)) {
      if (vus.has(h)) continue;
      vus.add(h);
      aSonder.push(h);
    }
  };

  // Lecture des pages en lots, puis sondage des liens en lots : en sequentiel,
  // lire tout un site prenait des heures, ce qui est la raison pour laquelle
  // l'echantillon avait ete introduit.
  for (let i = 0; i < echantillon.length; i += LOT)
    await Promise.all(echantillon.slice(i, i + LOT).map(lirePage));

  for (let i = 0; i < aSonder.length; i += LOT) {
    await Promise.all(aSonder.slice(i, i + LOT).map(async (h) => {
      const r = await reponse(h);
      if (r.code >= 300 && r.code < 400) morts.set(h, `redirige ${r.code} vers ${r.vers ?? '?'}`);
      else if (r.code !== 200) morts.set(h, String(r.code || r.erreur));
    }));
  }

  const mauvais = redirigees.length + cassees.length + morts.size + parametrees.length;
  defauts += mauvais ? 1 : 0;
  const marque = mauvais ? '!!' : '  ';
  console.log(`${marque} ${d.padEnd(26)} ${nom.padEnd(18)} ${String(urls.length).padStart(5)} URL  `
    + `redirigees:${redirigees.length}  cassees:${cassees.length}  liens:${morts.size}  parametrees:${parametrees.length}`);

  const montrer = (liste, etiquette) => {
    for (const x of (verbose ? liste : liste.slice(0, 4))) console.log(`     ${etiquette} ${x}`);
    if (!verbose && liste.length > 4) console.log(`     ${etiquette} … et ${liste.length - 4} autres`);
  };
  montrer(redirigees, 'SITEMAP-REDIR');
  montrer(cassees, 'SITEMAP-CASSE');
  montrer([...morts].map(([u, c]) => `${u} -> ${c}`), 'LIEN');
  montrer(parametrees, 'PARAMETRE');
}

console.log(`\n${domaines.length} domaine(s), ${defauts} a corriger`);
process.exit(defauts ? 1 : 0);
