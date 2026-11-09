/** Titles 50-60 characters, descriptions 150-160 (RECETTE §11). A page gives several candidates; the
 *  first one inside the range wins, and the build fails if none fits (check-snippets.py would anyway). */
export function fit(cands: string[], lo: number, hi: number, what: string): string {
  const ok = cands.find((c) => c.length >= lo && c.length <= hi);
  if (!ok) throw new Error(`${what}: no candidate within ${lo}-${hi}: ${cands.map((c) => `${c.length}:${c}`).join(' | ')}`);
  return ok;
}
export const title = (c: string[]) => fit(c, 50, 60, 'title');
export const desc = (c: string[]) => fit(c, 150, 160, 'description');
/** Pads a description with short endings until it reaches 150-160 characters. */
export function descPad(base: string, ends: string[]): string {
  const c = [base, ...ends.map((e) => `${base} ${e}`)];
  for (let i = 0; i < ends.length; i++) for (let j = i + 1; j < ends.length; j++) c.push(`${base} ${ends[i]} ${ends[j]}`);
  return desc(c);
}
