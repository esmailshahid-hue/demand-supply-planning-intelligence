import { useEffect, useRef, useState } from 'react';
import { api } from './api';
import { scenarioApi, type Plan } from './scenarioApi';
import type { components } from './contracts.generated';
import type { Review, ReviewGate, ReviewMutationPhase, ReviewRecovery } from './reviewState';

export default function ReviewControls({plan,recovery,mutationPhase,onPlan,onProtected,onGate,onRecovery,onRecoveryClear,onMutation}:{plan:Plan;recovery:ReviewRecovery|null;mutationPhase:ReviewMutationPhase;onPlan:(p:Plan)=>void;onProtected:(v:boolean)=>void;onGate:(v:ReviewGate)=>void;onRecovery:(v:ReviewRecovery)=>void;onRecoveryClear:(reference:string)=>void;onMutation:(v:ReviewMutationPhase)=>void}) {
  const [review,setReview]=useState<Review|null>(null);
  const [action,setAction]=useState('');const [quantity,setQuantity]=useState('');const [note,setNote]=useState('');
  const [error,setError]=useState('');const [busy,setBusy]=useState(false);const [ack,setAck]=useState(false);
  const submitting=useRef(false);
  const [retry,setRetry]=useState(0);
  const reviewLoad=useRef<AbortController|null>(null);
  const operation=useRef<AbortController|null>(null);
  const pendingPlan=recovery&&recovery.previousReference===plan.review_id?recovery.review.reference:null;
  useEffect(()=>{const blocked=!!pendingPlan||(!review&&!!plan.review_id)||review?.state==='stale';onGate({blocked:!!blocked,reason:pendingPlan?'The replacement calculation is saved, but its result has not loaded.':!review&&plan.review_id?'Review state is still loading or unavailable.':review?.state==='stale'?'Review changes require regeneration before this plan can be used.':''});},[review,plan.review_id,pendingPlan,onGate]);
  useEffect(()=>{onProtected(review?(review.decisions.length>0||review.state==='accepted'||review.state==='read_only'||review.state==='stale'):!!plan.review_id);},[review?.state,review?.decisions.length,plan.review_id]);
  useEffect(()=>{reviewLoad.current?.abort();const c=new AbortController();reviewLoad.current=c;setReview(null);setError('');setAck(false);
    const savedRecovery=recovery;
    if(savedRecovery&&savedRecovery.previousReference===plan.review_id){setReview(savedRecovery.review);return()=>c.abort();}
    if(plan.review_id)api<Review>(`/api/workflow/review/${plan.review_id}`,c.signal).then(r=>{if(!c.signal.aborted)setReview(r);}).catch(e=>{if(!c.signal.aborted)setError(e.message);});
    return()=>c.abort();
  },[plan.review_id,retry,recovery]);
  useEffect(()=>()=>{reviewLoad.current?.abort();operation.current?.abort();},[]);
  const current=[...(plan.proposed?.purchases||[]),...(plan.proposed?.movements||[])];
  const previous=(review?.decisions||[]).map(d=>d.original as components['schemas']['Purchase']|components['schemas']['Movement']);
  const actions=[...current,...previous.filter(a=>!current.some(p=>p.action_id===a.action_id))];
  const selected=actions.find(a=>a.action_id===action)||actions[0];
  const submit=async(action:string,extra:object={},reload=false)=>{if(!review||submitting.current)return;submitting.current=true;operation.current?.abort();const c=new AbortController();operation.current=c;setBusy(true);setError('');onMutation('awaiting-response');let awaitingResponse=true;
    try {const previousReference=review.reference;const next=await scenarioApi<Review>(`/api/workflow/review/${previousReference}/${action}`,c.signal,{revision:review.revision,...extra});if(c.signal.aborted)return;setReview(next);
      if(reload){onRecovery({previousReference,operation:action==='new-draft'?'new-draft':'regenerate',review:next});onMutation('idle');awaitingResponse=false;const p=await api<Plan>(`/api/workflow/review/${next.reference}/plan`,c.signal);if(!c.signal.aborted){setBusy(false);submitting.current=false;onPlan(p);onRecoveryClear(next.reference);}}
      else {setBusy(false);submitting.current=false;onPlan({...plan,review_id:next.reference});onMutation('idle');awaitingResponse=false;}
    } catch(e){if(!c.signal.aborted)setError((e as Error).message);}finally{if(awaitingResponse)onMutation('idle');submitting.current=false;if(!c.signal.aborted)setBusy(false);}
  };
  const reloadPlan=async()=>{if(!pendingPlan||submitting.current)return;submitting.current=true;const c=new AbortController();operation.current?.abort();operation.current=c;setBusy(true);try{const p=await api<Plan>(`/api/workflow/review/${pendingPlan}/plan`,c.signal);if(!c.signal.aborted){setError('');setBusy(false);submitting.current=false;onPlan(p);onRecoveryClear(pendingPlan);}}catch(e){if(!c.signal.aborted)setError((e as Error).message);}finally{submitting.current=false;if(!c.signal.aborted)setBusy(false);}};
  const immutable=review?.state==='accepted'||review?.state==='read_only';
  return <section className="panel review-controls" aria-label="Reviewed actions" aria-busy={busy}><h2>Review and final acceptance</h2>
    {plan.review_id&&!review&&!error&&<p role="status">Loading reviewed action state…</p>}{!plan.review_id&&<p className="notice">Review files require private session storage. Open Data and Assumptions to check availability, then recalculate. Hosted storage is not configured.</p>}
    {pendingPlan&&<p role="status" className="notice">The new calculation has not loaded. Displayed quantities are from the previous plan. <button disabled={busy} onClick={reloadPlan}>Load regenerated result</button></p>}{review&&<><p role="status">Plan state: <strong>{review.state}</strong>{review.state==='stale'?' — regenerate the complete plan before acceptance or export. Displayed quantities belong to the previous calculation.':''}</p><p>No purchase orders or transfers are sent. Action acceptance locks exact terms; final acceptance is a separate step.</p>
      {!immutable&&<><div className="review-fields"><label>Action to review<select value={selected?.action_id||''} disabled={busy} onChange={e=>{setAction(e.target.value);setQuantity('');}}>{actions.map(a=><option key={a.action_id} value={a.action_id}>{a.action_id} · {a.sku} · {a.units} units</option>)}</select></label>{' '}
        <label>Reviewed quantity<input type="number" min="1" step="1" disabled={busy} value={quantity} onChange={e=>setQuantity(e.target.value)}/></label>{' '}<label>Review note<input disabled={busy} value={note} maxLength={1000} onChange={e=>setNote(e.target.value)}/></label></div>
        <div className="scenario-buttons">{[['Accept action','accepted'],['Reject action','rejected'],['Apply quantity edit','edited_quantity'],['Return action to draft','draft']].map(([label,status])=><button key={status} disabled={busy||!!pendingPlan||!selected} onClick={()=>submit('decision',{action_id:selected!.action_id,status,quantity:status==='edited_quantity'?Number(quantity):null,note})}>{label}</button>)}</div>
        <button className="primary-button" disabled={busy||!!pendingPlan} onClick={()=>submit('regenerate',{},true)}>Regenerate reviewed plan</button>
        <p><label><input type="checkbox" disabled={busy||!!pendingPlan} checked={ack} onChange={e=>setAck(e.target.checked)}/>I acknowledge the displayed remaining service and buffer shortfalls</label></p>
        <button disabled={busy||!!pendingPlan||review.state!=='draft'} onClick={()=>submit('accept',{acknowledge_shortfalls:ack})}>Finally accept plan</button>
      </>}
      {immutable&&<><p>Accepted version {review.accepted_version} is immutable. Reopened snapshots are read-only until a new draft is explicitly created.</p><button disabled={busy||!!pendingPlan} onClick={()=>submit('new-draft',{},true)}>Create new draft</button></>}
      <p>Exports become available only after the current plan is finally accepted. Acceptance does not place orders or execute transfers.</p><p className="download-actions">{immutable?<><a href={`/api/workflow/review/${review.reference}/download/workbook`}>Download reviewed workbook</a> · <a href={`/api/workflow/review/${review.reference}/download/snapshot`}>Download portable snapshot</a></>:<><button disabled>Download reviewed workbook</button> <button disabled>Download portable snapshot</button></>}</p>
      <details><summary>Review decisions · {review.decisions.length}</summary>{review.decisions.map((d,i)=><p key={i}>{String(d.action_type)} · {String(d.business_key).slice(0,12)} · {String(d.status)} · {String(d.original_quantity)} → {String(d.reviewed_quantity??'prohibited')} · {String(d.disposition)}</p>)}</details>
      {review.failures.map((f,i)=><p className="error" key={i}>{String(f.code)} · {String(f.message)}</p>)}
    </>}{mutationPhase==='awaiting-response'?<p role="status">Saving review mutation…</p>:busy&&<p role="status">Checking review dependencies and independent stock/cash replay…</p>}{error&&<div className="error" role="alert"><p>{error}</p>{!review&&<button disabled={busy} onClick={()=>setRetry(v=>v+1)}>Retry review</button>}</div>}
  </section>;
}
