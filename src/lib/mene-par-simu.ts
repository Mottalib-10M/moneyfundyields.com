// Page qui commence par un simulateur (RECETTE §8.4, même définition que check-trame.py) :
// premier champ de saisie à moins de 250 mots du titre. Sur une telle page, la date de mise à
// jour ne se met pas au-dessus du simulateur ; sur une page de lecture, elle se montre en haut.
const SIMU_INPUT = /<input\b(?![^>]*type="(?:hidden|search|checkbox|radio|submit|button)")[^>]*>|<select\b|<button\b[^>]*\baria-pressed=|role="slider"/i;

export function meneParSimu(avant: string, html: string): boolean {
  const fi = html.search(SIMU_INPUT);
  if (fi < 0) return false;
  const txt = `${avant} ${html.slice(0, fi)}`
    .replace(/<script[\s\S]*?<\/script>/g, ' ').replace(/<style[\s\S]*?<\/style>/g, ' ').replace(/<[^>]+>/g, ' ');
  return txt.split(/\s+/).filter(Boolean).length < 250;
}
