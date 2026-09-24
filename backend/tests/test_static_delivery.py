import json
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from backend.app.main import DIST, app


ROOT = Path(__file__).resolve().parents[2]


def test_public_shell_and_hashed_assets_have_safe_cache_policies():
    asset = next((DIST / 'assets').glob('index-*.js'), None)
    if asset is None:
        pytest.skip('compiled frontend is verified after the production build')
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
    config = json.loads((ROOT / 'vercel.json').read_text())

    assert not (ROOT / 'pyproject.toml').exists()
    assert config['buildCommand'].endswith('npm --prefix frontend run build:vercel')
    assert config['rewrites'] == [{'source': '/', 'destination': '/index.html'}]
    scripts = json.loads((ROOT / 'frontend/package.json').read_text())['scripts']
    assert '--outDir ../public' in scripts['build:vercel']
    assert config['functions']['app.py']['maxDuration'] == 60
    headers = {entry['source']: entry['headers'][0]['value'] for entry in config['headers']}
    assert headers['/assets/(.*)'].endswith('immutable')
    assert headers['/'] == 'public, max-age=0, must-revalidate'


def test_vercel_public_artifact_is_only_the_compiled_frontend():
    public = ROOT / 'public'
    if not (public / 'index.html').exists():
        pytest.skip('CDN artifact is verified after build:vercel')
    files = {p.relative_to(public).as_posix() for p in public.rglob('*') if p.is_file()}
    assert files == {'index.html'} | {p for p in files if p.startswith('assets/index-') and p.endswith(('.js', '.css'))}
    assert (public / 'index.html').read_bytes() == (DIST / 'index.html').read_bytes()
    for path in files:
        assert (public / path).read_bytes() == (DIST / path).read_bytes()
