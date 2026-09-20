"""The manual probe can be tested without dependencies or production requests."""
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from threading import Thread
import unittest
from unittest.mock import patch

from scripts import production_latency as latency


def timing(path='/api/health', seconds=1, connections=1, status=200, exitcode=0):
    return {'http_code': status, 'exitcode': exitcode, 'time_namelookup': .01,
            'time_connect': .02 if connections else 0,
            'time_appconnect': .08 if connections else 0,
            'time_starttransfer': seconds - .1, 'time_total': seconds,
            'num_connects': connections, 'http_version': '2',
            'url_effective': latency.CANONICAL + path}


def curl_result(output, specs, records, bodies):
    for (name, _, _), body in zip(specs, bodies):
        (output / (name + '.body.json')).write_bytes(body)
        (output / (name + '.headers')).write_text('HTTP/2 200\nx-vercel-id: iad1::probe\n')
    return subprocess.CompletedProcess([], 0, '\n'.join(map(json.dumps, records)), '')


class ProductionLatencyTests(unittest.TestCase):
    def test_slow_first_is_retained_and_does_not_hide_repeat(self):
        with TemporaryDirectory() as root:
            probe = latency.Probe(root)
            specs = [('first', '/api/health', None), ('repeat', '/api/health', None)]
            response = curl_result(probe.output, specs,
                [timing(seconds=10), timing(seconds=.5, connections=0)], [b'{}', b'{}'])
            with patch.object(latency.subprocess, 'run', return_value=response):
                self.assertEqual(probe.batch(specs), [{}, {}])
            self.assertEqual(len(probe.rows), 2)
            self.assertEqual(probe.rows[0]['http_s'], 10)
            self.assertAlmostEqual(probe.rows[0]['body_drain_s'], .1)
            self.assertEqual(len(probe.failures), 1)
            self.assertIn('first ten-second', probe.failures[0])
            self.assertTrue(any(c['name'] == 'repeat ten-second HTTP gate' and c['passed'] for c in probe.checks))
            self.assertEqual(len(json.loads((probe.output / 'results.json').read_text())['measurements']), 2)

    def test_malformed_response_preserves_timings_and_continues(self):
        with TemporaryDirectory() as root:
            probe = latency.Probe(root)
            specs = [('bad', '/api/health', None), ('good', '/api/health', None)]
            response = curl_result(probe.output, specs,
                [timing(status=502), timing(connections=0)], [b'<html>failure</html>', b'{}'])
            with patch.object(latency.subprocess, 'run', return_value=response):
                self.assertEqual(probe.batch(specs), [None, {}])
            self.assertEqual(len(probe.rows), 2)
            self.assertEqual(probe.rows[0]['status'], 502)
            self.assertTrue(any('JSON response' in f for f in probe.failures))
            self.assertTrue(any('HTTP 200' in f for f in probe.failures))
            self.assertEqual((probe.output / 'bad.body.json').read_bytes(), b'<html>failure</html>')

    def test_failed_transport_size_and_unobserved_reuse_fail(self):
        with TemporaryDirectory() as root:
            probe = latency.Probe(root)
            specs = [('first', '/api/health', None), ('repeat', '/api/health', None)]
            response = curl_result(probe.output, specs,
                [timing(exitcode=28), timing(connections=1)], [b'{}', b'{}'])
            with patch.object(latency.subprocess, 'run', return_value=response), patch.object(latency, 'BYTE_LIMIT', 2):
                probe.batch(specs)
            self.assertTrue(any('transport' in f for f in probe.failures))
            self.assertTrue(any('payload limit' in f for f in probe.failures))
            self.assertTrue(any('repeat connection mode' in f for f in probe.failures))

    def test_missing_curl_measurements_cannot_pass(self):
        with TemporaryDirectory() as root:
            probe = latency.Probe(root)
            response = subprocess.CompletedProcess([], 2, '', 'invalid option')
            with patch.object(latency.subprocess, 'run', return_value=response):
                self.assertEqual(probe.batch([('health', '/api/health', None)]), [None])
            self.assertTrue(probe.failures)
            self.assertTrue((probe.output / 'health.stderr.log').exists())

    def test_financial_feasibility_and_fallback_assertions_are_not_replaced(self):
        # Exercise the existing acceptance function through the new compact gate.
        plan = {'proposed': {'replay': {'feasible': False, 'failures': []}}}
        with self.assertRaises(AssertionError):
            latency.validate_compact(plan, 'fixture')

    def test_money_and_complete_policy_drift_fail(self):
        ledger = {'feasible': True, 'failures': [], 'stock': [], 'service_groups': [],
                  'summary': {'commitments': 1, 'payments': 1, 'movement_expense': .5},
                  'payments': [{'kind': 'movement', 'amount': .5}, {'kind': 'purchase', 'amount': .5}],
                  'cash': [{'payment_headroom': 0, 'commitment_headroom': 0, 'transfer_headroom': 0}]}
        policy = {'purchases': [{'units': 1, 'value': 1}], 'movements': [{'units': 1}],
                  'replay': ledger, 'explanations': []}
        plan = {'status': 'feasible_fallback', 'failures': [], 'exceptions': [],
                'stages': [{'name': 'joint_model', 'status': 'not_attempted'},
                           {'name': 'independent_fallback', 'status': 'benchmark'}],
                'stock_detail': 'on_demand', 'stock_row_count': 2800,
                'forecasts': [{}] * 40, 'provenance': {'dataset_hash': 'test'},
                'proposed': deepcopy(policy), 'benchmark': deepcopy(policy), 'no_action': deepcopy(policy)}
        latency.validate_compact(plan, 'fixture')
        broken = deepcopy(plan)
        broken['proposed']['replay']['payments'][0]['amount'] = .6
        with self.assertRaises(AssertionError):
            latency.validate_compact(broken, 'fixture')
        complete = deepcopy(plan)
        complete['proposed']['replay']['stock'] = [{}] * 2800
        latency.validate_complete(plan, complete)
        for field in ('purchases', 'movements', 'explanations'):
            changed = deepcopy(plan)
            changed['proposed'][field].append({'unexpected': 'change'})
            with self.subTest(field=field), self.assertRaises(AssertionError):
                latency.validate_complete(changed, complete)

    def test_scoped_evidence_must_match_authoritative_replay_and_identity(self):
        stock = [{'sku': 'SKU001', 'day': i} for i in range(280)]
        cash = [{'payments': 25}]
        plan = {'input_hash': 'dataset', 'provenance': {'dataset_hash': 'dataset'},
                'proposed': {'purchases': [], 'movements': [], 'replay': {'cash': cash}}}
        complete = {'proposed': {'replay': {'stock': stock}}}
        capture = {'baseline': {'snapshot_id': 'snapshot'}, 'original': {'action_hash': 'actions'}}
        detail = {'feasible': True, 'failures': [], 'stock': stock, 'cash': cash,
                  'provenance': plan['provenance'], 'baseline_id': 'snapshot',
                  'action_hash': 'actions', 'assumptions_hash': 'dataset',
                  'forecast_version': 'forecast', 'purchases': [], 'movements': []}
        latency.validate_detail(plan, complete, capture, detail)
        for key, bad in [('stock', stock[:-1]), ('cash', []), ('provenance', {}),
                         ('baseline_id', 'stale'), ('action_hash', 'stale'),
                         ('assumptions_hash', 'stale'), ('forecast_version', '')]:
            with self.subTest(key=key), self.assertRaises(AssertionError):
                latency.validate_detail(plan, complete, capture, {**detail, key: bad})

    def test_real_curl_reuses_connection_and_preserves_post_bodies(self):
        received = []
        class Handler(BaseHTTPRequestHandler):
            protocol_version = 'HTTP/1.1'
            def do_POST(self):
                body = self.rfile.read(int(self.headers['Content-Length']))
                received.append((self.client_address, json.loads(body)))
                self.send_response(200)
                self.send_header('Content-Length', '2')
                self.end_headers()
                self.wfile.write(b'{}')
            def log_message(self, *args):
                pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        worker = Thread(target=server.serve_forever, daemon=True)
        worker.start()
        original = latency.curl_command
        def local_command(output, specs):
            return ['=http' if a == '=https' else a for a in original(output, specs)]
        try:
            with TemporaryDirectory() as root, \
                 patch.object(latency, 'CANONICAL', f'http://127.0.0.1:{server.server_port}'), \
                 patch.object(latency, 'curl_command', local_command):
                probe = latency.Probe(root)
                probe.batch([('first', '/api/plan/sample', {'size': 'fixture'}),
                             ('repeat', '/api/plan/sample', {'size': 'fixture'})])
                self.assertEqual(probe.failures, [])
                self.assertEqual([r['new_connections'] for r in probe.rows], [1, 0])
                self.assertEqual(received[0], received[1])
                self.assertEqual(received[0][1], {'size': 'fixture'})
        finally:
            server.shutdown()
            server.server_close()
            worker.join()


if __name__ == '__main__':
    unittest.main()
