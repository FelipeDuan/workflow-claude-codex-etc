"""Recursos do Mac com leituras sintéticas, sem comandos reais do sistema."""
import contextlib
import datetime as dt
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

if sys.version_info < (3, 11):
    raise unittest.SkipTest('requer Python >= 3.11')

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'scripts/metrics'))
import hygiene
import process_scan
import paseo_watchdog as wd
import report


class MemoryTests(unittest.TestCase):
    def reads(self, command, **kwargs):
        if command[0] == 'top':
            text = 'PID COMMAND MEM\n10 claude 10M\n11 MCP com espaços 20M+\n12 astro 30M\n13 node 4M\n14 Safari 5M\n15 Editor 6M\n16 OrbStack 7M\n17 Paseo Helper 8M\n18 codex 9M\n19 opencode 2M\n20 ai-memory 1M\n21 playwright 3M\n'
        elif command[0] == 'memory_pressure':
            text = 'System-wide memory free percentage: 31%'
        elif 'vm.swapusage' in command:
            text = 'vm.swapusage: total = 12G used = 3.5G free = 8.5G'
        else:
            text = '2\n'
        return subprocess.CompletedProcess(command, 0, text, '')

    def test_tree_components_footprint_and_single_top(self):
        rows = {10: {'ppid': 1, 'raw_command': '/bin/claude'},
                11: {'ppid': 10, 'raw_command': '/bin/python3 /x/mcp.py'},
                12: {'ppid': 1, 'raw_command': '/h/.paseo/worktrees/g/p/astro dev'},
                13: {'ppid': 1, 'raw_command': '/bin/node'},
                14: {'ppid': 1, 'raw_command': '/Applications/Safari.app/Contents/MacOS/Safari'},
                15: {'ppid': 1, 'raw_command': '/Applications/Editor App.app/Contents/MacOS/Editor'},
                16: {'ppid': 1, 'raw_command': '/Applications/OrbStack.app/Contents/MacOS/OrbStack'},
                17: {'ppid': 1, 'raw_command': '/Applications/Paseo.app/Contents/MacOS/Paseo'},
                18: {'ppid': 1, 'raw_command': '/bin/codex'},
                19: {'ppid': 1, 'raw_command': '/bin/opencode'},
                20: {'ppid': 1, 'raw_command': '/bin/ai-memory'},
                21: {'ppid': 1, 'raw_command': '/bin/node /mcp/playwright/index.js'}}
        snapshot = {'rows': rows, 'cwds': {13: '/h/.paseo/worktrees/g/p'}, 'reason': None}
        with patch.object(hygiene.subprocess, 'run', side_effect=self.reads) as run:
            info = hygiene.memory_info(snapshot, home=Path('/h'))
        groups = {row['component']: row for row in info['components']}
        self.assertEqual(groups['sessões Claude Code com filhos']['footprint_bytes'], 30 * 1024**2)
        self.assertEqual(groups['processos de worktrees de agentes']['footprint_bytes'], 34 * 1024**2)
        self.assertEqual(groups['outros apps: Editor App']['footprint_bytes'], 6 * 1024**2)
        for label in ('OrbStack', 'Paseo (app+daemon)', 'Codex', 'OpenCode', 'ai-memory', 'playwright MCP', 'navegador'):
            self.assertIn(label, groups)
        self.assertNotIn('/Applications', json.dumps(info))
        self.assertEqual(info['pressure_level_code'], 2)
        self.assertEqual(info['swap_used_bytes'], int(3.5 * 1024**3))
        self.assertEqual(sum(call.args[0][0] == 'top' for call in run.call_args_list), 1)

    def test_bad_reads_are_null_with_reason(self):
        for failure in (subprocess.CompletedProcess([], 1, '', 'segredo /private/caminho'), OSError('falhou')):
            with self.subTest(failure=type(failure).__name__):
                kwargs = {'side_effect': failure} if isinstance(failure, Exception) else {'return_value': failure}
                with patch.object(hygiene.subprocess, 'run', **kwargs):
                    info = hygiene.memory_info({'rows': {}, 'reason': 'ps indisponível'})
                for key in ('pressure_level', 'pressure_level_code', 'swap_total_bytes', 'swap_used_bytes', 'free_percentage', 'components'):
                    self.assertIsNone(info[key])
                    self.assertTrue(info['reason'][key])
                self.assertNotIn('segredo', json.dumps(info))
        for raw in ('1..2M', 'oops', '-1M'):
            self.assertIsNone(hygiene._bytes(raw))

    def test_missing_pid_preserves_sum_and_marks_partial(self):
        snapshot = {'rows': {10: {'ppid': 1, 'raw_command': 'claude'}, 999: {'ppid': 10, 'raw_command': 'mcp'}}, 'cwds': {}}
        with patch.object(hygiene.subprocess, 'run', side_effect=self.reads):
            info = hygiene.memory_info(snapshot)
        component = info['components'][0]
        self.assertEqual(component['footprint_bytes'], 10 * 1024**2)
        self.assertEqual(component['missing_count'], 1)
        self.assertTrue(component['partial'])
        self.assertTrue(component['reason'])
        with patch.object(hygiene.subprocess, 'run', side_effect=self.reads):
            info = hygiene.memory_info({'rows': {999: snapshot['rows'][999]}, 'cwds': {}})
        self.assertIsNone(info['components'][0]['footprint_bytes'])
        self.assertEqual(info['components'][0]['missing_count'], 1)

    def test_arguments_do_not_reclassify_an_unrelated_process(self):
        rows = {1: {'ppid': 0, 'raw_command': '/bin/python -c "codex paseo playwright"'}}
        self.assertEqual(hygiene._memory_component(1, rows, {}, {}, Path('/h')), 'outros processos')

    def test_native_claude_version_path_owns_children(self):
        rows = {10: {'ppid': 1, 'raw_command': '/h/.local/share/claude/versions/2.1.1'},
                11: {'ppid': 10, 'raw_command': '/bin/python3 /x/mcp.py'}}
        self.assertEqual(hygiene._memory_component(11, rows, {}, {}, Path('/h')),
                         'sessões Claude Code com filhos')
        self.assertEqual(hygiene._memory_component(11, rows, {}, {}, Path('/other')),
                         'outros processos')

    def test_components_require_exact_cli_or_app_executable(self):
        cases = {
            '/Applications/Claude.app/Contents/MacOS/claude': 'outros apps: Claude',
            '/Applications/Claude.app/Contents/MacOS/Claude': 'outros apps: Claude',
            '/bin/node /x/claude-code/cli.js': 'outros processos',
            '/x/claude-code/cli.js': 'outros processos',
            '/x/node_modules/@anthropic-ai/claude-code/cli.js': 'sessões Claude Code com filhos',
            '/bin/node /x/node_modules/@anthropic-ai/claude-code/cli.js': 'sessões Claude Code com filhos',
            '/bin/paseo-wrapper': 'outros processos',
            '/bin/codex-other': 'outros processos',
            '/x/codex/project/python': 'outros processos',
            '/bin/opencode': 'OpenCode',
            '/Applications/Zen.app/Contents/MacOS/zen': 'navegador',
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome --flag': 'navegador',
            '/Applications/Safari.app/Contents/MacOS/SafariCloudHistoryPushAgent': 'outros apps: Safari',
            '/Applications/Safari.app/Contents/MacOS/SafariBookmarksSyncAgent': 'outros apps: Safari',
            '/System/Library/PrivateFrameworks/Safari.framework/SafariSafeBrowsingService': 'outros processos',
            '/Applications/Paseo.app/Contents/MacOS/other': 'outros apps: Paseo',
            '/Applications/Codex.app/Contents/MacOS/other': 'outros apps: Codex',
        }
        for command, expected in cases.items():
            with self.subTest(command=command):
                rows = {10: {'ppid': 1, 'raw_command': command}}
                self.assertEqual(hygiene._memory_component(10, rows, {}, {}, Path('/h')), expected)

    def test_top_runs_immediately_after_ps_and_excludes_collector_tree(self):
        calls = []
        ps = ('10 1 Mon Nov 9 12:00:00 2026 100 claude\n'
              '11 10 Mon Nov 9 12:00:00 2026 100 python3 hygiene.py\n'
              '12 11 Mon Nov 9 12:00:00 2026 100 ps\n')
        def run(command, **kwargs):
            calls.append(command[0])
            if command[0] == 'ps':
                return subprocess.CompletedProcess(command, 0, ps, '')
            if command[0] == 'lsof':
                return subprocess.CompletedProcess(command, 0, '', '')
            return self.reads(command, **kwargs)
        snapshot = {}
        with patch.object(hygiene.subprocess, 'run', side_effect=run):
            process_scan.scan_processes([], snapshot=snapshot, after_ps=hygiene.collect_top, exclude_tree_pid=11)
            info = hygiene.memory_info(snapshot)
        self.assertEqual(calls[:3], ['ps', 'top', 'lsof'])
        self.assertEqual(calls.count('ps'), 1)
        self.assertEqual(calls.count('top'), 1)
        group = info['components'][0]
        self.assertEqual(group['process_count'], 1)
        self.assertEqual(group['footprint_bytes'], 10 * 1024**2)

    def test_snapshot_reuses_ps_and_does_not_serialize_raw_command(self):
        ps = '10 1 Mon Nov  9 12:00:00 2026 100 /bin/claude /sensitive/path\n'
        snapshot = {}
        with patch.object(process_scan, '_run', side_effect=[ps, 'p10\nn/work/tree\n', ''] ) as run:
            rows, _, error = process_scan.scan_processes([{'path': '/work/tree'}], snapshot=snapshot)
        self.assertIsNone(error)
        self.assertEqual(sum(call.args[0][0] == 'ps' for call in run.call_args_list), 1)
        self.assertIn('/sensitive/path', snapshot['rows'][10]['raw_command'])
        self.assertNotIn('/sensitive/path', json.dumps(rows))

    def test_cwd_failure_makes_component_classification_unknown(self):
        snapshot = {}
        with patch.object(process_scan, '_run', side_effect=[
                '10 1 Mon Nov  9 12:00:00 2026 100 /bin/node\n', None, '']):
            process_scan.scan_processes([], snapshot=snapshot)
        with patch.object(hygiene.subprocess, 'run', side_effect=self.reads):
            info = hygiene.memory_info(snapshot)
        self.assertIsNone(info['components'])
        self.assertIn('cwd', info['reason']['components'])


