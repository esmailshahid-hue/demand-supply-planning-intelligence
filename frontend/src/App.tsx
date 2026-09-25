import { useCallback, useEffect, useState } from 'react';
import { api, number, setDatasetReference, type Catalog, type ForecastResult, type Size } from './api';
import type { components } from './contracts.generated';
import DataWorkspace from './DataWorkspace';
import Demand from './Demand';
import PlanReview from './PlanReview';
import Scenarios from './Scenarios';
import type { Detail, Plan } from './scenarioApi';
import type { ReviewMutationPhase, ReviewRecovery } from './reviewState';
import { useReviewState } from './useReviewState';

const screens = ['Plan Review', 'Demand Review', 'Scenarios', 'Data and Assumptions'] as const;
type Screen = typeof screens[number];
type PlanContext = { plan: Plan; size: Size };

export default function App() {
  const [screen, setScreen] = useState<Screen>('Plan Review');
  const [source, setSource] = useState<components['schemas']['ImportResult'] | null>(null);
  const [openedPlan, setOpenedPlan] = useState<Plan | null>(null);
  const [planContext, setPlanContext] = useState<PlanContext | null>(null);
  const [scenarioInitial, setScenarioInitial] = useState<PlanContext | null>(null);
  const [scenarioDerived, setScenarioDerived] = useState<{ reviewId: string; original: PlanContext | null } | null>(null);
  const [reviewRecovery, setReviewRecovery] = useState<ReviewRecovery | null>(null);
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
  const cachedPlan = openedPlan || planContext?.plan || null;
  const reviewState = useReviewState(cachedPlan, reviewRecovery, mutationPhase);

  const clearWorkflow = () => {
    setOpenedPlan(null);
    setPlanContext(null);
    setScenarioInitial(null);
    setScenarioDerived(null);
    setReviewRecovery(null);
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
    setDatasetGeneration(value => value + 1);
    setScreen('Plan Review');
  };

  const rememberPlan = useCallback((plan: Plan, nextSize: Size) => {
    setPlanContext({ plan, size: nextSize });
    setSize(nextSize);
  }, []);
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
  };

  const currentPlanBlocked = !!cachedPlan && reviewState.gate.blocked;
  const scenariosDisabled = mutationPending || !!scenarioDerived || currentPlanBlocked;
  const scenarioDerivedActive = !!scenarioDerived && (
    scenarioDerived.reviewId === (openedPlan?.review_id || planContext?.plan.review_id)
    || scenarioDerived.reviewId === reviewRecovery?.review.reference
  );
  const openScenarios = (context: PlanContext | null = planContext) => {
    if (mutationPending || scenarioDerived || (context && reviewState.gate.blocked)) return;
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
    setScreen('Scenarios');
  };
  const navigate = (name: Screen) => {
    if (mutationPending) return;
    if (name === 'Scenarios') openScenarios();
    else setScreen(name);
  };
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
                ? 'Return to the original baseline before starting another comparison.'
                : reviewState.gate.reason || 'Finish the current review before testing scenarios.'
              : undefined;
            return <button key={name} className={screen === name ? 'nav-item active' : 'nav-item'} aria-current={screen === name ? 'page' : undefined} disabled={disabled} title={title} onClick={() => navigate(name)}><span className="nav-number" aria-hidden="true">0{index + 1}</span>{name}</button>;
          })}
        </nav>
        <div className="sidebar-note">
          <p><span className="live-dot"/>{mutationPending ? 'Saving review' : source?.provenance?.source === 'portable' ? 'Portable snapshot' : source ? 'Uploaded dataset' : 'Synthetic data'}</p>
          <small>{mutationPending ? 'Navigation resumes once the change is saved.' : source ? 'Private temporary server processing.' : 'Independent example. No company-supplied data.'}</small>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar"><span>Planning workspace <span className="crumb">/ {screen}</span></span><span className="sample-label">{source?.provenance?.source === 'portable' ? 'PORTABLE SNAPSHOT' : source ? 'UPLOADED DATA' : 'SYNTHETIC DATA'} <span>· SAR · Riyadh</span></span></header>
        <main id="main-content" tabIndex={-1}>
          <div className="page-heading"><div><p className="eyebrow">Demand and supply planning</p><h1>{screen}</h1><p>{screen === 'Demand Review' ? 'Selected forecast method, its error history and data quality.' : screen === 'Plan Review' ? 'What to buy, where stock goes, and which demand remains uncovered.' : screen === 'Data and Assumptions' ? 'Datasets, limits and your own data.' : 'Test changes to demand, supply and funding.'}</p></div></div>
          {reviewState.error && <div role="alert" className="error"><p>Review status could not be loaded: {reviewState.error}</p><button disabled={mutationPending} onClick={reviewState.retry}>Retry review</button></div>}
          {screen === 'Data and Assumptions' ? (
            <DataWorkspace onUse={useData} onReset={resetData} onReopen={reopen} reconciliationReference={reviewRecovery?.review.reference || openedPlan?.review_id}/>
          ) : screen === 'Demand Review' && linkedForecast ? (
            <><section className="panel"><h2>Plan forecast · {linkedForecast.policy}</h2><p>Buffer {number(linkedForecast.policy_buffer.units)} units · {linkedForecast.policy_buffer.protection_days} days. Scenario changes apply to future demand only; the error history is unchanged.</p>{linkedForecast.adjustments.length > 0 && <details><summary>Dated scenario adjustments · {linkedForecast.adjustments.length}</summary>{linkedForecast.adjustments.map(adjustment => <p key={adjustment.day}>{adjustment.day}: {number(adjustment.original)} → {number(adjustment.adjusted)} units · {adjustment.reason}</p>)}</details>}<details><summary>Calculation details</summary><p>Scenario assumptions {linkedForecast.assumptions_hash}</p><p>Forecast version {linkedForecast.forecast_version}</p></details><button onClick={() => setLinkedForecast(null)}>Back to forecast controls</button></section><Demand result={linkedForecast.forecast}/></>
          ) : screen === 'Demand Review' ? (
            <>
              <p className="dataset-context">{catalog ? `Planning date ${catalog.as_of}` : catalogError ? 'Dataset unavailable. Retry or reopen your data.' : 'Loading dataset…'}</p>
              <section className="filters" aria-label="Sample controls">
                <label>Dataset<select value={source ? 'uploaded' : size} onChange={event => changeSize(event.target.value as Size)} disabled={!!source || mutationPending}>{source ? <option value="uploaded">{source.provenance?.source === 'portable' ? 'Portable snapshot' : 'Uploaded dataset'}</option> : <><option value="fixture">Small sample · 10 SKUs</option><option value="full">Full sample · 60 SKUs</option></>}</select></label>
                <label>Product<select value={sku} onChange={event => setSku(event.target.value)} disabled={!catalog || forecastBusy}>{catalog ? catalog.products.map(product => <option key={product.sku} value={product.sku}>{product.sku} · {product.name}</option>) : <option>Loading products…</option>}</select></label>
                <label>Store<select value={location} onChange={event => setLocation(event.target.value)} disabled={!catalog || forecastBusy}>{catalog ? catalog.locations.map(item => <option key={item.location_id} value={item.location_id}>{item.name}</option>) : <option>Loading stores…</option>}</select></label>
                <button className="primary-button" disabled={forecastBusy || mutationPending} onClick={() => { if (!mutationPending) setForecastRefresh(value => value + 1); }}>{forecastBusy ? 'Calculating…' : '↻ Recalculate forecast'}</button>
              </section>
              <div role="status" aria-live="polite">{forecastBusy && <div className="loading"><span className="spinner"/>Calculating the forecast and its error history…</div>}</div>
              {(forecastError || catalogError) && <div role="alert" className="error"><strong>Calculation unavailable</strong><p>{forecastError || catalogError}</p><button onClick={() => { setCatalog(null); setForecastRefresh(value => value + 1); }}>Try again</button></div>}
              {forecast && !forecastBusy && <Demand result={forecast}/>}
            </>
          ) : screen === 'Plan Review' ? (
            !sessionReady ? <div className="loading" role="status">Preparing the plan…</div> : <>
              {sessionError && <p className="notice" role="alert">Review availability could not be checked. Planning still works. <button onClick={() => setSessionRetry(value => value + 1)}>Retry</button></p>}
              <PlanReview key={`${source?.reference?.object_id || 'sample'}:${datasetGeneration}`} initialPlan={cachedPlan} datasetLocked={!!openedPlan} recovery={reviewRecovery} reviewState={reviewState} scenarioDerived={scenarioDerivedActive} mutationPhase={mutationPhase} onReviewed={reviewPlan} uploaded={!!source} onReady={rememberPlan} onPlanInvalidated={invalidatePlan} onForecast={openForecast} onScenarios={(plan, nextSize) => openScenarios({ plan, size: nextSize })} onReturnToOriginalScenario={returnToOriginalScenario} onRecovery={recordRecovery} onRecoveryClear={clearRecovery} onMutation={setMutationPhase}/>
            </>
          ) : currentPlanBlocked ? (
            <p role="status">{reviewState.gate.reason} Scenarios stay blocked until it is resolved.</p>
          ) : (
            <Scenarios uploaded={!!source} firstSku={catalog?.products[0]?.sku || firstPlanForecast?.sku} firstStore={catalog?.locations[0]?.location_id || firstPlanForecast?.location_id} initial={scenarioInitial} onForecast={openForecast} onReview={plan => { if (mutationPending) return; setScenarioDerived({ reviewId: plan.review_id!, original: scenarioInitial }); setReviewRecovery(null); setOpenedPlan(plan); setScreen('Plan Review'); }}/>
          )}
          <footer>Synthetic data. Suggested actions only; no orders are placed. <span>Expected demand is a model estimate, not a service guarantee.</span></footer>
        </main>
      </div>
    </div>
  );
}
