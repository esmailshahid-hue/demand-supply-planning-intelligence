from datetime import timedelta
import pytest
from backend.app.contracts import CandidateRecord, Event, WindowRecord
from backend.app.forecasting.engine import Series, forecast, midnight, pool_metrics, select_model


def metric(result, phase="selection", method="seasonal_naive", horizon=28):
    return next(m for r in getattr(result, phase) if r.method == method for m in r.metrics if m.horizon == horizon)


def test_methods_hand_calculated_and_calendar_weights(regular):
    origin = regular.settings.as_of
    rows = {r.day: r for r in regular.demand_history}
    for k, value in enumerate((40, 30, 20, 10), 1):
        rows[origin-timedelta(days=7*k)].sales_units = value
    predicted = Series(regular, "SKU001", "S1").predict_all(origin, 56)
    assert predicted["seasonal_naive"][0].forecast_units == 40
    assert predicted["weekday_mean"][0].forecast_units == 25
    assert predicted["weighted_weekday_mean"][0].forecast_units == pytest.approx(30)
    assert predicted["weighted_weekday_mean"][28].forecast_units == pytest.approx(30)
    rows[origin-timedelta(days=14)].sales_units = None
    predicted = Series(regular, "SKU001", "S1").predict_all(origin, 7)
    assert predicted["weighted_weekday_mean"][0].forecast_units == pytest.approx((40*.4+20*.2+10*.1)/.7)


def test_future_sales_and_late_reports_cannot_change_earlier_forecast(regular):
    origin = regular.settings.as_of-timedelta(days=100)
    before = Series(regular, "SKU001", "S1").predict_all(origin, 28)
    for row in regular.demand_history:
        if row.day >= origin:
            row.sales_units = 99999
    assert Series(regular, "SKU001", "S1").predict_all(origin, 28) == before
    late = next(r for r in regular.demand_history if r.day == origin-timedelta(days=7))
    late.available_at = midnight(origin+timedelta(days=1))
    baseline = Series(regular, "SKU001", "S1").predict_all(origin, 28)
    late.sales_units = 333333
    assert Series(regular, "SKU001", "S1").predict_all(origin, 28) == baseline


def test_final_holdout_does_not_select_model_or_buffer(regular):
    original = forecast(regular, "SKU001", "S1")
    cutoff = original.selection_cutoff
    for row in regular.demand_history:
        if row.day >= cutoff:
            row.sales_units = 1000
    changed = forecast(regular, "SKU001", "S1")
    assert changed.selection == original.selection
    assert changed.selected_method == original.selected_method
    assert changed.buffer == original.buffer
    assert changed.final_check != original.final_check
    assert changed.visible_units != original.visible_units  # honest refit after freezing selection
    assert all(w.origin + timedelta(days=28) <= cutoff for r in changed.selection for w in r.windows)


def test_delayed_selection_labels_are_not_known_at_selection_cutoff(regular):
    cutoff = regular.settings.as_of-timedelta(days=28)
    row = next(r for r in regular.demand_history if r.day == cutoff-timedelta(days=10))
    row.available_at = midnight(cutoff+timedelta(days=2))
    first = forecast(regular, "SKU001", "S1")
    row.sales_units = 9999
    second = forecast(regular, "SKU001", "S1")
    assert first.selection == second.selection


def test_censor_estimate_is_prior_only_and_never_scored(regular):
    origin = regular.settings.as_of
    censored = next(r for r in regular.demand_history if r.day == origin-timedelta(days=60))
    censored.sales_units = 2
    censored.stock_available = False
    for row in regular.demand_history:
        if row.day > censored.day:
            row.sales_units = 1000
    _, estimates, _ = Series(regular, "SKU001", "S1").training(origin)
    assert estimates[censored.day] == 10  # never 1000 from later observations
    result = forecast(regular, "SKU001", "S1")
    m = metric(result)
    assert m.excluded_by_reason["censored"] == 1
    w = next(w for w in result.selection[0].windows if w.horizon == 28 and w.origin <= censored.day < w.origin+timedelta(days=28))
    assert not w.complete
    assert w.valid_observations == 27
    assert w.underforecast_units is None


def test_missing_and_zero_sales_remain_distinct(regular):
    cutoff = regular.settings.as_of-timedelta(days=28)
    zero = next(r for r in regular.demand_history if r.day == cutoff-timedelta(days=5))
    missing = next(r for r in regular.demand_history if r.day == cutoff-timedelta(days=6))
    zero.sales_units = 0
    missing.sales_units = None
    series = Series(regular, "SKU001", "S1")
    assert series.status(zero.day, cutoff) == "observed"
    assert series.status(missing.day, cutoff) == "missing"
    m = metric(forecast(regular, "SKU001", "S1"))
    assert m.excluded_by_reason["missing"] == 1
    assert m.actual_units == (m.valid_observations-1)*10


