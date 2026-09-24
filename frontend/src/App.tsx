import { useCallback, useEffect, useState } from 'react';
import { api, number, setDatasetReference, type Catalog, type ForecastResult, type Size } from './api';
import type { components } from './contracts.generated';
import DataWorkspace from './DataWorkspace';
import Demand from './Demand';
import PlanReview from './PlanReview';
import Scenarios from './Scenarios';
import type { Detail, Plan } from './scenarioApi';
import type { ReviewGate, ReviewMutationPhase, ReviewRecovery } from './reviewState';

const screens = ['Plan Review', 'Demand Review', 'Scenarios', 'Data and Assumptions'] as const;
type Screen = typeof screens[number];
type PlanContext = { plan: Plan; size: Size };
const planKey = (plan: Plan) => plan.review_id || plan.run_id;

export default function App() {
  const [screen, setScreen] = useState<Screen>('Plan Review');
  const [source, setSource] = useState<components['schemas']['ImportResult'] | null>(null);
  const [openedPlan, setOpenedPlan] = useState<Plan | null>(null);
  const [planContext, setPlanContext] = useState<PlanContext | null>(null);
  const [scenarioInitial, setScenarioInitial] = useState<PlanContext | null>(null);
  const [scenarioDerived, setScenarioDerived] = useState<{ reviewId: string; original: PlanContext | null } | null>(null);
  const [reviewRecovery, setReviewRecovery] = useState<ReviewRecovery | null>(null);
  const [planGate, setPlanGate] = useState<{ key: string; gate: ReviewGate } | null>(null);
  const [mutationPhase, setMutationPhase] = useState<ReviewMutationPhase>('idle');
  const [linkedForecast, setLinkedForecast] = useState<Detail | null>(null);
  const [size, setSize] = useState<Size>('fixture');
  const [sku, setSku] = useState('SKU001');
  const [location, setLocation] = useState('S1');
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [catalogError, setCatalogError] = useState('');
  const [forecast, setForecast] = useState<ForecastResult | null>(null);
  const [forecastError, setForecastError] = useState('');
  const [forecastBusy, setForecastBusy] = useState(false);
  const [forecastRefresh, setForecastRefresh] = useState(0);
  const [sessionReady, setSessionReady] = useState(false);
  const [sessionError, setSessionError] = useState('');
  const [sessionRetry, setSessionRetry] = useState(0);
  const [datasetGeneration, setDatasetGeneration] = useState(0);
  const mutationPending = mutationPhase === 'awaiting-response';

  const clearWorkflow = () => {
    setOpenedPlan(null);
    setPlanContext(null);
    setScenarioInitial(null);
    setScenarioDerived(null);
    setReviewRecovery(null);
    setPlanGate(null);
    setMutationPhase('idle');
    setLinkedForecast(null);
  };

  useEffect(() => {
    const controller = new AbortController();
    setSessionReady(false);
    setSessionError('');
    api<unknown>('/api/workflow/session', controller.signal)
      .catch((error: Error) => {
        if (!controller.signal.aborted) setSessionError(error.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setSessionReady(true);
      });
    return () => controller.abort();
  }, [sessionRetry]);

  useEffect(() => {
    if (screen !== 'Demand Review' || linkedForecast || catalog) return;
    const controller = new AbortController();
    setCatalogError('');
    api<Catalog>(`/api/sample?size=${size}`, controller.signal)
      .then(next => {
        if (!controller.signal.aborted) setCatalog(next);
      })
      .catch((error: Error) => {
        if (!controller.signal.aborted) setCatalogError(error.message);
      });
    return () => controller.abort();
  }, [screen, linkedForecast, catalog, size, source]);

  useEffect(() => {
    if (screen !== 'Demand Review' || linkedForecast) return;
    const controller = new AbortController();
    setForecastBusy(true);
    setForecastError('');
    setForecast(null);
    api<ForecastResult>('/api/forecast/sample', controller.signal, { size, sku, location_id: location })
      .then(next => {
        if (!controller.signal.aborted) setForecast(next);
      })
      .catch((error: Error) => {
        if (!controller.signal.aborted) setForecastError(error.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setForecastBusy(false);
      });
    return () => controller.abort();
  }, [screen, linkedForecast, size, sku, location, forecastRefresh, source]);

  const useData = (data: components['schemas']['ImportResult']) => {
    if (mutationPending) return;
    setDatasetReference(data.reference!.object_id);
    setSource(data);
    setCatalog(data.catalog!);
    setForecast(null);
    clearWorkflow();
    setSku(data.catalog!.products[0].sku);
    setLocation(data.catalog!.locations[0].location_id);
    setDatasetGeneration(value => value + 1);
    setScreen('Plan Review');
  };

  const resetData = () => {
    if (mutationPending) return;
    setDatasetReference(null);
    setSource(null);
    setCatalog(null);
    setForecast(null);
    clearWorkflow();
    setSize('fixture');
    setSku('SKU001');
    setLocation('S1');
    setDatasetGeneration(value => value + 1);
    setScreen('Plan Review');
  };

  const reopen = async (review: components['schemas']['ReviewView'], signal: AbortSignal) => {
    if (mutationPending) return;
    if (!review.dataset_ref) throw new Error('Portable dataset reference is unavailable. Reopen the downloaded snapshot.');
    const headers = { 'X-Dataset-Ref': review.dataset_ref };
    const [nextCatalog, plan] = await Promise.all([
      api<Catalog>('/api/sample', signal, undefined, headers),
      api<Plan>(`/api/workflow/review/${review.reference}/plan`, signal, undefined, headers),
    ]);
    if (signal.aborted) return;
    setDatasetReference(review.dataset_ref);
    setSource({
      reference: { object_id: review.dataset_ref, driver: 'local' },
      catalog: nextCatalog,
      issues: [],
      measurements: {},
      input_hash: review.provenance?.dataset_hash,
      provenance: review.provenance,
    });
    setCatalog(nextCatalog);
    setSku(nextCatalog.products[0].sku);
    setLocation(nextCatalog.locations[0].location_id);
    clearWorkflow();
    setOpenedPlan(plan);
    setPlanGate({ key: planKey(plan), gate: { blocked: true, reason: 'Review state is loading.' } });
    setDatasetGeneration(value => value + 1);
    setScreen('Plan Review');
  };

  const rememberPlan = useCallback((plan: Plan, nextSize: Size) => {
    setPlanContext({ plan, size: nextSize });
    setSize(nextSize);
    setPlanGate(current => current?.key === planKey(plan) ? current : {
      key: planKey(plan),
      gate: { blocked: !!plan.review_id, reason: plan.review_id ? 'Review state is loading.' : '' },
    });
  }, []);
  const updateScenarioState = useCallback((plan: Plan, gate: ReviewGate) => setPlanGate({ key: planKey(plan), gate }), []);
  const recordRecovery = useCallback((next: ReviewRecovery) => {
    setReviewRecovery(next);
    setScenarioDerived(current => current ? { ...current, reviewId: next.review.reference } : current);
  }, []);
  const clearRecovery = useCallback((reference: string) => setReviewRecovery(current => current?.review.reference === reference ? null : current), []);
  const reviewPlan = useCallback((plan: Plan) => {
    setOpenedPlan(plan);
    setScenarioDerived(current => current && plan.review_id ? { ...current, reviewId: plan.review_id } : current);
  }, []);
  const openForecast = (detail: Detail) => {
    if (mutationPending) return;
    setLinkedForecast(detail);
    setScreen('Demand Review');
  };
  const changeSize = (value: Size) => {
    if (mutationPending) return;
    setSize(value);
    setSku('SKU001');
    setLocation('S1');
    setCatalog(null);
    setForecast(null);
    clearWorkflow();
    setDatasetGeneration(generation => generation + 1);
  };
  const invalidatePlan = (nextSize: Size) => {
    setSize(nextSize);
    setCatalog(null);
    setForecast(null);
    setOpenedPlan(null);
    setPlanContext(null);
    setScenarioInitial(null);
    setScenarioDerived(null);
    setReviewRecovery(null);
    setPlanGate(null);
  };

  const currentPlanBlocked = !!planContext && (!planGate || planGate.key !== planKey(planContext.plan) || planGate.gate.blocked);
  const scenariosDisabled = mutationPending || !!scenarioDerived || currentPlanBlocked;
  const scenarioDerivedActive = !!scenarioDerived && (
    scenarioDerived.reviewId === (openedPlan?.review_id || planContext?.plan.review_id)
    || scenarioDerived.reviewId === reviewRecovery?.review.reference
  );
  const openScenarios = (context: PlanContext | null = planContext) => {
    if (mutationPending || scenarioDerived || (context && (!planGate || planGate.key !== planKey(context.plan) || planGate.gate.blocked))) return;
    setScenarioInitial(context);
    setLinkedForecast(null);
    setScreen('Scenarios');
  };
  const returnToOriginalScenario = () => {
    if (mutationPending) return;
    const original = scenarioDerived?.original || null;
    setScenarioDerived(null);
    setReviewRecovery(null);
    setOpenedPlan(original?.plan || null);
    setPlanContext(original);
    setScenarioInitial(original);
    setPlanGate(original ? { key: planKey(original.plan), gate: { blocked: false, reason: '' } } : null);
    setScreen('Scenarios');
  };
  const navigate = (name: Screen) => {
    if (mutationPending) return;
    if (name === 'Scenarios') openScenarios();
    else setScreen(name);
  };
  const cachedPlan = openedPlan || planContext?.plan || null;
  const firstPlanForecast = planContext?.plan.forecasts[0];

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">Skip to content</a>
      <aside className="sidebar">
        <a className="brand" href="#" aria-disabled={mutationPending || undefined} onClick={event => { event.preventDefault(); navigate('Plan Review'); }}>
          <span className="brand-mark" aria-hidden="true">▥</span>
          <span>Demand & Supply<small>PLANNING INTELLIGENCE</small></span>
        </a>
        <div className="workspace-label">RIYADH RETAIL NETWORK</div>
        <nav aria-label="Primary navigation">
          {screens.map((name, index) => {
            const disabled = mutationPending || (name === 'Scenarios' && scenariosDisabled);
            const title = name === 'Scenarios' && scenariosDisabled
              ? scenarioDerived
                ? 'Return to the original scenario baseline before starting another comparison.'
                : planGate?.gate.reason || 'Finish the current review before testing scenarios.'
              : undefined;
            return <button key={name} className={screen === name ? 'nav-item active' : 'nav-item'} aria-current={screen === name ? 'page' : undefined} disabled={disabled} title={title} onClick={() => navigate(name)}><span className="nav-number" aria-hidden="true">0{index + 1}</span>{name}</button>;
          })}
        </nav>
        <div className="sidebar-note">
          <span className="live-dot"/> {mutationPending ? 'Saving review mutation' : source?.provenance?.source === 'portable' ? 'Portable snapshot' : source ? 'Uploaded dataset' : 'Synthetic portfolio'}
          <p>Transparent planning evidence.</p>
          <small>{mutationPending ? 'Navigation resumes when the mutation response is safely recorded.' : source ? 'Private temporary server processing.' : 'Independent example. No company-supplied data.'}</small>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar"><span>Planning workspace <span className="crumb">/ {screen}</span></span><span className="sample-label">{source?.provenance?.source === 'portable' ? 'PORTABLE SNAPSHOT' : source ? 'UPLOADED DATA' : 'SYNTHETIC DATA'} <span>· SAR · Riyadh</span></span></header>
        <main id="main-content" tabIndex={-1}>
          <div className="page-heading"><div><p className="eyebrow">Demand and supply planning</p><h1>{screen}</h1><p>{screen === 'Demand Review' ? 'A forecast you can trace back to the evidence.' : screen === 'Plan Review' ? 'What to buy, where stock goes, and which demand remains uncovered.' : screen === 'Data and Assumptions' ? 'Know what is included, and where the evidence stops.' : 'Compare the shock with keeping your actions and with replanning.'}</p></div><span className="phase-tag">Portfolio MVP</span></div>
          {screen === 'Data and Assumptions' ? (
            <DataWorkspace onUse={useData} onReset={resetData} onReopen={reopen} reconciliationReference={reviewRecovery?.review.reference || openedPlan?.review_id}/>
          ) : screen === 'Demand Review' && linkedForecast ? (
            <><section className="panel"><h2>Selected plan forecast · {linkedForecast.policy}</h2><details><summary>Selected policy and forecast version</summary><p>Scenario assumptions {linkedForecast.assumptions_hash}</p><p>Forecast version {linkedForecast.forecast_version}</p></details><p>Scenario policy buffer: {number(linkedForecast.policy_buffer.units)} units · {linkedForecast.policy_buffer.protection_days} days.</p><p>Historical evaluation stays unchanged. Scenario adjustments below apply only to future expected demand.</p>{linkedForecast.adjustments.map(adjustment => <p key={adjustment.day}>{adjustment.day}: {number(adjustment.original)} → {number(adjustment.adjusted)} units · {adjustment.reason}</p>)}<button onClick={() => setLinkedForecast(null)}>Return to sample forecast controls</button></section><Demand result={linkedForecast.forecast}/></>
          ) : screen === 'Demand Review' ? (
            <>
              <p className="dataset-context">{catalog ? `${catalog.dataset_id} · planning date ${catalog.as_of}` : catalogError ? 'Dataset unavailable — retry or reopen your data.' : 'Loading selected dataset…'}</p>
              <section className="filters" aria-label="Sample controls">
                <label>Dataset<select value={source ? 'uploaded' : size} onChange={event => changeSize(event.target.value as Size)} disabled={!!source || mutationPending}>{source ? <option value="uploaded">{source.provenance?.source === 'portable' ? 'Portable snapshot' : 'Uploaded dataset'}</option> : <><option value="fixture">Small fixture · 10 SKUs</option><option value="full">Full sample · 60 SKUs</option></>}</select></label>
                <label>Product<select value={sku} onChange={event => setSku(event.target.value)} disabled={!catalog || forecastBusy}>{catalog ? catalog.products.map(product => <option key={product.sku} value={product.sku}>{product.sku} · {product.name}</option>) : <option>Loading products…</option>}</select></label>
                <label>Store<select value={location} onChange={event => setLocation(event.target.value)} disabled={!catalog || forecastBusy}>{catalog ? catalog.locations.map(item => <option key={item.location_id} value={item.location_id}>{item.name}</option>) : <option>Loading stores…</option>}</select></label>
                <button className="primary-button" disabled={forecastBusy || mutationPending} onClick={() => { if (!mutationPending) setForecastRefresh(value => value + 1); }}>{forecastBusy ? 'Calculating…' : '↻ Recalculate live'}</button>
              </section>
              <div role="status" aria-live="polite">{forecastBusy && <div className="loading"><span className="spinner"/>Calculating the forecast and its historical evaluation…</div>}</div>
              {(forecastError || catalogError) && <div role="alert" className="error"><strong>Calculation unavailable</strong><p>{forecastError || catalogError}</p><button onClick={() => { setCatalog(null); setForecastRefresh(value => value + 1); }}>Try again</button></div>}
              {forecast && !forecastBusy && <Demand result={forecast}/>}
            </>
          ) : screen === 'Plan Review' ? (
            !sessionReady ? <div className="loading" role="status">Preparing the planning workspace…</div> : <>
              {sessionError && <p className="notice" role="alert">Review availability could not be checked. Sample planning remains available. <button onClick={() => setSessionRetry(value => value + 1)}>Retry availability</button></p>}
              <PlanReview key={`${source?.reference?.object_id || 'sample'}:${datasetGeneration}`} initialPlan={cachedPlan} datasetLocked={!!openedPlan} recovery={reviewRecovery} scenarioDerived={scenarioDerivedActive} mutationPhase={mutationPhase} onReviewed={reviewPlan} uploaded={!!source} onReady={rememberPlan} onPlanInvalidated={invalidatePlan} onForecast={openForecast} onScenarios={(plan, nextSize) => openScenarios({ plan, size: nextSize })} onReturnToOriginalScenario={returnToOriginalScenario} onScenarioState={updateScenarioState} onRecovery={recordRecovery} onRecoveryClear={clearRecovery} onMutation={setMutationPhase}/>
            </>
          ) : (
            <Scenarios uploaded={!!source} firstSku={catalog?.products[0]?.sku || firstPlanForecast?.sku} firstStore={catalog?.locations[0]?.location_id || firstPlanForecast?.location_id} initial={scenarioInitial} onForecast={openForecast} onReview={plan => { if (mutationPending) return; setScenarioDerived({ reviewId: plan.review_id!, original: scenarioInitial }); setReviewRecovery(null); setOpenedPlan(plan); setScreen('Plan Review'); }}/>
          )}
          <footer>Independent Saudi retail planning example <span>Expected demand is a model estimate, not a service guarantee.</span></footer>
        </main>
      </div>
    </div>
  );
}
