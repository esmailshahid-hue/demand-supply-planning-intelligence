import json
import tomllib
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import DIST, app


ROOT = Path(__file__).resolve().parents[2]


def test_public_shell_and_hashed_assets_have_safe_cache_policies():
    asset = next((DIST / 'assets').glob('index-*.js'))
    with TestClient(app) as client:
        shell = client.get('/')
        compiled = client.get(f'/assets/{asset.name}')

    assert shell.status_code == 200
    assert '<div id="root"></div>' in shell.text
    assert shell.headers['cache-control'] == 'public, max-age=0, must-revalidate'
    assert compiled.status_code == 200
    assert compiled.headers['cache-control'] == 'public, max-age=31536000, immutable'


def test_frontend_never_swallows_api_or_missing_asset_404s():
    with TestClient(app) as client:
        api_missing = client.get('/api/not-a-route', headers={'accept': 'text/html'})
        asset_missing = client.get('/assets/not-a-real-build.js', headers={'accept': 'text/html'})
        page_missing = client.get('/not-a-client-route', headers={'accept': 'text/html'})

    assert api_missing.status_code == 404
    assert api_missing.json() == {'detail': 'Not Found'}
    assert asset_missing.status_code == 404
    assert 'id="root"' not in asset_missing.text
    assert page_missing.status_code == 404
    assert 'id="root"' not in page_missing.text


def test_operational_and_documentation_routes_keep_priority():
    with TestClient(app) as client:
        health = client.get('/api/health')
        docs = client.get('/docs')
        schema = client.get('/openapi.json')

    assert health.status_code == 200
    assert health.json()['status'] == 'ok'
    assert docs.status_code == 200
    assert schema.status_code == 200
    assert '/api/health' in schema.json()['paths']


def test_vercel_only_promotes_declared_public_frontend_files():
    static = tomllib.loads((ROOT / 'pyproject.toml').read_text())['tool']['vercel']['fastapi']['static']
    config = json.loads((ROOT / 'vercel.json').read_text())

    assert static == {'cdn': True}
    assert config['functions']['app.py']['maxDuration'] == 60
    headers = {entry['source']: entry['headers'][0]['value'] for entry in config['headers']}
    assert headers['/assets/(.*)'].endswith('immutable')
    assert headers['/'] == 'public, max-age=0, must-revalidate'
