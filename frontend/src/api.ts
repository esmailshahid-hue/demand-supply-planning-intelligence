import type { components } from './contracts.generated';
export type ForecastResult = components['schemas']['ForecastResult'];
export type Catalog = components['schemas']['SampleCatalog'];
export type Method = ForecastResult['selected_method'];
export type Size = 'fixture' | 'full';
export const methodNames: Record<Method, string> = {
  seasonal_naive: 'Seasonal naive', weekday_mean: 'Four-week weekday mean', weighted_weekday_mean: 'Recency-weighted weekday mean',
};
export async function api<T>(path: string, signal: AbortSignal, body?: unknown): Promise<T> {
  const response = await fetch(path, { signal, ...(body ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : {}) });
  const result = await response.json();
  if (!response.ok) throw new Error(result.message ?? 'The calculation could not be completed. Please retry.');
  return result as T;
}
export const number = (n: number | null | undefined, digits = 1) => n == null ? 'Unavailable' : n.toLocaleString('en-GB', { maximumFractionDigits: digits });
const roundedForDisplay = (n: number, digits: number) => {
  const factor = 10 ** digits;
  return Math.round((n + Number.EPSILON) * factor) / factor;
};
export const fixedNumber = (n: number | null | undefined, digits = 1) => n == null ? 'Unavailable' : roundedForDisplay(n, digits).toLocaleString('en-GB', { minimumFractionDigits: digits, maximumFractionDigits: digits });
export const displayedMaeImprovement = (baselineMae: number | null | undefined, selectedMae: number | null | undefined) => {
  if (baselineMae == null || selectedMae == null) return null;
  const displayedBaseline = roundedForDisplay(baselineMae, 1);
  const displayedSelected = roundedForDisplay(selectedMae, 1);
  if (displayedBaseline === 0) return null;
  return Math.round(100 * (displayedBaseline - displayedSelected) / displayedBaseline);
};
export const percent = (n: number | null | undefined, digits = 1) => n == null ? 'Unavailable' : `${number(n, digits)}%`;
export const signedPercent = (n: number | null | undefined) => {
  if (n == null) return 'Unavailable';
  if (n > 0 && n < 0.1) return '<0.1%';
  if (n < 0 && n > -0.1) return '>−0.1%';
  return percent(n);
};
export const shortDate = (day: string) => new Date(`${day}T12:00:00+03:00`).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', timeZone: 'Asia/Riyadh' });
