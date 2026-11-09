/**
 * Découpage du résumé replié (Clamp.astro). Règles (RECETTE §26 du 2026-10-02, testeurs naïfs du
 * 2026-11-08) : jamais de coupure au milieu d'une phrase ; AU MOINS DEUX phrases visibles (avec une
 * seule, « Read the rest… » sous une ligne faisait croire à un texte vide ou à une autre page) ; un
 * début visible d'au moins 25 mots, quitte à montrer une phrase de plus ; rien à replier quand la
 * suite serait plus courte qu'une phrase.
 * Sigles (goldbycarat.co.uk, 2026-11-08) : un sigle employé dans la partie visible et défini plus
 * loin (« salaire journalier de référence (SJR) », « SJR (salaire…) », « SJR, c'est-à-dire … »)
 * fait descendre la coupure jusqu'à la phrase de sa définition : on ne montre jamais un sigle dont
 * l'explication est repliée. Une parenthèse ouverte n'est jamais coupée.
 */
// Fin de phrase : . ! ? (ou … ) suivi d'une espace puis d'une majuscule, d'un chiffre ou d'un guillemet ;
// 。！？ (chinois, japonais) sans espace.
const FIN = /(?<=[.!?…])\s+(?=[\p{Lu}\p{N}«“"(¿¡])|(?<=[。！？])/u;
// Points qui ne finissent pas une phrase : ordinal ou jour (« 1. April », « 3. Säule »), initiales
// (« U.S. », « z. B. »), abréviations courantes.
const ABREV = /(?:^|\s)(?:\d{1,2}|[\p{L}]|(?:[\p{L}]\.){1,3}[\p{L}]?|Mr|Mrs|Ms|Dr|Prof|St|Sr|Jr|Mt|Ft|vs|etc|approx|incl|ca|bzw|ggf|inkl|Nr|Abs|Art|art|Bd|av|env|cf|p|pp|No|no|n°|S|vgl|zB|Co|Inc|Ltd|Sra|Sto|Dott|Avv|Ing|sig)\.$/u;

export function decouperPhrases(text: string): string[] {
  const brut = text.trim().split(FIN).filter(Boolean);
  const out: string[] = [];
  for (const p of brut) {
    if (out.length && ABREV.test(out[out.length - 1])) out[out.length - 1] += ` ${p}`;
    else out.push(p);
  }
  // Jamais de coupure dans une parenthèse ouverte (« (soit 1,5 fois le SMIC. Voir plus bas) »).
  const fus: string[] = [];
  for (const p of out) {
    const prec = fus[fus.length - 1];
    if (prec !== undefined && (prec.match(/\(/g) ?? []).length > (prec.match(/\)/g) ?? []).length) fus[fus.length - 1] = `${prec} ${p}`;
    else fus.push(p);
  }
  return fus.map((s) => s.trim());
}

const SIGLE = '[A-ZÀ-Þ][A-ZÀ-Þ0-9&]{1,7}';
/** Rang de la phrase qui définit chaque sigle du texte. */
export function definitionsDeSigles(ps: string[]): Map<string, number> {
  const defs = new Map<string, number>();
  const motifs = [
    new RegExp(`\\p{L}[^()]{3,}\\((${SIGLE})\\)`, 'gu'),          // forme longue (SIGLE)
    new RegExp(`\\b(${SIGLE})\\s*\\((?=[^)]*\\p{Ll})`, 'gu'),    // SIGLE (forme longue)
    new RegExp(`\\b(${SIGLE}),?\\s+(?:c['’]est-à-dire|soit|autrement dit|i\\.e\\.|that is|meaning|which stands for|d\\.h\\.|es decir|cioè|ou seja|dat wil zeggen)\\b`, 'gu'),
  ];
  ps.forEach((ph, i) => { for (const m of motifs) for (const x of ph.matchAll(m)) if (!defs.has(x[1])) defs.set(x[1], i); });
  return defs;
}

const mots = (s: string) => (/[぀-ヿ㐀-鿿가-힯]/.test(s) ? Math.ceil(s.length / 2) : s.split(/\s+/).filter(Boolean).length);

export function replier(text: string, { phrases = 2, minMots = 25 }: { phrases?: number; minMots?: number } = {}): { tete: string; suite: string } {
  const ps = decouperPhrases(text);
  let n = Math.max(2, phrases);
  while (n < ps.length && mots(ps.slice(0, n).join(' ')) < minMots) n++;
  // Sigle visible mais défini dans la partie repliée : la coupure descend jusqu'à sa définition.
  const defs = definitionsDeSigles(ps);
  for (let change = true; change;) {
    change = false;
    const tete = ps.slice(0, n).join(' ');
    for (const [sg, i] of defs) if (i >= n && new RegExp(`(^|[^\\p{L}])${sg}(?![\\p{L}])`, 'u').test(tete)) { n = i + 1; change = true; }
  }
  if (ps.length - n < 1) return { tete: ps.join(' '), suite: '' };
  return { tete: ps.slice(0, n).join(' '), suite: ps.slice(n).join(' ') };
}
