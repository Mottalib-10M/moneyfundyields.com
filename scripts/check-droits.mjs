#!/usr/bin/env node
/**
 * check-droits.mjs — fiabilité des données et droits d'affichage (RECETTE-SITE.md §12.1).
 *
 * Pourquoi ce contrôle existe. Le 2026-10-24, l'éditeur demande : « sur tous les sites on
 * a les infos fiables qu'on promet afficher et on a le droit de les afficher ? ». L'audit
 * des 12 sites du lot (reports/AUDIT-DONNEES-DROITS-2026-10-24.md) trouve : 93 liens
 * profonds vers onemotoring.lta.gov.sg sans l'autorisation écrite que la LTA exige, des
 * statuts lus sur FindLaw ou Justia présentés comme « official text », des copies Wayback
 * libellées « page officielle », des données OGL / CC BY / INE sans l'attribution que la
 * licence impose, et des promesses de relecture « every working day » sans aucun flux
 * planifié. Tous les contrôles de la trame étaient à 0.
 *
 * Ce que le script vérifie dans dist/ (chaque page HTML, redirections exclues) :
 *   a. Aucun lien vers un domaine dont les liens profonds demandent une autorisation :
 *      lta.gov.sg, onemotoring.lta.gov.sg, iras.gov.sg, cpf.gov.sg (et leurs sous-domaines),
 *      et mas.gov.sg hors accueil et /terms-of-use. On cite l'organisme sans lien.
 *   b. Aucun lien vers un relais juridique (findlaw.com, justia.com, law.cornell.edu,
 *      onecle, public.law) sauf s'il est présenté à côté comme « relais non officiel ».
 *      FindLaw interdit la reprise : jamais de lien, même présenté comme relais.
 *   c. Aucun lien web.archive.org entouré du mot « official / officiel / ufficiale… »
 *      sans « archive / archived / archivée / copia archiviata… » à proximité.
 *   d. Si le site cite une licence OGL, CC BY ou une donnée INE, le pied de page de chaque
 *      page porte la phrase d'attribution et le lien vers la licence.
 *   e. Une promesse de mise à jour automatique ou régulière (« every working day »,
 *      « chaque semaine », « automatically », « aucune valeur saisie à la main »,
 *      « every value is compared »…) n'apparaît que si le site a un workflow planifié
 *      (.github/workflows/*.yml avec `schedule:` / `cron`).
 *
 * Usage : node scripts/check-droits.mjs <dossier-du-site> [--liste]
 * Sortie : défauts par règle, code 1 s'il y en a.
 */
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative, resolve } from 'node:path';

const site = resolve(process.argv[2] || '.');
const LISTE = process.argv.includes('--liste');
const dist = ['dist', 'out'].map((d) => join(site, d)).find((d) => existsSync(d));
if (!dist) { console.error(`check-droits : pas de dist/ dans ${site} (lancer le build d'abord)`); process.exit(2); }

function* html(dir) {
  for (const e of readdirSync(dir)) {
    const p = join(dir, e);
    if (statSync(p).isDirectory()) yield* html(p);
    else if (e.endsWith('.html')) yield p;
  }
}

const ENT = { amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ', rsquo: '’', lsquo: '‘', laquo: '«', raquo: '»', ndash: '–', mdash: '—', middot: '·', hellip: '…', copy: '©' };
const decode = (s) => s
  .replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16)))
  .replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(Number(d)))
  .replace(/&([a-z]+);/gi, (m, n) => ENT[n.toLowerCase()] ?? m);
const sansCode = (h) => h.replace(/<!--[\s\S]*?-->/g, ' ').replace(/<(script|style|noscript|template)\b[\s\S]*?<\/\1>/gi, ' ');
const texte = (h) => decode(sansCode(h).replace(/<[^>]+>/g, ' ')).replace(/\s+/g, ' ').trim();

// ----- motifs -------------------------------------------------------------------------
const hote = (u) => { try { return new URL(u).hostname.toLowerCase().replace(/^www\./, ''); } catch { return ''; } };
const chemin = (u) => { try { return new URL(u).pathname.replace(/\/+$/, '') || '/'; } catch { return '/'; } };
const sous = (h, d) => h === d || h.endsWith('.' + d);

