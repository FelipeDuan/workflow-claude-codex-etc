import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

if sys.version_info < (3, 11):
    raise unittest.SkipTest('ai_os_task requer Python >= 3.11 (tomllib)')

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import ai_os_task as task


class TaskTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.state = self.root / 'state'
        self.policy = self.root / 'policy.toml'
        self.policy.write_text('[restricted]\npaths = []\n')
        self.env = patch.dict(os.environ, {'AI_OS_STATE_DIR': str(self.state)})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.paseo_patch = patch.object(task.wd, 'paseo_json', return_value=[])
        self.paseo_patch.start()
        self.addCleanup(self.paseo_patch.stop)

    def call(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(task.main(['--restricted-config', str(self.policy), '--cwd', str(self.root), *args]), 0)
        return out.getvalue().strip()

    def events(self):
        return task.read_events(self.state / 'history')

    def test_cycle_and_contract(self):
        tid = self.call('open', 'Corrigir validação', '--risk', 'medium', '--category', 'backend')
        self.assertRegex(tid, r'^T-\d{8}-01$')
        self.call('link', tid, 'agent-1', '--role', 'exec')
        self.call('close', tid, 'aceito', '--nota', 'verificado')
        events = self.events()
        self.assertEqual([e['type'] for e in events], ['task.opened', 'task.linked', 'task.closed'])
        self.assertEqual(events[-1]['verdict'], 'aceito')
        self.assertEqual(json.loads(self.call('list', '--open')), [])
        self.assertEqual(json.loads(self.call('list'))[0]['agents'], [{'agent_id': 'agent-1', 'role': 'exec'}])
        for e in events:
            self.assertEqual(e['schema_version'], 1)
            self.assertEqual(e['source'], 'ai-os-task')
            self.assertEqual(e['confidence'], 'observed')
            self.assertTrue(e['observed_at'].endswith('Z'))
            self.assertTrue(e['occurred_at'].endswith('Z'))
            self.assertEqual(e['task_id'], tid)
            self.assertIn('source_version', e)

    def test_close_avisa_e_registra_processos_remanescentes(self):
        tid = self.call('open', 'Fechar tarefa')
        self.call('link', tid, 'agent-1')
        home = self.root / 'home'
        worktree = home / '.paseo' / 'worktrees' / 'g1' / 'repo'
        (worktree / '.astro').mkdir(parents=True)
        candidate_pid, residual_pid = 9000001, 9000002
        (worktree / '.astro' / 'dev.json').write_text(json.dumps({'pid': candidate_pid}))
        current, parent = os.getpid(), os.getppid()

        paseo_calls = []
        command_calls = []
        def paseo(args):
            paseo_calls.append(args)
            if args[0] == 'ls':
                return [{'id': 'agent-1', 'cwd': str(worktree), 'status': 'closed'}]
            return {'Id': 'agent-1', 'Cwd': str(worktree), 'Status': 'closed'}

        def run(command, **kwargs):
            command_calls.append(command)
            if command[0] == 'ps':
                output = (f'{current} {parent} Mon Nov  9 10:00:00 2026 1000 python3 close\n'
                          f'{parent} 1 Mon Nov  9 09:00:00 2026 1000 python3 parent\n'
                          f'{candidate_pid} 1 Fri Oct 23 10:00:00 2026 4 astro dev --host\n'
                          f'{residual_pid} 42 Fri Oct 23 10:00:00 2026 8 tmux\n')
            elif '-d' in command:
                output = (f'p{current}\ncpython3\nfcwd\nn{worktree}\n'
                          f'p{parent}\ncpython3\nfcwd\nn{worktree}\n'
                          f'p{candidate_pid}\ncastro\nfcwd\nn{worktree}\n'
                          f'p{residual_pid}\nctmux\nfcwd\nn{worktree}\n')
            else:
                output = ''
            return subprocess.CompletedProcess(command, 0, stdout=output, stderr='')

        with patch.object(task.Path, 'home', return_value=home), \
                patch.object(task.wd, 'paseo_json', side_effect=paseo), \
                patch.object(task.scan_processes.__globals__['subprocess'], 'run', side_effect=run):
            rows, _, error = task.leftover_processes({'agents': [{'agent_id': 'agent-1'}]}, [])
            self.assertTrue(rows, repr(error))
            warning = io.StringIO()
            with contextlib.redirect_stderr(warning):
                self.call('close', tid, 'aceito')
        self.assertIn(['inspect', 'agent-1', '--json'], paseo_calls)
        self.assertTrue(any(command[0] == 'ps' for command in command_calls))
        self.assertIn('processo(s) remanescente(s)', warning.getvalue())
        self.assertIn('astro dev stop', warning.getvalue())
        self.assertIn(f'pid {residual_pid} (tmux), RESIDUO_AGENTE', warning.getvalue())
        self.assertEqual(warning.getvalue().count('sugestão (NÃO executada):'), 1)
        self.assertNotIn(f'pid {current}', warning.getvalue())
        self.assertNotIn(f'pid {parent}', warning.getvalue())
        leftover = [event for event in self.events() if event['type'] == 'resource.leftover']
        self.assertEqual(len(leftover), 1)
        self.assertEqual(leftover[0]['task_id'], tid)
        self.assertEqual(leftover[0]['pids'], [candidate_pid, residual_pid])

    def test_invalid_transitions_and_reopen(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.call('close', 'T-20261109-01', 'aceito')
        tid = self.call('open', 'Verificar')
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.call('reopen', tid, '--motivo', 'sem fechamento')
        self.call('close', tid, 'retrabalho')
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.call('close', tid, 'aceito')
        self.call('reopen', tid, '--motivo', 'ajuste solicitado')
        pending = json.loads(self.call('list', '--open'))
        self.assertEqual(pending[0]['status'], 'em_reavaliacao')
        self.assertIsNone(pending[0]['verdict'])
        self.call('close', tid, 'aceito')
        self.assertEqual(len(self.events()), 4)

    def test_restricted_content_is_not_recorded(self):
        self.policy.write_text(f'[restricted]\npaths = ["{self.root}"]\n')
        tid = self.call('open', 'objetivo confidencial', '--category', 'cliente secreto')
        self.call('close', tid, 'retrabalho', '--nota', 'nota confidencial')
        self.call('reopen', tid, '--motivo', 'motivo confidencial')
        events = self.events()
        self.assertEqual(events[0]['objective'], 'restrito')
        self.assertEqual(events[0]['project'], 'restrito')
        self.assertEqual(events[1]['note'], 'restrito')
        self.assertEqual(events[2]['reason'], 'restrito')
        self.assertNotIn('confidencial', json.dumps(events))

    def test_sanitization_and_limit(self):
        self.call('open', '  token=segredo\npassword="muito secreto" ' + 'x' * 160)
        objective = self.events()[0]['objective']
        self.assertEqual(len(objective), 120)
        self.assertIn('token=*** password=***', objective)
        self.assertNotIn('segredo', objective)
        self.assertNotIn('\n', objective)

    def test_partial_line_and_daily_sequence(self):
        tid = self.call('open', 'Primeira')
        path = next((self.state / 'history').glob('tasks-*.jsonl'))
        with path.open('ab') as handle:
            handle.write(b'{"linha":')
        second = self.call('open', 'Segunda')
        self.assertEqual(second.rsplit('-', 1)[1], '02')
        self.assertEqual(len(self.events()), 2)
        self.assertIn(b'{"linha":\n{', path.read_bytes())
        self.assertNotEqual(tid, second)

    def test_concurrent_open_ids_are_unique(self):
        cmd = [sys.executable, str(ROOT / 'scripts/ai_os_task.py'), '--restricted-config',
               str(self.policy), '--cwd', str(self.root), 'open', 'Concorrente']
        processes = [subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(5)]
        ids = []
        for proc in processes:
            stdout, stderr = proc.communicate(timeout=20)
            self.assertEqual(proc.returncode, 0, stderr)
            ids.append(stdout.strip())
        self.assertEqual(len(set(ids)), 5)
        self.assertEqual(sorted(t.rsplit('-', 1)[1] for t in ids), ['01', '02', '03', '04', '05'])

    def test_cwd_after_subcommand(self):
        self.policy.write_text(f'[restricted]\npaths = ["{self.root}"]\n')
        self.call('open', 'Privado', '--cwd', str(self.root))
        self.assertEqual(self.events()[0]['objective'], 'restrito')

    def test_open_requires_explicit_cwd(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            task.main(['--restricted-config', str(self.policy), 'open', 'Objetivo'])
        self.assertEqual(error.exception.code, 2)
        self.assertFalse(self.state.exists())

    def test_missing_invalid_or_unreadable_policy_fails_closed(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                self.call('open', 'Não gravar', '--restricted-config', str(self.root / 'ausente.toml'))
            self.assertEqual(error.exception.code, 2)
            self.policy.write_text('[restricted')
            with self.assertRaises(SystemExit) as error:
                self.call('open', 'Não gravar')
            self.assertEqual(error.exception.code, 2)
            with patch.object(task, 'load_restricted_roots', side_effect=PermissionError('sem acesso')):
                with self.assertRaises(SystemExit) as error:
                    self.call('open', 'Não gravar')
            self.assertEqual(error.exception.code, 2)
        self.assertFalse(self.state.exists())

    def test_duplicate_links_are_rejected_including_reopened_task(self):
        first = self.call('open', 'Primeira')
        second = self.call('open', 'Segunda')
        self.call('link', first, 'agent-1')
        for tid in (first, second):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                self.call('link', tid, 'agent-1', '--role', 'review')
            self.assertEqual(error.exception.code, 2)
        self.call('close', first, 'aceito')
        self.call('reopen', first, '--motivo', 'nova avaliação')
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            self.call('link', second, 'agent-1')
        self.assertEqual(error.exception.code, 2)
        self.assertEqual(len([e for e in self.events() if e['type'] == 'task.linked']), 1)

    def test_each_sensitive_pattern_is_masked_in_objective_note_and_reason(self):
        patterns = ['token=segredo', 'sk-proj-abc123', 'ghp_abc123', 'gho_abc123',
                    'xoxb-123-abc', 'xoxp-123-abc', 'Bearer abc123.xyz',
                    'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.assinatura',
                    'nome.sobrenome@example.com', '/Users/pessoa/secreto',
                    '/home/pessoa/secreto', '~/projeto/secreto']
        for secret in patterns:
            with self.subTest(pattern=secret):
                tid = self.call('open', 'Revisar ' + secret)
                self.call('close', tid, 'retrabalho', '--nota', 'Revisar ' + secret)
                self.call('reopen', tid, '--motivo', 'Revisar ' + secret)
                opened, closed, reopened = self.events()[-3:]
                for text in (opened['objective'], closed['note'], reopened['reason']):
                    self.assertEqual(text, 'Revisar ' + ('token=***' if secret.startswith('token=') else '***'))

    def test_python_39_has_clear_version_error(self):
        binary = Path('/usr/bin/python3')
        if not binary.exists():
            self.skipTest('Python do sistema indisponível')
        version = subprocess.run([str(binary), '-c', 'import sys;print(sys.version_info[:2] < (3,11))'],
                                 capture_output=True, text=True, check=True)
        if version.stdout.strip() != 'True':
            self.skipTest('Python do sistema já suporta tomllib')
        proc = subprocess.run([str(binary), str(ROOT / 'scripts/ai_os_task.py'), '--help'],
                              capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('requer Python >= 3.11; rode com /opt/homebrew/bin/python3', proc.stderr)
        self.assertNotIn('Traceback', proc.stderr)

    def test_local_day_and_month_with_utc_timestamps(self):
        class FixedDate(datetime):
            @classmethod
            def now(cls, tz=None):
                return datetime(2026, 11, 1, 1, tzinfo=timezone.utc)

        try:
            with patch.dict(os.environ, {'TZ': 'America/Fortaleza'}), patch.object(task, 'datetime', FixedDate):
                time.tzset()
                tid = self.call('open', 'Virada local')
            self.assertEqual(tid, 'T-20261031-01')
            self.assertTrue((self.state / 'history/tasks-2026-10.jsonl').is_file())
            self.assertEqual(self.events()[0]['occurred_at'], '2026-11-01T01:00:00Z')
        finally:
            time.tzset()


if __name__ == '__main__':
    unittest.main()
