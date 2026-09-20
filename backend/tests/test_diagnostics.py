from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.diagnostics import collect, measure

def test_timing_headers_are_opt_in_and_do_not_include_inputs(monkeypatch):
    with TestClient(app) as client:
        monkeypatch.delenv('PLANNING_DIAGNOSTICS',raising=False)
        assert 'server-timing' not in client.get('/api/health').headers
        monkeypatch.setenv('PLANNING_DIAGNOSTICS','1')
        response=client.get('/api/health?secret=not-a-metric')
        assert response.headers['server-timing'].startswith('response_ready;dur=')
        assert 'secret' not in response.headers['server-timing']
    with collect() as first:
        with measure('buffers'):pass
    with collect() as second:assert not second
    assert first['buffers']>=0
