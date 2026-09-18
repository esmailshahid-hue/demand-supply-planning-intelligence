"""Leakage-safe daily weekday forecasts and disjoint 28-day origin evaluation."""
from collections import Counter
from datetime import date, datetime, time, timedelta
from hashlib import sha256
from statistics import mean
from time import perf_counter
from uuid import uuid4
from zoneinfo import ZoneInfo

from backend.app.contracts import (
    BufferEvidence, CandidateRecord, Dataset, ForecastDay, ForecastResult,
    HistoryDay, Metrics, WindowRecord,
)
from backend.app.data.validation import event_matches

METHODS = ("seasonal_naive", "weekday_mean", "weighted_weekday_mean")
POLICY = ("Eight disjoint 28-day selection windows where history permits; at least four complete windows required. "
          "Final 28 days are held out. Selection scores use observations available before the holdout origin. "
          "Daily WAPE and signed bias use pooled uncensored units; quantity error uses complete windows only. "
          "Known event days are excluded from ordinary training pools. Positive bias is overforecasting.")


def midnight(day):
    return datetime.combine(day, time(), ZoneInfo("Asia/Riyadh"))


class Series:
    def __init__(self, data: Dataset, sku: str, location_id: str):
        self.data = data
        self.product = next(p for p in data.products if p.sku == sku)
        self.location = next(l for l in data.locations if l.location_id == location_id)
        self.assortment = next(a for a in data.assortment if a.sku == sku and a.location_id == location_id)
        self.rows = {r.day: r for r in data.demand_history if r.sku == sku and r.location_id == location_id}
        self.events = [e for e in data.events if event_matches(e, self.product, location_id)]
        self._ranged = {}
        self._events = {}
        self._statuses = {}
        self._training = {}

    def ranged(self, day):
        if day in self._ranged:
            return self._ranged[day]
        a, p = self.assortment, self.product
        value = (a.ranged_from <= day and (a.ranged_to is None or day <= a.ranged_to)
                 and p.active_from <= day and (p.active_to is None or day <= p.active_to))
        self._ranged[day] = value
        return value

    def event(self, day, origin):
        key = day, origin
        if key not in self._events:
            self._events[key] = next((e for e in self.events if e.start <= day <= e.end and e.known_at < midnight(origin)), None)
        return self._events[key]

    def status(self, day, knowledge_cutoff):
        key = day, knowledge_cutoff
        if key in self._statuses:
            return self._statuses[key]
        if not self.ranged(day):
            value = "unranged"
        elif (row := self.rows.get(day)) is not None and row.available_at < midnight(knowledge_cutoff):
            if not row.is_open:
                value = "closed"
            elif row.sales_units is None or row.stock_available is None:
                value = "missing"
            else:
                value = "observed" if row.stock_available else "censored"
        elif day.weekday() not in self.location.open_weekdays:
            value = "closed"
        else:
            value = "missing" if row is None else "not_yet_available"
        self._statuses[key] = value
        return value

    def training(self, origin):
        """Censored estimates use strictly earlier uncensored values, never later rows or estimates."""
        if origin in self._training:
            return self._training[origin]
        observed, values, estimates = {}, {}, {}
        for day in sorted(d for d in self.rows if d < origin):
            status = self.status(day, origin)
            if self.event(day, origin) is not None:
                continue
            if status == "observed":
                observed[day] = values[day] = self.rows[day].sales_units
            elif status == "censored":
                pool = [observed[d] for d in observed if day - timedelta(days=28) <= d < day and d.weekday() == day.weekday()]
                if pool:
                    estimate = max(self.rows[day].sales_units, mean(pool))
                    values[day] = estimates[day] = estimate
        self._training[origin] = values, estimates, observed
        return self._training[origin]

    def predict_all(self, origin, horizon):
        values, _, observed = self.training(origin)
        a = self.assortment
        launch = a.launch_daily_units if a.launch_known_at is not None and a.launch_known_at < midnight(origin) else None
        recent = [v for d, v in observed.items() if d >= origin - timedelta(days=28)]
        short = len(observed) < 28
        forecasts = {m: [] for m in METHODS}
        for i in range(horizon):
            day = origin + timedelta(days=i)
            # Fixed-origin multi-step forecasts repeat the most recent pre-origin weekday.
            anchor = origin - timedelta(days=(origin.weekday() - day.weekday()) % 7 or 7)
            candidates = [(values[d], weight) for k, weight in enumerate((.4, .3, .2, .1))
                          if (d := anchor - timedelta(days=7 * k)) in values]
            for method in METHODS:
                fallback = None
                if not self.ranged(day) or day.weekday() not in self.location.open_weekdays:
                    baseline = 0.0
                    fallback = "Closed or unranged: no demand planned"
                elif short and launch is not None:
                    baseline = launch
                    fallback = "Declared launch estimate: " + (a.launch_reason or "")
                elif candidates:
                    if method == "seasonal_naive":
                        baseline = candidates[0][0]
                    elif method == "weekday_mean":
                        baseline = mean(v for v, _ in candidates)
                    else:
                        baseline = sum(v * w for v, w in candidates) / sum(w for _, w in candidates)
                    if anchor not in values or len(candidates) < (1 if method == "seasonal_naive" else 4):
                        fallback = "Available same-weekday observations; incomplete four-week pool"
                    if short:
                        fallback = "Short history: available weekday evidence, provisional"
                elif recent:
                    baseline = mean(recent)
                    fallback = "Missing weekday: mean of prior 28 days' uncensored ordinary observations"
                elif launch is not None:
                    baseline = launch
                    fallback = "Declared launch estimate: " + (a.launch_reason or "")
                else:
                    baseline = None
                    fallback = "No eligible recent observations or declared launch estimate"
                event = self.event(day, origin) if self.ranged(day) and day.weekday() in self.location.open_weekdays else None
                revised = baseline
                if event is not None:
                    revised = event.value if event.kind == "replacement" else (baseline * event.value if baseline is not None else None)
                forecasts[method].append(ForecastDay(day=day, baseline_units=baseline, forecast_units=revised,
                    provisional_tail=i >= 28, fallback=fallback, event_id=event.event_id if event else None,
                    reason=event.reason if event else None))
        return forecasts


