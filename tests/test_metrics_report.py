"""Relatório GQM com fontes sintéticas, sem ler o estado real."""
import contextlib
import datetime as dt
import io
import json
import os
from pathlib import Path
import sys
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

if sys.version_info < (3, 11):
    raise unittest.SkipTest('requer Python >= 3.11; rode com /opt/homebrew/bin/python3')

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/metrics'))
import report
from metrics_common import Ctx, encode_path, parse_tz


def event(kind, when, **fields):
    return {'type': kind, 'observed_at': when, 'occurred_at': when, 'confidence': 'observed', **fields}


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.state = self.home / 'state'
        self.tz = parse_tz('-03:00')
        self.start = report.stamp('2026-11-01T03:00:00Z')
        self.end = report.stamp('2026-11-02T03:00:00Z')
        self.ctx = Ctx(tz=self.tz, home=self.home, restricted=[str(self.home / 'sigilo')])

    def history(self, group, rows, month='2026-11', suffix=''):
        path = self.state / 'history' / f'{group}-{month}.jsonl'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(''.join(json.dumps(r) + '\n' for r in rows) + suffix)
        return path

    def collect(self, **kwargs):
        return report.collect(self.ctx, self.state, self.start, self.end, live=False,
                              runner=lambda cmd: 'a' * 40 if cmd[0] == 'git' else None, **kwargs)

    def test_partial_window_invalid_lines_and_unknown_not_zero(self):
        self.history('tasks', [event('task.opened', '2026-11-01T04:00:00Z', task_id='T-20261101-01'),
                               event('task.opened', '2026-11-01T02:59:00Z', task_id='outside')],
                     suffix='{broken\n[]\n{"type":"task.opened","observed_at":"bad"}\n')
        self.history('tasks', [], month='2026-10', suffix='{not-read\n')
        result = self.collect()
        self.assertEqual(result['read']['files'], 1)
        self.assertEqual(result['read']['invalid_lines'], 3)
        self.assertEqual(result['Q1']['evaluation_coverage']['value'], 0)
        self.assertEqual(result['Q1']['evaluation_coverage']['n'], 1)
        self.assertIsNone(result['Q1']['first_delivery_acceptance']['value'])
        self.assertEqual(result['Q1']['first_delivery_acceptance']['status'], 'unknown')
        self.assertIsNone(result['Q5']['collector_cost']['value'])
        self.assertIn('Dados insuficientes', report.render_md(result))
        self.assertIsNone(result['Q4']['collector_gaps']['value'])

    def test_malformed_field_types_count_as_invalid(self):
        self.history('agents', [event('agent.transition', '2026-11-01T04:00:00Z', agent_id='a', to=[]),
                                event('agent.transition', '2026-11-01T04:00:00Z', provider={}, to='erro')])
        self.history('quota', [event('quota.sample', '2026-11-01T04:00:00Z', used_percent='50')])
        result = self.collect()
        self.assertEqual(result['read']['invalid_lines'], 3)

    def test_reopen_without_rework_does_not_invent_human_verdict(self):
        self.history('tasks', [event('task.opened', '2026-11-01T04:00:00Z', task_id='one'),
                               event('task.closed', '2026-11-01T05:00:00Z', task_id='one', verdict='aceito'),
                               event('task.reopened', '2026-11-01T06:00:00Z', task_id='one', reason='mudança de escopo'),
                               event('task.closed', '2026-11-01T07:00:00Z', task_id='one', verdict='aceito')])
        q1 = self.collect()['Q1']
        self.assertEqual(q1['rework_rate']['value'], 0)
        self.assertEqual(q1['first_delivery_acceptance']['value'], 1)

    def test_reopen_removes_verdict_until_new_close(self):
        self.history('tasks', [event('task.opened', '2026-11-01T04:00:00Z', task_id='one'),
                               event('task.closed', '2026-11-01T05:00:00Z', task_id='one', verdict='retrabalho'),
                               event('task.reopened', '2026-11-01T06:00:00Z', task_id='one', reason='corrigir')])
        result = self.collect()
        q1 = result['Q1']
        self.assertEqual(q1['evaluation_coverage']['value'], 0)
        self.assertIsNone(q1['rework_rate']['value'])
        self.assertIsNone(q1['first_delivery_acceptance']['value'])
        self.assertEqual(result['Q3']['by_task'][0]['evaluation_status'], 'em_reavaliacao')

    def test_unknown_latest_quota_preserves_last_sample_status(self):
        self.history('quota', [event('quota.sample', '2026-11-01T04:00:00Z', provider='claude', used_percent=40),
                               event('quota.sample', '2026-11-01T04:10:00Z', provider='claude', used_percent=None, confidence='unknown')])
        quota = self.collect()['Q2']['quota_windows'][0]
        self.assertIsNone(quota['last_reading']['value'])
        self.assertEqual(quota['maximum']['value'], 40)

    def test_task_cohort_coverage_reopen_and_exec_relaunch(self):
        rows = [event('task.opened', '2026-11-01T04:00:00Z', task_id=t) for t in ('one', 'two', 'three')]
        rows += [event('task.linked', '2026-11-01T05:00:00Z', task_id='one', agent_id=a, role='exec') for a in ('a', 'b')]
        rows += [event('task.closed', '2026-11-01T06:00:00Z', task_id='one', verdict='aceito'),
                 event('task.closed', '2026-11-01T06:00:00Z', task_id='two', verdict='retrabalho'),
                 event('task.reopened', '2026-11-01T07:00:00Z', task_id='two'),
                 event('task.closed', '2026-11-01T08:00:00Z', task_id='two', verdict='aceito'),
                 event('task.closed', '2026-11-01T08:00:00Z', task_id='outside-cohort', verdict='aceito')]
        self.history('tasks', rows)
        result = self.collect()
        self.assertAlmostEqual(result['Q1']['evaluation_coverage']['value'], 2 / 3)
        self.assertEqual(result['Q1']['first_delivery_acceptance']['value'], 0)
        self.assertEqual(result['Q1']['rework_rate']['value'], .5)
        self.assertEqual(result['Q3']['relaunches']['value'], 1)

    def test_quota_expiration_unknown_minutes_and_unclassified_saturation(self):
        self.history('quota', [event('quota.sample', '2026-11-01T04:00:00Z', provider='claude', window_kind='five_hour', used_percent=40),
                               event('quota.sample', '2026-11-01T04:10:00Z', provider='claude', window_kind='five_hour', used_percent=None, confidence='unknown'),
                               event('quota.sample', '2026-11-01T04:30:00Z', provider='claude', window_kind='five_hour', used_percent=70)])
        self.history('agents', [event('agent.transition', '2026-11-01T04:00:00Z', agent_id='a', provider='claude', to='trabalhando', reason_code='first_seen'),
                                event('agent.transition', '2026-11-01T05:00:00Z', agent_id='a', provider='claude', to='erro', reason_code='state_changed', reason='campos ausentes')])
        q2 = self.collect()['Q2']
        window = q2['quota_windows'][0]
        self.assertEqual(window['last_reading']['value'], 70)
        self.assertEqual(window['maximum']['value'], 70)
        self.assertEqual(window['sample_count']['value'], 3)
        self.assertEqual(window['unknown_minutes']['value'], 1440 - 25)
        self.assertIsNone(q2['saturations_per_100'][0]['value'])

    def test_saturation_known_limit_per_100_started_and_failure(self):
        self.history('agents', [event('agent.transition', '2026-11-01T04:00:00Z', agent_id=a, provider='codex', to='trabalhando', reason_code='first_seen') for a in ('a', 'b')] +
                               [event('agent.transition', '2026-11-01T05:00:00Z', agent_id='a', provider='codex', to='erro', reason='usage limit'),
                                event('agent.transition', '2026-11-01T05:00:00Z', agent_id='b', provider='codex', to='concluido')])
        result = self.collect()
        self.assertEqual(result['Q2']['saturations_per_100'][0]['value'], 50)
        self.assertEqual(result['Q2']['saturations_per_100'][0]['status'], 'estimated')
        self.assertEqual(result['Q4']['technical_failure_rate']['value'], .5)

    def test_archive_prefix_and_explicit_link_dedup_do_not_output_title(self):
        archive = self.state / 'arquivo-agentes' / '20261101'
        archive.mkdir(parents=True)
        (archive / 'a.inspect.txt').write_text('Id a\nName [T-20261101-01] SEGREDO\nProvider codex\nCreatedAt 2026-11-01T04:00:00Z\n')
        (archive / 'b.inspect.json').write_text(json.dumps({'id': 'b', 'title': '[T-20261101-01] OUTRO SEGREDO', 'createdAt': '2026-11-01T04:00:00Z', 'provider': 'codex'}))
        (archive / 'c.inspect.json').write_text(json.dumps({'id': 'c', 'title': 'SEM VINCULO', 'createdAt': '2026-11-01T04:00:00Z', 'provider': 'codex'}))
        self.history('tasks', [event('task.opened', '2026-11-01T04:00:00Z', task_id='T-20261101-01'),
                               event('task.linked', '2026-11-01T04:01:00Z', task_id='T-20261101-01', agent_id='b', role='review')])
        result = self.collect(archive=archive.parent)
        self.assertEqual(result['Q3']['agents_per_task']['value'], 2)
        self.assertEqual(result['Q3']['link_coverage']['value'], 2 / 3)
        self.assertIsNone(result['Q3']['relaunches']['value'])
        self.assertNotIn('SEGREDO', json.dumps(result))

    def test_live_prefix_preserves_archived_link_and_never_outputs_title(self):
        self.history('tasks', [event('task.opened', '2026-11-01T04:00:00Z', task_id=tid)
                               for tid in ('T-20261101-01', 'T-20261101-02')])
        archive = self.state / 'arquivo-agentes' / '20261101'
        archive.mkdir(parents=True)
        (archive / 'a.inspect.txt').write_text('Id a\nName [T-20261101-01] SEGREDO ARQUIVO\nProvider codex\nCreatedAt 2026-11-01T04:00:00Z\n')
        live = [{'id': 'a', 'title': None, 'provider': 'codex', 'createdAt': '2026-11-01T04:00:00Z'},
                {'id': 'b', 'title': '[T-20261101-02] SEGREDO LIVE', 'provider': 'codex', 'createdAt': '2026-11-01T04:00:00Z'}]
        commands = []

        def runner(cmd):
            commands.append(cmd)
            return json.dumps(live) if cmd[0] == 'paseo' else 'a' * 40

        result = report.collect(self.ctx, self.state, self.start, self.end, archive=archive.parent,
                                live=True, runner=runner)
        self.assertIn(['paseo', 'ls', '--json', '-a'], commands)
        self.assertEqual(result['Q3']['link_coverage']['value'], 1)
        self.assertEqual({r['task_id'] for r in result['Q3']['by_task']}, {'T-20261101-01', 'T-20261101-02'})
        self.assertTrue(all(r['relaunches'] is None and r['relaunch_status'] == 'unknown' for r in result['Q3']['by_task']))
        self.assertNotIn('SEGREDO', json.dumps(result))

    def test_proxy_cutoff_tool_result_and_restricted(self):
        root = self.home / 'transcripts'
        project = root / encode_path(self.home / 'sigilo')
        project.mkdir(parents=True)
        rows = [dict(type='user', timestamp=f'2026-11-01T04:{minute}:00Z', uuid=str(minute), message={'content': 'SEGREDO'})
                for minute in ('00', '10', '21', '25')]
        rows += [dict(type='user', timestamp='2026-11-01T04:15:00Z', message={'content': [{'type': 'tool_result', 'content': 'SEGREDO'}]})]
        (project / 'a.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
        (project / 'branch.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
        proxy = self.collect(claude_root=root)['Q3']['interaction_time_proxy']
        self.assertEqual(proxy['value'], 14)
        self.assertEqual(proxy['n'], 4)
        self.assertEqual(proxy['status'], 'estimated')
        self.assertEqual(proxy['by_day_project'][0]['project'], 'restrito')
        self.assertNotIn('SEGREDO', json.dumps(proxy))
        self.assertIn('Não mede esforço humano', proxy['reason'])

    def test_proxy_session_separation_cwd_restriction_and_local_midnight(self):
        root = self.home / 'transcripts'
        project = root / 'paseo-worktree'
        project.mkdir(parents=True)
        since, until = report.stamp('2026-11-01T02:55:00Z'), report.stamp('2026-11-01T03:10:00Z')
        rows = [dict(type='user', cwd=str(self.home / 'sigilo'), timestamp=t, message={'content': [{'type': 'text', 'text': 'x'}]})
                for t in ('2026-11-01T02:58:00Z', '2026-11-01T03:02:00Z')]
        (project / 'a.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
        (project / 'b.jsonl').write_text(json.dumps(dict(type='user', timestamp='2026-11-01T03:05:00Z', message={'content': 'x'})) + '\n')
        proxy = report.interaction(self.ctx, root, since, until)
        self.assertEqual(proxy['minutes'], 4)
        restricted = [r for r in proxy['by_day_project'] if r['project'] == 'restrito']
        self.assertEqual([r['minutes'] for r in restricted], [None, None])
        self.assertTrue(all(r['status'] == 'unknown' and r['n'] == 1 and r['reason'] for r in restricted))

    def test_pre_window_agent_first_seen_and_limit_error_do_not_change_saturation(self):
        archive = self.state / 'archive'
        archive.mkdir(parents=True)
        (archive / 'old.inspect.json').write_text(json.dumps({'id': 'old', 'createdAt': '2026-10-31T03:00:00Z', 'provider': 'codex'}))
        _, _, pre_window = report.inventory(archive, self.start, self.end, live=False)
        self.assertEqual(pre_window, {'old'})
        base = [event('agent.transition', '2026-11-01T04:00:00Z', agent_id='new', provider='codex', to='trabalhando', reason_code='first_seen')]
        self.history('agents', base)
        before = self.collect(archive=archive)['Q2']['saturations_per_100'][0]
        old = [event('agent.transition', '2026-11-01T04:00:00Z', agent_id='old', provider='codex', to='trabalhando', reason_code='first_seen'),
               event('agent.transition', '2026-11-01T05:00:00Z', agent_id='old', provider='codex', to='erro', reason='usage limit'),
               event('agent.transition', '2026-11-01T06:00:00Z', agent_id='old', provider='codex', to='erro', reason='ausente', reason_code='state_changed')]
        self.history('agents', base + old)
        after = self.collect(archive=archive)['Q2']['saturations_per_100'][0]
        self.assertEqual((after['value'], after['n'], after['numerator']), (before['value'], before['n'], before['numerator']))
        self.assertEqual(after['n'], 1)

    def test_q3_uses_opened_cohort_and_has_sample_sizes_without_none_provider(self):
        self.history('tasks', [event('task.opened', '2026-11-01T04:00:00Z', task_id='current'),
                               event('task.linked', '2026-11-01T04:01:00Z', task_id='current', agent_id='a', role='exec'),
                               event('task.linked', '2026-11-01T04:02:00Z', task_id='old', agent_id='b', role='exec')])
        result = self.collect()
        self.assertEqual(result['Q3']['agents_per_task']['n'], 1)
        self.assertEqual(result['Q3']['agents_per_task']['value'], 1)
        self.assertEqual([r['task_id'] for r in result['Q3']['by_task']], ['current'])
        self.assertEqual(result['Q3']['by_task'][0]['n'], 1)
        self.assertTrue(all(r.get('provider', 'sem_provider') is not None for r in result['Q2']['saturations_per_100']))

    def test_proxy_excludes_synthetic_prefixes_meta_and_summary(self):
        root = self.home / 'transcripts'
        project = root / 'project'
        project.mkdir(parents=True)
        rows = [dict(type='user', timestamp=f'2026-11-01T04:{minute:02}:00Z', message={'content': text})
                for minute, text in enumerate(('<local-command-stdout>...', '<command-name>...', '<command-message>...',
                                               '<system-reminder>...', '<task-notification>...'))]
        rows += [dict(type='user', timestamp='2026-11-01T04:05:00Z', isMeta=True, message={'content': 'meta'}),
                 dict(type='user', timestamp='2026-11-01T04:06:00Z', isCompactSummary=True, message={'content': 'summary'}),
                 dict(type='user', timestamp='2026-11-01T04:07:00Z', message={'content': [{'type': 'text', 'text': '<system-reminder>...' }, {'type': 'text', 'text': 'continuação'}]}),
                 dict(type='user', timestamp='2026-11-01T04:08:00Z', message={'content': 'humana única'})]
        (project / 'a.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
        proxy = self.collect(claude_root=root)['Q3']['interaction_time_proxy']
        self.assertEqual(proxy['n'], 1)
        self.assertIsNone(proxy['value'])
        self.assertEqual(proxy['status'], 'unknown')
        self.assertIn('menos de duas mensagens humanas na janela', proxy['reason'])
        self.assertIsNone(proxy['by_day_project'][0]['minutes'])

    def test_permission_wait_crossing_collector_gap_is_unknown(self):
        self.history('agents', [event('agent.transition', '2026-11-01T04:00:00Z', agent_id='a', to='waiting_permission'),
                                event('agent.transition', '2026-11-01T04:30:00Z', agent_id='a', to='running')])
        self.history('collector', [event('collector.gap', '2026-11-01T04:20:00Z', start_at='2026-11-01T04:05:00Z', end_at='2026-11-01T04:20:00Z')])
        metric = self.collect()['Q4']['permission_waits_over_10_minutes']
        self.assertIsNone(metric['value'])
        self.assertEqual(metric['status'], 'unknown')
        self.assertEqual(metric['unknown_waits'], 1)
        self.assertIn('collector.gap', metric['reason'])

    @unittest.skipUnless(hasattr(time, 'tzset'), 'requer fuso local configurável')
    def test_monthly_names_follow_system_timezone_not_report_timezone(self):
        previous = os.environ.get('TZ')
        try:
            os.environ['TZ'] = 'America/Fortaleza'
            time.tzset()
            start, end = report.stamp('2026-11-01T00:00:00Z'), report.stamp('2026-11-01T01:00:00Z')
            self.history('tasks', [event('task.opened', '2026-11-01T00:30:00Z', task_id='local-october')], month='2026-10')
            self.history('tasks', [], month='2026-11', suffix='{must-not-read\n')
            ctx = Ctx(tz=parse_tz('UTC'), home=self.home)
            result = report.collect(ctx, self.state, start, end, live=False, runner=lambda cmd: None)
            self.assertEqual(result['read']['files'], 1)
            self.assertEqual(result['read']['invalid_lines'], 0)
            self.assertEqual(result['Q1']['evaluation_coverage']['n'], 1)
            self.assertEqual(list(report.months(start, end)), ['2026-10'])
        finally:
            if previous is None:
                os.environ.pop('TZ', None)
            else:
                os.environ['TZ'] = previous
            time.tzset()

    @unittest.skipUnless(Path('/usr/bin/python3').is_file(), 'Python do sistema indisponível')
    def test_system_python_fails_with_explicit_version_guidance(self):
        version = subprocess.run(['/usr/bin/python3', '-c', 'import sys; print(sys.version_info < (3, 11))'], capture_output=True, text=True)
        if version.stdout.strip() != 'True':
            self.skipTest('Python do sistema já satisfaz o requisito')
        result = subprocess.run(['/usr/bin/python3', str(ROOT / 'scripts/metrics/report.py'), '--help'], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('requer Python >= 3.11; rode com /opt/homebrew/bin/python3', result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_daily_complete_day_only_and_overlapping_gaps(self):
        self.end = report.stamp('2026-11-03T03:00:00Z')
        self.history('collector', [event('collector.daily', '2026-11-02T03:05:00Z', date='2026-11-01', cycles=2, total_ms=20, max_ms=15, bytes_appended=100),
                                   event('collector.gap', '2026-11-01T05:00:00Z', start_at='2026-11-01T04:00:00Z', end_at='2026-11-01T05:00:00Z'),
                                   event('collector.gap', '2026-11-01T05:30:00Z', start_at='2026-11-01T04:30:00Z', end_at='2026-11-01T05:30:00Z')])
        result = self.collect()
        self.assertEqual(result['Q5']['by_day'][0]['mean_ms']['value'], 10)
        self.assertEqual(result['Q4']['collector_gap_minutes']['value'], 90)
        self.start = report.stamp('2026-11-01T04:00:00Z')
        self.assertEqual(self.collect()['Q5']['by_day'], [])

    def test_waits_greater_than_10_minutes(self):
        self.history('agents', [event('agent.transition', '2026-11-01T04:00:00Z', agent_id='a', to='waiting_permission'),
                                event('agent.transition', '2026-11-01T04:10:00Z', agent_id='a', to='running'),
                                event('agent.transition', '2026-11-01T05:00:00Z', agent_id='b', to='aguardando_aprovacao'),
                                event('agent.transition', '2026-11-01T05:11:00Z', agent_id='b', to='running')])
        self.assertEqual(self.collect()['Q4']['permission_waits_over_10_minutes']['value'], 1)

    def test_cli_uses_env_state_and_writes_both_formats(self):
        out = self.home / 'out'
        with patch.dict(os.environ, {'AI_OS_STATE_DIR': str(self.state)}), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(report.main(['--since', '2026-11-01', '--until', '2026-11-01', '--tz=-03:00',
                                          '--home', str(self.home), '--no-paseo-live', '--out', str(out)]), 0)
        result = json.loads((out / 'relatorio.json').read_text())
        self.assertEqual(result['window']['until'], '2026-11-02T03:00:00Z')
        self.assertTrue((out / 'RELATORIO.md').is_file())


if __name__ == '__main__':
    unittest.main()
