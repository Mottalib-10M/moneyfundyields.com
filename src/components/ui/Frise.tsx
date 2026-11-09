import { useMemo, useState } from 'react';

/* Frise d'une démarche (RECETTE §17.6, demande de l'éditeur du 2026-10-25).
   Une démarche en étapes officielles (dépôt → test → entretien → décision → cérémonie…),
   chacune avec sa durée officielle min–max en jours. Le lecteur saisit sa date de départ :
   la frise place chaque étape dans le temps, montre où il en est aujourd'hui, et donne
   la fenêtre de fin. Deux vues du même mécanisme :
   1. la barre proportionnelle (SVG) : la longueur de chaque étape est sa durée, le repère
      « aujourd'hui » dit où l'on est ;
   2. la liste des étapes (ol) : horizontale à partir de md, verticale sur mobile.
   Aucune durée ne se tape à la main : elles viennent des paramètres sourcés du site. */

export interface FriseStep {
  id: string;
  title: string;
  detail?: string;
  /** Durée officielle de l'étape, en jours (min = max pour un délai fixe ; 0 pour un jalon). */
  minDays: number;
  maxDays: number;
  source?: { label: string; href: string };
}

export interface FriseLabels {
  start: string;          // « Date de dépôt du dossier »
  startHelp?: string;
  end: string;            // « Fin estimée »
  between: string;        // « entre »
  and: string;            // « et »
  today: string;          // « Aujourd'hui »
  done: string;           // « Terminé »
  current: string;        // « En cours »
  upcoming: string;       // « À venir »
  day: string; days: string; week: string; weeks: string; month: string; months: string;
  milestone: string;      // « jalon »
  caption: string;        // phrase qui dit ce que montre la frise (figcaption + aria-label)
}

interface Props {
  steps: FriseStep[];
  labels: FriseLabels;
  locale: string;                 // « fr-FR », « en-GB »…
  defaultStart?: string;          // ISO ; sinon il y a 3 mois
  id?: string;
}

const DAY = 86_400_000;
const iso = (d: Date) => d.toISOString().slice(0, 10);
const addDays = (d: Date, n: number) => new Date(d.getTime() + n * DAY);