def test_all_zero_has_no_percentage_accuracy(regular):
    for row in regular.demand_history:
        row.sales_units = 0
    result = forecast(regular, "SKU001", "S1")
    assert result.selected_method == "seasonal_naive"
    assert result.visible_units == 0
    assert metric(result).wape is None
    assert metric(result).signed_bias_pct is None
    assert metric(result).absolute_error == 0
    assert metric(result).mean_absolute_quantity_error == 0
    assert "zero" in result.selection_reason


def test_short_history_launch_and_no_evidence_fallback(dataset):
    result = forecast(dataset, "SKU007", "S1")
    assert result.status == "provisional"
    assert result.selected_method == "seasonal_naive"
    assert result.visible_units == 28*8
    assert metric(result).complete_windows == 0
    assert metric(result).mean_absolute_quantity_error is None
    assert all("launch" in p.fallback for p in result.forecast)
    assert result.buffer.method == "days_of_demand"
    dataset.demand_history = []
    result = forecast(dataset, "SKU001", "S1")
    assert result.status == "unavailable"
    assert result.visible_units is None
    assert result.buffer.method == "unavailable"
    assert all(p.forecast_units is None for p in result.forecast)


def test_short_history_without_launch_uses_labeled_observations(regular):
    regular.demand_history = regular.demand_history[-10:]
    result = forecast(regular, "SKU001", "S1")
    assert result.status == "provisional"
    assert result.selected_method == "seasonal_naive"
    assert result.visible_units == 280
    assert all(p.fallback for p in result.forecast)


def test_known_event_excluded_and_applied_once(regular):
    origin = regular.settings.as_of
    past = origin-timedelta(days=7)
    regular.events = [Event(event_id="PAST", scope="sku", scope_id="SKU001", start=past, end=past,
                            kind="uplift", value=2, reason="test", known_at=midnight(past-timedelta(days=1))),
                      Event(event_id="NEXT", scope="sku", scope_id="SKU001", start=origin, end=origin,
                            kind="uplift", value=2, reason="test", known_at=midnight(origin-timedelta(days=1)))]
    next(r for r in regular.demand_history if r.day == past).sales_units = 20
    p = Series(regular,"SKU001","S1").predict_all(origin,7)["weekday_mean"][0]
    assert p.baseline_units == 10
    assert p.forecast_units == 20
    assert p.event_id == "NEXT"
    regular.events[1].known_at = midnight(origin+timedelta(days=1))
    assert Series(regular,"SKU001","S1").predict_all(origin,7)["weekday_mean"][0].forecast_units == 10


def test_closed_unranged_and_missing_weekday(regular):
    origin = regular.settings.as_of
    for row in regular.demand_history:
        if row.day.weekday() == origin.weekday():
            row.sales_units = None
    p = Series(regular, "SKU001", "S1").predict_all(origin, 7)["seasonal_naive"][0]
    assert p.forecast_units == 10
    assert "Missing weekday" in p.fallback
    a = next(a for a in regular.assortment if a.sku == "SKU001" and a.location_id == "S1")
    a.ranged_to = origin
    p = Series(regular, "SKU001", "S1").predict_all(origin, 7)["seasonal_naive"][1]
    assert p.forecast_units == 0
    row = regular.demand_history[-10]
    row.is_open = False
    assert Series(regular,"SKU001","S1").status(row.day,origin) == "closed"


def fake_record(method, errors):
    from datetime import date
    windows = [WindowRecord(origin=date(2025,1,1)+timedelta(days=28*i), horizon=28, complete=True,
                            valid_observations=28, excluded_by_reason={}, actual_units=100,
                            forecast_units=100+e, absolute_error=abs(e), signed_error=e, underforecast_units=max(0,-e)) for i,e in enumerate(errors)]
    return CandidateRecord(method=method, windows=windows, metrics=[pool_metrics(windows,28)])


@pytest.mark.parametrize("errors,expected", [([9.5,-9.5,9.5,-9.5],"weekday_mean"), ([9.6,-9.6,9.6,-9.6],"seasonal_naive"), ([1,1,1,1],"seasonal_naive")])
def test_exact_selection_threshold_and_bias_guard(errors,expected):
    records = [fake_record("seasonal_naive",[10,-10,10,-10]), fake_record("weekday_mean",errors), fake_record("weighted_weekday_mean",[10,-10,10,-10])]
    assert select_model(records)[0] == expected


def test_requires_four_complete_windows_even_with_good_challenger():
    records = [fake_record("seasonal_naive",[10,-10,10]),fake_record("weekday_mean",[0,0,0])]
    assert select_model(records)[:2] == ("seasonal_naive","provisional")


def test_pool_wape_is_ratio_of_sums_not_mean_of_percentages():
    a = fake_record("seasonal_naive",[10]).windows[0]
    b = a.model_copy(update={"actual_units":1,"forecast_units":2,"absolute_error":1,"signed_error":1})
    metric = pool_metrics([a,b],28)
    assert metric.wape == pytest.approx(100*11/101)
    assert metric.wape != 55
    assert metric.signed_bias_units == 11


def test_runtime_budget_fails_without_partial_result(regular):
    with pytest.raises(TimeoutError):
        forecast(regular,"SKU001","S1",runtime_seconds=0)
