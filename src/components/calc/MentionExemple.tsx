/**
 * Mention posée sur un résultat calculé avec les valeurs d'exemple (testeurs naïfs du 2026-11-08,
 * RECETTE §15.8) : tant que le lecteur n'a modifié aucun champ, le résultat n'est pas le sien.
 * Elle disparaît dès la première saisie. À poser dans le bloc du résultat de tout calculateur
 * pré-rempli : `<MentionExemple lang={lang} touched={touched} />`.
 */
import { libellesTrame, resultatExemple } from '../../lib/libelles-trame';

/** `aide` remplace la suite de la mention quand il n'y a pas de chiffre à changer, seulement un choix
 *  (testeurs naïfs du 2026-11-09 : « change a figure » au-dessus d'une simple liste de fonds). */
export default function MentionExemple({ lang, touched, className = '', aide }: { lang?: string; touched?: Record<string, boolean>; className?: string; aide?: string }) {
  if (!resultatExemple(touched)) return null;
  const l = libellesTrame(lang);
  return (
    <p data-exemple className={`mb-2 inline-flex flex-wrap items-baseline gap-x-1 rounded-md border border-amber-300 bg-amber-50 px-2 py-0.5 text-xs text-amber-900 ${className}`}>
      <strong className="font-semibold">{l.exemple}</strong><span>· {aide ?? l.exempleAide}</span>
    </p>
  );
}
