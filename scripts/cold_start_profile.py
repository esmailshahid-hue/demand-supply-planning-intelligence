"""Measure production-style startup plus the first full request in fresh processes.

No health, fixture, or planning request is sent before the measured full plan.
The TCP readiness probe does not enter the ASGI application. Each process also
serves one ordinary repeat request so cache effects remain visible.
"""
import argparse
import http.client
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from time import perf_counter

from scripts.planning_smoke import stable_plan, validate_plan
from scripts.production_latency import server_timings


def available_port():
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        return listener.getsockname()[1]


def wait_until_listening(process, port, deadline):
    while perf_counter() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f'Application process exited with {process.returncode}')
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=.05):
                return
        except OSError:
            continue
    raise TimeoutError('Application did not begin listening within 30 seconds')


def request(connection):
    body = b'{"size":"full"}'
    started = perf_counter()
    connection.request('POST', '/api/plan/sample', body=body, headers={
        'Content-Type': 'application/json', 'Content-Length': str(len(body)),
    })
    response = connection.getresponse()
    first_byte = perf_counter()
    raw = response.read()
    finished = perf_counter()
    if response.status != 200:
        raise AssertionError(f'HTTP {response.status}: {raw[:500]!r}')
    value = json.loads(raw)
    validate_plan(value)
    return value, {
        'status': response.status,
        'first_byte_s': first_byte - started,
        'body_drain_s': finished - first_byte,
        'http_s': finished - started,
        'bytes': len(raw),
        'server_timings_ms': server_timings(response.getheader('Server-Timing')),
        'engine_ms': value['elapsed_ms'],
        'result_status': value['status'],
        'independent_replay': value['proposed']['replay']['feasible'],
        'stages': value['stages'],
    }


def one_process(index):
    port = available_port()
    environment = {**os.environ, 'VERCEL': '1'}
    command = [sys.executable, '-m', 'uvicorn', 'backend.app.main:app',
               '--host', '127.0.0.1', '--port', str(port), '--log-level', 'warning']
    launched = perf_counter()
    process = subprocess.Popen(command, cwd=Path(__file__).resolve().parents[1],
                               env=environment, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
    try:
        wait_until_listening(process, port, launched + 30)
        ready = perf_counter()
        connection = http.client.HTTPConnection('127.0.0.1', port, timeout=60)
        try:
            first_value, first = request(connection)
            repeat_value, repeat = request(connection)
        finally:
            connection.close()
        if stable_plan(first_value) != stable_plan(repeat_value):
            raise AssertionError('First and repeat plans differ')
        first['startup_s'] = ready - launched
        first['startup_plus_http_s'] = first['startup_s'] + first['http_s']
        return {'process': index, 'first': first, 'repeat': repeat,
                'signature': stable_plan(first_value)}
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runs', type=int, default=3)
    args = parser.parse_args()
    if args.runs < 3:
        parser.error('--runs must be at least 3')
    rows = []
    reference = None
    for index in range(1, args.runs + 1):
        row = one_process(index)
        signature = row.pop('signature')
        if reference is None:
            reference = signature
        elif signature != reference:
            raise AssertionError('Fresh-process plans differ')
        rows.append(row)
        print(json.dumps(row), flush=True)
    print(json.dumps({'runs': args.runs, 'fresh_process_determinism': 'matched',
        'startup_s': [row['first']['startup_s'] for row in rows],
        'first_http_s': [row['first']['http_s'] for row in rows],
        'repeat_http_s': [row['repeat']['http_s'] for row in rows]}), flush=True)


if __name__ == '__main__':
    main()
