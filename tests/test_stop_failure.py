import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('harden', ROOT / 'scripts/harden.py')
harden = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harden)


class StopFailureTests(unittest.TestCase):
    def test_stdin_dry_run_and_mock(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / '.ai-memory.toml').write_text('workspace = "teste"\nproject = "teste"\n')
            fake = directory / 'ai-memory'
            fake.write_text('#!' + sys.executable + '\nimport json,os,sys\nprint(json.dumps({"cwd":os.getcwd(),"argv":["ai-memory"]+sys.argv[1:]}))\n')
            fake.chmod(0o755)
            env = dict(os.environ, PATH=str(directory) + os.pathsep + os.environ['PATH'])
            for error in ('rate_limit', 'overloaded', 'billing_error'):
                payload = dict(hook_event_name='StopFailure', error=error,
                               cwd=str(directory), session_id='sessao-teste')
                outputs = []
                for args in (['--dry-run'], []):
                    result = subprocess.run([sys.executable, str(ROOT / 'scripts/stop-failure.py')] + args,
                                            input=json.dumps(payload), text=True, capture_output=True, env=env)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    outputs.append(json.loads(result.stdout))
                self.assertEqual(outputs[0], outputs[1])
                self.assertEqual(outputs[1]['cwd'], str(directory.resolve()))
                self.assertEqual(outputs[1]['argv'], ['ai-memory', 'finalize-session', '--agent',
                                                     'claude-code', '--session-id', 'sessao-teste'])
            for changes in ({'error': 'authentication_failed'}, {'hook_event_name': 'Stop'},
                            {'cwd': None}, {'session_id': None}, {'cwd': 'relative'}):
                invalid = dict(payload, **changes)
                result = subprocess.run([sys.executable, str(ROOT / 'scripts/stop-failure.py')],
                                        input=json.dumps(invalid), text=True, capture_output=True, env=env)
                self.assertEqual(result.stdout, '')
            (directory / '.ai-memory.toml').unlink()
            for raw in (json.dumps(payload), '[]', 'invalid-json'):
                result = subprocess.run([sys.executable, str(ROOT / 'scripts/stop-failure.py')],
                                        input=raw, text=True, capture_output=True, env=env)
                self.assertEqual(result.stdout, '')

    def test_settings_merge_idempotent_preserves_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = Path(tmp) / 'settings.json'
            original = {'env': {'existing': '1'}, 'hooks': {'Stop': [{'hooks': []}],
                        'StopFailure': [{'matcher': 'server_error', 'hooks': []}]}}
            settings.write_text(json.dumps(original))
            before = settings.read_bytes()
            self.assertEqual(harden.claude_stop_failure(str(settings), False), 10)
            self.assertEqual(settings.read_bytes(), before)
            self.assertEqual(harden.claude_stop_failure(str(settings), True), 10)
            merged = json.loads(settings.read_text())
            self.assertEqual(merged['env'], original['env'])
            self.assertEqual(merged['hooks']['Stop'], original['hooks']['Stop'])
            self.assertEqual(merged['hooks']['StopFailure'][0], original['hooks']['StopFailure'][0])
            before = settings.read_bytes()
            self.assertEqual(harden.claude_stop_failure(str(settings), True), 0)
            self.assertEqual(settings.read_bytes(), before)
            settings.write_text('{broken')
            self.assertEqual(harden.claude_stop_failure(str(settings), True), 2)
            self.assertEqual(settings.read_text(), '{broken')


if __name__ == '__main__':
    unittest.main()
