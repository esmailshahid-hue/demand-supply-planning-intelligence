import { useEffect, useRef, useState } from 'react';
import { api } from './api';
import { scenarioApi, type Plan } from './scenarioApi';
import type { components } from './contracts.generated';
type Review=components['schemas']['ReviewView'];

export default function ReviewControls({plan,onPlan,onProtected}:{plan:Plan;onPlan:(p:Plan)=>void;onProtected:(v:boolean)=>void}) {
  const [review,setReview]=useState<Review|null>(null);
  const [action,setAction]=useState('');const [quantity,setQuantity]=useState('');const [note,setNote]=useState('');
  const [error,setError]=useState('');const [busy,setBusy]=useState(false);const [ack,setAck]=useState(false);
  const active=useRef<AbortController|null>(null);
  useEffect(()=>{onProtected(review?(review.decisions.length>0||review.state==='accepted'||review.state==='read_only'||review.state==='stale'):!!plan.review_id);},[review?.state,review?.decisions.length,plan.review_id]);
  useEffect(()=>{active.current?.abort();const c=new AbortController();active.current=c;setReview(null);setError('');setAck(false);
    if(plan.review_id)api<Review>(`/api/workflow/review/${plan.review_id}`,c.signal).then(r=>{if(!c.signal.aborted)setReview(r);}).catch(e=>{if(!c.signal.aborted)setError(e.message);});
    return()=>c.abort();
  },[plan.review_id]);
  const current=[...(plan.proposed?.purchases||[]),...(plan.proposed?.movements||[])];
  const previous=(review?.decisions||[]).map(d=>d.original as components['schemas']['Purchase']|components['schemas']['Movement']);
  const actions=[...current,...previous.filter(a=>!current.some(p=>p.action_id===a.action_id))];
  const selected=actions.find(a=>a.action_id===action)||actions[0];
  const submit=async(operation:string,extra:object={},reload=false)=>{if(!review)return;active.current?.abort();const c=new AbortController();active.current=c;setBusy(true);setError('');
    try {const next=await scenarioApi<Review>(`/api/workflow/review/${review.reference}/${operation}`,c.signal,{revision:review.revision,...extra});if(c.signal.aborted)return;setReview(next);
      if(reload){const p=await api<Plan>(`/api/workflow/review/${next.reference}/plan`,c.signal);if(!c.signal.aborted)onPlan(p);}else onPlan({...plan,review_id:next.reference});
    } catch(e){if(!c.signal.aborted)setError((e as Error).message);}finally{if(!c.signal.aborted)setBusy(false);}
  };
  const immutable=review?.state==='accepted'||review?.state==='read_only';
  return <section className="panel" aria-label="Reviewed actions"><h2>Review and final acceptance</h2>
    {!plan.review_id&&<p className="notice">Review files require private session storage. Open Data and Assumptions to check availability, then recalculate. Hosted storage is not configured.</p>}
    {review&&<><p role="status">Plan state: <strong>{review.state}</strong>{review.state==='stale'?' — regenerate the complete plan before acceptance or export. Displayed quantities belong to the previous calculation.':''}</p><p>No purchase orders or transfers are sent. Action acceptance locks exact terms; final acceptance is a separate step.</p>
      {!immutable&&<><label>Action to review<select value={selected?.action_id||''} disabled={busy} onChange={e=>{setAction(e.target.value);setQuantity('');}}>{actions.map(a=><option key={a.action_id} value={a.action_id}>{a.action_id} · {a.sku} · {a.units} units</option>)}</select></label>{' '}
        <label>Reviewed quantity<input type="number" min="1" step="1" value={quantity} onChange={e=>setQuantity(e.target.value)}/></label>{' '}<label>Review note<input value={note} maxLength={1000} onChange={e=>setNote(e.target.value)}/></label>
        <div className="scenario-buttons">{[['Accept action','accepted'],['Reject action','rejected'],['Apply quantity edit','edited_quantity'],['Return action to draft','draft']].map(([label,status])=><button key={status} disabled={busy||!selected} onClick={()=>submit('decision',{action_id:selected!.action_id,status,quantity:status==='edited_quantity'?Number(quantity):null,note})}>{label}</button>)}</div>
        <button className="primary-button" disabled={busy} onClick={()=>submit('regenerate',{},true)}>Regenerate reviewed plan</button>
        <p><label><input type="checkbox" checked={ack} onChange={e=>setAck(e.target.checked)}/>I acknowledge the displayed remaining service and buffer shortfalls</label></p>
        <button disabled={busy||review.state!=='draft'} onClick={()=>submit('accept',{acknowledge_shortfalls:ack})}>Finally accept plan</button>
      </>}
      {immutable&&<><p>Accepted version {review.accepted_version} is immutable. Reopened snapshots are read-only until a new draft is explicitly created.</p><button disabled={busy} onClick={()=>submit('new-draft',{},true)}>Create new draft</button></>}
      <p>{immutable?<><a href={`/api/workflow/review/${review.reference}/download/workbook`}>Download reviewed workbook</a> · <a href={`/api/workflow/review/${review.reference}/download/snapshot`}>Download portable snapshot</a></>:<><button disabled>Download reviewed workbook</button> <button disabled>Download portable snapshot</button></>}</p>
      <details><summary>Review decisions · {review.decisions.length}</summary>{review.decisions.map((d,i)=><p key={i}>{String(d.action_type)} · {String(d.business_key).slice(0,12)} · {String(d.status)} · {String(d.original_quantity)} → {String(d.reviewed_quantity??'prohibited')} · {String(d.disposition)}</p>)}</details>
      {review.failures.map((f,i)=><p className="error" key={i}>{String(f.code)} · {String(f.message)}</p>)}
    </>}{busy&&<p role="status">Checking review dependencies and independent stock/cash replay…</p>}{error&&<p className="error" role="alert">{error}</p>}
  </section>;
}
