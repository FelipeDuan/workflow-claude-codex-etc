import contextlib
import copy
from datetime import datetime, timedelta, timezone
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

if sys.version_info < (3, 11):
    raise unittest.SkipTest('preflight requer Python >= 3.11 (tomllib)')

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('preflight', ROOT / 'scripts/preflight.py')
pf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pf)
NOW = datetime(2026, 11, 9, 19, 0, tzinfo=timezone.utc)
DOCS = ['skills/ai-os-orchestration/SKILL.md', 'docs/ai-os/USO-DIARIO.md', 'docs/ai-os/MODELOS_2026.md', 'docs/ai-os/decisions/0002-roteamento-por-capacidade-e-franquia.md']


def documentary_errors(text, policy):
    """Percentuais de regra devem casar com JSON; medições são históricas."""
    errors = []
    limits = policy['quota']['thresholds']
    astra = policy['astra']['five_hour_used_percent_exclusive_max']
    historical_section = False
    for line in text.splitlines():
        if text.startswith('# ADR-0002') and line.startswith('## '):
            historical_section = line.startswith(('## Alternativas adiadas', '## Referências de capacidade'))
        if historical_section:
            continue
        if re.search(r'reset|exceção|exception', line, re.I):
            for minutes in re.findall(r'(\d+)\s*(?:min\b|minutos\b|minutes\b)', line):
                if int(minutes) != policy['quota']['reset_exception']['max_minutes_to_reset']:
                    errors.append('reset_exception_mismatch')
        heavy = re.search(r'(one|two|uma|duas|\d+)\s+(?:heavy\s+Codex\s+tasks?|tarefas?\s+pesadas?(?:\s+do\s+Codex)?)\s+(?:at a time|por vez)', line, re.I)
        if heavy:
            count = {'one': 1, 'uma': 1, 'two': 2, 'duas': 2}.get(heavy[1].lower())
            count = int(heavy[1]) if count is None else count
            if count != policy['concurrency']['codex']['max_heavy']:
                errors.append('heavy_concurrency_mismatch')
        if not re.search(r'\d+\s*%|full-access|bypassPermissions', line):
            continue
        # Medições identificadas como observação não são limiares de despacho.
        measurement = bool(re.search(r'medição|consumiu|cost|measurement|registro histórico', line, re.I))
        for match in re.finditer(r'(?P<operator>[<>]\s*=?|≥|≤)?\s*(?P<number>\d+(?:\.\d+)?)\s*%', line):
            value = float(match['number'])
            before = line[:match.start()]
            operator = (match['operator'] or '').replace(' ', '')
            if operator in ('<', '<='):
                if value != astra or operator != '<':
                    errors.append('astra_limit_mismatch')
            elif operator or not measurement:
                windows = list(re.finditer(r'5h|five.hour|seman\w*|week\w*', before, re.I))
                nearest = windows[-1].group().lower() if windows else ''
                if nearest.startswith(('seman', 'week')):
                    expected = limits['weekly']
                elif nearest:
                    expected = limits['five_hour']
                else:
                    expected = None
                if (expected is not None and value != expected) or (expected is None and value not in limits.values()):
                    errors.append('quota_limit_mismatch')
        for provider, setting in policy['providers'].items():
            for mode in setting['forbidden_modes']:
                if mode in line and not re.search(r'never|do not|not allowed|nunca|proibid|não us|nao us|deny|forbidden', line, re.I):
                    errors.append('forbidden_mode_mismatch')
    return errors


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads((ROOT / 'docs/ai-os/roteamento.json').read_text())
        self.task = {'provider': 'codex/gpt-6.1-sol', 'mode': 'auto-review', 'thinking': 'medium',
                     'base': 'main', 'base_exists': True, 'new_workspace': 'worktree', 'risk': 'medium', 'now': NOW.isoformat()}
        self.quotas = {p: {'provider': p, 'status': 'ok', 'fetched_at': NOW.isoformat(),
                          'windows': [{'kind': 'five_hour', 'used_percent': 10},
                                      {'kind': 'weekly', 'used_percent': 20}]}
                       for p, settings in self.policy['providers'].items() if settings['quota_metered']}
        self.quotas['opencode'] = None
        self.restricted = {'enabled': False, 'allowed_models': ['claude', 'codex', 'opencode/glm-5.3-flash-free']}

    def decide(self, **changes):
        return pf.decide(dict(self.task, **changes), self.policy, self.quotas, [], self.restricted)

    def assert_reason(self, decision, reason, **changes):
        result = self.decide(**changes)
        self.assertEqual(result['decision'], decision, result)
        self.assertIn(reason, result['reason_codes'])
        return result

    def test_i17_base_missing_or_nonexistent(self):
        result = self.assert_reason('deny', 'base_required', base=None)
        self.assertTrue(result['hints'])
        self.assert_reason('deny', 'base_not_found', base_exists=False)

    def test_i19_provider_model_and_mode_explicit(self):
        self.assert_reason('deny', 'provider_model_required', provider='codex')
        self.assert_reason('deny', 'mode_required', mode=None)
        self.assert_reason('deny', 'provider_unknown', provider=None)

    def test_i23_heavy_codex_concurrency(self):
        for agent in ({'Provider': 'codex', 'Model': 'gpt-6-astra', 'Status': 'running'},
                      {'provider': 'codex/gpt-6-astra', 'status': 'running'},
                      {'provider': 'codex', 'status': 'running'}):
            with self.subTest(agent=agent):
                result = pf.decide(self.task, self.policy, self.quotas, [agent], self.restricted)
                self.assertEqual(result['reason_codes'], ['provider_heavy_concurrency'])
        for model in ('gpt-6-luna', 'codex/gpt-6-luna'):
            result = pf.decide(self.task, self.policy, self.quotas,
                               [{'Provider': 'codex', 'Model': model, 'Status': 'running'}], self.restricted)
            self.assertEqual(result['decision'], 'allow')
        result = pf.decide(self.task, self.policy, self.quotas,
                           [{'provider': 'codex', 'model': 'gpt-6-astra', 'status': 'idle'}], self.restricted)
        self.assertEqual(result['decision'], 'allow')

    def test_i32_full_access_and_claude_bypass(self):
        self.assert_reason('deny', 'mode_forbidden', mode='full-access')
        self.assert_reason('deny', 'mode_forbidden', provider='claude/sonnet', mode='bypassPermissions')

    def test_i34_antigravity_never_dispatched(self):
        self.assert_reason('deny', 'provider_forbidden', provider='antigravity/gemini', base=None)
        self.assert_reason('deny', 'provider_forbidden', provider='agy/gemini')

    def test_codex_thinking_required(self):
        self.assert_reason('deny', 'thinking_required', thinking=None)

    def test_astra_rules(self):
        task = {'provider': 'codex/gpt-6-astra', 'thinking': 'low', 'risk': 'high', 'no_cheaper_eligible': True}
        self.assertEqual(self.decide(**task)['decision'], 'allow')
        self.assert_reason('deny', 'astra_risk_forbidden', **dict(task, risk='low'))
        self.assert_reason('deny', 'astra_thinking_forbidden', **dict(task, thinking='high'))
        self.assert_reason('deny', 'astra_cheaper_eligible_not_ruled_out', **dict(task, no_cheaper_eligible=False))
        self.quotas['codex']['windows'][0]['used_percent'] = 50
        self.assert_reason('deny', 'astra_quota_limit', **task)
        self.quotas['codex']['status'] = 'unknown'
        self.assert_reason('deny', 'astra_quota_unknown', **task)

    def test_quota_threshold_boundaries_and_high_risk_floor(self):
        for index, threshold in ((0, 85), (1, 75)):
            with self.subTest(index=index):
                self.setUp()
                self.quotas['codex']['windows'][index]['used_percent'] = threshold - 0.01
                self.assertEqual(self.decide(risk='low', provider='codex/gpt-6-luna')['decision'], 'allow')
                self.quotas['codex']['windows'][index]['used_percent'] = threshold
                result = self.decide(risk='low', provider='codex/gpt-6-luna')
                self.assertEqual(result['decision'], 'ask_human')
                self.assertTrue(result['alternatives'])
                self.assertTrue(all(not alt['provider'].startswith('codex/') for alt in result['alternatives']))
                self.quotas['claude']['windows'][index]['used_percent'] = threshold
                self.assertEqual(self.decide(provider='claude/opus', mode='default', risk='high')['decision'], 'allow')
        self.assert_reason('deny', 'risk_quality_floor', provider='opencode/glm-5.3-flash-free', mode='build', risk='high')

    def test_restricted_allowed_normalization(self):
        self.restricted['enabled'] = True
        self.assert_reason('deny', 'restricted_model_not_allowed', provider='opencode/unapproved', mode='build', risk='low')
        for label in ('opencode/glm-5.3-flash-free', 'opencode/opencode/glm-5.3-flash-free', 'codex/gpt-6-luna'):
            with self.subTest(label=label):
                result = self.decide(provider=label, mode='auto-review' if label.startswith('codex') else 'build', risk='low')
                self.assertEqual(result['decision'], 'allow', result)
        self.assertFalse(pf.model_allowed('codexevil/model', ['codex']))

    def test_stale_unknown_malformed_quota(self):
        self.quotas['codex']['fetched_at'] = (NOW - timedelta(seconds=901)).isoformat()
        self.assert_reason('ask_human', 'quota_stale')
        self.quotas['codex']['fetched_at'] = (NOW - timedelta(seconds=900)).isoformat()
        self.assertEqual(self.decide()['decision'], 'allow')
        for snapshot in (None, {}, {'provider': 'codex', 'status': 'ok', 'fetched_at': NOW.isoformat(),
                                    'windows': [{'kind': [], 'used_percent': 0}]}):
            self.quotas['codex'] = snapshot
            self.assert_reason('ask_human', 'quota_unknown')

    def test_weekly_alias_and_missing_window(self):
        self.quotas['codex']['windows'][1]['kind'] = 'seven_day'
        self.quotas['codex']['windows'][1]['used_percent'] = 75
        self.assert_reason('ask_human', 'quota_weekly_limit')
        self.quotas['codex']['windows'].pop()
        self.assert_reason('ask_human', 'quota_unknown')

    def test_gate_precedence(self):
        self.quotas['codex'] = None
        self.assert_reason('deny', 'mode_forbidden', mode='full-access', base=None)
        self.assert_reason('deny', 'base_required', base=None)
        result = pf.decide(self.task, self.policy, self.quotas, [{'Provider': 'codex', 'Status': 'running'}], self.restricted)
        self.assertEqual(result['reason_codes'], ['quota_unknown'])

    def test_unknown_agents_requires_human(self):
        result = pf.decide(self.task, self.policy, self.quotas, None, self.restricted)
        self.assertEqual(result['reason_codes'], ['running_agents_unknown'])
        for agent in ({}, {'Provider': None}, {'Provider': 'codex', 'Model': []}, {'Provider': 'codex', 'Status': {}}):
            result = pf.decide(self.task, self.policy, self.quotas, [agent], self.restricted)
            self.assertEqual(result['reason_codes'], ['running_agents_unknown'])

    def test_alternatives_pass_restriction_and_preserve_high_floor(self):
        self.restricted.update(enabled=True, allowed_models=['codex'])
        self.quotas['codex']['windows'][0]['used_percent'] = 85
        self.assertEqual(self.decide()['alternatives'], [])
        self.restricted.update(enabled=False)
        result = self.decide(provider='codex/gpt-6-astra', risk='high', thinking='low', no_cheaper_eligible=True)
        self.assertEqual(result['alternatives'], [{'provider': 'claude/opus', 'mode': 'default', 'thinking': None}])

    def test_happy_pure_no_mutation_or_io(self):
        before = copy.deepcopy((self.task, self.policy, self.quotas, self.restricted))
        with patch.object(pf, '_run', side_effect=AssertionError('I/O')), patch.object(Path, 'read_text', side_effect=AssertionError('I/O')), patch.object(pf, 'datetime', wraps=datetime) as clock:
            clock.now.side_effect = AssertionError('relógio')
            result = self.decide()
            self.assertEqual(self.decide(), result)
        self.assertEqual(result['decision'], 'allow')
        self.assertEqual(result['policy_version'], self.policy['policy_version'])
        self.assertEqual(result['quota_freshness']['status'], 'fresh')
        self.assertEqual(before, (self.task, self.policy, self.quotas, self.restricted))

    def test_reset_exception_short_task_and_boundaries(self):
        window = self.quotas['codex']['windows'][0]
        window['used_percent'] = 85
        for minutes, expected in ((0, 'allow'), (19, 'allow'), (20, 'allow'), (21, 'ask_human'), (-1, 'ask_human')):
            with self.subTest(minutes=minutes):
                window['resets_at'] = (NOW + timedelta(minutes=minutes)).isoformat()
                result = self.decide(short_task=True)
                self.assertEqual(result['decision'], expected, result)
                if expected == 'allow':
                    self.assertEqual(result['reason_codes'], ['quota_reset_exception'])
        window['resets_at'] = (NOW + timedelta(minutes=19)).isoformat()
        self.assertEqual(self.decide()['decision'], 'ask_human')
        for reset in (None, '', 'bad', '2026-11-09T19:10:00'):
            window['resets_at'] = reset
            self.assertEqual(self.decide(short_task=True)['decision'], 'ask_human')
        window['resets_at'] = (NOW + timedelta(minutes=19)).isoformat()
        self.quotas['codex']['windows'][1].update(used_percent=75, resets_at=window['resets_at'])
        self.assert_reason('ask_human', 'quota_weekly_limit', short_task=True)
        self.quotas['codex']['windows'][1]['used_percent'] = 10
        result = pf.decide(dict(self.task, short_task=True), self.policy, self.quotas,
                           [{'Provider': 'codex', 'Model': 'gpt-6-astra', 'Status': 'waiting'}], self.restricted)
        self.assertEqual(result['reason_codes'], ['provider_heavy_concurrency'])

    def test_base_required_only_for_worktree(self):
        for workspace in (None, 'local'):
            self.assertEqual(self.decide(new_workspace=workspace, base=None, base_exists=False)['decision'], 'allow')
            self.assert_reason('deny', 'base_not_found', new_workspace=workspace, base_exists=False)
        self.assert_reason('deny', 'new_workspace_invalid', new_workspace='directory')

    def test_unmetered_opencode_without_quota(self):
        for quotas in (None, {}, {'opencode': None}):
            task = dict(self.task, provider='opencode/opencode/glm-5.3-flash-free', mode='build', risk='low')
            result = pf.decide(task, self.policy, quotas, [], self.restricted)
            self.assertEqual(result['decision'], 'allow', result)
            self.assertEqual(result['quota_freshness']['status'], 'unmetered')
        self.quotas['claude'] = None
        self.assert_reason('ask_human', 'quota_unknown', provider='claude/sonnet', mode='default')

    def test_planned_heavy_added_to_global_active_count(self):
        self.assertEqual(self.decide(planned_heavy=0)['decision'], 'allow')
        self.assert_reason('ask_human', 'provider_heavy_concurrency', planned_heavy=1)
        self.assert_reason('deny', 'planned_heavy_invalid', planned_heavy=-1)
        self.assert_reason('deny', 'planned_heavy_invalid', planned_heavy='1')
        for state in ('running', 'waiting', 'starting', 'unknown', ''):
            result = pf.decide(self.task, self.policy, self.quotas,
                               [{'provider': 'codex', 'model': 'gpt-6-astra', 'status': state, 'archived': True}], self.restricted)
            self.assertEqual(result['decision'], 'ask_human', state)
        for state in ('idle', 'closed', 'error'):
            result = pf.decide(self.task, self.policy, self.quotas,
                               [{'provider': 'codex', 'model': 'gpt-6-astra', 'status': state}], self.restricted)
            self.assertEqual(result['decision'], 'allow', state)

    def test_model_eligibility_not_broadened(self):
        self.assert_reason('deny', 'risk_quality_floor', provider='claude/opus', mode='default', risk='medium')
        self.assert_reason('deny', 'risk_quality_floor', provider='claude/sonnet', mode='default', risk='low')
        self.assert_reason('deny', 'risk_quality_floor', provider='codex/gpt-6.1-sol', risk='low')
        self.assert_reason('deny', 'risk_quality_floor', provider='codex/unknown', risk='low')
        self.assert_reason('deny', 'risk_quality_floor', provider='opencode/unknown', mode='build', risk='low')

    def test_restored_policy_invariants_and_metering_schema(self):
        self.assertEqual(self.policy['acesso_dados'], {
            'pessoal-publico': ['claude', 'codex', 'opencode'],
            'pessoal-restrito': ['claude', 'codex'],
            'institucional': ['claude', 'codex', 'opencode/glm-5.3-flash-free',
                              'opencode/deepseek-v4.1-flash-free'],
        })
        self.assertIn('Claude/Codex = assinaturas, não gateway', self.policy['nota_institucional'])
        self.assertEqual(self.policy['reviewers']['high'], {'different_model_family': True})
        self.assertEqual(self.policy['reviewers']['medium'], {
            'order': ['outro harness elegível', 'codex/gpt-6.1-sol', 'codex/gpt-6-luna'],
            'sol_thinking': ['low', 'medium'], 'luna_only_mechanical': True,
        })
        self.assertEqual(self.policy['guardrails']['limite_fallback'], 2)
        self.assertTrue({'acesso_dados', 'nota_institucional', 'reviewers',
                         'guardrails.limite_fallback'} <= set(self.policy['documented_only']))
        self.assertNotIn('restricted_config', self.policy)
        for provider, expected in (('claude', True), ('codex', True), ('opencode', False)):
            self.assertIs(self.policy['providers'][provider]['quota_metered'], expected)
            for invalid in (None, 0, 1, 'false'):
                with self.subTest(provider=provider, invalid=invalid):
                    bad = copy.deepcopy(self.policy)
                    bad['providers'][provider]['quota_metered'] = invalid
                    with self.assertRaises(ValueError):
                        pf.validate_policy(bad)

    def test_schema_required_types_and_keys(self):
        mutations = [('schema_version', '3'), ('policy_version', None), ('providers', []), ('astra', {}), ('quota', {}), ('concurrency', {})]
        for key, value in mutations:
            with self.subTest(key=key):
                bad = dict(self.policy, **{key: value})
                result = pf.decide(self.task, bad, self.quotas, [], self.restricted)
                self.assertEqual(result['reason_codes'], ['policy_invalid'])
        bad = copy.deepcopy(self.policy)
        bad['providers']['codex']['thinking_required'] = 1
        with self.assertRaises(ValueError):
            pf.validate_policy(bad)

    def test_documentary_consistency(self):
        for name in DOCS:
            with self.subTest(doc=name):
                text = (ROOT / name).read_text()
                self.assertEqual(documentary_errors(text, self.policy), [])
                if name in DOCS[:2]:
                    self.assertIn('roteamento.json', text)
                    self.assertIn('scripts/preflight.py', text)
                    minutes = self.policy['quota']['reset_exception']['max_minutes_to_reset']
                    self.assertRegex(text, str(minutes) + r'\s*(?:min|minutes)')
                    self.assertRegex(text.lower(), r'(?:one heavy codex task at a time|uma tarefa pesada do codex por vez)')
                if '0002-' in name:
                    self.assertRegex(text, str(self.policy['quota']['reset_exception']['max_minutes_to_reset']) + r'\s*min')

    def test_documentary_checker_detects_mutated_rules(self):
        for original, mutation in [('5h ≥85%', '5h ≥86%'), ('semanal ≥75%', 'semanal ≥76%'),
                                   ('Codex 5h <50%', 'Codex 5h <51%'),
                                   ('Codex 5h < 50%', 'Codex 5h < 51%'),
                                   ('5h ≥85% ou semanal ≥75%', '5h ≥85% ou semanal ≥76%'),
                                   ('Do not use full-access', 'Use full-access'),
                                   ('Never use full-access', 'Use full-access'),
                                   ('Tarefa curta a 20 min do reset', 'Tarefa curta a 21 min do reset'),
                                   ('Uma tarefa pesada do Codex por vez', 'Duas tarefas pesadas do Codex por vez'),
                                   ('One heavy Codex task at a time', 'Two heavy Codex tasks at a time'),
                                   ('Medição: 5h ≥85%', 'Medição: 5h ≥86%'),
                                   ('Medição:5h >85%', 'Medição:5h >86%')]:
            self.assertEqual(documentary_errors(original, self.policy), [])
            self.assertTrue(documentary_errors(mutation, self.policy), mutation)
        self.assertEqual(documentary_errors('Uma medição consumiu 27% da janela 5h.', self.policy), [])


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)
        self.config = self.path / 'restricted.toml'
        self.config.write_text('[restricted]\npaths=[]\nallowed_models=["codex"]\n')
        self.args = ['--provider', 'codex/gpt-6.1-sol', '--mode', 'auto-review', '--thinking', 'medium',
                     '--base', 'HEAD', '--cwd', str(ROOT), '--risk', 'medium', '--quota-dir', str(self.path),
                     '--restricted-config', str(self.config), '--now', NOW.isoformat()]
        for provider in ('codex', 'claude'):
            (self.path / (provider + '.json')).write_text(json.dumps({'provider': provider, 'status': 'ok',
                'fetched_at': NOW.isoformat(), 'windows': [{'kind': 'five_hour', 'used_percent': 0}, {'kind': 'weekly', 'used_percent': 0}]}))

    def call(self, *more):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = pf.main(self.args + list(more))
        return code, json.loads(out.getvalue())

    def test_cli_only_calls_paseo_ls_never_run(self):
        real = pf._run
        calls = []
        def run(argv, cwd=None):
            calls.append(argv)
            if argv[0] == 'paseo':
                self.assertEqual(argv, ['paseo', 'ls', '--json', '-a', '-g', '--background'])
                return subprocess.CompletedProcess(argv, 0, '[{"Provider":"codex","Model":"gpt-6-luna","Status":"running"}]', '')
            return real(argv, cwd)
        with patch.object(pf, '_run', side_effect=run):
            code, result = self.call()
        self.assertEqual(code, 0)
        self.assertEqual(result['decision'], 'allow')
        self.assertTrue(any(argv[0] == 'paseo' for argv in calls))

    def test_cli_agents_fixture_and_invalid_json(self):
        fixture = self.path / 'agents.json'
        fixture.write_text('[]')
        self.assertEqual(self.call('--agents-file', str(fixture))[0], 0)
        fixture.write_text('{bad')
        code, result = self.call('--agents-file', str(fixture))
        self.assertEqual((code, result['reason_codes']), (2, ['running_agents_unknown']))
        code, result = self.call('--policy', str(fixture))
        self.assertEqual((code, result['reason_codes']), (1, ['preflight_input_error']))

    def test_cli_fails_closed_restriction_and_missing_base(self):
        self.config.write_text('bad toml')
        self.assertEqual(self.call()[0], 1)
        self.config.write_text('[restricted]\npaths=[]\nallowed_models=["codex"]\n')
        code, result = self.call('--base', 'branch-that-does-not-exist')
        self.assertEqual((code, result['reason_codes']), (1, ['base_not_found']))

    def test_linked_worktree_classification_and_failure(self):
        (self.path / '.git').write_text('gitdir: /nonexistent')
        self.config.write_text(f'[restricted]\npaths=["{self.path.parent / "institution"}"]\nallowed_models=["codex"]\n')
        with patch.object(pf, 'git', return_value=str(self.path.parent / 'institution/.git')):
            self.assertTrue(pf.load_restricted(self.path, self.config)['enabled'])
        with patch.object(pf, 'git', return_value=None), self.assertRaises(ValueError):
            pf.load_restricted(self.path, self.config)

    def test_cli_arguments_errors_are_json_and_cwd_required(self):
        script = str(ROOT / 'scripts/preflight.py')
        without_cwd = self.args.copy()
        index = without_cwd.index('--cwd')
        del without_cwd[index:index + 2]
        for args in (without_cwd, self.args + ['--new-workspace', 'directory'],
                     self.args + ['--risk', 'invalid'], self.args + ['--planned-heavy', 'bad'],
                     self.args + ['--unknown-option']):
            proc = subprocess.run([sys.executable, script, *args], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 1, proc.stderr)
            self.assertEqual(json.loads(proc.stdout)['decision'], 'deny')
            self.assertNotIn('Traceback', proc.stderr)
        proc = subprocess.run([sys.executable, script, '--help'], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)

    def test_cli_workspace_base_semantics(self):
        args = self.args.copy()
        index = args.index('--base')
        del args[index:index + 2]
        fixture = self.path / 'agents.json'
        fixture.write_text('[]')
        for workspace in ([], ['--new-workspace', 'local']):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = pf.main(args + workspace + ['--agents-file', str(fixture)])
            self.assertEqual((code, json.loads(out.getvalue())['decision']), (0, 'allow'))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = pf.main(args + ['--new-workspace', 'worktree', '--agents-file', str(fixture)])
        self.assertEqual((code, json.loads(out.getvalue())['reason_codes']), (1, ['base_required']))

    def test_paseo_unavailable_is_unknown(self):
        with patch.object(pf, 'read_agents', side_effect=OSError('unavailable')):
            self.assertEqual(self.call()[1]['reason_codes'], ['running_agents_unknown'])


if __name__ == '__main__':
    unittest.main()