export default function Frise({ steps, labels: L, locale, defaultStart, id = 'frise' }: Props) {
  const [start, setStart] = useState(() => defaultStart ?? iso(addDays(new Date(), -90)));
  const fmt = useMemo(() => new Intl.DateTimeFormat(locale, { day: 'numeric', month: 'short', year: 'numeric' }), [locale]);

  const dur = (min: number, max: number) => {
    const one = (n: number) =>
      n >= 60 ? [Math.round(n / 30.4), Math.round(n / 30.4) > 1 ? L.months : L.month] as const
      : n >= 14 ? [Math.round(n / 7), Math.round(n / 7) > 1 ? L.weeks : L.week] as const
      : [n, n > 1 ? L.days : L.day] as const;
    if (max === 0) return L.milestone;
    const [a, ua] = one(min), [b, ub] = one(max);
    if (min === max || (a === b && ua === ub)) return `${b} ${ub}`;
    return ua === ub ? `${a}–${b} ${ub}` : `${a} ${ua} – ${b} ${ub}`;
  };

  // Fenêtre de chaque étape : début au plus tôt (somme des min) et fin au plus tard (somme des max).
  const timeline = useMemo(() => {
    const s = new Date(`${start}T12:00:00`);
    if (Number.isNaN(s.getTime())) return null;
    let lo = 0, hi = 0;
    const rows = steps.map((st) => {
      const from = { lo, hi };
      lo += st.minDays; hi += st.maxDays;
      // Le statut suit la durée médiane cumulée : une seule étape « en cours » à la fois.
      return { ...st, startLo: addDays(s, from.lo), startHi: addDays(s, from.hi), endLo: addDays(s, lo), endHi: addDays(s, hi),
        midStart: addDays(s, (from.lo + from.hi) / 2), midEnd: addDays(s, (lo + hi) / 2) };
    });
    return { s, rows, endLo: addDays(s, lo), endHi: addDays(s, hi), totalMid: (lo + hi) / 2 };
  }, [start, steps]);

  const now = new Date();
  const status = (r: { midStart: Date; midEnd: Date }) =>
    now >= r.midEnd ? 'done' : now >= r.midStart ? 'current' : 'upcoming';

  // Barre proportionnelle : largeur = durée médiane de l'étape (un jalon garde 1,5 % pour rester visible).
  const W = 1000, H = 76, padX = 8, trackY = 30, trackH = 18;
  const mids = steps.map((s) => Math.max((s.minDays + s.maxDays) / 2, 0));
  const total = mids.reduce((a, b) => a + b, 0) || 1;
  const minW = 0.015 * (W - 2 * padX);
  const raw = mids.map((m) => (m / total) * (W - 2 * padX));
  const extra = raw.reduce((a, w) => a + Math.max(0, minW - w), 0);
  const big = raw.filter((w) => w > minW).reduce((a, b) => a + b, 0) || 1;
  const widths = raw.map((w) => (w <= minW ? minW : w - (extra * w) / big));
  const xs = widths.reduce<number[]>((acc, w, i) => (acc.push(i === 0 ? padX : acc[i - 1] + widths[i - 1]), acc), []);
  const elapsed = timeline ? (now.getTime() - timeline.s.getTime()) / DAY : 0;
  const todayX = timeline && timeline.totalMid > 0 ? padX + Math.min(Math.max(elapsed / timeline.totalMid, 0), 1) * (W - 2 * padX) : null;
  const shade = ['var(--color-accent-700)', 'var(--color-accent-500)', 'var(--color-accent-300)'];

  return (
    <figure className="frise not-prose my-10 rounded-2xl border border-navy-200 bg-white p-5 shadow-sm sm:p-7" aria-labelledby={`${id}-cap`}>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <label htmlFor={`${id}-start`} className="mb-1 block text-sm font-medium text-navy-700">{L.start}</label>
          <input id={`${id}-start`} type="date" value={start} onChange={(e) => setStart(e.target.value)}
            className="h-12 rounded-lg border border-navy-300 bg-white px-4 text-lg tabular-nums text-navy-900 focus:border-accent-500 focus:outline-none focus:ring-2 focus:ring-accent-500/20" />
          {L.startHelp && <p className="mt-1 text-xs text-navy-500">{L.startHelp}</p>}
        </div>
        {timeline && (
          <p className="rounded-xl bg-accent-50 px-4 py-3 text-sm text-navy-800 sm:text-right" aria-live="polite">
            <span className="block text-xs font-semibold uppercase tracking-wide text-accent-700">{L.end}</span>
            <span className="font-serif text-lg font-semibold tabular-nums">
              {+timeline.endLo === +timeline.endHi ? fmt.format(timeline.endHi) : <>{L.between} {fmt.format(timeline.endLo)} {L.and} {fmt.format(timeline.endHi)}</>}
            </span>
          </p>
        )}
      </div>

      {timeline && (
        <svg viewBox={`0 0 ${W} ${H}`} className="mt-6 h-auto w-full text-navy-700" role="img" aria-label={L.caption}>
          {widths.map((w, i) => (
            <g key={steps[i].id}>
              <rect x={xs[i]} y={trackY} width={Math.max(w - 3, 2)} height={trackH} rx={4} fill={shade[i % shade.length]} />
              {w >= 18 && (
                <text x={xs[i] + (w - 3) / 2} y={trackY + trackH + 20} fontSize={13} fontWeight={600} textAnchor="middle" fill="currentColor">{i + 1}</text>
              )}
            </g>
          ))}
          {todayX !== null && (
            <g>
              <line x1={todayX} x2={todayX} y1={22} y2={trackY + trackH + 3} stroke="var(--color-navy-900)" strokeWidth={2} />
              <polygon points={`${todayX - 6},16 ${todayX + 6},16 ${todayX},23`} fill="var(--color-navy-900)" />
              <text x={Math.min(Math.max(todayX, 45), W - 45)} y={12} fontSize={12} fontWeight={600} textAnchor="middle" fill="var(--color-navy-900)">{L.today}</text>
            </g>
          )}
        </svg>
      )}

      <ol className="relative mt-6 grid gap-6 md:gap-4" data-steps={steps.length}>
        {timeline?.rows.map((r, i) => {
          const st = status(r);
          return (
            <li key={r.id} className={`frise-step relative pl-12 md:pl-0 md:pt-12 ${st}`}>
              <span aria-hidden="true" className={`absolute left-0 top-0 grid h-9 w-9 place-items-center rounded-full border-2 text-sm font-bold tabular-nums md:left-0
                ${st === 'done' ? 'border-accent-700 bg-accent-700 text-white' : st === 'current' ? 'border-accent-600 bg-white text-accent-700 ring-4 ring-accent-200' : 'border-navy-300 bg-white text-navy-500'}`}>
                {st === 'done' ? '✓' : i + 1}
              </span>
              <p className="text-xs font-semibold uppercase tracking-wide text-navy-500">
                <span className="sr-only">{i + 1}. </span>{st === 'done' ? L.done : st === 'current' ? L.current : L.upcoming} · {dur(r.minDays, r.maxDays)}
              </p>
              <h3 className="mt-1 font-serif text-base font-semibold leading-snug text-navy-900">{r.title}</h3>
              <p className="mt-1 text-sm tabular-nums text-accent-800">
                {+r.endLo === +r.endHi ? fmt.format(r.endHi) : `${fmt.format(r.endLo)} – ${fmt.format(r.endHi)}`}
              </p>
              {r.detail && <p className="mt-2 text-sm leading-relaxed text-navy-600">{r.detail}</p>}
              {r.source && <a href={r.source.href} rel="noopener" target="_blank" className="mt-2 inline-block text-xs text-navy-500 underline decoration-navy-300 underline-offset-2 hover:text-accent-700">{r.source.label}</a>}
            </li>
          );
        })}
      </ol>
      <figcaption id={`${id}-cap`} className="mt-6 border-t border-navy-100 pt-4 text-sm text-navy-500">{L.caption}</figcaption>

      <style>{`
        .frise ol { grid-template-columns: 1fr; }
        .frise ol::before { content: ''; position: absolute; left: 17px; top: 18px; bottom: 18px; width: 2px; background: var(--color-navy-200); }
        @media (min-width: 768px) {
          .frise ol { grid-template-columns: repeat(${Math.min(steps.length, 6)}, minmax(0, 1fr)); }
          .frise ol::before { left: 18px; right: 18px; top: 17px; bottom: auto; width: auto; height: 2px; }
        }
        .frise-step.done::after { content: ''; position: absolute; left: 17px; top: 36px; bottom: -24px; width: 2px; background: var(--color-accent-700); }
        @media (min-width: 768px) { .frise-step.done::after { left: 36px; top: 17px; bottom: auto; right: -16px; width: auto; height: 2px; } }
        .frise-step:last-child::after { display: none; }
      `}</style>
    </figure>
  );
}
