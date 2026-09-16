import { useState } from 'react';
import { type ForecastResult, methodNames, number, percent, shortDate } from './api';

export default function Evaluation({ result }: { result: ForecastResult }) {
  const [phase, setPhase] = useState<'selection' | 'final_check'>('selection');
  const [horizon, setHorizon] = useState(28);
  const records = result[phase];
  const horizons = records[0].metrics.map(m => m.horizon);
  const selected = records.find(r => r.method === result.selected_method)!;
  return <section className="panel">
    <div className="section-heading"><div><p className="eyebrow">Evidence, before decisions</p><h2>How the methods compare</h2></div><div className="segmented" aria-label="Evaluation period">
      <button aria-pressed={phase === 'selection'} onClick={() => setPhase('selection')}>Model selection</button><button aria-pressed={phase === 'final_check'} onClick={() => setPhase('final_check')}>Held-out final check</button>
    </div></div>
    <div className="evaluation-intro"><p>{phase === 'selection' ? `Earlier rolling origins select the method. Evidence closes before ${shortDate(result.selection_cutoff)}.` : `The final 28 historical days test the frozen selection. These results do not choose the winner.`}</p>
      <label className="inline-label">Horizon <select value={horizon} onChange={e => setHorizon(Number(e.target.value))}>{horizons.map(h => <option key={h} value={h}>{h} days{h === result.buffer.protection_days ? ' · protection period' : ''}</option>)}</select></label></div>
    <div className="table-scroll"><table><caption className="sr-only">{phase === 'selection' ? 'Selection' : 'Final check'} metrics at {horizon} days</caption><thead><tr><th>Method</th><th>Quantity MAE¹</th><th>Quantity bias¹</th><th>Daily abs. error</th><th>Pooled WAPE</th><th>Signed bias²</th><th>Valid / possible</th><th>Complete windows</th></tr></thead><tbody>{records.map(record => {
      const m = record.metrics.find(metric => metric.horizon === horizon)!;
      return <tr key={record.method} className={record.method === result.selected_method ? 'selected-row' : ''}><th scope="row">{methodNames[record.method]}{record.method === result.selected_method && <span className="mini-tag">Selected</span>}{record.method === 'seasonal_naive' && <small>Baseline</small>}</th><td>{number(m.mean_absolute_quantity_error)}</td><td>{number(m.mean_quantity_bias)}</td><td>{number(m.absolute_error)}</td><td>{percent(m.wape)}</td><td>{percent(m.signed_bias_pct)}<small>{number(m.signed_bias_units)} units</small></td><td>{m.valid_observations} / {m.windows * m.horizon}<small>{m.excluded_observations} excluded</small></td><td>{m.complete_windows} / {m.windows}</td></tr>;
    })}</tbody></table></div>
    <p className="footnote">¹ Mean absolute error and mean signed bias of total quantities, using complete windows only. These are the selection criteria. ² Positive bias means overforecasting. WAPE pools absolute daily errors over observed units. Percentages are unavailable when observed demand totals zero.</p>
    <details><summary>Inspect origins and excluded coverage</summary><p className="muted">{result.evaluation_policy}</p><div className="table-scroll"><table><thead><tr><th>Forecast origin</th><th>Observed units</th><th>Forecast on scored days</th><th>Signed error</th><th>Coverage</th><th>Excluded reasons</th></tr></thead><tbody>{selected.windows.filter(w => w.horizon === horizon).map(w => <tr key={w.origin}><th scope="row">{w.origin}</th><td>{number(w.valid_observations ? w.actual_units : null)}</td><td>{number(w.valid_observations ? w.forecast_units : null)}</td><td>{number(w.valid_observations ? w.signed_error : null)}</td><td>{w.valid_observations}/{w.horizon}{w.complete ? '' : ' · partial'}</td><td>{Object.entries(w.excluded_by_reason).map(([reason, count]) => `${reason.replaceAll('_', ' ')}: ${count}`).join(', ') || 'None'}</td></tr>)}</tbody></table></div></details>
  </section>;
}
