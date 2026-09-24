"""Read-only hosted CDN verification. Requires an explicit, already deployed URL.

First/repeat are measured requests, not a claim of forced process-cold starts.
Correlate source SHA and function logs separately before closing a release.
"""
import argparse
import json
import re
from time import perf_counter
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from scripts.production_latency import server_timings


def probe(url):
    rows = []

    def get(path, headers=None):
        start = perf_counter()
        try:
            response = urlopen(Request(url.rstrip('/')+path, headers=headers or {}), timeout=60)
        except HTTPError as error:
            response = error
        with response:
            body = response.read()
            row = dict(path=path, status=response.status, seconds=perf_counter()-start,
                       bytes=len(body), headers=dict(response.headers.items()))
        rows.append(row)
        print(json.dumps(row), flush=True)
        return response.status, response.headers, body

    status, headers, body = get('/')
    assert status == 200 and b'id="root"' in body
    assert not server_timings(headers.get('server-timing')), 'Root still invokes Python'
    assert 'max-age=0' in headers.get('cache-control', '') and 'must-revalidate' in headers.get('cache-control', '')
    asset = re.search(rb'src="(/assets/[^"?]+\.js)"', body)
    assert asset, 'Missing hashed JS'
    etag = headers.get('etag')
    assert etag, 'Static shell must expose a revalidation validator'
    status, headers, _ = get('/', {'If-None-Match': etag})
    assert status == 304 and not server_timings(headers.get('server-timing'))
    for _ in range(2):
        status, headers, body = get(asset.group(1).decode())
        assert status == 200 and body
        assert 'immutable' in headers.get('cache-control', '')
        assert not server_timings(headers.get('server-timing')), 'Asset still invokes Python'
    status, headers, _ = get('/api/health')
    assert status == 200 and server_timings(headers.get('server-timing')), 'API timing missing'
    for path in ('/docs', '/openapi.json'):
        assert get(path)[0] == 200
    for path in ('/api/not-a-route', '/assets/not-a-real-build.js', '/not-a-client-route'):
        status, _, body = get(path)
        assert status == 404 and b'id="root"' not in body
    print('Static/CDN routing probe passed; deployment identity, cold-load comparison and browser checks are separate gates.')
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    probe(parser.parse_args().url)
