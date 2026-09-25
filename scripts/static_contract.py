"""Shared public delivery contract; no application/dependency imports."""
from html.parser import HTMLParser
import json
import re

HASHED_ASSET = re.compile(r'^/assets/[\w.-]+-[\w-]{8,}\.(js|css)$')


class Assets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = []
        self.root = False

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        self.root |= tag == 'div' and attrs.get('id') == 'root'
        path = None
        if tag == 'script':
            path = attrs.get('src')
        elif tag == 'link' and attrs.get('rel') in ('stylesheet', 'modulepreload'):
            path = attrs.get('href')
        if path and path not in self.paths:
            self.paths.append(path)


def html_assets(raw):
    parser = Assets()
    parser.feed(raw.decode('utf-8'))
    assert parser.root, 'Missing application root marker'
    assert any(p.endswith('.js') for p in parser.paths), 'Missing hashed JavaScript'
    assert all(HASHED_ASSET.fullmatch(p) for p in parser.paths), 'Unexpected non-hashed or cross-origin asset'
    return parser.paths


def validate_content(path, headers, raw, *, cdn=False):
    """Assert bytes and MIME types, never use cache HIT/timing as a gate."""
    mime = headers.get('content-type', '').split(';')[0].strip().lower()
    assert raw.strip(), 'Empty response'
    assert not raw.lstrip().startswith(b'{"detail"'), 'FastAPI error response'
    cache = headers.get('cache-control', '').lower()
    if path in ('/', '/index.html'):
        assert mime == 'text/html', 'Expected HTML content type'
        assert 'immutable' not in cache, 'HTML must not be immutable'
        html_assets(raw)
    elif HASHED_ASSET.fullmatch(path):
        expected = ('text/javascript', 'application/javascript') if path.endswith('.js') else ('text/css',)
        assert mime in expected, 'Incorrect asset content type'
        assert not raw.lstrip().startswith((b'<', b'{"')), 'Asset is HTML/JSON error content'
        assert 'immutable' in cache and re.search(r'max-age=31536000(?:\D|$)', cache), 'Missing immutable asset cache policy'
    elif path == '/docs':
        assert mime == 'text/html' and b'swagger-ui' in raw, 'Missing API documentation'
    else:
        assert mime == 'application/json', 'Expected JSON content type'
        value = json.loads(raw)
        assert isinstance(value, dict), 'Expected JSON object'
        if path == '/api/health':
            assert value.get('status') == 'ok', 'Unhealthy API'
            assert value.get('engine_version') and value.get('schema_version'), 'Missing API versions'
            assert {'forecast', 'planning'} <= set(value.get('capabilities', [])), 'Missing API capabilities'
        elif path == '/openapi.json':
            assert value.get('openapi') and '/api/health' in value.get('paths', {}), 'Invalid OpenAPI schema'
        elif path == '/api/sample?size=fixture':
            assert value.get('dataset_id') == 'sample-v3-fixture-97', 'Unexpected dataset release'
    if cdn and (path in ('/', '/index.html') or HASHED_ASSET.fullmatch(path)):
        # Known application metrics are positive evidence that Python ran.
        from scripts.production_latency import server_timings
        assert not server_timings(headers.get('server-timing')), 'Static request reached Python'


def sanitized_excerpt(raw):
    text = raw[:2048].decode('utf-8', errors='replace')
    text = re.sub(r'<script\b.*?(?:</script>|$)', '[script omitted]', text, flags=re.I | re.S)
    text = re.sub(r'(?i)(token|secret|password|authorization|cookie)[\s"\x27:=]+[^\s,;}<]+', r'\1=[redacted]', text)
    text = re.sub(r'[A-Za-z0-9_./+=-]{32,}', '[redacted]', text)
    return re.sub(r'\s+', ' ', ''.join(c if c.isprintable() else ' ' for c in text))[:240]
