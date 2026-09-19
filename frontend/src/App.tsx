import { useEffect, useState, useCallback } from 'react';
import { api, type Catalog, type ForecastResult, type Size, number, setDatasetReference } from './api';
import DataWorkspace from './DataWorkspace';
import type { components } from './contracts.generated';
import Demand from './Demand';
import PlanReview from './PlanReview';
import Scenarios from './Scenarios';
import type { Detail, Plan } from './scenarioApi';
import type { ReviewGate, ReviewMutationPhase, ReviewRecovery } from './reviewState';

const screens = ['Plan Review', 'Demand Review', 'Scenarios', 'Data and Assumptions'] as const;
type Screen = typeof screens[number];
type PlanContext = {plan:Plan;size:Size};
const planKey=(plan:Plan)=>plan.review_id||plan.run_id;

export default function App() {
  const [source,setSource]=useState<components['schemas']['ImportResult']|null>(null);
  const [openedPlan,setOpenedPlan]=useState<Plan|null>(null);
  const [planContext,setPlanContext]=useState<PlanContext|null>(null);
  const [scenarioInitial,setScenarioInitial]=useState<PlanContext|null>(null);
  const [scenarioDerived,setScenarioDerived]=useState<{reviewId:string;original:PlanContext|null}|null>(null);
  const [reviewRecovery,setReviewRecovery]=useState<ReviewRecovery|null>(null);
  const [planGate,setPlanGate]=useState<{key:string;gate:ReviewGate}|null>(null);
  const [mutationPhase,setMutationPhase]=useState<ReviewMutationPhase>('idle');
  const mutationPending=mutationPhase==='awaiting-response';
  const clearWorkflow=()=>{setOpenedPlan(null);setPlanContext(null);setScenarioInitial(null);setScenarioDerived(null);setReviewRecovery(null);setPlanGate(null);setMutationPhase('idle');setLinkedForecast(null);};
  const useData=(data:components['schemas']['ImportResult'])=>{if(mutationPending)return;setBusy(true);setDatasetReference(data.reference!.object_id);setSource(data);clearWorkflow();setSku(data.catalog!.products[0].sku);setLocation(data.catalog!.locations[0].location_id);setScreen('Plan Review');};
  const resetData=()=>{if(mutationPending)return;setDatasetReference(null);setSource(null);clearWorkflow();setSku('SKU001');setLocation('S1');setScreen('Demand Review');setRefresh(v=>v+1);};
  const reopen=async(review:components['schemas']['ReviewView'],signal:AbortSignal)=>{
    if(mutationPending)return;
    if(!review.dataset_ref)throw new Error('Portable dataset reference is unavailable. Reopen the downloaded snapshot.');
    const headers={'X-Dataset-Ref':review.dataset_ref};
    const [nextCatalog,p]=await Promise.all([api<Catalog>('/api/sample',signal,undefined,headers),api<Plan>(`/api/workflow/review/${review.reference}/plan`,signal,undefined,headers)]);
    if(signal.aborted)return;
    setDatasetReference(review.dataset_ref);setSource({reference:{object_id:review.dataset_ref,driver:'local'},catalog:nextCatalog,issues:[],measurements:{},input_hash:review.provenance?.dataset_hash,provenance:review.provenance});
    setSku(nextCatalog.products[0].sku);setLocation(nextCatalog.locations[0].location_id);clearWorkflow();setOpenedPlan(p);setPlanGate({key:planKey(p),gate:{blocked:true,reason:'Review state is loading.'}});setScreen('Plan Review');
  };
  const [linkedForecast,setLinkedForecast]=useState<Detail|null>(null);
  const rememberPlan=useCallback((plan:Plan,size:Size)=>{setPlanContext({plan,size});setPlanGate(current=>current?.key===planKey(plan)?current:{key:planKey(plan),gate:{blocked:!!plan.review_id,reason:plan.review_id?'Review state is loading.':''}});},[]);
  const updateScenarioState=useCallback((plan:Plan,gate:ReviewGate)=>setPlanGate({key:planKey(plan),gate}),[]);
  const recordRecovery=useCallback((next:ReviewRecovery)=>{setReviewRecovery(next);setScenarioDerived(current=>current?{...current,reviewId:next.review.reference}:current);},[]);
  const clearRecovery=useCallback((reference:string)=>setReviewRecovery(current=>current?.review.reference===reference?null:current),[]);
  const reviewPlan=useCallback((plan:Plan)=>{setOpenedPlan(plan);setScenarioDerived(current=>current&&plan.review_id?{...current,reviewId:plan.review_id}:current);},[]);
  const openForecast=(d:Detail)=>{if(mutationPending)return;setLinkedForecast(d);setScreen('Demand Review');};
  const [screen, setScreen] = useState<Screen>('Demand Review');
  const [size, setSize] = useState<Size>('fixture');
  const [sku, setSku] = useState('SKU001');
  const [location, setLocation] = useState('S1');
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [result, setResult] = useState<ForecastResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(true);
  const [refresh, setRefresh] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setBusy(true); setError(null); setResult(null);
    fetch('/api/workflow/session',{signal:controller.signal}).then(()=>Promise.all([
      api<Catalog>(`/api/sample?size=${size}`, controller.signal),
      api<ForecastResult>('/api/forecast/sample', controller.signal, { size, sku, location_id: location }),
    ])).then(([nextCatalog, nextResult]) => { if (!controller.signal.aborted) { setCatalog(nextCatalog); setResult(nextResult); } })
      .catch((e: Error) => { if (!controller.signal.aborted) setError(e.message); })
      .finally(() => { if (!controller.signal.aborted) setBusy(false); });
    return () => controller.abort();
  }, [size, sku, location, refresh, source]);
  const changeSize = (value: Size) => { if(mutationPending)return;setSize(value); setSku('SKU001'); setCatalog(null); clearWorkflow(); };
  const currentPlanBlocked=!!planContext&&(!planGate||planGate.key!==planKey(planContext.plan)||planGate.gate.blocked);
  const scenariosDisabled=mutationPending||!!scenarioDerived||currentPlanBlocked;
  const scenarioDerivedActive=!!scenarioDerived&&(scenarioDerived.reviewId===(openedPlan?.review_id||planContext?.plan.review_id)||scenarioDerived.reviewId===reviewRecovery?.review.reference);
  const openScenarios=(context:PlanContext|null=planContext)=>{if(mutationPending||scenarioDerived||(context&&(!planGate||planGate.key!==planKey(context.plan)||planGate.gate.blocked)))return;setScenarioInitial(context);setLinkedForecast(null);setScreen('Scenarios');};
  const returnToOriginalScenario=()=>{if(mutationPending)return;const original=scenarioDerived?.original||null;setScenarioDerived(null);setReviewRecovery(null);setOpenedPlan(original?.plan||null);setPlanContext(original);setScenarioInitial(original);setPlanGate(original?{key:planKey(original.plan),gate:{blocked:false,reason:''}}:null);setScreen('Scenarios');};
  const navigate=(name:Screen)=>{if(mutationPending)return;if(name==='Scenarios')openScenarios();else setScreen(name);};
  return <div className="app-shell">
    <a className="skip-link" href="#main-content">Skip to content</a>
    <aside className="sidebar"><a className="brand" href="#" aria-disabled={mutationPending||undefined} onClick={e => { e.preventDefault(); navigate('Demand Review'); }}><span className="brand-mark" aria-hidden="true">▥</span><span>Demand & Supply<small>PLANNING INTELLIGENCE</small></span></a>
      <div className="workspace-label">RIYADH RETAIL NETWORK</div>
      <nav aria-label="Primary navigation">{screens.map((name, i) => {const disabled=mutationPending||(name==='Scenarios'&&scenariosDisabled);return <button key={name} className={screen === name ? 'nav-item active' : 'nav-item'} aria-current={screen === name ? 'page' : undefined} disabled={disabled} title={name==='Scenarios'&&scenariosDisabled?(scenarioDerived?'Return to the original scenario baseline before starting another comparison.':planGate?.gate.reason||'Finish the current review before testing scenarios.'):undefined} onClick={() => navigate(name)}><span className="nav-number" aria-hidden="true">0{i + 1}</span>{name}</button>;})}</nav>
      <div className="sidebar-note"><span className="live-dot"/> {mutationPending?'Saving review mutation':source?.provenance?.source==='portable'?'Portable snapshot':source?'Uploaded dataset':'Synthetic portfolio'}<p>Transparent planning evidence.</p><small>{mutationPending?'Navigation resumes when the mutation response is safely recorded.':source?'Private temporary server processing.':'Independent example. No company-supplied data.'}</small></div>
    </aside>
    <div className="workspace"><header className="topbar"><span>Planning workspace <span className="crumb">/ {screen}</span></span><span className="sample-label">{source?.provenance?.source==='portable'?'PORTABLE SNAPSHOT':source?'UPLOADED DATA':'SYNTHETIC DATA'} <span>· SAR · Riyadh</span></span></header>
      <main id="main-content" tabIndex={-1}><div className="page-heading"><div><p className="eyebrow">Demand and supply planning</p><h1>{screen}</h1><p>{screen === 'Demand Review' ? 'A forecast you can trace back to the evidence.' : screen === 'Plan Review' ? 'What to buy, where stock goes, and which demand remains uncovered.' : screen === 'Data and Assumptions' ? 'Know what is included, and where the evidence stops.' : 'Compare the shock with keeping your actions and with replanning.'}</p></div><span className="phase-tag">Portfolio MVP</span></div>
      {screen === 'Data and Assumptions' ? <DataWorkspace onUse={useData} onReset={resetData} onReopen={reopen} reconciliationReference={reviewRecovery?.review.reference||openedPlan?.review_id}/> : screen === 'Demand Review' && linkedForecast ? <><section className="panel"><h2>Selected plan forecast · {linkedForecast.policy}</h2><details><summary>Selected policy and forecast version</summary><p>Scenario assumptions {linkedForecast.assumptions_hash}</p><p>Forecast version {linkedForecast.forecast_version}</p></details><p>Scenario policy buffer: {number(linkedForecast.policy_buffer.units)} units · {linkedForecast.policy_buffer.protection_days} days.</p><p>Historical evaluation stays unchanged. Scenario adjustments below apply only to future expected demand.</p>{linkedForecast.adjustments.map(a=><p key={a.day}>{a.day}: {number(a.original)} → {number(a.adjusted)} units · {a.reason}</p>)}<button onClick={()=>setLinkedForecast(null)}>Return to sample forecast controls</button></section><Demand result={linkedForecast.forecast}/></> : screen === 'Demand Review' ? <>
        <p className="dataset-context">{busy?'Loading selected dataset…':catalog?`${catalog.dataset_id} · planning date ${catalog.as_of}`:'Dataset unavailable — retry or reopen your data.'}</p>
        <section className="filters" aria-label="Sample controls"><label>Dataset<select value={source?'uploaded':size} onChange={e => changeSize(e.target.value as Size)} disabled={busy||!!source||mutationPending}>{source?<option value="uploaded">{source?.provenance?.source==='portable'?'Portable snapshot':'Uploaded dataset'}</option>:<><option value="fixture">Small fixture · 10 SKUs</option><option value="full">Full sample · 60 SKUs</option></>}</select></label>
          {screen === 'Demand Review' && <><label>Product<select value={sku} onChange={e => setSku(e.target.value)} disabled={busy || !catalog}>{catalog ? catalog.products.map(p => <option key={p.sku} value={p.sku}>{p.sku} · {p.name}</option>) : <option>Loading products…</option>}</select></label><label>Store<select value={location} onChange={e => setLocation(e.target.value)} disabled={busy || !catalog}>{catalog ? catalog.locations.map(l => <option key={l.location_id} value={l.location_id}>{l.name}</option>) : <option>Loading stores…</option>}</select></label></>}
          <button className="primary-button" disabled={busy||mutationPending} onClick={() => {if(!mutationPending)setRefresh(v => v + 1);}}>{busy ? 'Calculating…' : '↻ Recalculate live'}</button></section>
        <div role="status" aria-live="polite">{busy && <div className="loading"><span className="spinner"/>Calculating the forecast and its historical evaluation…</div>}</div>
        {error && <div role="alert" className="error"><strong>Calculation unavailable</strong><p>{error}</p><button onClick={() => setRefresh(v => v + 1)}>Try again</button></div>}
        {result && !busy && <Demand result={result}/>}
      </> : screen === 'Plan Review' ? (busy ? <div className="loading" role="status">Finishing the current forecast…</div> : <PlanReview key={source?.reference?.object_id||'sample'} initialPlan={openedPlan} recovery={reviewRecovery} scenarioDerived={scenarioDerivedActive} mutationPhase={mutationPhase} onReviewed={reviewPlan} uploaded={!!source} onReady={rememberPlan} onForecast={openForecast} onScenarios={(plan,nextSize)=>openScenarios({plan,size:nextSize})} onReturnToOriginalScenario={returnToOriginalScenario} onScenarioState={updateScenarioState} onRecovery={recordRecovery} onRecoveryClear={clearRecovery} onMutation={setMutationPhase}/>) : <Scenarios uploaded={!!source} firstSku={catalog?.products[0]?.sku} firstStore={catalog?.locations[0]?.location_id} initial={scenarioInitial} onForecast={openForecast} onReview={p=>{if(mutationPending)return;setScenarioDerived({reviewId:p.review_id!,original:scenarioInitial});setReviewRecovery(null);setOpenedPlan(p);setScreen('Plan Review');}}/>}
      <footer>Independent Saudi retail planning example <span>Expected demand is a model estimate, not a service guarantee.</span></footer>
      </main>
    </div>
  </div>;
}
