"""Behavioral frontend/API smoke; hosted mode also rejects Python static delivery."""
import argparse
from tempfile import TemporaryDirectory

from scripts import production_latency as latency
from scripts.static_contract import html_assets


def probe(url, local=False):
    latency.CANONICAL = url.rstrip('/')
    with TemporaryDirectory() as output:
        check = latency.Probe(output)
        shell = check.public_get('/', cdn=not local)
        cache = check.routes[-1]['cache_control'] or ''
        assert 'max-age=0' in cache and 'must-revalidate' in cache
        if not local:
            etag = check.routes[-1]['etag']
            assert etag, 'Static shell must expose a revalidation validator'
            check.public_get('/', expected_status=304, request_headers={'If-None-Match': etag})
        check.public_get('/index.html', cdn=not local)
        for asset in html_assets(shell):
            check.public_get(asset, cdn=not local)
            if not local:
                check.public_get(asset)
        for path in ('/api/health', '/docs', '/openapi.json', '/api/sample?size=fixture'):
            check.public_get(path, cdn=not local)
            if not local and path == '/api/health':
                assert check.routes[-1]['server_timings_ms'], 'API timing missing'
        for path in ('/api/not-a-route', '/assets/not-a-real-build.js', '/not-a-client-route'):
            check.public_get(path, expected_status=404)
        for row in check.routes:
            print(f'{row["url"]}: {row["status"]} {row["content_type"]}, {row["bytes"]} bytes, {row["http_s"]:.3f}s')
        print('Frontend, every referenced asset, API, docs and sample passed.')
        return check.routes


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--local', action='store_true', help='Local/Docker serve static files through FastAPI')
    args = parser.parse_args()
    probe(args.url, args.local)
