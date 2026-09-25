import json
from pathlib import Path
import tomllib

from fastapi.testclient import TestClient
import pytest

from backend.app.main import DIST, app
from scripts.static_contract import html_assets, validate_content

ROOT = Path(__file__).resolve().parents[2]


def test_public_shell_and_hashed_assets_have_safe_cache_policies():
    if not (DIST / 'index.html').exists():
        pytest.skip('compiled frontend is verified after the production build')
    with TestClient(app) as client:
        for path in ('/', '/index.html'):
            shell = client.get(path)
            assert shell.status_code == 200
            validate_content(path, shell.headers, shell.content)
            assert shell.headers['cache-control'] == 'public, max-age=0, must-revalidate'
            assets = html_assets(shell.content)
            assert any(p.endswith('.css') for p in assets)
            for asset in assets:
                compiled = client.get(asset)
                assert compiled.status_code == 200
                assert compiled.content == (DIST / asset.lstrip('/')).read_bytes()
                validate_content(asset, compiled.headers, compiled.content)


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
        for path in ('/api/health', '/docs', '/openapi.json'):
            response = client.get(path)
            assert response.status_code == 200
            validate_content(path, response.headers, response.content)


def test_vercel_only_promotes_declared_public_frontend_files():
    config = json.loads((ROOT / 'vercel.json').read_text())
    manifest = tomllib.loads((ROOT / 'pyproject.toml').read_text())
    assert manifest['project']['name'] and manifest['project']['version']
    pins = [line for line in (ROOT / 'requirements.txt').read_text().splitlines() if line and not line.startswith('#')]
    assert manifest['project']['dependencies'] == pins
    assert manifest['tool']['vercel']['fastapi']['static']['cdn'] is True
    assert config['buildCommand'].endswith('npm --prefix frontend run build:vercel')
    assert not config.get('rewrites')
    assert config['functions']['app.py']['maxDuration'] == 60
    headers = {entry['source']: entry['headers'][0]['value'] for entry in config['headers']}
    assert headers['/assets/(.*)'].endswith('immutable')
    assert headers['/'] == headers['/index.html'] == 'public, max-age=0, must-revalidate'


def test_vercel_public_artifact_is_only_the_compiled_frontend():
    if not (DIST / 'index.html').exists():
        pytest.skip('CDN artifact is verified after build:vercel')
    assets = html_assets((DIST / 'index.html').read_bytes())
    files = {p.relative_to(DIST).as_posix() for p in DIST.rglob('*') if p.is_file()}
    assert files == {'index.html', 'release.json'} | {p.lstrip('/') for p in assets}
    for path in assets:
        assert (DIST / path.lstrip('/')).stat().st_size > 0
    identity = json.loads((DIST / 'release.json').read_text())
    assert set(identity) == {'commit', 'deployment_host'}
