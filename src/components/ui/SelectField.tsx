/**
 * Liste déroulante de la trame. Le choix affiché se lit EN ENTIER : sur un téléphone de 390 px, le
 * `<select>` natif coupait le libellé vers 26 caractères (« No state chosen (board fees n… »), et
 * trois testeurs naïfs sur trois ne savaient plus ce qu'ils avaient choisi (financecertcost.com,
 * dumpfeesbystate.com, 2026-11-08). Le libellé choisi s'affiche donc dans un bloc qui passe à la
 * ligne ; le vrai `<select>`, transparent, le recouvre exactement : clavier, lecteur d'écran, liste
 * native du téléphone et contrôles de check-layout (hauteur 48 px, marge droite de la flèche)
 * restent ceux d'un `<select>`. Jusqu'à deux lignes, le champ garde ses 48 px ; au-delà il grandit
 * (et check-layout le signale dans une rangée : raccourcir alors le libellé).
 */
interface Option { value: string; label: string }
interface Props { id: string; label: string; value: string; onChange: (v: string) => void; options: Option[]; help?: string; className?: string }

export default function SelectField({ id, label, value, onChange, options, help, className = '' }: Props) {
  const choisi = options.find((o) => o.value === value)?.label ?? '';
  return (
    <div className={`grid grid-rows-subgrid row-span-3 content-start gap-y-0 ${className}`}>
      <label htmlFor={id} className="mb-1 block text-sm font-medium text-navy-700">{label}</label>
      <div className="relative self-start rounded-lg border border-navy-300 bg-white text-navy-900 has-[select:focus-visible]:border-accent-500 has-[select:focus-visible]:ring-2 has-[select:focus-visible]:ring-accent-500/40">
        <span aria-hidden="true" data-choix className="flex min-h-[calc(3rem-2px)] items-center py-0.5 pl-3 pr-10 text-[0.9rem] leading-[1.2] [overflow-wrap:anywhere]">{choisi}</span>
        <select id={id} value={value} onChange={(e) => onChange(e.target.value)} aria-describedby={help ? `${id}-help` : undefined}
          className="absolute -inset-px cursor-pointer appearance-none rounded-lg bg-transparent pl-3 pr-10 opacity-0 focus:outline-none">
          {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <svg className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-navy-500" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><path d="M5 7.5l5 5 5-5" strokeLinecap="round" strokeLinejoin="round" /></svg>
      </div>
      {help && <p id={`${id}-help`} className="mt-1 text-xs text-navy-500">{help}</p>}
    </div>
  );
}