function autorisation(u) { // (a)
  const h = hote(u);
  for (const d of ['lta.gov.sg', 'iras.gov.sg', 'cpf.gov.sg']) if (sous(h, d)) return d === 'lta.gov.sg' && h.startsWith('onemotoring') ? 'onemotoring.lta.gov.sg' : d;
  if (sous(h, 'mas.gov.sg')) { const p = chemin(u).toLowerCase(); if (p !== '/' && p !== '/terms-of-use') return 'mas.gov.sg (page interne)'; }
  return null;
}
function relais(u) { // (b)
  const h = hote(u);
  if (sous(h, 'findlaw.com')) return 'findlaw.com';
  if (sous(h, 'justia.com')) return 'justia.com';
  if (h === 'law.cornell.edu' || sous(h, 'law.cornell.edu')) return 'law.cornell.edu';
  if (/(^|\.)onecle\.[a-z]+$/.test(h)) return 'onecle';
  if (sous(h, 'public.law')) return 'public.law';
  return null;
}
const NON_OFFICIEL = /relais non officiel|non officiel|non-officiel|pas officiel|unofficial|non-official|not official|not an official|not the official|non ufficiale|inoffiziell|nicht amtlich|no oficial|não oficial|niet officieel|非官方/i;
const OFFICIEL = /\b(official|officially|officiel|officielle|officiels|officielles|ufficiale|ufficiali|offiziell\w*|amtlich\w*|oficial|oficiales|oficiais|officieel|officiële)\b|官方/i;
const ARCHIVE = /archive|archiv|wayback|copia archiviata|gearchiveerd|存档|档案/i;

const WINDOW = 260;
function contexte(h, debut, fin) {
  const avant = texte(h.slice(Math.max(0, debut - 2500), debut));
  const apres = texte(h.slice(fin, fin + 2500));
  return { avant: avant.slice(-WINDOW), apres: apres.slice(0, WINDOW) };
}

// Le bloc qui contient le lien (puce, paragraphe, cellule) : la mention « relais non officiel » doit
// être dans le même bloc, pas dans la puce voisine.
const OUVRE = /<(li|p|td|th|dd|dt|tr|div|h[1-6]|figcaption|blockquote|section)\b[^>]*>/gi;
function bloc(h, debut, fin) {
  const avant = h.slice(Math.max(0, debut - 3000), debut);
  let d = 0; for (const m of avant.matchAll(OUVRE)) d = m.index + m[0].length;
  const apres = h.slice(fin, fin + 3000);
  const f = apres.search(/<\/(li|p|td|th|dd|dt|tr|div|h[1-6]|figcaption|blockquote|section)>|<(li|p|td|tr|div|h[1-6])\b/i);
  return texte(avant.slice(d) + h.slice(debut, fin) + (f < 0 ? apres : apres.slice(0, f)));
}

