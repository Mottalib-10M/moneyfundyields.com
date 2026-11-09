/** État du calculateur encodé dans l'URL (lien partageable). Aucune donnée n'est transmise à un serveur.
 *
 * RÈGLE D’HYDRATATION (RECETTE-SITE.md §17.4) — ne jamais lire l’URL ni la date du jour pendant le
 * premier rendu d’un calculateur : le HTML servi a été calculé au build avec les valeurs par défaut, et
 * React signale une erreur (#418) dès que le premier rendu du navigateur diffère. Le schéma :
 *   const sp = new URLSearchParams();                       // premier rendu = valeurs par défaut
 *   const [gross, setGross] = useState(num(sp, 'brut', 2500));
 *   const [start, setStart] = useState(str(sp, 'd', __BUILD_DAY__));
 *   useEffect(() => { const u = readParams(window.location.search);
 *     setGross(num(u, 'brut', 2500)); setStart(str(u, 'd', new Date().toISOString().slice(0, 10))); }, []);
 * `check-layout.mjs` le contrôle (horloge avancée de deux jours, lien partagé rechargé).
 */
export function encodeState(params: Record<string, string | number | boolean | undefined>): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) if (v !== undefined && v !== null && v !== '') sp.set(k, String(v));
  return sp.toString();
}
export function readParams(search: string): URLSearchParams { return new URLSearchParams(search); }
export function num(sp: URLSearchParams, key: string, def: number): number {
  const v = sp.get(key); if (v === null) return def; const n = parseFloat(v); return isNaN(n) ? def : n;
}
export function str(sp: URLSearchParams, key: string, def: string): string { return sp.get(key) ?? def; }

let interacted = false;
if (typeof window !== 'undefined') {
  const mark = () => { interacted = true; };
  // Saisie, choix ou clic sur un bouton du calculateur : avant cela, la barre d'adresse reste
  // exactement l'URL de la page (sitemap, canonical, barre finale). check-url-propre.mjs.
  for (const t of ['input', 'change', 'click', 'keydown']) document.addEventListener(t, mark, { once: true, capture: true });
}
export function updateURL(params: Record<string, string | number | boolean | undefined>): void {
  if (!interacted || typeof window === 'undefined') return;
  const enc = encodeState(params);
  // Appel sur le prototype : un outil de mesure (Clarity) qui surveille history.replaceState
  // ne voit pas ce changement, et les valeurs saisies ne quittent donc pas le navigateur.
  History.prototype.replaceState.call(window.history, null, '', `${window.location.pathname}${enc ? '?' + enc : ''}`);
}
