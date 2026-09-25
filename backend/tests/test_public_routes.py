"""Deployment preflight regressions; no network or production access."""
import io
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts import production_latency as latency
from scripts.static_contract import html_assets, sanitized_excerpt

SHELL = b'<html><div id="root"></div><script src="/assets/index-abcdefgh.js"></script><link rel="stylesheet" href="/assets/index-abcdefgh.css"></html>'
SHA = 'a' * 40


class Response(io.BytesIO):
    def __init__(self, body, mime, status=200, cache='', timing=''):
        super().__init__(body)
        self.status = status
        self.headers = {'content-type': mime, 'cache-control': cache, 'server-timing': timing}


def responses():
    return [Response(SHELL, 'text/html'),
            Response(b'console.log("application")', 'text/javascript', cache='public, max-age=31536000, immutable'),
            Response(b'body{color:black}', 'text/css', cache='public, max-age=31536000, immutable'),
            Response(SHELL, 'text/html'),
            Response(b'{"status":"ok","engine_version":"v1","schema_version":"v1","capabilities":["forecast","planning"]}', 'application/json'),
            Response(b'<html>swagger-ui</html>', 'text/html'),
            Response(b'{"openapi":"3.1.0","paths":{"/api/health":{}}}', 'application/json'),
            Response(b'{"dataset_id":"sample-v3-fixture-97"}', 'application/json'),
            Response(json.dumps({'commit': SHA, 'deployment_host': 'build-123.vercel.app'}).encode(), 'application/json')]


class PublicRoutesTests(unittest.TestCase):
    def test_all_referenced_assets_and_operational_routes_checked(self):
        with TemporaryDirectory() as root, patch.object(latency, 'build_opener') as opener, patch.dict(os.environ, GITHUB_SHA=SHA):
            opener.return_value.open.side_effect = responses()
            probe = latency.Probe(root)
            probe.preflight()
            self.assertEqual(len(probe.routes), 9)
            self.assertTrue(all(r['passed'] for r in probe.routes))
            self.assertEqual(probe.deployment['commit'], SHA)
            self.assertIn('Frontend: PASS', probe.summary())
            self.assertNotIn('body', json.loads((Path(root) / 'results.json').read_text())['public_routes'][0])

    def test_first_broken_route_stops_before_expensive_planning(self):
        for index in range(9):
            with self.subTest(index=index), TemporaryDirectory() as root, patch.object(latency, 'build_opener') as opener, patch.dict(os.environ, GITHUB_SHA=SHA):
                values = responses()
                values[index] = Response(b'{"detail":"Not Found"}', 'application/json', 404)
                opener.return_value.open.side_effect = values
                probe = latency.Probe(root)
                with patch.object(probe, 'batch') as batch, self.assertRaisesRegex(AssertionError, 'status=404.*application/json.*Not Found'):
                    latency.run_sequence(probe)
                batch.assert_not_called()
                self.assertEqual(len(probe.routes), index + 1)
                self.assertFalse(probe.routes[-1]['passed'])

    def test_invalid_content_and_python_serving_are_rejected(self):
        bad = [Response(b'{}', 'application/json'), Response(b'', 'text/javascript'),
               Response(b'<html>error</html>', 'text/javascript'),
               Response(b'javascript', 'text/javascript', cache='max-age=0'),
               Response(b'javascript', 'text/javascript', cache='max-age=31536000, immutable', timing='application_import;dur=5')]
        for response in bad:
            with self.subTest(headers=response.headers), TemporaryDirectory() as root, patch.object(latency, 'build_opener') as opener:
                opener.return_value.open.return_value = response
                probe = latency.Probe(root)
                with self.assertRaises(AssertionError):
                    probe.public_get('/assets/index-abcdefgh.js')

    def test_stale_commit_and_dataset_fail(self):
        for index, body in [(7, b'{"dataset_id":"sample-v2-fixture-97"}'), (8, b'{"commit":"old","deployment_host":"build.vercel.app"}')]:
            with self.subTest(index=index), TemporaryDirectory() as root, patch.object(latency, 'build_opener') as opener, patch.dict(os.environ, GITHUB_SHA=SHA):
                values = responses()
                values[index] = Response(body, 'application/json')
                opener.return_value.open.side_effect = values
                with self.assertRaises(AssertionError):
                    latency.Probe(root).preflight()

    def test_unsafe_html_cache_and_cross_origin_assets_fail(self):
        with TemporaryDirectory() as root, patch.object(latency, 'build_opener') as opener:
            opener.return_value.open.return_value = Response(SHELL, 'text/html', cache='immutable')
            with self.assertRaisesRegex(AssertionError, 'HTML must not be immutable'):
                latency.Probe(root).public_get('/')
        with self.assertRaises(AssertionError):
            html_assets(SHELL.replace(b'/assets/index-abcdefgh.js', b'https://example.com/script.js'))

    def test_first_failure_still_writes_json_and_summary(self):
        with TemporaryDirectory() as root, patch.object(latency, 'build_opener') as opener, patch.object(latency.subprocess, 'check_output', return_value='curl test'), patch.object(latency.platform, 'platform', return_value='test'), patch('sys.argv', ['probe', '--output', root]):
            opener.return_value.open.return_value = Response(b'{"detail":"Not Found"}', 'application/json', 404)
            with self.assertRaises(SystemExit) as result:
                latency.main()
            self.assertEqual(result.exception.code, True)
            evidence = json.loads((Path(root) / 'results.json').read_text())
            self.assertEqual(evidence['measurements'], [])
            self.assertEqual(evidence['public_routes'][0]['status'], 404)
            self.assertTrue(evidence['failures'])
            self.assertIn('FAIL', (Path(root) / 'summary.md').read_text())

    def test_excerpt_is_bounded_and_redacts_secrets(self):
        excerpt = sanitized_excerpt(b'{"token":"secret-value", "password":"password-value"}\n' + b'x' * 400)
        self.assertNotIn('secret-value', excerpt)
        self.assertNotIn('password-value', excerpt)
        self.assertNotIn('\n', excerpt)
        self.assertLessEqual(len(excerpt), 240)

    def test_late_latency_failure_retains_summary_and_route_evidence(self):
        from backend.tests.test_production_latency import timing, curl_result
        def late_failure(probe):
            probe.preflight()
            specs = [('full-first', '/api/plan/sample', None)]
            response = curl_result(probe.output, specs, [timing(path='/api/plan/sample', seconds=10)], [b'{}'])
            with patch.object(latency.subprocess, 'run', return_value=response):
                probe.batch(specs)
        with TemporaryDirectory() as root, patch.object(latency, 'build_opener') as opener, \
             patch.dict(os.environ, GITHUB_SHA=SHA), patch.object(latency, 'run_sequence', side_effect=late_failure), \
             patch.object(latency.subprocess, 'check_output', return_value='curl test'), \
             patch.object(latency.platform, 'platform', return_value='test'), \
             patch('sys.argv', ['probe', '--output', root]):
            opener.return_value.open.side_effect = responses()
            with self.assertRaises(SystemExit) as result:
                latency.main()
            self.assertEqual(result.exception.code, True)
            evidence = json.loads((Path(root) / 'results.json').read_text())
            self.assertEqual(len(evidence['public_routes']), 9)
            self.assertEqual(evidence['measurements'][0]['http_s'], 10)
            summary = (Path(root) / 'summary.md').read_text()
            self.assertIn('Frontend: PASS', summary)
            self.assertIn('full-first', summary)
            self.assertIn('ten-second', summary)


if __name__ == '__main__':
    unittest.main()
