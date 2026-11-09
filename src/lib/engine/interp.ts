/** Interpolation linéaire monotone sur une grille croissante (xs trié). Prolonge linéairement hors bornes. */
export function interp(xs: number[], ys: number[], x: number): { y: number; extrapolated: boolean } {
  const n = xs.length;
  if (n === 0) return { y: 0, extrapolated: true };
  if (n === 1) return { y: ys[0], extrapolated: x !== xs[0] };
  if (x <= xs[0]) {
    const slope = (ys[1] - ys[0]) / (xs[1] - xs[0]);
    return { y: Math.max(0, ys[0] + slope * (x - xs[0])), extrapolated: x < xs[0] };
  }
  if (x >= xs[n - 1]) {
    const slope = (ys[n - 1] - ys[n - 2]) / (xs[n - 1] - xs[n - 2]);
    return { y: ys[n - 1] + slope * (x - xs[n - 1]), extrapolated: x > xs[n - 1] };
  }
  let lo = 0, hi = n - 1;
  while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (xs[mid] <= x) lo = mid; else hi = mid; }
  const t = (x - xs[lo]) / (xs[hi] - xs[lo]);
  return { y: ys[lo] + t * (ys[hi] - ys[lo]), extrapolated: false };
}