def score_window(series, origin, forecast, horizon, cutoff):
    excluded = Counter()
    actual = predicted = absolute = 0.0
    valid = 0
    for point in forecast[:horizon]:
        status = series.status(point.day, cutoff)
        if status != "observed":
            excluded[status] += 1
            continue
        if point.forecast_units is None:
            excluded["forecast_unavailable"] += 1
            continue
        y = series.rows[point.day].sales_units
        actual += y
        predicted += point.forecast_units
        absolute += abs(point.forecast_units - y)
        valid += 1
    signed = predicted - actual
    return WindowRecord(origin=origin, horizon=horizon, complete=valid == horizon,
        valid_observations=valid, excluded_by_reason=dict(excluded), actual_units=actual,
        forecast_units=predicted, absolute_error=absolute, signed_error=signed,
        underforecast_units=max(0.0, -signed) if valid == horizon else None)


def pool_metrics(windows, horizon):
    """Pool units, never average series or window percentages. Also usable for network aggregation."""
    rows = [w for w in windows if w.horizon == horizon]
    complete = [w for w in rows if w.complete]
    valid = sum(w.valid_observations for w in rows)
    actual = sum(w.actual_units for w in rows)
    absolute = sum(w.absolute_error for w in rows)
    signed = sum(w.signed_error for w in rows)
    excluded = Counter()
    for w in rows:
        excluded.update(w.excluded_by_reason)
    return Metrics(horizon=horizon, windows=len(rows), complete_windows=len(complete),
        valid_observations=valid, excluded_observations=sum(excluded.values()), excluded_by_reason=dict(excluded),
        absolute_error=absolute if valid else None, actual_units=actual,
        wape=100 * absolute / actual if actual else None,
        signed_bias_units=signed if valid else None, signed_bias_pct=100 * signed / actual if actual else None,
        mean_absolute_quantity_error=mean(abs(w.signed_error) for w in complete) if complete else None,
        mean_quantity_bias=mean(w.signed_error for w in complete) if complete else None)


def evaluate(series, origins, cutoff, deadline=None):
    horizons = sorted({7, 28, series.data.settings.protection_days})
    records = {m: [] for m in METHODS}
    for origin in origins:
        if deadline is not None and perf_counter() > deadline:
            raise TimeoutError("Forecast runtime budget exceeded")
        predicted = series.predict_all(origin, 28)
        for method in METHODS:
            for h in horizons:
                records[method].append(score_window(series, origin, predicted[method], h, cutoff))
    return [CandidateRecord(method=m, windows=records[m], metrics=[pool_metrics(records[m], h) for h in horizons]) for m in METHODS]


