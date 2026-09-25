"""Inspect real CLI-generated artifacts, never synthesize deployment output.

--prepare creates credential-free local project metadata only, for CI. It refuses
an existing project link and never contacts Vercel or pulls environment variables.
"""
import argparse
import json
from pathlib import Path
import re

from scripts.static_contract import html_assets, validate_content


def prepare(root):
    directory = root / '.vercel'
    directory.mkdir(exist_ok=True)
    project = directory / 'project.json'
    if project.exists():
        raise RuntimeError('Refusing to overwrite existing Vercel project metadata')
    project.write_text(json.dumps({
        'projectId': 'prj_local_static_regression', 'orgId': 'team_local_static_regression',
        'settings': {'framework': 'fastapi', 'buildCommand': None, 'installCommand': None,
                     'outputDirectory': None, 'devCommand': None, 'nodeVersion': '24.x'},
    }))
    (directory / 'empty-auth').mkdir(exist_ok=True)
    # CLI 60.0.1 gates the documented collector behind this platform capability.
    # This is a local test flag, not a production secret or project-setting change.
    (directory / '.env.preview.local').write_text('VERCEL_FASTAPI_STATIC_CDN=1\n')


def inspect(output):
    static = output / 'static'
    shell = (static / 'index.html').read_bytes()
    paths = ['/', '/index.html', *html_assets(shell), '/release.json']
    files = {p.relative_to(static).as_posix() for p in static.rglob('*') if p.is_file()}
    assert files == {p.lstrip('/') for p in paths if p != '/'}, 'Unexpected/missing CDN files'
    assert any(p.endswith('.css') for p in paths), 'Missing CSS'
    config = json.loads((output / 'config.json').read_text())
    assert config['version'] == 3
    routes = config['routes']
    before_files = []
    for route in routes:
        if 'handle' in route:
            break  # filesystem is implicit at the end of the initial routing phase
        before_files.append(route)
    for path in paths:
        headers = {}
        for route in before_files:
            if re.search(route.get('src', '(?!)'), path):
                assert route.get('continue'), f'{path} intercepted before static filesystem: {route}'
                headers.update({k.lower(): v for k, v in route.get('headers', {}).items()})
        mime = ('text/html' if path in ('/', '/index.html') else
                'text/javascript' if path.endswith('.js') else
                'text/css' if path.endswith('.css') else 'application/json')
        raw = (static / ('index.html' if path == '/' else path.lstrip('/'))).read_bytes()
        validate_content(path, {**headers, 'content-type': mime}, raw)
    function = output / 'functions' / 'fastapi.func' / '.vc-config.json'
    assert json.loads(function.read_text())['runtime'].startswith('python'), 'Missing Python function'
    for path, method in [('/api/health', 'GET'), ('/api/plan/sample', 'POST'),
                         ('/api/forecast/sample', 'POST'), ('/api/scenarios/detail', 'POST'),
                         ('/docs', 'GET'), ('/openapi.json', 'GET')]:
        matches = [r for r in before_files if not r.get('continue') and
                   method in r.get('methods', [method]) and re.search(r.get('src', '(?!)'), path)]
        assert matches and matches[0]['dest'] == '/fastapi', f'{method} {path} lacks API precedence'
    assert {'handle': 'rewrite'} in routes
    assert routes[-1]['dest'] == '/fastapi', 'Unmatched requests must retain FastAPI 404 behavior'
    assert not any(r.get('dest') == '/index.html' for r in routes), 'Unexpected SPA catch-all/rewrite'
    return {'passed': True, 'static_files': sorted(files), 'routes': routes,
            'note': 'Real build-output inspection; hosted CDN responses remain a separate gate.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--output', type=Path, default=Path('.vercel/output'))
    parser.add_argument('--evidence', type=Path)
    args = parser.parse_args()
    if args.prepare:
        prepare(Path.cwd())
        return
    result = inspect(args.output)
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
