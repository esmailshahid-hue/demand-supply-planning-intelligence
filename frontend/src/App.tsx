import { useEffect, useState, useCallback } from 'react';
import { api, type Catalog, type ForecastResult, type Size, number } from './api';
import Demand from './Demand';
import PlanReview from './PlanReview';
import Scenarios from './Scenarios';
import type { Detail, Plan } from './scenarioApi';

const screens = ['Plan Review', 'Demand Review', 'Scenarios', 'Data and Assumptions'] as const;
type Screen = typeof screens[number];

export default function App() {
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
    Promise.all([
      api<Catalog>(`/api/sample?size=${size}`, controller.signal),
      api<ForecastResult>('/api/forecast/sample', controller.signal, { size, sku, location_id: location }),
    ]).then(([nextCatalog, nextResult]) => { if (!controller.signal.aborted) { setCatalog(nextCatalog); setResult(nextResult); } })
      .catch((e: Error) => { if (!controller.signal.aborted) setError(e.message); })
      .finally(() => { if (!controller.signal.aborted) setBusy(false); });
    return () => controller.abort();
  }, [size, sku, location, refresh]);
  const changeSize = (value: Size) => { setSize(value); setSku('SKU001'); setCatalog(null); };
  return <div className="app-shell">
    <a className="skip-link" href="#main-content">Skip to content</a>
    <aside className="sidebar"><a className="brand" href="#" onClick={e => { e.preventDefault(); setScreen('Demand Review'); }}><span className="brand-mark" aria-hidden="true">▥</span><span>Demand & Supply<small>PLANNING INTELLIGENCE</small></span></a>
      <div className="workspace-label">RIYADH RETAIL NETWORK</div>
      <nav aria-label="Primary navigation">{screens.map((name, i) => <button key={name} className={screen === name ? 'nav-item active' : 'nav-item'} aria-current={screen === name ? 'page' : undefined} onClick={() => { if(name === 'Scenarios') setLinkedForecast(null); setScreen(name); }}><span className="nav-number">0{i + 1}</span>{name}</button>)}</nav>
      <div className="sidebar-note"><span className="live-dot"/> Synthetic portfolio<p>One DC. Four stores.<br/>Transparent planning evidence.</p><small>Independent example.<br/>No company-supplied data.</small></div>
    </aside>
    <div className="workspace"><header className="topbar"><span>Planning workspace <span className="crumb">/ {screen}</span></span><span className="sample-label">SYNTHETIC DATA <span>· SAR · Riyadh</span></span></header>
      <main id="main-content" tabIndex={-1}><div className="page-heading"><div><p className="eyebrow">Demand and supply planning</p><h1>{screen}</h1><p>{screen === 'Demand Review' ? 'A forecast you can trace back to the evidence.' : screen === 'Plan Review' ? 'What to buy, where stock goes, and which demand remains uncovered.' : screen === 'Data and Assumptions' ? 'Know what is included, and where the evidence stops.' : 'Compare the shock with keeping your actions and with replanning.'}</p></div><span className="phase-tag">Pass 3 / 6</span></div>
      {screen === 'Demand Review' && linkedForecast ? <><section className="panel"><h2>Selected plan forecast · {linkedForecast.policy}</h2><details><summary>Selected policy and forecast version</summary><p>Scenario assumptions {linkedForecast.assumptions_hash}</p><p>Forecast version {linkedForecast.forecast_version}</p></details><p>Scenario policy buffer: {number(linkedForecast.policy_buffer.units)} units · {linkedForecast.policy_buffer.protection_days} days.</p><p>Historical evaluation stays unchanged. Scenario adjustments below apply only to future expected demand.</p>{linkedForecast.adjustments.map(a=><p key={a.day}>{a.day}: {number(a.original)} → {number(a.adjusted)} units · {a.reason}</p>)}<button onClick={()=>setLinkedForecast(null)}>Return to sample forecast controls</button></section><Demand result={linkedForecast.forecast}/></> : screen === 'Demand Review' || screen === 'Data and Assumptions' ? <>
        <section className="filters" aria-label="Sample controls"><label>Dataset<select value={size} onChange={e => changeSize(e.target.value as Size)} disabled={busy}><option value="fixture">Small fixture · 10 SKUs</option><option value="full">Full sample · 60 SKUs</option></select></label>
          {screen === 'Demand Review' && <><label>Product<select value={sku} onChange={e => setSku(e.target.value)} disabled={busy || !catalog}>{catalog ? catalog.products.map(p => <option key={p.sku} value={p.sku}>{p.sku} · {p.name}</option>) : <option>Loading products…</option>}</select></label><label>Store<select value={location} onChange={e => setLocation(e.target.value)} disabled={busy || !catalog}>{catalog ? catalog.locations.map(l => <option key={l.location_id} value={l.location_id}>{l.name}</option>) : <option>Loading stores…</option>}</select></label></>}
          <button className="primary-button" disabled={busy} onClick={() => setRefresh(v => v + 1)}>{busy ? 'Calculating…' : '↻ Recalculate live'}</button></section>
        <div role="status" aria-live="polite">{busy && <div className="loading"><span className="spinner"/>Calculating the forecast and its historical evaluation…</div>}</div>
        {error && <div role="alert" className="error"><strong>Calculation unavailable</strong><p>{error}</p><button onClick={() => setRefresh(v => v + 1)}>Try again</button></div>}
        {result && !busy && (screen === 'Demand Review' ? <Demand result={result}/> : <DataView result={result} catalog={catalog!}/>)}
      </> : screen === 'Plan Review' ? (busy ? <div className="loading">Finishing the current forecast…</div> : <PlanReview onReady={rememberPlan} onForecast={openForecast} onScenarios={()=>{setLinkedForecast(null);setScreen('Scenarios');}}/>) : <Scenarios initial={planContext} onForecast={openForecast}/>}
      <footer>Independent Saudi retail planning example <span>Expected demand is a model estimate, not a service guarantee.</span></footer>
      </main>
    </div>
  </div>;
}

