"""The profiler must invoke the production route with a real request context."""
from scripts import planning_profile as profile
from backend.app.data.storage import store


def test_profiler_route_accepts_fixture_and_full_without_creating_session_objects(monkeypatch):
    seen=[]
    marker=object()
    def calculate(data,issues=None,review=None):
        seen.append((len(data.products),issues,review))
        return marker
    monkeypatch.setattr(profile.api,'calculate_plan',calculate)
    before=set(store.records)
    assert profile.invoke_production_route('fixture') is marker
    assert profile.invoke_production_route('full') is marker
    assert [row[0] for row in seen]==[10,60]
    assert all(row[1] is not None and row[2] is None for row in seen)
    assert set(store.records)==before
