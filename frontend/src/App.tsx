import { useEffect, useState, useCallback } from 'react';
import { api, type Catalog, type ForecastResult, type Size, number, setDatasetReference } from './api';
import DataWorkspace from './DataWorkspace';
import type { components } from './contracts.generated';
import Demand from './Demand';
import PlanReview from './PlanReview';
import Scenarios from './Scenarios';
import type { Detail, Plan } from './scenarioApi';

const screens = ['Plan Review', 'Demand Review', 'Scenarios', 'Data and Assumptions'] as const;
type Screen = typeof screens[number];

export default function App() {
  const [source,setSource]=useState<components['schemas']['ImportResult']|null>(null);
  const [openedPlan,setOpenedPlan]=useState<Plan|null>(null);
  const useData=(data:components['schemas']['ImportResult'])=>{setBusy(true);setDatasetReference(data.reference!.object_id);setSource(data);setOpenedPlan(null);setPlanContext(null);setLinkedForecast(null);setSku(data.catalog!.products[0].sku);setLocation(data.catalog!.locations[0].location_id);setScreen('Plan Review');};
  const resetData=()=>{setDatasetReference(null);setSource(null);setOpenedPlan(null);setPlanContext(null);setLinkedForecast(null);setSku('SKU001');setLocation('S1');setScreen('Demand Review');setRefresh(v=>v+1);};
  const reopen=async(review:components['schemas']['ReviewView'])=>{const c=new AbortController();if(review.dataset_ref){setBusy(true);setDatasetReference(review.dataset_ref);const catalog=await api<Catalog>('/api/sample',c.signal);setSource({reference:{object_id:review.dataset_ref,driver:'local'},catalog,issues:[],measurements:{},input_hash:null});setSku(catalog.products[0].sku);setLocation(catalog.locations[0].location_id);}const p=await api<Plan>(`/api/workflow/review/${review.reference}/plan`,c.signal);setOpenedPlan(p);setPlanContext(null);setLinkedForecast(null);setScreen('Plan Review');};
  const [planContext,setPlanContext]=useState<{plan:Plan;size:Size}|null>(null);
  const [linkedForecast,setLinkedForecast]=useState<Detail|null>(null);
  const rememberPlan=useCallback((plan:Plan,size:Size)=>setPlanContext({plan,size}),[]);
  const openForecast=(d:Detail)=>{setLinkedForecast(d);setScreen('Demand Review');};
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
  const changeSize = (value: Size) => { setSize(value); setSku('SKU001'); setCatalog(null); };
  return <div className="app-shell">
    <a className="skip-link" href="#main-content">Skip to content</a>
    <aside className="sidebar"><a className="brand" href="#" onClick={e => { e.preventDefault(); setScreen('Demand Review'); }}><span className="brand-mark" aria-hidden="true">▥</span><span>Demand & Supply<small>PLANNING INTELLIGENCE</small></span></a>
      <div className="workspace-label">RIYADH RETAIL NETWORK</div>
      <nav aria-label="Primary navigation">{screens.map((name, i) => <button key={name} className={screen === name ? 'nav-item active' : 'nav-item'} aria-current={screen === name ? 'page' : undefined} onClick={() => { if(name === 'Scenarios') setLinkedForecast(null); setScreen(name); }}><span className="nav-number">0{i + 1}</span>{name}</button>)}</nav>
      <div className="sidebar-note"><span className="live-dot"/> {source?'Uploaded dataset':'Synthetic portfolio'}<p>Transparent planning evidence.</p><small>{source?'Private temporary server processing.':'Independent example. No company-supplied data.'}</small></div>
    </aside>
    <div className="workspace"><header className="topbar"><span>Planning workspace <span className="crumb">/ {screen}</span></span><span className="sample-label">{source?'UPLOADED DATA':'SYNTHETIC DATA'} <span>· SAR · Riyadh</span></span></header>
      <main id="main-content" tabIndex={-1}><div className="page-heading"><div><p className="eyebrow">Demand and supply planning</p><h1>{screen}</h1><p>{screen === 'Demand Review' ? 'A forecast you can trace back to the evidence.' : screen === 'Plan Review' ? 'What to buy, where stock goes, and which demand remains uncovered.' : screen === 'Data and Assumptions' ? 'Know what is included, and where the evidence stops.' : 'Compare the shock with keeping your actions and with replanning.'}</p></div><span className="phase-tag">Pass 4 / 6</span></div>
      {screen === 'Data and Assumptions' ? <DataWorkspace onUse={useData} onReset={resetData} onReopen={reopen} reconciliationReference={openedPlan?.review_id}/> : screen === 'Demand Review' && linkedForecast ? <><section className="panel"><h2>Selected plan forecast · {linkedForecast.policy}</h2><details><summary>Selected policy and forecast version</summary><p>Scenario assumptions {linkedForecast.assumptions_hash}</p><p>Forecast version {linkedForecast.forecast_version}</p></details><p>Scenario policy buffer: {number(linkedForecast.policy_buffer.units)} units · {linkedForecast.policy_buffer.protection_days} days.</p><p>Historical evaluation stays unchanged. Scenario adjustments below apply only to future expected demand.</p>{linkedForecast.adjustments.map(a=><p key={a.day}>{a.day}: {number(a.original)} → {number(a.adjusted)} units · {a.reason}</p>)}<button onClick={()=>setLinkedForecast(null)}>Return to sample forecast controls</button></section><Demand result={linkedForecast.forecast}/></> : screen === 'Demand Review' ? <>
        <section className="filters" aria-label="Sample controls"><label>Dataset<select value={source?'uploaded':size} onChange={e => changeSize(e.target.value as Size)} disabled={busy||!!source}>{source?<option value="uploaded">Uploaded dataset</option>:<><option value="fixture">Small fixture · 10 SKUs</option><option value="full">Full sample · 60 SKUs</option></>}</select></label>
          {screen === 'Demand Review' && <><label>Product<select value={sku} onChange={e => setSku(e.target.value)} disabled={busy || !catalog}>{catalog ? catalog.products.map(p => <option key={p.sku} value={p.sku}>{p.sku} · {p.name}</option>) : <option>Loading products…</option>}</select></label><label>Store<select value={location} onChange={e => setLocation(e.target.value)} disabled={busy || !catalog}>{catalog ? catalog.locations.map(l => <option key={l.location_id} value={l.location_id}>{l.name}</option>) : <option>Loading stores…</option>}</select></label></>}
          <button className="primary-button" disabled={busy} onClick={() => setRefresh(v => v + 1)}>{busy ? 'Calculating…' : '↻ Recalculate live'}</button></section>
        <div role="status" aria-live="polite">{busy && <div className="loading"><span className="spinner"/>Calculating the forecast and its historical evaluation…</div>}</div>
        {error && <div role="alert" className="error"><strong>Calculation unavailable</strong><p>{error}</p><button onClick={() => setRefresh(v => v + 1)}>Try again</button></div>}
        {result && !busy && <Demand result={result}/>}
      </> : screen === 'Plan Review' ? (busy ? <div className="loading">Finishing the current forecast…</div> : <PlanReview key={source?.reference?.object_id||'sample'} initialPlan={openedPlan} onReviewed={setOpenedPlan} uploaded={!!source} onReady={rememberPlan} onForecast={openForecast} onScenarios={()=>{setLinkedForecast(null);setScreen('Scenarios');}}/>) : <Scenarios uploaded={!!source} firstSku={catalog?.products[0]?.sku} firstStore={catalog?.locations[0]?.location_id} initial={openedPlan?null:planContext} onForecast={openForecast} onReview={p=>{setOpenedPlan(p);setScreen('Plan Review');}}/>}
      <footer>Independent Saudi retail planning example <span>Expected demand is a model estimate, not a service guarantee.</span></footer>
      </main>
    </div>
  </div>;
}