function DataView({ result, catalog }: { result: ForecastResult; catalog: Catalog }) {
  return <div className="result-content"><section className="panel"><p className="eyebrow">Seeded synthetic inputs</p><h2>{catalog.products.length} products · one DC · four stores</h2><p>{number(catalog.history_rows, 0)} recorded daily observations over a 420-day history envelope. New products have shorter histories. As-of {result.as_of}, Asia/Riyadh; all financial inputs use SAR per base unit.</p><div className="notice">Calculations run on the Python server. Uploads and workbook downloads are unavailable until Pass 4. No browser-only privacy claim applies.</div><h3>Forecast assumptions</h3><ul><li>Seasonal naive repeats the most recent available same weekday.</li><li>Four-week means use the four calendar occurrences before the origin.</li><li>Recency weights are 40/30/20/10%, renormalized over eligible observations.</li><li>Known event days are excluded from the ordinary pool; dated changes apply once afterward.</li><li>Unknown days remain unknown. Open, available days with zero sales are valid zeros.</li><li>Four complete selection windows are required; the last 28 historical days remain a final check.</li></ul><h3>Operational assumptions</h3><p>Stock is in base units. Usable stock is on-hand minus blocked minus reserved. Reservations represent stock already committed outside this demand forecast and are deducted once. Commitment limits are remaining authority for new purchases; unpaid obligations consume payment ceilings. Tax and receivables are outside scope.</p></section><section className="panel"><h2>Validation warnings</h2>{result.warnings.map(w => <p className="warning-line" key={w.code}><strong>{w.code.replaceAll('_', ' ')} · {w.count}</strong><span>{w.message}</span></p>)}</section><section className="panel"><h2>Own-data workflow</h2><p>Template, upload, dated override editing and exports will be added in later passes.</p><button disabled>Download template · unavailable</button> <button disabled>Upload workbook · unavailable</button></section></div>;
}
