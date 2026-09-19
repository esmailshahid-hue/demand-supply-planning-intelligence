// Keep structured API evidence visible, including FastAPI field-validation details.
type ErrorBody = {message?:string;detail?:string|{loc?:unknown[];msg?:string}[];code?:string;failures?:{code:string;message:string}[];issues?:{code:string;message?:string;guidance?:string}[]};
export function apiError(value: ErrorBody, status: number): string {
  const detail = typeof value.detail === 'string' ? value.detail : value.detail?.map(x=>`${x.loc?.join(' / ') || 'Input'}: ${x.msg}`).join('; ');
  const evidence = [...(value.failures || []).map(f=>`${f.code}: ${f.message}`), ...(value.issues || []).map(i=>`${i.code}: ${i.message || i.guidance || ''}`)];
  const recovery = status === 401 || status === 404 ? 'Open Data and Assumptions to reimport your workbook or reopen a downloaded snapshot, or reset to the bundled sample.' : status === 429 ? 'Another calculation is running. Wait for it to finish, then retry.' : '';
  return [value.code, value.message || detail || `Request failed (${status}). Retry after checking the inputs.`, ...evidence, recovery].filter(Boolean).join(' · ');
}
export async function responseValue(response: Response) {
  try { return await response.json(); }
  catch { throw new Error(`The server returned an unreadable response (${response.status}). Check the connection and retry.`); }
}
export function requestError(error: unknown): string {
  return error instanceof TypeError ? 'Network request failed. Check the connection and retry. No new result has been confirmed.' : error instanceof Error ? error.message : 'Request failed. Please retry.';
}
