"""Manual canonical-host probe. Standard library + curl; no deployment access.

Every curl process starts a fresh session. Its --next requests run serially and
can reuse that connection. No retries, redirects, parallelism or warm-up plans.
DNS/TCP/TLS are cumulative milestones; zero connection times on a reused socket
do not mean a new connection was free. Public-route and build-identity gates run
first; the manual workflow adds desktop/mobile browser evidence afterward.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import traceback
from time import perf_counter
from urllib.error import HTTPError
from urllib.request import Request, build_opener, HTTPRedirectHandler

from scripts.planning_smoke import stable_plan, validate_plan
from scripts.static_contract import html_assets, sanitized_excerpt, validate_content

CANONICAL = 'https://demand-supply-planning-intelligence.vercel.app'
HTTP_LIMIT = 10
BYTE_LIMIT = 4_500_000
SERVER_TIMING_PHASES = frozenset({
    'application_import', 'benchmark', 'buffers', 'dataset_context',
    'dataset_validation', 'explanations', 'fastapi_construction',
    'fastapi_setup', 'fastapi_startup', 'forecast_contract',
    'forecast_identity', 'forecast_reuse', 'independent_replay',
    'input_normalization', 'module_bootstrap', 'network_forecast',
    'planning', 'protection_paths', 'request_body', 'request_validation',
    'response_construction', 'response_ready', 'response_serialization',
    'response_validation', 'review_attachment', 'route',
    'sample_construction', 'sample_input', 'scenario_import',
    'series_forecast', 'workflow_import',
})


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def server_timings(header):
    """Parse our bounded Server-Timing metrics without accepting dynamic names."""
    values = {}
    for metric in (header or '').split(','):
        parts = [part.strip() for part in metric.split(';')]
        if not parts or parts[0] not in SERVER_TIMING_PHASES:
            continue
        duration = next((part[4:] for part in parts[1:] if part.startswith('dur=')), None)
        try:
            values[parts[0]] = float(duration) if duration is not None else None
        except ValueError:
            values[parts[0]] = None
    return values


def curl_command(output, specs):
    # Disabling curlrc prevents local defaults from adding retries or redirects.
    command = ['curl', '--disable']
    for index, (name, path, body) in enumerate(specs):
        if index:
            command.append('--next')
        command += ['--silent', '--show-error', '--max-time', '60',
                    '--connect-timeout', '25', '--proto', '=https',
                    '--dump-header', str(output / (name + '.headers')),
                    '--output', str(output / (name + '.body.json')),
                    '--write-out', '%{json}\n']
        if body is not None:
            source = output / (name + '.request.json')
            source.write_text(json.dumps(body))
            command += ['--header', 'Content-Type: application/json',
                        '--data-binary', '@' + str(source)]
        command.append(CANONICAL + path)
    return command


def measurement(name, path, timing, headers, raw, value, started, session, index):
    policy = value.get('proposed') or value.get('original') or {}
    return {
        'name': name, 'path': path, 'batch_started_utc': started,
        'session': session, 'session_request': index + 1,
        'status': timing['http_code'], 'curl_exit_code': timing['exitcode'],
        'dns_s': timing['time_namelookup'], 'tcp_ready_s': timing['time_connect'],
        'tls_ready_s': timing['time_appconnect'],
        'first_byte_s': timing['time_starttransfer'],
        'body_drain_s': timing['time_total'] - timing['time_starttransfer'],
        'http_s': timing['time_total'], 'bytes': len(raw),
        'new_connections': timing['num_connects'],
        'http_version': timing['http_version'], 'remote_ip': timing.get('remote_ip'),
        'vercel_id': headers.get('x-vercel-id'),
        'server_timing': headers.get('server-timing'),
        'server_timings_ms': server_timings(headers.get('server-timing')),
        'engine_ms': value.get('elapsed_ms'),
        'result_status': value.get('status', policy.get('status')),
        'stages': value.get('stages', policy.get('stages')),
        'independent_replay': policy.get('replay', {}).get('feasible',
                                    policy.get('feasible', value.get('feasible'))),
    }


class Probe:
    def __init__(self, output):
        self.output = Path(output)
        self.output.mkdir(parents=True, exist_ok=True)
        self.rows, self.checks, self.failures = [], [], []
        self.routes = []
        self.deployment = {}

    def save(self):
        (self.output / 'results.json').write_text(json.dumps({
            'canonical_url': CANONICAL, 'measurements': self.rows,
            'checks': self.checks, 'failures': self.failures,
            'public_routes': self.routes, 'deployment': self.deployment,
        }, indent=2))

    def check(self, name, operation):
        try:
            operation()
        except Exception as error:
            self.failures.append(f'{name}: {type(error).__name__}: {error}')
            self.checks.append({'name': name, 'passed': False})
            # These are public synthetic inputs, no private sessions or tokens.
            with (self.output / 'errors.log').open('a') as log:
                traceback.print_exc(file=log)
            self.save()
            return False
        self.checks.append({'name': name, 'passed': True})
        self.save()
        return True

    def batch(self, specs):
        session = specs[0][0]
        started = utcnow()
        command = curl_command(self.output, specs)
        # Individual curl transfers are bounded, and subprocess errors remain
        # failures. Raw responses/headers survive timeout or JSON parse failures.
        run = subprocess.run(command, capture_output=True, text=True,
                             timeout=65 * len(specs) + 5)
        (self.output / (session + '.curl.jsonl')).write_text(run.stdout)
        (self.output / (session + '.stderr.log')).write_text(run.stderr)
        records = run.stdout.splitlines()
        self.check(session + ' curl process', lambda: require(
            run.returncode == 0, f'curl exited {run.returncode}: {run.stderr}'))
        self.check(session + ' measurement count', lambda: require(
            len(records) == len(specs), 'Missing or extra curl write-out records'))
        values = []
        for index, (name, path, _) in enumerate(specs):
            value = None
            try:
                timing = json.loads(records[index])
                raw = (self.output / (name + '.body.json')).read_bytes()
                headers = {}
                for line in (self.output / (name + '.headers')).read_text().splitlines():
                    if ':' in line:
                        key, text = line.split(':', 1)
                        headers[key.lower()] = text.strip()
                # Preserve timings even when the response is not valid JSON.
                row = measurement(name, path, timing, headers, raw, {}, started, session, index)
                self.rows.append(row)
                self.save()
                def decode():
                    nonlocal value
                    value = json.loads(raw)
                    require(isinstance(value, dict), 'Expected an object response')
                decoded = self.check(name + ' JSON response', decode)
                if decoded:
                    row.update(measurement(name, path, timing, headers, raw, value, started, session, index))
                else:
                    value = None
                print(json.dumps(row), flush=True)
                self.check(name + ' HTTP 200', lambda: require(row['status'] == 200, str(row['status'])))
                self.check(name + ' transport', lambda: require(row['curl_exit_code'] == 0, str(row['curl_exit_code'])))
                self.check(name + ' ten-second HTTP gate', lambda: require(row['http_s'] < HTTP_LIMIT, str(row['http_s'])))
                self.check(name + ' payload limit', lambda: require(row['bytes'] < BYTE_LIMIT, str(row['bytes'])))
                self.check(name + ' canonical URL', lambda: require(
                    timing['url_effective'] == CANONICAL + path, timing['url_effective']))
                self.check(name + ' connection mode', lambda: require(
                    row['new_connections'] == (1 if index == 0 else 0),
                    'Fresh first connection / reused repeat connection was not observed'))
            except Exception as error:
                self.failures.append(f'{name}: request/measurement error: {type(error).__name__}: {error}')
                with (self.output / 'errors.log').open('a') as log:
                    traceback.print_exc(file=log)
            self.save()
            values.append(value)
        return values

    def public_get(self, path, *, cdn=True, expected_status=200, request_headers=None):
        """Fail on the first broken route; keep only bounded public evidence."""
        class NoRedirect(HTTPRedirectHandler):
            def redirect_request(self, *args, **kwargs):
                return None
        url = CANONICAL + path
        row = {'url': url, 'status': 0, 'content_type': '', 'passed': False}
        raw = b''
        started = perf_counter()
        try:
            try:
                response = build_opener(NoRedirect).open(Request(url, headers=request_headers or {}), timeout=60)
            except HTTPError as error:
                response = error
            with response:
                raw = response.read(BYTE_LIMIT + 1)
                headers = {k.lower(): v for k, v in response.headers.items()}
                row.update(status=response.status, content_type=headers.get('content-type', ''),
                           cache_control=headers.get('cache-control'), vercel_id=headers.get('x-vercel-id'),
                           etag=headers.get('etag'), bytes=len(raw),
                           server_timings_ms=server_timings(headers.get('server-timing')))
            require(row['status'] == expected_status, f'Expected HTTP {expected_status}')
            require(len(raw) <= BYTE_LIMIT, 'Public response exceeds bounded size')
            if expected_status == 200:
                validate_content(path, headers, raw, cdn=cdn)
            elif expected_status == 404:
                require(b'id="root"' not in raw, 'Missing route swallowed by frontend')
                if path.startswith('/api/'):
                    require(json.loads(raw) == {'detail': 'Not Found'}, 'API 404 shadowed')
            elif expected_status == 304:
                require(not raw and not server_timings(headers.get('server-timing')),
                        'Conditional static response reached Python or has a body')
            row['passed'] = True
            return raw
        except Exception as error:
            row['excerpt'] = sanitized_excerpt(raw)
            row['error'] = str(error) if isinstance(error, AssertionError) else type(error).__name__
            raise AssertionError(f"{url}: status={row['status']} content-type={row['content_type']!r}; "
                                 f"{row['error']}; excerpt={row['excerpt']!r}") from None
        finally:
            row['http_s'] = perf_counter() - started
            self.routes.append(row)
            self.save()

    def preflight(self):
        shell = self.public_get('/')
        for path in html_assets(shell):
            self.public_get(path)
        self.public_get('/index.html')
        for path in ('/api/health', '/docs', '/openapi.json', '/api/sample?size=fixture'):
            self.public_get(path)
        identity = json.loads(self.public_get('/release.json'))
        require(re.fullmatch(r'[a-f0-9]{40}', identity.get('commit') or '') is not None,
                'Invalid build-time commit evidence')
        require(re.fullmatch(r'[a-z0-9-]+\.vercel\.app', identity.get('deployment_host') or '') is not None,
                'Missing build-time immutable deployment hostname')
        self.deployment = {key: identity[key] for key in ('commit', 'deployment_host')}
        require(self.deployment.get('commit') == os.environ.get('GITHUB_SHA') and
                bool(self.deployment.get('commit')), 'Canonical deployed commit differs from workflow checkout')
        self.save()

    def summary(self):
        def result(paths, count=None):
            rows = [r for r in self.routes if paths(r['url'].removeprefix(CANONICAL))]
            return 'PASS' if rows and (count is None or len(rows) == count) and all(r['passed'] for r in rows) else 'FAIL / not reached'
        lines = ['## Canonical production verification', f'Host: {CANONICAL}',
                 f'Probe commit: {os.getenv("GITHUB_SHA", "local")}',
                 f'Deployed commit: {self.deployment.get("commit", "not verified")}',
                 f'Deployment host: {self.deployment.get("deployment_host", "not verified")}',
                 f'Frontend: {result(lambda p: p in ("/", "/index.html"), 2)}',
                 f'Assets: {result(lambda p: p.startswith("/assets/"))}',
                 f'API/docs/sample: {result(lambda p: p.startswith("/api/") or p in ("/docs", "/openapi.json"), 4)}', '',
                 '| Probe | HTTP seconds | Bytes | Status | Replay |',
                 '|---|---:|---:|---:|---|']
        for row in self.rows:
            lines.append(f'| {row["name"]} | {row["http_s"]:.3f} | {row["bytes"]} | {row["status"]} | {row["independent_replay"]} |')
        lines.extend(['', 'Public route timings (availability/content gates; no CDN timing threshold):'])
        lines.extend(f'- {r["url"]}: {r["status"]}, {r["http_s"]:.3f}s' for r in self.routes)
        lines.extend(['', f'Latency/check failures: {len(self.failures)}'])
        lines.extend('- ' + sanitized_excerpt(f.encode()).replace('`', '') for f in self.failures)
        return '\n\n'.join(lines[:8]) + '\n' + '\n'.join(lines[8:]) + '\n'


def validate_compact(plan, size):
    validate_plan(plan)
    count = 40 if size == 'fixture' else 240
    require(len(plan['forecasts']) == count, 'Forecast dimensions changed')
    require(plan['stock_detail'] == 'on_demand', 'Expected compact response')
    require(plan['stock_row_count'] == 56 * (count + count // 4), 'Stock dimensions changed')
    require(all(not plan[k]['replay']['stock'] for k in ('proposed', 'benchmark', 'no_action')),
            'Daily stock duplicated in compact response')


def validate_complete(compact, complete):
    validate_plan(complete)
    require(len(complete['proposed']['replay']['stock']) == compact['stock_row_count'],
            'Incomplete authoritative stock ledger')
    expected = deepcopy(stable_plan(complete))
    for name in ('proposed', 'benchmark', 'no_action'):
        expected[name]['replay']['stock'] = []
    require(stable_plan(compact) == expected, 'Compact/complete policy differs')
    require(compact['provenance'] == complete['provenance'], 'Complete provenance differs')


def validate_capture(plan, capture):
    original = capture['original']
    require(original['feasible'] and not original['failures'], 'Capture replay failed')
    require(capture['baseline']['dataset_hash'] == plan['input_hash'], 'Capture dataset mismatch')
    require(capture['baseline']['provenance'] == plan['provenance'], 'Capture provenance mismatch')
    for key in ('purchases', 'movements'):
        require(original[key] == plan['proposed'][key], 'Capture actions differ')
    for key in ('summary', 'cash'):
        require(original[key] == plan['proposed']['replay'][key], 'Capture ledger differs')
    require('stock' not in original, 'Capture duplicates daily stock')


def validate_detail(plan, complete, capture, detail):
    require(detail['feasible'] and not detail['failures'], 'Detail replay failed')
    stock = [r for r in complete['proposed']['replay']['stock'] if r['sku'] == 'SKU001']
    require(len(stock) == 280 and detail['stock'] == stock, 'Scoped stock mismatch')
    require(detail['cash'] == plan['proposed']['replay']['cash'], 'Scoped cash mismatch')
    require(detail['provenance'] == plan['provenance'], 'Scoped provenance mismatch')
    require(detail['baseline_id'] == capture['baseline']['snapshot_id'], 'Baseline identity mismatch')
    require(detail['action_hash'] == capture['original']['action_hash'], 'Action identity mismatch')
    require(detail['assumptions_hash'] == plan['input_hash'], 'Dataset identity mismatch')
    require(bool(detail['forecast_version']), 'Missing forecast identity')
    for key in ('purchases', 'movements'):
        require(detail[key] == [a for a in plan['proposed'][key] if a['sku'] == 'SKU001'],
                'Scoped actions differ')


def run_sequence(probe):
    probe.preflight()
    plans = {}
    for size in ('fixture', 'full'):
        first, repeat = probe.batch([
            (size + '-first', '/api/plan/sample', {'size': size}),
            (size + '-repeat', '/api/plan/sample', {'size': size}),
        ])
        for label, plan in (('first', first), ('repeat', repeat)):
            probe.check(size + ' ' + label + ' replay/finance/dimensions',
                        lambda: validate_compact(plan, size))
        probe.check(size + ' actions/totals/explanations deterministic', lambda: require(
            stable_plan(first) == stable_plan(repeat), 'Repeated policy differs'))
        plans[size] = repeat
    plan = plans['full']
    # Missing/malformed responses fail explicitly; dependent requests cannot use
    # fabricated actions. The top-level handler persists their traceback.
    actions = plan['proposed']
    body = {'size': 'full', 'dataset_hash': plan['input_hash'],
            'purchases': actions['purchases'], 'movements': actions['movements']}
    captures = probe.batch([('capture-first', '/api/scenarios/capture', body),
                            ('capture-repeat', '/api/scenarios/capture', body)])
    for capture in captures:
        probe.check('capture independent replay and reconciliation', lambda: validate_capture(plan, capture))
    capture = captures[0]
    probe.check('capture repeat determinism', lambda: require(
        {k: captures[0][k] for k in ('baseline', 'original')} ==
        {k: captures[1][k] for k in ('baseline', 'original')}, 'Capture changed'))
    body = {'baseline': capture['baseline'], 'policy': 'original', 'sku': 'SKU001',
            'location_id': 'S1', 'expected_action_hash': capture['original']['action_hash']}
    details = probe.batch([('detail-first', '/api/scenarios/detail', body),
                           ('detail-repeat', '/api/scenarios/detail', body)])
    # Separate authoritative calculation, after the first/repeat measurements.
    for size in ('fixture', 'full'):
        complete = probe.batch([(size + '-complete', '/api/plan/sample?include_stock=true', {'size': size})])[0]
        probe.check(size + ' compact/complete equality', lambda: validate_complete(plans[size], complete))
        if size == 'full':
            for detail in details:
                probe.check('scoped stock/cash/provenance equality', lambda: validate_detail(plan, complete, capture, detail))
    keys = ('stock', 'cash', 'payments', 'purchases', 'movements', 'baseline_id',
            'scenario_hash', 'action_hash', 'forecast_version', 'provenance')
    probe.check('detail repeat determinism', lambda: require(
        {k: details[0][k] for k in keys} == {k: details[1][k] for k in keys}, 'Scoped evidence changed'))
    require(json.loads(probe.public_get('/release.json')) == probe.deployment,
            'Canonical deployment changed during serial verification')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('artifacts/production-latency'))
    probe = Probe(parser.parse_args().output)
    metadata = {'started_utc': utcnow(), 'canonical_url': CANONICAL,
                'python': platform.python_version(), 'platform': platform.platform(),
                'runner': {k: os.getenv(k) for k in ('GITHUB_SHA', 'GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT',
                    'GITHUB_REPOSITORY', 'RUNNER_OS', 'RUNNER_ARCH', 'RUNNER_ENVIRONMENT')},
                'note': 'Build-time release.json binds canonical frontend to commit and immutable deployment host.'}
    (probe.output / 'environment.json').write_text(json.dumps(metadata, indent=2))
    probe.save()
    try:
        metadata['curl'] = subprocess.check_output(['curl', '--version'], text=True)
        run_sequence(probe)
    except Exception as error:
        probe.failures.append(f'Probe/dependent requests failed: {type(error).__name__}: {error}')
        with (probe.output / 'errors.log').open('a') as log:
            traceback.print_exc(file=log)
    metadata['ended_utc'] = utcnow()
    (probe.output / 'environment.json').write_text(json.dumps(metadata, indent=2))
    probe.save()
    (probe.output / 'summary.md').write_text(probe.summary())
    print(json.dumps({'passed': not probe.failures, 'failures': probe.failures}, indent=2))
    raise SystemExit(bool(probe.failures))


if __name__ == '__main__':
    main()
