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
export const percent = (n: number | null | undefined) => n == null ? 'Unavailable' : `${number(n)}%`;
export const shortDate = (day: string) => new Date(`${day}T12:00:00+03:00`).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', timeZone: 'Asia/Riyadh' });
