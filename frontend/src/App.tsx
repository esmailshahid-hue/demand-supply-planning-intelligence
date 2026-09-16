import { useEffect, useState } from 'react';
import { api, type Catalog, type ForecastResult, type Size, methodNames, number, percent, shortDate, signedPercent } from './api';
import ForecastChart from './ForecastChart';
import Evaluation from './Evaluation';

const screens = ['Plan Review', 'Demand Review', 'Scenarios', 'Data and Assumptions'] as const;
type Screen = typeof screens[number];

export default function App() {
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
      <nav aria-label="Primary navigation">{screens.map((name, i) => <button key={name} className={screen === name ? 'nav-item active' : 'nav-item'} aria-current={screen === name ? 'page' : undefined} onClick={() => setScreen(name)}><span className="nav-number">0{i + 1}</span>{name}</button>)}</nav>
      <div className="sidebar-note"><span className="live-dot"/> Synthetic portfolio<p>One DC. Four stores.<br/>Transparent planning evidence.</p><small>Independent example.<br/>No company-supplied data.</small></div>
    </aside>
    <div className="workspace"><header className="topbar"><span>Planning workspace <span className="crumb">/ {screen}</span></span><span className="sample-label">SYNTHETIC DATA <span>· SAR · Riyadh</span></span></header>
      <main id="main-content" tabIndex={-1}><div className="page-heading"><div><p className="eyebrow">Demand and supply planning · Foundation</p><h1>{screen}</h1><p>{screen === 'Demand Review' ? 'A forecast you can trace back to the evidence.' : screen === 'Data and Assumptions' ? 'Know what is included, and where the evidence stops.' : 'This workspace is reserved for the next build stages.'}</p></div><span className="phase-tag">Pass 1 / 6</span></div>
      {screen === 'Demand Review' || screen === 'Data and Assumptions' ? <>
        <section className="filters" aria-label="Sample controls"><label>Dataset<select value={size} onChange={e => changeSize(e.target.value as Size)} disabled={busy}><option value="fixture">Small fixture · 10 SKUs</option><option value="full">Full sample · 60 SKUs</option></select></label>
          {screen === 'Demand Review' && <><label>Product<select value={sku} onChange={e => setSku(e.target.value)} disabled={busy || !catalog}>{catalog ? catalog.products.map(p => <option key={p.sku} value={p.sku}>{p.sku} · {p.name}</option>) : <option>Loading products…</option>}</select></label><label>Store<select value={location} onChange={e => setLocation(e.target.value)} disabled={busy || !catalog}>{catalog ? catalog.locations.map(l => <option key={l.location_id} value={l.location_id}>{l.name}</option>) : <option>Loading stores…</option>}</select></label></>}
          <button className="primary-button" disabled={busy} onClick={() => setRefresh(v => v + 1)}>{busy ? 'Calculating…' : '↻ Recalculate live'}</button></section>
        <div role="status" aria-live="polite">{busy && <div className="loading"><span className="spinner"/>Calculating the forecast and its historical evaluation…</div>}</div>
        {error && <div role="alert" className="error"><strong>Calculation unavailable</strong><p>{error}</p><button onClick={() => setRefresh(v => v + 1)}>Try again</button></div>}
        {result && !busy && (screen === 'Demand Review' ? <Demand result={result}/> : <DataView result={result} catalog={catalog!}/>)}
      </> : <section className="panel unavailable"><span className="unavailable-icon" aria-hidden="true">{screen === 'Plan Review' ? '↔' : <ScenarioIcon/>}</span><p className="eyebrow">Not available in Pass 1</p><h2>{screen === 'Plan Review' ? 'Purchasing and allocation come next.' : 'Scenario comparisons need a validated plan.'}</h2><p>{screen === 'Plan Review' ? 'Pass 2 adds shared-stock allocation, purchasing, cash schedules and independent feasibility checks. There are no plan recommendations yet.' : 'Pass 3 adds demand, supplier and funding changes, with frozen-plan and replanned comparisons.'}</p><button className="primary-button" onClick={() => setScreen('Demand Review')}>Review the live forecast →</button></section>}
      <footer>Independent Saudi retail planning example <span>Expected demand is a model estimate, not a service guarantee.</span></footer>
      </main>
    </div>
  </div>;
}

