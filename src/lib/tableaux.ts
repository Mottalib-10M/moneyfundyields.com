/**
 * Tableaux lisibles sur téléphone (testeurs naïfs du 2026-11-08, RECETTE §15.8).
 *
 * Sur quatre sites, les trois testeurs ont lu « $2,00( » au bord droit d'un tableau sans comprendre
 * qu'il fallait le faire glisser : le défilement horizontal avec ombre (audit du 2026-10-28) ne suffit
 * pas, la colonne qui porte la réponse reste hors de l'écran. Règle de la trame :
 *
 * - sous 768 px, un tableau du contenu de TROIS COLONNES OU PLUS devient une pile de fiches, qu'il déborde
 *   ou non (aucun testeur ne fait défiler, calculobeca.com) : une fiche par ligne, la première cellule en
 *   titre, chaque autre valeur précédée du nom de sa colonne (`data-label`). Un tableau de deux colonnes
 *   reste un tableau, sauf s'il déborde (il devient alors aussi des fiches) ;
 * - `data-label` est posé au build par `ContentTable.astro` et `tableHtml()` ; le script de BaseLayout
 *   (`SCRIPT_TABLEAUX`) le pose sur les autres tableaux (Markdown, HTML écrit à la main) à partir de leur
 *   `<thead>`, décide de l'empilement au rendu, et garde l'ombre de défilement pour ce qui déborde encore ;
 * - `empile: true` force les fiches sous 768 px, même à deux colonnes ; `data-pas-de-fiches` (ou `empile: false`) les refuse
 *   (tableau à lire en grille : barème croisé, calendrier) : il défile alors, avec l'ombre ;
 * - un tableau rendu par React (dans un `astro-island`) n'est pas modifié par le script, pour ne pas
 *   troubler l'hydratation : le composant pose lui-même `className="empile"` et `data-label`
 *   (`etiquettes()`).
 * - titre de la fiche (report du 2026-11-08) : quand la première colonne n'est qu'un rang (« # », « Rank »,
 *   « Rang »…, ou des nombres sans en-tête), la fiche prend pour titre la colonne suivante si elle porte du texte (le nom de
 *   l'État), et le rang reste affiché dans la fiche avec son libellé (`data-titre="2"` sur le `<table>`, ordre
 *   rétabli par CSS). Une 1re colonne de nombres qui porte un vrai nom (« Personas », « Lump sum ») reste le titre,
 *   précédé du nom de sa colonne (« Personas: 3 », calculobeca.com) ;
 * - une cellule qui porte du HTML (« <strong>Prix</strong> : … ») est enveloppée dans un seul `<span>` : la
 *   cellule d'une fiche est en `display: flex`, et chaque morceau y deviendrait sinon une colonne
 *   (financecertcost.com, sbaloancosts.com). `tableHtml(…, { html: true })` le fait au build, le script au rendu.
 * Styles : `table.empile` dans `global.css`.
 */
export type Cellule = string | number;
export interface OptionsTableau { caption?: string; align?: Array<'l' | 'r'>; empile?: boolean | 'auto'; className?: string; highlightRow?: number; html?: boolean }