// (e) promesses de mise à jour
const DIRECT = [
  /aucune valeur (n['’]est )?(saisie|tapée|entrée) à la main/i,
  /no value (is )?(typed|entered|keyed|input)( in)? by hand/i,
  /nothing is (typed|entered|keyed) by hand/i,
  /every (single )?(value|figure|number) is (compared|checked|cross-checked|verified) (against|with)/i,
  /chaque (valeur|chiffre) (est )?(comparée?|vérifiée?|contrôlée?) (à|avec|aux)/i,
  /nessun valore (è |viene )?(inserito|digitato|scritto) a mano/i,
  /ogni valore (è |viene )?(confrontato|verificato) con/i,
  /kein (einziger )?Wert (wird )?(von Hand|manuell|händisch) (eingegeben|eingetragen)/i,
  /jeder Wert wird (mit .{0,40})?(verglichen|abgeglichen)/i,
  /ningún valor (se )?(introduce|teclea|escribe) a mano/i,
  /nenhum valor (é )?(digitado|introduzido) à mão/i,
  /geen (enkele )?waarde (wordt )?(met de hand|handmatig) (ingevoerd|ingetypt)/i,
  /ningun[ao]? (valor|cifra|dato) se (escribe|introduce|teclea) a mano/i,
  /no (figure|number) is (typed|entered|written) by hand/i,
  /nessun[ao]? (cifra|dato) (è |viene )?(inserit[oa]|digitat[oa]|scritt[oa]) a mano/i,
  /compar\w* (chaque|every|each|ogni|jeden|cada|elke) (valeur|value|figure|valore|Wert|valor|waarde)/i,
];
// Fréquences en locution : le verbe peut être avant ou après (« chaque semaine, le script relit », « täglich aktualisiert »).
const FREQ = /\b(every (working |business |single )?day|every weekday|every (week|month|quarter|night)|each (working )?(day|week|month|quarter)|automatically|chaque (jour( ouvré| ouvrable)?|semaine|mois|trimestre|nuit)|tous les (jours( ouvrés)?|mois)|toutes les semaines|automatiquement|quotidiennement|ogni (giorno( lavorativo)?|settimana|mese|trimestre)|settimanalmente|quotidianamente|mensilmente|automaticamente|jede[nr]? (Woche|Werktag|Arbeitstag|Tag|Monat|Quartal)|wöchentlich|täglich|werktäglich|monatlich|vierteljährlich|automatisch|elke (week|werkdag|dag|maand)|wekelijks|dagelijks|maandelijks|cada (semana|día|dia|mes|mês|trimestre)( hábil| útil)?|semanalmente|diariamente|mensualmente|trimestralmente|todos os (dias|meses)( úteis)?|todas as semanas|automáticamente)\b|每天|每周|每月|每季度|每个工作日|自动(?!化)/i;
// Adjectifs anglais nus (« daily rate », « monthly premium ») : seulement juste après le verbe (« updated daily »).
// Adjectifs anglais nus (« daily rate », « weekly check » = chèque de paie) : seulement collés au verbe
// (« updated daily ») ou au flux du site (« weekly job »).
const FREQ_ADJ = /\b(updated|refreshed|re-?read|re-?checked|fetched|pulled) (\w+ ){0,2}(daily|weekly|monthly|quarterly|nightly)\b|\b(daily|weekly|monthly|quarterly|nightly) (job|script|workflow|cron|run|refresh)\b/i;
// Verbes « forts » : relire une source, faire tourner un script — c'est forcément le site qui le fait.
const MAJ_FORT = /\b(read again|checked again|re-?reads?|re-?read|reloads?|relu[e]?s?|relit|relisons|relecture|rilegge\w*|rilett\w*|rilettura|neu eingelesen|neu (ge)?laden|herlezen|opnieuw gelezen|relee\w*|reli\w+ por|(scripts?|jobs?|workflows?|cron|procedura|tâche)\S* (\S+ ){0,3}(runs|tourne|draait|läuft|lädt|gira|corre|s['’]exécute)|(runs|tourne|draait|läuft|lädt|gira|corre) (\S+ ){0,3}(scripts?|jobs?|workflows?))\b/i;
// Verbes « faibles » : « updated every quarter » peut décrire l'administration (« Oregon publishes one schedule,
// updated every month ») ; on n'en retient que les phrases où le site parle de lui-même.
const MAJ_FAIBLE = /\b(updated|updating|refresh(e[sd])?|re-?checked|re-?fetched|fetched|pulled|downloaded|mis[e]? à jour|actualisée?s?|récupérée?s?|téléchargée?s?|aggiornat\w*|aggiorna|scaricat\w*|aktualisiert|abgerufen|eingelesen|abgeglichen|bijgewerkt|geüpdatet|opgehaald|actualizad\w*|atualizad\w*|descargad\w*)\b|更新|读取|抓取/i;
const SOI = /\b(script|job|workflow|cron|procedura|procédure|Verfahren|this (site|page)|the site|our|we|ce site|cette page|nos|notre|nous|questo sito|questa pagina|nostr[aoie]|diese (Seite|Website)|unsere?|wir|este sitio|esta página|nuestr[ao]s?|deze (site|pagina)|onze|we|calculat\w+|calculateur\w*|calcolator\w*|Rechner)\b|本站|本页|计算器/i;
const MANUEL = /\b(not|no longer|never|n['’]est pas|ne sont pas|pas encore|ne plus|nicht|kein\w*|non è|non viene|niet|no se|não|à la main|by hand|manual\w*|manuel\w*|manuell\w*|a mano|handmatig|à mão|pour l['’]instant|for now|per ora|vorerst|dès la mise en ligne|once (the site is )?live)\b|不|未|手动/i;

const CHAINE = /\b(scripts?|API|interfaces? officielles?|official (API|interface)|télécharg\w*|download\w*|fetch\w*|scaricat?\w*|herunterge\w*|descarg\w*|transfer\w*|automat\w*)\b/i;
const QUOTIDIEN = /day|jour|giorn|tag|täglich|dag|día|dia|nightly|nuit|notte|nacht|daily|automat|自动|每天|每个工作日/i;
const AUTO = /\b(script|job|workflow|cron|scheduled|automat\w*|planifié\w*|programmé\w*|pianificat\w*|programmat\w*|geplant\w*|zeitgesteuert|gepland\w*|programad\w*|agendad\w*)|自动|定时/i;

function promesses(t) {
  const out = [];
  // « Aucune valeur saisie à la main », « every value is compared » : la promesse d'une chaîne
  // automatique depuis la source. Sans contexte d'automatisation autour (« les calculateurs lisent ce
  // fichier ; aucun chiffre n'est tapé à la main »), c'est seulement « une seule source pour toutes les
  // pages », qui peut être vrai sans flux : on ne retient pas la phrase.
  for (const re of DIRECT) {
    const m = t.match(re); if (!m) continue;
    const autour = t.slice(Math.max(0, m.index - 300), m.index); // ce qui précède : « un script télécharge… »
    if (CHAINE.test(autour)) out.push({ p: m[0], direct: true });
  }
  for (const phrase of t.split(/(?<=[.!?;:·|])\s+|。/)) {
    if (phrase.length > 400) continue; // bloc sans ponctuation : listes de liens, menus
    if (MANUEL.test(phrase)) continue;              // phrase honnête : manuel, pas encore, négation
    const f = phrase.match(FREQ);
    const fort = phrase.match(MAJ_FORT), faible = SOI.test(phrase) ? phrase.match(MAJ_FAIBLE) : null;
    const ecart = (v) => (v.index > f.index ? v.index - (f.index + f[0].length) : f.index - (v.index + v[0].length));
    const proche = f && [fort, faible].some((v) => v && ecart(v) <= 40); // le verbe porte sur la fréquence
    const adj = phrase.match(FREQ_ADJ);
    if (!proche && !adj) continue;
    // Chaque jour ouvré, chaque nuit, « automatically » : intenable à la main, la promesse vise un flux.
    // Chaque semaine, mois, trimestre : une relecture humaine est possible (« relus chaque trimestre »
    // dans une charte éditoriale) ; on ne retient la phrase que si elle parle d'un flux automatique.
    const freq = (proche ? f[0] : '') + ' ' + (adj ? adj[0] : '');
    if (!QUOTIDIEN.test(freq) && !AUTO.test(phrase)) continue;
    out.push({ p: phrase.trim().slice(0, 160), direct: false });
  }
  return out;
}

// (d) licences
const LICENCES = {
  OGL: {
    cite: (t, h) => /Open Government Licen[cs]e|\bOGL\b/.test(t) || /nationalarchives\.gov\.uk\/doc\/open-government-licence/i.test(h),
    phrase: (ft) => /Open Government Licen[cs]e/i.test(ft),
    lien: (fh) => /href="[^"]*nationalarchives\.gov\.uk\/doc\/open-government-licence/i.test(fh),
    attendu: '« Contains public sector information licensed under the Open Government Licence v3.0. » + lien https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/',
  },
  'CC BY': {
    cite: (t, h) => /\bCC[ -]BY\b|Creative Commons Attribution/i.test(t) || /href="[^"]*creativecommons\.org\/licenses\/by\//i.test(h),
    phrase: (ft) => /\bCC[ -]BY\b|Creative Commons/i.test(ft),
    lien: (fh) => /href="[^"]*creativecommons\.org\/licenses\/by\//i.test(fh),
    attendu: 'producteur + jeu de données + « CC BY x.y » avec lien creativecommons.org/licenses/by/… + « adapté / calculs Radif Partners »',
  },
  INE: {
    cite: (t, h) => /href="https?:\/\/(www\.)?ine\.es[/"]/i.test(h),
    phrase: (ft) => /Elaboraci[oó]n propia con datos extra[ií]dos del sitio web del INE/i.test(ft),
    lien: (fh) => /ine\.es/i.test(fh),
    attendu: '« Elaboración propia con datos extraídos del sitio web del INE: www.ine.es »',
  },
};

// ----- passage sur le dist ------------------------------------------------------------
const defauts = { a: [], b: [], c: [], d: [], e: [] };
const pages = [];
for (const f of html(dist)) {
  const h = readFileSync(f, 'utf8');
  const rel = '/' + relative(dist, f);
  if (/<meta[^>]+http-equiv=["']?refresh/i.test(h) || !/<body/i.test(h)) continue; // redirection, fichier de vérification
  pages.push({ rel, h, t: texte(h) });
}

const licencesCitees = new Set();
for (const { rel, h, t } of pages) {
  for (const m of h.matchAll(/<a\b[^>]*\bhref\s*=\s*["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi)) {
    const url = decode(m[1]);
    if (!/^https?:\/\//i.test(url)) continue;
    const debut = m.index, fin = m.index + m[0].length;
    const lien = texte(m[2]);
    const a = autorisation(url);
    if (a) { defauts.a.push(`${rel} → ${url}  [${a}]`); continue; }
    const r = relais(url);
    if (r) {
      if (r === 'findlaw.com' || !NON_OFFICIEL.test(bloc(h, debut, fin)))
        defauts.b.push(`${rel} → ${url}${r === 'findlaw.com' ? '  [FindLaw interdit la reprise : relire le texte de la législature]' : ''}`);
      continue;
    }
    if (hote(url) === 'web.archive.org') {
      const { avant, apres } = contexte(h, debut, fin);
      const zone = avant + ' ' + lien + ' ' + apres;
      if (OFFICIEL.test(zone) && !ARCHIVE.test(zone)) {
        const mot = zone.match(OFFICIEL)[0];
        defauts.c.push(`${rel} → ${url.slice(0, 110)}  [« ${mot} » sans « copie archivée du … »] lien : « ${lien.slice(0, 70)} »`);
      }
    }
  }
  for (const [nom, L] of Object.entries(LICENCES)) if (L.cite(t, sansCode(h))) licencesCitees.add(nom);
}

for (const nom of licencesCitees) {
  const L = LICENCES[nom];
  const sansPhrase = [], sansLien = [];
  for (const { rel, h } of pages) {
    const fs = [...sansCode(h).matchAll(/<footer\b[\s\S]*?<\/footer>/gi)].map((m) => m[0]).join(' ');
    const fh = fs || sansCode(h); // un embed sans <footer> : la page entière tient lieu de pied
    if (!L.phrase(texte(fh))) sansPhrase.push(rel); else if (!L.lien(fh)) sansLien.push(rel);
  }
  const ex = (l) => l.slice(0, 3).join(', ');
  if (sansPhrase.length) defauts.d.push(`${nom} cité par le site : phrase d'attribution absente du pied de page sur ${sansPhrase.length}/${pages.length} page(s) (ex. ${ex(sansPhrase)}) — attendu : ${L.attendu}`);
  if (sansLien.length) defauts.d.push(`${nom} cité par le site : la licence est nommée dans le pied de page mais sans lien vers son texte sur ${sansLien.length}/${pages.length} page(s) (ex. ${ex(sansLien)}) — attendu : ${L.attendu}`);
}

const wfDir = join(site, '.github', 'workflows');
const wfs = existsSync(wfDir) ? readdirSync(wfDir).filter((x) => /\.ya?ml$/.test(x)) : [];
const planifie = wfs.some((x) => /^\s*schedule\s*:/m.test(readFileSync(join(wfDir, x), 'utf8')) && /cron\s*:/.test(readFileSync(join(wfDir, x), 'utf8')));
// Une fréquence promise exige un workflow planifié ; « aucune valeur saisie à la main » exige au moins
// un workflow (règle de l'éditeur, 2026-10-24) : un script lancé une fois peut avoir tout écrit.
if (!planifie) {
  const vus = new Map();
  for (const { rel, t } of pages) for (const { p, direct } of promesses(t)) {
    if (direct && wfs.length) continue;
    if (!vus.has(p)) vus.set(p, []); vus.get(p).push(rel);
  }
  const cause = wfs.length ? `aucun des workflows (${wfs.join(', ')}) n'est planifié (schedule/cron)` : 'aucun fichier .github/workflows/*.yml';
  for (const [p, rels] of vus) defauts.e.push(`« ${p} » — ${rels.length} page(s), ex. ${rels.slice(0, 3).join(', ')} ; ${cause}`);
}

// ----- compte rendu -------------------------------------------------------------------
const TITRES = {
  a: 'liens soumis à autorisation (citer l’organisme sans lien : titre, adresse en texte, date)',
  b: 'relais juridique présenté comme officiel (lien vers le texte officiel, ou « relais non officiel »)',
  c: 'copie web.archive.org présentée comme officielle (écrire « copie archivée du JJ/MM/AAAA »)',
  d: 'attribution de licence absente du pied de page',
  e: 'promesse de mise à jour sans workflow planifié (écrire « lu le JJ/MM/AAAA, mise à jour manuelle »)',
};
let total = 0;
console.log(`check-droits : ${pages.length} page(s) lues dans ${relative(process.cwd(), dist) || dist} ; licences citées : ${[...licencesCitees].join(', ') || 'aucune'} ; workflow planifié : ${planifie ? 'oui' : 'non'}`);
for (const k of Object.keys(TITRES)) {
  const l = defauts[k]; total += l.length;
  console.log(`  (${k}) ${TITRES[k]} : ${l.length}`);
  for (const x of (LISTE ? l : l.slice(0, 8))) console.log(`      ${x}`);
  if (!LISTE && l.length > 8) console.log(`      … ${l.length - 8} de plus (--liste pour tout voir)`);
}
console.log(total ? `check-droits : ${total} défaut(s)` : 'check-droits : 0 défaut');
process.exit(total ? 1 : 0);
