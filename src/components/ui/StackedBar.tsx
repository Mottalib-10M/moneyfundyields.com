import { LOCALE_TAG } from '../../data/site-config';
// « 50% » en anglais, « 50 % » en français ou en allemand (2026-10-24 : les pages anglaises affichaient « 50 % »).
const PCT = /^(en|it|pt|zh|ja|ko)/.test(LOCALE_TAG) ? '%' : '\u00a0%';
interface Segment { label: string; value: number; color: string }
/** Couleur du pourcentage écrit dans un segment : blanc sur fond sombre, ardoise sur fond clair (contraste AA, RECETTE §10.4). */
function labelColor(hex: string): string {
  const h = hex.replace('#', ''); const [r, g, b] = [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16) / 255).map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  const L = 0.2126 * r + 0.7152 * g + 0.0722 * b;
  return (1.05) / (L + 0.05) >= 4.5 ? '#ffffff' : '#0f172a';
}
export default function StackedBar({ segments, total, ariaPrefix }: { segments: Segment[]; total: number; ariaPrefix: string }) {
  if (total <= 0) return null;
  const desc = segments.filter((s) => s.value / total >= 0.005).map((s) => `${s.label}: ${((s.value / total) * 100).toFixed(1)}${PCT}`).join(', ');
  return (
    <div role="img" aria-label={`${ariaPrefix}: ${desc}`}>
      <div className="flex h-9 overflow-hidden rounded-lg">
        {segments.map((s, i) => {
          const pct = (s.value / total) * 100; if (pct < 0.5) return null;
          return <div key={i} className="flex items-center justify-center text-xs font-medium" style={{ width: `${pct}%`, backgroundColor: s.color, color: labelColor(s.color), minWidth: pct > 3 ? undefined : '4px' }} title={`${s.label}: ${pct.toFixed(1)}${PCT}`}>{pct > 9 && <span className="truncate px-1">{pct.toFixed(0)}{PCT}</span>}</div>;
        })}
      </div>
      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1">
        {segments.map((s, i) => <div key={i} className="flex items-center gap-1.5 text-xs text-navy-600"><span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: s.color }} aria-hidden="true" />{s.label} {Math.round((s.value / total) * 100)}{PCT}</div>)}
      </div>
    </div>
  );
}