function Demand({ result }: { result: ForecastResult }) {
  const selected = result.selection.find(r => r.method === result.selected_method)!;
  const m = selected.metrics.find(m => m.horizon === 28)!;
  const baseline = result.selection[0].metrics.find(m => m.horizon === 28)!;
  return <div className="result-content" data-testid="forecast-result" data-run-id={result.run_id}>
    <section className="decision-banner"><div><span className={`status-tag ${result.status}`}>{result.status === 'evaluated' ? 'Historically evaluated' : result.status === 'provisional' ? 'Provisional forecast' : 'Incomplete forecast'}</span><h2>{methodNames[result.selected_method]}</h2><p>{result.selection_reason}</p></div><div className="as-of"><span>FORECAST FROM</span><strong>{shortDate(result.as_of)} {result.as_of.slice(0, 4)}</strong><small>{result.location_name} · {result.sku}</small></div></section>
    <div className="metric-grid"><Metric label="Next 28 days" value={number(result.visible_units)} unit="expected units" detail="Visible decision window"/><Metric label="Versus seasonal naive" value={percent(result.improvement_pct, 0)} unit="quantity MAE improvement" detail={`Baseline ${number(baseline.mean_absolute_quantity_error)} → selected ${number(m.mean_absolute_quantity_error)} units`}/><Metric label="Pooled signed bias" value={signedPercent(m.signed_bias_pct)} unit="pooled signed error" detail={`${number(m.signed_bias_units)} units · positive = overforecast`}/><Metric label="Evaluation coverage" value={`${m.valid_observations} / ${m.windows * 28}`} unit="scored daily observations" detail={`${m.complete_windows} complete windows · ${m.excluded_observations} excluded`}/></div>
    <section className="panel"><div className="section-heading"><div><p className="eyebrow">{result.product_name} · {result.location_name}</p><h2>From observed sales to expected demand</h2></div><span className="subtle-tag">56-day model horizon</span></div><ForecastChart result={result}/><div className="chart-note"><span><strong>Days 29–56:</strong> {number(result.tail_units)} units, provisional.</span><span>Known events adjust the ordinary baseline once.</span></div>
      <details><summary>Daily quantities, fallback reasons and censored history</summary><div className="table-scroll daily-table"><table><thead><tr><th>Date</th><th>Ordinary baseline</th><th>Expected demand</th><th>Window</th><th>Event / fallback</th></tr></thead><tbody>{result.forecast.map(p => <tr key={p.day}><th scope="row">{p.day}</th><td>{number(p.baseline_units)}</td><td>{number(p.forecast_units)}</td><td>{p.provisional_tail ? 'Provisional tail' : 'Visible'}</td><td>{[p.reason, p.fallback].filter(Boolean).join(' · ') || 'Ordinary weekday'}</td></tr>)}</tbody></table></div><h3>Recent historical evidence</h3><div className="table-scroll daily-table"><table><thead><tr><th>Date</th><th>Observed sales</th><th>Training estimate</th><th>Observation status</th></tr></thead><tbody>{result.history.map(p => <tr key={p.day}><th scope="row">{p.day}</th><td>{number(p.observed_sales)}</td><td>{number(p.training_estimate)}</td><td>{p.status.replaceAll('_', ' ')}</td></tr>)}</tbody></table></div></details>
    </section>
    <Evaluation result={result}/>
    <div className="two-column"><section className="panel"><p className="eyebrow">Protection-period evidence</p><h2>{number(result.buffer.units)} units <span className="heading-note">illustrative buffer</span></h2><p>{result.buffer.method === 'empirical_underforecast' ? `${result.buffer.percentile}th percentile of ${result.buffer.sample_count} complete ${result.buffer.protection_days}-day underforecast errors.` : `${result.buffer.fallback_days} days of forecast demand; only ${result.buffer.sample_count} complete protection-period windows.`}</p><p className="muted">{result.buffer.note}</p></section><section className="panel"><p className="eyebrow">Dataset quality</p><h2>Keep unknown demand visible</h2>{result.warnings.map(w => <p className="warning-line" key={w.code}><strong>{w.count} · {w.code.replaceAll('_', ' ')}</strong><span>{w.message}</span></p>)}<p className="footnote">Counts cover the dataset. Series-level exclusions appear in the evaluation record.</p></section></div>
    <details className="metadata"><summary>Calculation record</summary><dl><dt>Run ID</dt><dd>{result.run_id}</dd><dt>Engine / schema</dt><dd>{result.engine_version} / {result.schema_version}</dd><dt>Input hash</dt><dd>{result.input_hash}</dd><dt>Engine calculation time</dt><dd>{number(result.elapsed_ms)} ms</dd></dl><p>Live server calculation. No sample result snapshot is substituted.</p></details>
  </div>;
}
function Metric({ label, value, unit, detail }: { label: string; value: string; unit: string; detail: string }) {
  return <section className="metric"><p>{label}</p><strong>{value}</strong><span>{unit}</span><small>{detail}</small></section>;
}
function ScenarioIcon() {
  return <svg viewBox="0 0 24 24" focusable="false"><path d="M5 4v4c0 2.2 1.8 4 4 4h9m0 0-3-3m3 3-3 3M5 20v-4c0-2.2 1.8-4 4-4"/></svg>;
}
function DataView({ result, catalog }: { result: ForecastResult; catalog: Catalog }) {
  return <div className="result-content"><section className="panel"><p className="eyebrow">Seeded synthetic inputs</p><h2>{catalog.products.length} products · one DC · four stores</h2><p>{number(catalog.history_rows, 0)} recorded daily observations over a 420-day history envelope. New products have shorter histories. As-of {result.as_of}, Asia/Riyadh; all financial inputs use SAR per base unit.</p><div className="notice">Calculations run on the Python server. Uploads and workbook downloads are unavailable until Pass 4. No browser-only privacy claim applies.</div><h3>Forecast assumptions</h3><ul><li>Seasonal naive repeats the most recent available same weekday.</li><li>Four-week means use the four calendar occurrences before the origin.</li><li>Recency weights are 40/30/20/10%, renormalized over eligible observations.</li><li>Known event days are excluded from the ordinary pool; dated changes apply once afterward.</li><li>Unknown days remain unknown. Open, available days with zero sales are valid zeros.</li><li>Four complete selection windows are required; the last 28 historical days remain a final check.</li></ul><h3>Operational assumptions prepared for Pass 2</h3><p>Stock is in base units. Usable stock is on-hand minus blocked minus reserved. Reservations represent stock already committed outside this demand forecast and are deducted once. Commitment limits are remaining authority for new purchases; unpaid obligations consume payment ceilings. Tax and receivables are outside scope.</p></section><section className="panel"><h2>Validation warnings</h2>{result.warnings.map(w => <p className="warning-line" key={w.code}><strong>{w.code.replaceAll('_', ' ')} · {w.count}</strong><span>{w.message}</span></p>)}</section><section className="panel"><h2>Own-data workflow</h2><p>Template, upload, dated override editing and exports will be added in later passes.</p><button disabled>Download template · unavailable</button> <button disabled>Upload workbook · unavailable</button></section></div>;
}