def select_model(records):
    baseline = records[0]
    base = next(m for m in baseline.metrics if m.horizon == 28)
    if base.complete_windows < 4:
        return METHODS[0], "provisional", "Fewer than four complete 28-day selection windows; retain seasonal naive provisionally.", None
    if base.mean_absolute_quantity_error == 0:
        return METHODS[0], "evaluated", "Baseline 28-day quantity error is zero; retain seasonal naive (no tie promotion).", None
    eligible = []
    # Use identical complete origins for comparisons, never a challenger's easier subset.
    base_origins = {w.origin for w in baseline.windows if w.horizon == 28 and w.complete}
    for record in records[1:]:
        metric = next(m for m in record.metrics if m.horizon == 28)
        origins = {w.origin for w in record.windows if w.horizon == 28 and w.complete}
        if origins != base_origins or metric.mean_absolute_quantity_error is None:
            continue
        improvement = 100 * (base.mean_absolute_quantity_error - metric.mean_absolute_quantity_error) / base.mean_absolute_quantity_error
        if improvement >= 5 - 1e-9 and abs(metric.mean_quantity_bias) <= abs(base.mean_quantity_bias) + 1e-9:
            eligible.append((metric.mean_absolute_quantity_error, METHODS.index(record.method), record.method, improvement))
    if eligible:
        _, _, method, improvement = min(eligible)
        return method, "evaluated", "Challenger improves mean absolute 28-day quantity error by at least 5% without worsening absolute quantity bias.", improvement
    return METHODS[0], "evaluated", "No challenger meets both the 5% quantity-error improvement and non-worsening absolute bias rule.", 0.0


def forecast(data: Dataset, sku: str, location_id: str, warnings=(), runtime_seconds=30):
    started = perf_counter()
    deadline = started + runtime_seconds
    series = Series(data, sku, location_id)
    as_of = data.settings.as_of
    cutoff = as_of - timedelta(days=28)
    start = as_of - timedelta(days=data.settings.history_days)
    origins = sorted(cutoff - timedelta(days=28 * k) for k in range(1, 9) if cutoff - timedelta(days=28 * k) >= start + timedelta(days=28))
    selection = evaluate(series, origins, cutoff, deadline)
    selected, status, reason, improvement = select_model(selection)
    final_check = evaluate(series, [cutoff] if cutoff >= start else [], as_of, deadline)
    predicted = series.predict_all(as_of, 56)[selected]
    _, estimates, observed = series.training(as_of)
    if len(observed) < 28:
        status = "provisional"
        reason += " Fewer than 28 uncensored ordinary observations; inspect the daily fallback labels."
    if any(p.forecast_units is None for p in predicted):
        status = "unavailable"
        reason += " Some future weekdays have no defensible estimate; no complete quantity is returned."
    if observed and all(v == 0 for v in observed.values()):
        reason += " All eligible observed demand is zero; ordinary baseline remains zero."
    elif observed and sum(v == 0 for v in observed.values()) / len(observed) >= .5:
        reason += " Intermittent series: no positive floor is imposed; weekday results may be zero."
    def total(points):
        return sum(p.forecast_units for p in points) if all(p.forecast_units is not None for p in points) else None
    chosen = next(r for r in selection if r.method == selected)
    errors = sorted(w.underforecast_units for w in chosen.windows if w.horizon == data.settings.protection_days and w.complete)
    if len(errors) >= 4:
        # Linear empirical percentile; no distributional/service guarantee.
        index = (len(errors) - 1) * data.settings.buffer_percentile / 100
        lo = int(index)
        units = errors[lo] + (errors[min(lo + 1, len(errors) - 1)] - errors[lo]) * (index - lo)
        buffer_method, fallback_days = "empirical_underforecast", None
    else:
        visible = total(predicted[:28])
        units = visible / 28 * data.settings.fallback_buffer_days if visible is not None else None
        buffer_method = "days_of_demand" if units is not None else "unavailable"
        fallback_days = data.settings.fallback_buffer_days
    history = []
    for i in range(56):
        day = as_of - timedelta(days=56 - i)
        state = series.status(day, as_of)
        row = series.rows.get(day)
        history.append(HistoryDay(day=day, observed_sales=row.sales_units if row and state in ("observed", "censored") else None,
            training_estimate=estimates.get(day), status=state))
    return ForecastResult(run_id=str(uuid4()), input_hash=sha256(data.model_dump_json().encode()).hexdigest(),
        dataset_id=data.dataset_id, synthetic=data.synthetic, as_of=as_of, sku=sku, product_name=series.product.name,
        location_id=location_id, location_name=series.location.name, selected_method=selected, status=status,
        selection_reason=reason, selection_cutoff=cutoff, improvement_pct=improvement, selection=selection,
        final_check=final_check, forecast=predicted, history=history, visible_units=total(predicted[:28]), tail_units=total(predicted[28:]),
        buffer=BufferEvidence(units=units, method=buffer_method, protection_days=data.settings.protection_days,
            percentile=data.settings.buffer_percentile, sample_count=len(errors), fallback_days=fallback_days,
            note="Selection-period cumulative underforecast errors only. Percentile is not a guaranteed fill rate; no DC buffer is added."),
        warnings=list(warnings), elapsed_ms=(perf_counter() - started) * 1000, evaluation_policy=POLICY)