/** Texte d'une cellule, balises retirées. */
const texte = (c: Cellule) => String(c).replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();
/** Une valeur seule, sans mot : « 3 », « #1 », « 12,5 % », « $1,200 », « 1–3 ». */
export const NOMBRE_SEUL = /^[#№=]?[\d\s.,%€$£¥+\-–−]+$/;
/** En-tête d'une colonne de rang. */
export const EN_TETE_RANG = /^(#|n[°º.]?|no\.?|nr\.?|rank|ranking|rang|classement|rango|platz|position|posizione|posição|pos\.?|lp\.?|sıra)$/i;

/**
 * Titre des fiches d'un tableau : `titre` = index de la colonne qui sert de titre (1 si la première n'est qu'un rang :
 * en-tête « # », « Rank », « Rang »…, ou colonne sans en-tête faite de nombres, et que la suivante porte du texte),
 * `nommer` = le titre n'est qu'un nombre et garde le nom de sa colonne devant lui (« Personas: 3 », « Age: 25 »).
 * Une 1re colonne chiffrée qui a un vrai nom (« Lump sum », « ZIP code ») reste le titre, nommée : la colonne
 * suivante (« 11.9 months ») n'en ferait pas un meilleur.
 */
export function ficheTitre(headers: Cellule[], rows: Cellule[][]): { titre: 0 | 1; nommer: boolean } {
  const lignes = rows.filter((r) => r.length >= 1);
  if (!lignes.length) return { titre: 0, nommer: false };
  const h0 = texte(headers[0] ?? '');
  const col0Nombres = lignes.every((r) => NOMBRE_SEUL.test(texte(r[0] ?? '')));
  const rang = EN_TETE_RANG.test(h0) || (h0 === '' && col0Nombres);
  const col1Texte = lignes.some((r) => { const t = texte(r[1] ?? ''); return t !== '' && !NOMBRE_SEUL.test(t); });
  if (rang && col1Texte && headers.length >= 2) return { titre: 1, nommer: false };
  return { titre: 0, nommer: col0Nombres && h0 !== '' && !EN_TETE_RANG.test(h0) };
}

/**
 * Nom de colonne de chaque cellule d'une ligne ; la cellule titre de la fiche n'en porte pas, sauf un titre qui
 * n'est qu'un nombre (`nommer`). Sans `fiche`, la première cellule est le titre.
 */
export function etiquettes(headers: string[], nCellules: number, fiche: { titre: 0 | 1; nommer: boolean } = { titre: 0, nommer: false }): string[] {
  return Array.from({ length: nCellules }, (_, i) => (i === fiche.titre && !fiche.nommer ? '' : (headers[i] ?? '').trim()));
}

const esc = (s: Cellule) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

/** Attributs du `<table>` selon la règle d'empilement (partagé par ContentTable.astro et tableHtml). */
export function attributsTableau(empile: boolean | 'auto' = 'auto', colonnes = 0): { classe: string; pasDeFiches: boolean } {
  return { classe: empile === true || (empile === 'auto' && colonnes >= 3) ? 'empile' : '', pasDeFiches: empile === false };
}

/** Contenu HTML d'une cellule : enveloppé dans un seul `<span>` s'il porte des balises (sinon la fiche, en flex, le coupe en colonnes). */
export const celluleHtml = (c: Cellule) => (typeof c === 'string' && /</.test(c) ? `<span>${c}</span>` : String(c));

/**
 * HTML d'un tableau de contenu (pages écrites en chaînes, `set:html`). Le texte des cellules est
 * échappé ; avec `html: true`, les cellules sont du HTML écrit par le site (non échappé, enveloppé par `celluleHtml`).
 */
export function tableHtml(headers: string[], rows: Cellule[][], o: OptionsTableau = {}): string {
  const { classe, pasDeFiches } = attributsTableau(o.empile, headers.length);
  const fiche = ficheTitre(headers, rows);
  const al = (i: number) => (o.align?.[i] === 'r' ? ' class="text-right"' : '');
  const cls = [classe, o.className].filter(Boolean).join(' ');
  const cel = (c: Cellule) => (o.html ? celluleHtml(c) : esc(c));
  return `<table${cls ? ` class="${cls}"` : ''}${pasDeFiches ? ' data-pas-de-fiches' : ''}${fiche.titre ? ' data-titre="2"' : ''}>`
    + (o.caption ? `<caption>${esc(o.caption)}</caption>` : '')
    + `<thead><tr>${headers.map((h, i) => `<th scope="col"${al(i)}>${esc(h)}</th>`).join('')}</tr></thead>`
    + `<tbody>${rows.map((r, ri) => {
      const lab = etiquettes(headers, r.length, fiche);
      return `<tr${ri === o.highlightRow ? ' class="ligne-vedette"' : ''}>${r.map((c, i) => `<td data-label="${esc(lab[i])}"${al(i)}>${cel(c)}</td>`).join('')}</tr>`;
    }).join('')}</tbody></table>`;
}

/**
 * Script de fin de page (BaseLayout) : fiches sous 768 px pour les tableaux de 3 colonnes ou plus et pour ceux qui débordent, puis ombre
 * de défilement (`.tableau-defile`, retirée en fin de défilement) pour ceux qui débordent encore.
 * Recalculé au chargement, quand le contenu de <main> change et quand la largeur change.
 * En ES5 et sans dépendance : il est injecté tel quel dans la page.
 */
export const SCRIPT_TABLEAUX = `(function(){var L=768;
function nc(t){var m=0;for(var i=0;i<t.rows.length;i++)m=Math.max(m,t.rows[i].cells.length);return m}
function ent(t){var h=t.tHead&&t.tHead.rows[t.tHead.rows.length-1];if(!h)return null;var e=[];for(var i=0;i<h.cells.length;i++){var c=h.cells[i];for(var k=0;k<(c.colSpan||1);k++)e.push((c.textContent||'').replace(/\\s+/g,' ').trim())}return e}
var NB=/^[#\u2116=]?[\\d\\s.,%\u20ac$\u00a3\u00a5+\\-\u2013\u2212]+$/,RG=/^(#|n[\u00b0\u00ba.]?|no\\.?|nr\\.?|rank|ranking|rang|classement|rango|platz|position|posizione|posi\u00e7\u00e3o|pos\\.?|lp\\.?|s\u0131ra)$/i;
function tx(c){return c?(c.textContent||'').replace(/\\s+/g,' ').trim():''}
function lig(t){var l=[];for(var j=0;j<t.tBodies.length;j++)for(var i=0;i<t.tBodies[j].rows.length;i++)if(t.tBodies[j].rows[i].cells.length)l.push(t.tBodies[j].rows[i]);return l}
function fic(t,e){var l=lig(t),c0=l.length>0,c1=false;for(var i=0;i<l.length;i++){if(!NB.test(tx(l[i].cells[0])))c0=false;var s=tx(l[i].cells[1]);if(s&&!NB.test(s))c1=true}
var h=e[0]||'',rg=RG.test(h)||(!h&&c0);if(l.length&&rg&&c1&&e.length>=2)return{t:1,n:false};return{t:0,n:c0&&!!h&&!RG.test(h)}}
function eti(t){var e=ent(t);if(!e)return false;var f=fic(t,e);if(f.t)t.setAttribute('data-titre','2');for(var j=0;j<t.tBodies.length;j++)for(var i=0;i<t.tBodies[j].rows.length;i++){var r=t.tBodies[j].rows[i],x=0;for(var k=0;k<r.cells.length;k++){var c=r.cells[k];if(!c.hasAttribute('data-label'))c.setAttribute('data-label',x===f.t&&!f.n?'':(e[x]||''));x+=c.colSpan||1}}return true}
function env(t){for(var j=0;j<t.tBodies.length;j++)for(var i=0;i<t.tBodies[j].rows.length;i++){var r=t.tBodies[j].rows[i];for(var k=0;k<r.cells.length;k++){var c=r.cells[k];if(c.childNodes&&c.childNodes.length>1){var s=document.createElement('span');while(c.firstChild)s.appendChild(c.firstChild);c.appendChild(s)}}}}
function deb(b){return b.scrollWidth-b.clientWidth>4}
function v(){var etroit=window.innerWidth<L;
document.querySelectorAll('main table').forEach(function(t){if(t.closest('astro-island'))return;if(etroit&&!t.classList.contains('empile')&&!t.hasAttribute('data-pas-de-fiches')){var b=t.closest('.overflow-x-auto')||t;var n=nc(t);if((n>=3||(n>=2&&deb(b)))&&eti(t))t.classList.add('empile','empile-auto')}if(t.classList.contains('empile'))env(t)});
document.querySelectorAll('main table,main .overflow-x-auto').forEach(function(t){var b=t.closest('.overflow-x-auto')||t,d=deb(b);b.classList.toggle('tableau-defile',d);if(d&&!b.__fin){b.__fin=1;b.addEventListener('scroll',function(){b.classList.toggle('fin',b.scrollLeft+b.clientWidth>=b.scrollWidth-4)},{passive:true})}})}
var r=0;function w(){if(!r){r=1;requestAnimationFrame(function(){r=0;v()})}}
v();addEventListener('load',function(){v();var m=document.querySelector('main');if(m&&window.MutationObserver)new MutationObserver(w).observe(m,{childList:true,subtree:true})});addEventListener('resize',w)})();`;
