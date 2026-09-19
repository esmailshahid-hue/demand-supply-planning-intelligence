import { apiError, responseValue, requestError } from './errors';
import type { components } from './contracts.generated';
import { sourceHeaders } from './api';
export type Baseline = components['schemas']['BaselineResult'];
export type Definition = components['schemas']['ScenarioDefinition'];
export type Comparison = components['schemas']['ScenarioResult'];
export type Outcome = components['schemas']['Outcome'];
export type Detail = components['schemas']['ScenarioDetail'];
export type DetailRequest = components['schemas']['DetailRequest'];
export type Plan = components['schemas']['PlanResult'];
export const emptyScenario = (): Definition => ({ uplifts: [], delays: [], availability: [], funding: [] });
// Aborting a browser request cannot cancel Python. Honour admission-control retry
// guidance while that calculation finishes, and abort the retry on a new draft.
export async function scenarioApi<T>(path: string, signal: AbortSignal, body: unknown): Promise<T> {
  const headers = {...sourceHeaders(),'Content-Type':'application/json'};
  for (let attempt = 0; ; attempt++) {
    let response: Response;
    try { response = await fetch(path, { method: 'POST', signal, headers, body: JSON.stringify(body) }); }
    catch(e) { if(signal.aborted) throw e; throw new Error(requestError(e)); }
    const value = await responseValue(response);
    if (response.status === 429 && attempt < 20) {
      await new Promise<void>((resolve,reject) => {
        const abort = () => { clearTimeout(timer); reject(new DOMException('Aborted','AbortError')); };
        const timer = setTimeout(() => { signal.removeEventListener('abort',abort); resolve(); }, 1000 * Number(response.headers.get('Retry-After') || 2));
        signal.addEventListener('abort',abort,{once:true}); if (signal.aborted) abort();
      });
      continue;
    }
    if (!response.ok) throw new Error(apiError(value,response.status));
    return value;
  }
}
