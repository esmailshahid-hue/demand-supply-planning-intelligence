from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.diagnostics import collect, measure, instrument_response_fields

def test_bounded_timing_headers_are_always_available_and_logs_are_opt_in(monkeypatch,caplog):
    with TestClient(app) as client:
        monkeypatch.delenv('PLANNING_DIAGNOSTICS',raising=False)
        response=client.get('/api/health?secret=not-a-metric')
        assert 'response_ready;dur=' in response.headers['server-timing']
        assert 'module_bootstrap;dur=' in response.headers['server-timing']
        assert 'secret' not in response.headers['server-timing']+caplog.text
        assert 'planning_request_complete' not in caplog.text
        monkeypatch.setenv('PLANNING_DIAGNOSTICS','1')
        response=client.get('/api/health?secret=not-a-metric')
        assert 'response_ready;dur=' in response.headers['server-timing']
        assert 'secret' not in response.headers['server-timing']
    with collect() as first:
        with measure('buffers'):pass
    with collect() as second:assert not second
    assert first['buffers']>=0


def test_actual_response_validation_and_serialization_are_timed(monkeypatch,caplog):
    monkeypatch.setenv('PLANNING_DIAGNOSTICS','1')
    instrument_response_fields(app)
    with TestClient(app) as client:
        response=client.post('/api/forecast/sample?private=never-log-this',json={'size':'fixture','sku':'SKU001','location_id':'S1'})
        assert response.status_code==200
        header=response.headers['server-timing']
        for phase in ('application_import','fastapi_setup','fastapi_startup','dataset_context',
                      'module_bootstrap','fastapi_construction','workflow_import','scenario_import',
                      'input_normalization','request_body','response_validation','response_serialization','response_ready'):
            assert phase+';dur=' in header
        assert response.json()['selected_method']=='weighted_weekday_mean'
        assert 'planning_request_complete' in caplog.text
        assert 'never-log-this' not in header+caplog.text
    with collect() as values:
        with measure('user-controlled-name'):pass
    assert not values
