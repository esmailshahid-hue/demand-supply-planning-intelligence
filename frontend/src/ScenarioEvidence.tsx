import { useEffect, useState, useRef } from 'react';
import { number, fixedNumber } from './api';
import { scenarioApi, type Detail, type DetailRequest } from './scenarioApi';
import Demand from './Demand';

export default function ScenarioEvidence({ request, onForecast, onClose }: {request: DetailRequest; onForecast?: (d: Detail) => void; onClose: () => void}) {
  const root=useRef<HTMLElement>(null);
  useEffect(()=>{root.current?.focus();root.current?.scrollIntoView({block:'start'});},[request]);
  const [data,setData]=useState<Detail|null>(null);const [error,setError]=useState('');
  useEffect(() => { const c=new AbortController();setData(null);setError('');
    scenarioApi<Detail>('/api/scenarios/detail',c.signal,request).then(d=>{if(!c.signal.aborted)setData(d);}).catch(e=>{if(!c.signal.aborted)setError(e.message);});
    return ()=>c.abort();
  },[request]);
  return <section ref={root} tabIndex={-1} className="panel" aria-label="Action evidence" data-testid="action-evidence"><div className="section-heading"><h2>Action and forecast evidence · {request.sku}</h2><button onClick={onClose}>Close evidence</button></div>
    {!data&&!error&&<p role="status">Reconstructing scoped stock, cash and forecast evidence…</p>}{error&&<p role="alert">{error}</p>}
    {data&&<><p>{data.policy} · {data.feasible?'Independently feasible':'Infeasible — stock and service metrics unavailable'}</p><p>{data.note}</p>
      {data.failures.map((f,i)=><p key={i} className="error">{f.code} · {f.sku} {f.day} · {f.message}</p>)}
      <h3>Selected action</h3>{[...data.purchases,...data.movements].filter(a=>!request.action_id||a.action_id===request.action_id).map(a=><div key={a.action_id}><p>{a.action_id} · {'supplier_id' in a?a.supplier_id:a.source} → {a.destination} · {a.units} units · {'order_date' in a?`order ${a.order_date} · value SAR ${fixedNumber(a.value,2)} · `:''}dispatch {a.dispatch_date} · arrival {a.arrival_date}. {a.reason}</p>{'supplier_id' in a&&<p className="notice">This purchase arrives into pooled DC inventory. {request.location_id} is the selected demand context, not a dedicated purchase destination; other ranged stores may compete for the same stock.</p>}</div>)}
      <h3>SKU payments and grouped movement fees</h3><p>Movement fees belong to the entire lane/date dispatch group, not to each SKU. Existing payables retain their fixed dates.</p><div className="table-scroll"><table><thead><tr><th>Reference</th><th>Kind</th><th>Due</th><th>SAR</th></tr></thead><tbody>{data.payments.map((p,i)=><tr key={i}><th>{p.reference}</th><td>{p.kind}</td><td>{p.due_date}</td><td>{fixedNumber(p.amount,2)}</td></tr>)}</tbody></table></div>
      <details><summary>Weekly cash and headroom</summary>{data.cash.map(w=><p key={w.week_start}>{w.week_start} · commitments {fixedNumber(w.commitments,2)} · payments {fixedNumber(w.total_payments,2)} · commitment / payment headroom {fixedNumber(w.commitment_headroom,2)} / {fixedNumber(w.payment_headroom,2)} SAR</p>)}</details>
      <details open><summary>Stock before and after dated events</summary><div className="table-scroll daily-table"><table><thead><tr><th>Location / date</th><th>Opening</th><th>Receipts</th><th>Demand</th><th>Fulfilled</th><th>Dispatch</th><th>Closing</th></tr></thead><tbody>{data.stock.map(r=><tr key={`${r.location_id}/${r.day}`}><th>{r.location_id} / {r.day}</th>{[r.opening,r.receipts,r.demand,r.fulfilled,r.dispatched,r.closing].map((v,i)=><td key={i}>{number(v)}</td>)}</tr>)}</tbody></table></div></details>
      <details><summary>Related receipts, movements and remaining shortages</summary>{data.confirmed_receipts.map(r=><p key={r.id}>Confirmed {r.id} · {r.units} units to {r.destination} on {r.arrival}</p>)}{data.purchases.map(p=><p key={p.action_id}>Purchase {p.action_id} · {p.units} to {p.destination} on {p.arrival_date}</p>)}{data.movements.map(m=><p key={m.action_id}>Movement {m.action_id} · {m.units} · {m.source} → {m.destination} · {m.dispatch_date} → {m.arrival_date}</p>)}{data.shortages.map(s=><p key={s.location_id}>{s.location_id}: {number(s.unmet)} visible / {number(s.tail_unmet)} provisional-tail unmet. {s.reason_codes.join(', ')}</p>)}</details>
      <p>Policy buffer: {number(data.policy_buffer.units)} units · {data.policy_buffer.method} · {data.policy_buffer.protection_days} protection days. This same buffer is used by frozen and replanned policies.</p><h3>Dated scenario adjustments</h3><p>Future expected demand only. These are not observed sales and do not change historical model evaluation.</p>{data.adjustments.length===0?<p>No scenario demand adjustment for this series.</p>:<div className="table-scroll"><table><thead><tr><th>Date</th><th>Underlying forecast</th><th>Scenario demand</th></tr></thead><tbody>{data.adjustments.map(a=><tr key={a.day}><th>{a.day}</th><td>{number(a.original)}</td><td>{number(a.adjusted)}</td></tr>)}</tbody></table></div>}
      {onForecast&&<button className="primary-button" onClick={()=>onForecast(data)}>Open this forecast in Demand Review</button>}
      <details><summary>Underlying evaluated forecast · {request.sku} / {request.location_id}</summary><Demand result={data.forecast}/></details>
      <details><summary>Evidence versions and calculation time</summary><p>Baseline {data.baseline_id}</p><p>Scenario {data.scenario_hash}</p><p>Policy assumptions {data.assumptions_hash}</p><p>Action snapshot {data.action_hash}</p><p>Forecast version {data.forecast_version}</p><p>{number(data.elapsed_ms)} ms · live scoped reconstruction</p></details>
    </>}
  </section>;
}