class RotationTests(unittest.TestCase):
    def test_configured_state_foreign_sources_and_unlink_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp).resolve() / 'custom-state'
            directory = state / 'higiene'
            directory.mkdir(parents=True)
            denied = directory / 'scan-20261109-0000.json'
            removed = directory / 'scan-20261109-0001.json'
            foreign = directory / 'scan-20261108-0000.json'
            plan = directory / 'plano-20261108-0000.md'
            denied.write_text('{"source":"hygiene"}')
            removed.write_text('{"source":"hygiene"}')
            foreign.write_text('{"source":"other"}')
            plan.write_text('# Plano escrito à mão')
            unlink = Path.unlink
            def remove(path, *args, **kwargs):
                if path == denied:
                    raise PermissionError('negado')
                return unlink(path, *args, **kwargs)
            output = io.StringIO()
            with patch.object(wd, '_state_dir', return_value=state), \
                    patch.object(Path, 'unlink', remove), contextlib.redirect_stderr(output):
                hygiene.rotate_scans(directory, keep=0)
            self.assertTrue(denied.exists())
            self.assertFalse(removed.exists())
            self.assertTrue(foreign.exists())
            self.assertTrue(plan.exists())
            self.assertIn('rotação continua', output.getvalue())

    def test_only_tool_files_in_canonical_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            directory = root / '.local/state/ai-os/higiene'
            directory.mkdir(parents=True)
            for i in range(30):
                (directory / f'scan-20261109-{i:04}.json').write_text(json.dumps({'source': 'hygiene'}))
                (directory / f'plano-20261109-{i:04}.md').write_text('<!-- hygiene:generated -->\nplano')
            sentinel = directory / 'scan-20261108-0000.json'
            sentinel.write_text('{}')
            other = directory / 'other.json'
            other.write_text('{}')
            outside = root / 'scan-20261101-0000.json'
            outside.write_text(json.dumps({'source': 'hygiene'}))
            link = directory / outside.name
            link.symlink_to(outside)
            with patch.object(wd, '_state_dir', return_value=root / '.local/state/ai-os'):
                hygiene.rotate_scans(directory)
                hygiene.rotate_scans(root)
            self.assertTrue(sentinel.exists())
            self.assertTrue(other.exists())
            self.assertTrue(outside.exists())
            self.assertTrue(link.is_symlink())
            self.assertFalse((directory / 'scan-20261109-0000.json').exists())
            self.assertEqual(len([p for p in directory.glob('scan-20261109-*.json')]), 28)
            self.assertEqual(len(list(directory.glob('plano-*.md'))), 28)

    def test_symlink_directory_or_ancestor_is_never_rotated(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            actual = root / 'actual'
            (actual / '.local/state/ai-os/higiene').mkdir(parents=True)
            victim = actual / '.local/state/ai-os/higiene/scan-20261101-0000.json'
            victim.write_text('{"source":"hygiene"}')
            link = root / 'linked'
            link.symlink_to(actual, target_is_directory=True)
            with patch.object(wd, '_state_dir', return_value=link / '.local/state/ai-os'):
                hygiene.rotate_scans(link / '.local/state/ai-os/higiene', keep=0)
            self.assertTrue(victim.exists())
            directory_link = root / '.local/state/ai-os/higiene'
            directory_link.parent.mkdir(parents=True)
            directory_link.symlink_to(actual / '.local/state/ai-os/higiene', target_is_directory=True)
            with patch.object(wd, '_state_dir', return_value=root / '.local/state/ai-os'):
                hygiene.rotate_scans(directory_link, keep=0)
            self.assertTrue(victim.exists())


class ScheduleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.now = dt.datetime(2026, 11, 9, 12, tzinfo=dt.timezone.utc)
        self.state = {}
        self.policy = wd.Policy([], [])
        for target, name, kwargs in (
                (wd, '_state_dir', {'return_value': self.directory}),
                (wd, '_hygiene_pid_identity', {'return_value': ('alive', 'Mon Nov 9 12:00:00 2026')}),
                (wd.subprocess, 'Popen', {'return_value': MagicMock(pid=1234)}),
                (wd, 'append_history', {}), (wd.os, 'kill', {}), (wd, 'log_event', {})):
            mocker = patch.object(target, name, **kwargs)
            setattr(self, name, mocker.start())
            self.addCleanup(mocker.stop)

    def cycle(self, seconds=0, state=None):
        wd.scheduled_hygiene_scan(self.state if state is None else state,
                                 self.now + dt.timedelta(seconds=seconds), self.policy, self.directory / 'log')

    def result(self, ok=True, duration=4500):
        job = json.loads((self.directory / 'hygiene-schedule.json').read_text())['job']
        (self.directory / 'hygiene-scan-result.json').write_text(json.dumps({
            'token': job['token'], 'pid': 1234, 'ok': ok, 'duration_ms': duration,
            'finished_at': wd._iso(self.now + dt.timedelta(seconds=5))}))

    def test_nonblocking_six_hours_zero_and_result_duration(self):
        self.cycle()
        self.Popen.return_value.wait.assert_not_called()
        self.assertTrue(self.Popen.call_args.kwargs['start_new_session'])
        self.assertEqual(self.Popen.call_args.kwargs['stdin'], subprocess.DEVNULL)
        self.assertIs(self.Popen.call_args.kwargs['stdout'], self.Popen.call_args.kwargs['stderr'])
        self.assertNotEqual(self.Popen.call_args.kwargs['stdout'], subprocess.PIPE)
        self.policy.hygiene_scan_hours = 0
        self.result()
        self._hygiene_pid_identity.return_value = ('gone', None)
        self.cycle(30)
        record = self.append_history.call_args.args[2]
        self.assertEqual(record['duration_ms'], 4500)
        self.assertTrue(record['ok'])
        self.assertIsNone(self.state['hygiene_job'])
        self.policy.hygiene_scan_hours = 6
        self.cycle(6 * 3600 - 1)
        self.assertEqual(self.Popen.call_count, 1)
        self._hygiene_pid_identity.return_value = ('alive', 'new')
        self.cycle(6 * 3600)
        self.assertEqual(self.Popen.call_count, 2)

    def test_running_state_is_reloaded_and_blocks_second_even_after_interval(self):
        self.cycle()
        self.cycle(7 * 3600, state={})
        self.assertEqual(self.Popen.call_count, 1)
        self.assertTrue((self.directory / 'hygiene-schedule.json').exists())
        self.assertEqual(self.kill.call_count, 1)

    def test_unknown_identity_never_signals_or_releases_ownership(self):
        self.cycle()
        self._hygiene_pid_identity.return_value = ('unknown', None)
        self.cycle(8 * 3600, state={})
        self.kill.assert_not_called()
        self.assertEqual(self.Popen.call_count, 1)
        self.assertIsNotNone(self.state['hygiene_job'])

    def test_timeout_only_own_pid_and_escalates_after_grace(self):
        import signal
        self.cycle()
        self.cycle(120)
        self.kill.assert_called_once_with(1234, signal.SIGTERM)
        self.cycle(140)
        self.assertEqual(self.kill.call_count, 1)
        self.cycle(150)
        self.kill.assert_called_with(1234, signal.SIGKILL)
        self.assertEqual(self.kill.call_count, 2)
        self._hygiene_pid_identity.return_value = ('gone', None)
        self.cycle(180)
        self.assertFalse(self.append_history.call_args.args[2]['ok'])
        self.assertIsNone(self.append_history.call_args.args[2]['duration_ms'])
        self.assertIsNone(self.state['hygiene_job'])

    def test_pid_reuse_is_not_signaled(self):
        self.cycle()
        self._hygiene_pid_identity.return_value = ('alive', 'different')
        self.cycle(120)
        self.kill.assert_not_called()
        self.assertFalse(self.append_history.call_args.args[2]['ok'])
        self.assertIsNone(self.state['hygiene_job'])

    def test_failure_after_spawn_preserves_persisted_intent(self):
        original = wd.write_hygiene_json
        calls = 0
        def save(path, data):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError('disco cheio')
            original(path, data)
        with patch.object(wd, 'write_hygiene_json', side_effect=save):
            self.cycle()
        self.cycle(8 * 3600, state={})
        self.assertEqual(self.Popen.call_count, 1)
        self.kill.assert_not_called()
        self.assertIsNotNone(json.loads((self.directory / 'hygiene-schedule.json').read_text())['job'])

    def test_spawn_error_and_dry_run(self):
        self.Popen.side_effect = OSError('falhou')
        self.cycle()
        self.assertFalse(self.append_history.call_args.args[2]['ok'])
        self.cycle(30)
        self.assertEqual(self.Popen.call_count, 1)
        wd.scheduled_hygiene_scan({}, self.now, self.policy, self.directory / 'log', True)
        self.assertEqual(self.Popen.call_count, 1)

    def test_busy_supervision_lock_does_not_wait_or_spawn(self):
        with patch.object(wd.fcntl, 'flock', side_effect=BlockingIOError):
            self.cycle()
        self.Popen.assert_not_called()

    def test_child_duration_does_not_enter_daily_collector_cost(self):
        self.cycle()
        self.result(duration=90000)
        self._hygiene_pid_identity.return_value = ('gone', None)
        self.state['_cycle_started'] = 100.0
        with patch.object(wd.time, 'perf_counter', return_value=100.005):
            self.cycle(30)
            wd.finish_cycle(self.state, self.now + dt.timedelta(seconds=30), self.directory / 'log')
        self.assertAlmostEqual(self.state['collector_daily']['total_ms'], 5.0, places=3)
        self.assertLess(self.state['collector_daily']['max_ms'], 6)


class ScheduledChildTests(unittest.TestCase):
    def test_deadline_escapes_exception_handlers_and_writes_error_result(self):
        import signal
        handlers = {}
        originals = {signal.SIGTERM: object(), signal.SIGALRM: object()}
        def install(kind, handler):
            prior = handlers.get(kind, originals[kind])
            handlers[kind] = handler
            return prior
        def scan(*args):
            try:
                handlers[signal.SIGALRM](signal.SIGALRM, None)
            except Exception:
                self.fail('o deadline foi engolido pelo except Exception')
        with tempfile.TemporaryDirectory() as temp:
            result = Path(temp) / 'result.json'
            with patch.object(hygiene.signal, 'signal', side_effect=install), \
                    patch.object(hygiene.signal, 'alarm') as alarm, \
                    patch.object(hygiene, 'build_scan', side_effect=scan), \
                    patch.object(wd, 'load_restricted_roots', return_value=[]), \
                    contextlib.redirect_stderr(io.StringIO()):
                code = hygiene.main(['scan', '--repo', '/synthetic', '--scheduled-result', str(result),
                                     '--scheduled-token', 'private-token'])
            self.assertEqual(code, 2)
            data = json.loads(result.read_text())
            self.assertFalse(data['ok'])
            self.assertEqual(data['token'], 'private-token')
            self.assertEqual(alarm.call_args_list[0].args, (120,))
            self.assertEqual(alarm.call_args_list[-1].args, (0,))
            self.assertIs(handlers[signal.SIGTERM], originals[signal.SIGTERM])
            self.assertIs(handlers[signal.SIGALRM], originals[signal.SIGALRM])



class ReportResourceTests(unittest.TestCase):
    def test_partial_footprint_is_explicit_in_json_and_markdown(self):
        from metrics_common import Ctx, parse_tz
        scan = {'version': 1, 'generated_at': '2026-11-09T12:00:00Z', 'disk': {}, 'processes': {},
                'memory': {'components': [{'component': 'Codex', 'footprint_bytes': 123,
                                           'process_count': 3, 'missing_count': 1, 'partial': True}]}}
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp)
            (state / 'higiene').mkdir()
            (state / 'higiene/scan-test.json').write_text(json.dumps(scan))
            result = report.collect(Ctx(tz=parse_tz('-03:00'), home=state), state,
                                    report.stamp('2026-11-09T00:00:00Z'), report.stamp('2026-11-10T00:00:00Z'),
                                    live=False, runner=lambda cmd: None)
        component = result['Q5']['hygiene_scan']['components'][0]
        self.assertEqual(component['footprint_bytes']['value'], 123)
        self.assertEqual(component['footprint_bytes']['status'], 'estimated')
        self.assertTrue(component['partial'])
        self.assertEqual(component['missing_count']['value'], 1)
        self.assertIn('soma disponível é parcial', report.render_md(result))

    def test_orphans_residuals_unknown_and_markdown(self):
        from metrics_common import Ctx, parse_tz
        process = {'pid': 10, 'ppid': 1, 'start_time': 'known', 'worktree': '/private/project',
                   'owner_known': True, 'owner_status': 'closed', 'age_hours': 20,
                   'is_paseo_worktree': True, 'is_main': False, 'active_connections': 0,
                   'command': 'astro dev', 'footprint_bytes': 100}
        items = [process, {**process, 'pid': 11, 'footprint_bytes': 200},
                 {**process, 'pid': 12, 'ppid': 20, 'command': 'tmux', 'footprint_bytes': 300}]
        scan = {'version': 1, 'generated_at': '2026-11-09T12:00:00Z',
                'memory': {'pressure_level': 'normal', 'components': [
                    {'component': 'Codex', 'footprint_bytes': 600, 'process_count': 3}]},
                'disk': {'free_bytes': 100}, 'scan_ms': 3, 'processes': {'items': items, 'error': None}}
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp)
            (state / 'higiene').mkdir()
            file = state / 'higiene/scan-test.json'
            file.write_text(json.dumps(scan))
            ctx = Ctx(tz=parse_tz('-03:00'), home=state)
            result = report.collect(ctx, state, report.stamp('2026-11-09T00:00:00Z'),
                                    report.stamp('2026-11-10T00:00:00Z'), live=False, runner=lambda cmd: None)
            resources = result['Q5']['hygiene_scan']
            self.assertEqual(resources['ORFAO_CANDIDATO']['count']['value'], 2)
            self.assertEqual(resources['ORFAO_CANDIDATO']['footprint_bytes']['value'], 300)
            self.assertEqual(resources['RESIDUO_AGENTE']['count']['value'], 1)
            self.assertEqual(resources['RESIDUO_AGENTE']['footprint_bytes']['value'], 300)
            md = report.render_md(result)
            self.assertIn('2026-11-09T12:00:00Z', md)
            self.assertIn('Codex', md)
            self.assertIn('Footprint (bytes)', md)
            self.assertNotIn('/private/project', md)
            self.assertNotIn('/private/project', json.dumps(result))
            items[1]['footprint_bytes'] = None
            file.write_text(json.dumps(scan))
            result = report.collect(ctx, state, report.stamp('2026-11-09T00:00:00Z'),
                                    report.stamp('2026-11-10T00:00:00Z'), live=False, runner=lambda cmd: None)
            footprint = result['Q5']['hygiene_scan']['ORFAO_CANDIDATO']['footprint_bytes']
            self.assertIsNone(footprint['value'])
            self.assertTrue(footprint['reason'])
        with patch.object(hygiene.subprocess, 'run', side_effect=MemoryTests().reads):
            info = hygiene.memory_info({'rows': {10: {'ppid': 1, 'raw_command': '/bin/astro dev'}}, 'cwds': {}}, [process])
        self.assertEqual(info['components'][0]['component'], 'servidores órfãos')

    def test_latest_window_override_and_private_projection(self):
        start = report.stamp('2026-11-09T00:00:00Z')
        end = report.stamp('2026-11-10T00:00:00Z')
        scan = {'version': 1, 'generated_at': '2026-11-09T12:00:00Z',
                'memory': {'pressure_level': 'aviso', 'swap_used_bytes': 12, 'components': [
                    {'component': 'Codex', 'footprint_bytes': 42, 'process_count': 2},
                    {'component': '/private/full/path', 'footprint_bytes': None, 'reason': '/secret', 'process_count': 1}]},
                'disk': {'free_bytes': 100}, 'scan_ms': 3, 'processes': {'items': []}}
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp) / 'higiene'
            directory.mkdir(parents=True)
            old = directory / 'scan-z.json'
            old.write_text(json.dumps({**scan, 'generated_at': report.iso(start)}))
            newest = directory / 'scan-a.json'
            newest.write_text(json.dumps(scan))
            outside = directory / 'scan-outside.json'
            outside.write_text(json.dumps({**scan, 'generated_at': report.iso(end)}))
            (directory / 'scan-invalid.json').write_text(json.dumps({'generated_at': '2026-11-09T23:00:00Z'}))
            selected, timestamp = report.latest_hygiene_scan(temp, start, end)
            self.assertEqual(timestamp, scan['generated_at'])
            self.assertIsNone(report.latest_hygiene_scan(temp, start, end, outside)[0])
            def metric(name, value, n, **kwargs):
                return {'value': value, 'n': n, 'status': 'unknown' if value is None else 'measured', **kwargs}
            projected = report.hygiene_metrics(selected, timestamp, metric)
            text = json.dumps(projected)
            self.assertNotIn('/private', text)
            self.assertNotIn('/secret', text)
            self.assertEqual(projected['components'][0]['footprint_bytes']['value'], 42)
            self.assertEqual(projected['ORFAO_CANDIDATO']['count']['value'], 0)
            unknown = report.hygiene_metrics(None, None, metric)
            self.assertIsNone(unknown['swap_used_bytes']['value'])
            self.assertTrue(unknown['swap_used_bytes']['reason'])
            self.assertIsNone(unknown['ORFAO_CANDIDATO']['count']['value'])
