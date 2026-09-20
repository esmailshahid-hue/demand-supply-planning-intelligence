"""Manual canonical-host probe. Standard library + curl; no deployment access.

Every curl process starts a fresh session. Its --next requests run serially and
can reuse that connection. No retries, redirects, parallelism or warm-up plans.
DNS/TCP/TLS are cumulative milestones; zero connection times on a reused socket
do not mean a new connection was free. A passed probe still needs deployment
identity and exact-deployment runtime-log correlation before release closure.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import subprocess
import traceback

from scripts.planning_smoke import stable_plan, validate_plan

CANONICAL = 'https://demand-supply-planning-intelligence.vercel.app'
HTTP_LIMIT = 10
BYTE_LIMIT = 4_500_000


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def require(condition, message):
    if not condition:
        raise AssertionError(message)


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

    def save(self):
        (self.output / 'results.json').write_text(json.dumps({
            'canonical_url': CANONICAL, 'measurements': self.rows,
            'checks': self.checks, 'failures': self.failures,
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
    probe.batch([('health', '/api/health', None)])
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('artifacts/production-latency'))
    probe = Probe(parser.parse_args().output)
    metadata = {'started_utc': utcnow(), 'canonical_url': CANONICAL,
                'python': platform.python_version(), 'platform': platform.platform(),
                'runner': {k: os.getenv(k) for k in ('GITHUB_SHA', 'GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT',
                    'GITHUB_REPOSITORY', 'RUNNER_OS', 'RUNNER_ARCH', 'RUNNER_ENVIRONMENT')},
                'note': 'Probe revision is not deployed revision. Correlate alias and runtime logs separately.'}
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
    print(json.dumps({'passed': not probe.failures, 'failures': probe.failures}, indent=2))
    raise SystemExit(bool(probe.failures))


if __name__ == '__main__':
    main()
