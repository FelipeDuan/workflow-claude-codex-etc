import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('quota_codex', ROOT / 'scripts/quota_codex.py')
quota = importlib.util.module_from_spec(spec)
spec.loader.exec_module(quota)


class QuotaCodexTests(unittest.TestCase):
    def fetch(self, result=None, error=None, timeout=False, cleanup_timeout=False,
              close_error=False, chunks=None, elapsed=None):
        process = MagicMock()
        selector = MagicMock()
        selector.select.return_value = [] if timeout else [(object(), 1)]
        messages = [{'method': 'account/updated'}, {'id': 88, 'result': {}},
                    {'id': 0, 'result': {'userAgent': 'test'}},
                    {'id': 1, 'error': error} if error else {'id': 1, 'result': result}]
        payload = ''.join(json.dumps(message) + '\n' for message in messages).encode()
        if cleanup_timeout:
            process.wait.side_effect = [subprocess.TimeoutExpired('codex', .3), 0]
        if close_error:
            process.stdin.close.side_effect = BrokenPipeError
        with patch.object(quota.subprocess, 'Popen', return_value=process) as popen, \
             patch.object(quota.selectors, 'DefaultSelector') as factory, \
             patch.object(quota.os, 'read', side_effect=chunks, return_value=payload), \
             patch.object(quota.time, 'monotonic', side_effect=elapsed, return_value=0):
            factory.return_value.__enter__.return_value = selector
            output = quota.fetch_quota()
        popen.assert_called_once_with(['codex', 'app-server'], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.assertEqual(set(output), {'provider', 'source', 'fetched_at', 'status', 'windows', 'note'})
        process.terminate.assert_called_once()
        process.stdin.close.assert_called_once()
        process.stdout.close.assert_called_once()
        self.assertTrue(all(0 <= call.kwargs['timeout'] <= 20 for call in process.wait.call_args_list))
        return output, process

    def test_fragmented_response(self):
        payload = b'{"id":0,"result":{}}\n{"id":1,"result":{"rateLimits":{"primary":{"usedPercent":2}}}}\n'
        output, _ = self.fetch(chunks=[payload[:7], payload[7:30], payload[30:]])
        self.assertEqual(output['status'], 'ok')
        self.assertEqual(output['windows'][0]['used_percent'], 2.0)

    def test_eof_is_error(self):
        output, _ = self.fetch(chunks=[b''])
        self.assertEqual(output['status'], 'error')
        self.assertEqual(output['windows'], [])

    def test_broken_pipe_during_cleanup_is_json_error(self):
        output, _ = self.fetch({'rateLimits': {'primary': {'usedPercent': 2}}}, close_error=True)
        self.assertEqual(output['status'], 'error')
        self.assertEqual(output['windows'], [])

    def test_deadline_does_not_restart_after_initialize(self):
        # O handshake consome 18s; a segunda leitura já encontra o prazo de19s.
        output, process = self.fetch({'rateLimits': {'primary': {'usedPercent': 2}}},
                                    elapsed=[0, 0, 1, 2, 18, 19.1, 19.2])
        self.assertEqual(output['status'], 'error')
        self.assertIn('Tempo limite', output['note'])
        self.assertEqual(len(process.stdin.write.call_args_list), 3)
        self.assertLessEqual(process.wait.call_args.kwargs['timeout'], .3)

    def test_ok_handshake_and_codex_bucket(self):
        output, process = self.fetch({'rateLimits': {'primary': {'usedPercent': 99}},
            'rateLimitsByLimitId': {'codex': {
                'primary': {'usedPercent': 40, 'windowDurationMins': 300, 'resetsAt': 0},
                'secondary': {'usedPercent': 20, 'windowDurationMins': 10080}},
                'other': {'primary': {'usedPercent': 80}}}})
        self.assertEqual(output['status'], 'ok')
        self.assertEqual(output['windows'], [
            {'kind': 'five_hour', 'used_percent': 40.0, 'resets_at': '1970-01-01T00:00:00Z', 'window_minutes': 300},
            {'kind': 'weekly', 'used_percent': 20.0, 'resets_at': None, 'window_minutes': 10080}])
        sent = [json.loads(call.args[0]) for call in process.stdin.write.call_args_list]
        self.assertEqual(sent, [
            {'id': 0, 'method': 'initialize', 'params': {'clientInfo': {'name': 'ai_os_quota', 'version': '1.0.0'}}},
            {'method': 'initialized'}, {'id': 1, 'method': 'account/rateLimits/read'}])

    def test_window_without_reset_or_duration(self):
        output, _ = self.fetch({'rateLimits': {'primary': {'usedPercent': 0}}})
        self.assertEqual(output['status'], 'ok')
        self.assertEqual(output['windows'], [{'kind': 'primary', 'used_percent': 0.0,
                                              'resets_at': None, 'window_minutes': None}])

    def test_rpc_error_never_echoes_server_payload(self):
        output, _ = self.fetch(error={'message': 'secret-token', 'code': -1})
        self.assertEqual(output['status'], 'error')
        self.assertEqual(output['windows'], [])
        self.assertNotIn('secret-token', json.dumps(output))

    def test_timeout_and_kill(self):
        output, process = self.fetch(timeout=True, cleanup_timeout=True)
        self.assertEqual(output['status'], 'error')
        self.assertIn('Tempo limite', output['note'])
        self.assertEqual(output['windows'], [])
        process.kill.assert_called_once()

    def test_no_windows_is_unknown(self):
        output, _ = self.fetch({'rateLimits': {'primary': None, 'secondary': None}})
        self.assertEqual(output['status'], 'unknown')
        self.assertEqual(output['windows'], [])

    def test_invalid_numeric_data_never_becomes_a_window(self):
        for used in (True, '40', 4.5, -1, None):
            with self.subTest(used=used):
                output, _ = self.fetch({'rateLimits': {'primary': {'usedPercent': used}}})
                self.assertEqual(output['status'], 'error')
                self.assertEqual(output['windows'], [])

    def test_missing_executable(self):
        with patch.object(quota.subprocess, 'Popen', side_effect=FileNotFoundError):
            output = quota.fetch_quota()
        self.assertEqual(output['status'], 'error')
        self.assertEqual(output['windows'], [])

    def test_stdout_without_write_does_not_save(self):
        output = dict(provider='codex', source='app-server', fetched_at=quota.iso(),
                      status='unknown', windows=[], note='Franquia indisponível.')
        with patch.object(quota, 'fetch_quota', return_value=output), \
             patch.object(quota, 'write_quota') as write, \
             patch.object(quota.sys, 'argv', ['quota_codex.py']), \
             patch('sys.stdout', new_callable=io.StringIO) as stdout:
            quota.main()
        write.assert_not_called()
        self.assertEqual(json.loads(stdout.getvalue()), output)

    def test_write_only_to_temporary_home_and_one_json_stdout(self):
        output = dict(provider='codex', source='app-server', fetched_at=quota.iso(),
                      status='unknown', windows=[], note='Franquia indisponível.')
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(quota.Path, 'home', return_value=Path(directory)), \
             patch.object(quota, 'fetch_quota', return_value=output), \
             patch.object(quota.sys, 'argv', ['quota_codex.py', '--write']), \
             patch('sys.stdout', new_callable=io.StringIO) as stdout:
            quota.main()
            saved = Path(directory) / '.local/state/ai-os/quota/codex.json'
            self.assertEqual(json.loads(saved.read_text()), output)
            self.assertEqual(json.loads(stdout.getvalue()), output)
            self.assertEqual(list(saved.parent.iterdir()), [saved])

    def test_write_failure_is_json_error(self):
        output = dict(provider='codex', source='app-server', fetched_at=quota.iso(),
                      status='ok', windows=[], note='')
        with patch.object(quota, 'fetch_quota', return_value=output), \
             patch.object(quota, 'write_quota', side_effect=PermissionError), \
             patch.object(quota.sys, 'argv', ['quota_codex.py', '--write']), \
             patch('sys.stdout', new_callable=io.StringIO) as stdout:
            quota.main()
        self.assertEqual(json.loads(stdout.getvalue())['status'], 'error')


if __name__ == '__main__':
    unittest.main()
