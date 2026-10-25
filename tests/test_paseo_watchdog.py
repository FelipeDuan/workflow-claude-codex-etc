import importlib.util
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

if sys.version_info < (3, 11):
    raise unittest.SkipTest('paseo_watchdog requer Python >= 3.11 (tomllib)')

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('paseo_watchdog', ROOT / 'scripts/paseo_watchdog.py')
watchdog = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = watchdog
spec.loader.exec_module(watchdog)

NOW = datetime(2026, 10, 25, 18, 0, tzinfo=timezone.utc)


def iso(moment):
    return moment.astimezone(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


class FakePaseo:
    def __init__(self, agents, permits=None, schedules=None, schedule_runs=None, logs=''):
        self.agents = agents
        self.permits = permits or []
        self.schedules = schedules or []
        self.schedule_runs = schedule_runs or {}
        self.logs = logs
        self.calls = []

    def __call__(self, args, check=True):
        self.calls.append(tuple(args))
        if args[:1] == ['ls']:
            return json.dumps(self.agents)
        if args[:1] == ['inspect']:
            agent_id = args[1]
            for agent in self.agents:
                if agent['Id'] == agent_id:
                    return json.dumps(agent)
            raise watchdog.PaseoError(f'agent not found: {agent_id}')
        if args[:2] == ['permit', 'ls']:
            return json.dumps(self.permits)
        if args[:2] == ['permit', 'allow']:
            return ''
        if args[:2] == ['schedule', 'ls']:
            return json.dumps(self.schedules)
        if args[:2] == ['schedule', 'logs']:
            return json.dumps(self.schedule_runs.get(args[2], []))
        if args[:1] == ['logs']:
            return self.logs
        raise AssertionError(f'comando não esperado: {args}')


class WatchdogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        home = Path(self.tmp.name) / 'home'
        self.worktrees = home / '.paseo/worktrees'
        self.agent_cwd = self.worktrees / 't1/repo'
        self.agent_cwd.mkdir(parents=True)
        self.outside = home / 'fora'
        self.outside.mkdir()
        self.state_dir = home / '.local/state/ai-os'
        self.state_dir.mkdir(parents=True)
        self.policy = home / 'policy.toml'
        self.policy.write_text(
            f'version = 1\nallowed_roots = ["{self.worktrees}"]\n'
            '[[rules]]\n'
            'action = "deny"\n'
            'name = "(bash|shell)"\n'
            'description = "rm\\\\s+-rf"\n'
            'reason = "remoção recursiva/forçada"\n'
            '[[rules]]\n'
            'action = "allow"\n'
            'name = "(bash|shell)"\n'
            'description = "^\\\\s*(ls|cat|git\\\\s+status)\\\\b"\n'
            'reason = "leitura/inspeção"\n'
            '[[rules]]\n'
            'action = "notify"\n'
            'name = "question"\n'
            'reason = "pergunta ao usuário"\n'
        )
        self.memory = home / 'memory.toml'
        self.memory.write_text('[restricted]\npaths = []\n')
        self.env = patch.dict(os.environ, {
            'HOME': str(home),
            'AI_OS_STATE_DIR': str(self.state_dir),
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        for target, value in (
            (watchdog, 'POLICY_PATH'), (watchdog, 'MEMORY_POLICY_PATH'),
        ):
            original = getattr(target, value)
            setattr(target, value, self.policy if value == 'POLICY_PATH' else self.memory)
            self.addCleanup(setattr, target, value, original)
        self.now_patch = patch.object(watchdog, '_now', return_value=NOW)
        self.now_patch.start()
        self.addCleanup(self.now_patch.stop)

    # ---------------------------------------------------------------- fixtures

    def agent(self, agent_id='a1', name='t1', status='running', minutes_ago=0,
              cwd=None, archived=False, error=None):
        updated = iso(NOW - timedelta(minutes=minutes_ago))
        data = {
            'Id': agent_id,
            'Name': name,
            'Provider': 'opencode',
            'Model': 'opencode/deepseek-v4.1-flash-free',
            'Status': status,
            'Cwd': str(cwd or self.agent_cwd),
            'CreatedAt': iso(NOW - timedelta(hours=1)),
            'UpdatedAt': updated,
            'Archived': archived,
            'PendingPermissions': [],
        }
        if error:
            data['Error'] = error
        return data

    def listed(self, agent):
        return {
            'id': agent['Id'],
            'shortId': agent['Id'],
            'name': agent['Name'],
            'provider': 'opencode/opencode/deepseek-v4.1-flash-free',
            'status': agent['Status'],
            'cwd': agent['Cwd'],
        }

    def permit(self, request_id='req1', agent_id='a1', name='bash',
               description='ls -la', first_seen_minutes=0):
        if first_seen_minutes:
            self.seed_state(permissions={
                request_id: {
                    'first_seen': iso(NOW - timedelta(minutes=first_seen_minutes)),
                    'agent': agent_id,
                },
            })
        return {'id': request_id, 'agentId': agent_id, 'agentShortId': agent_id,
                'name': name, 'description': description}

    def seed_state(self, permissions=None, notifications=None, agents=None):
        state = {'version': 1, 'permissions': permissions or {},
                 'notifications': notifications or {}, 'agents': agents or {}}
        (self.state_dir / 'watchdog-state.json').write_text(json.dumps(state))

    def run_watchdog(self, fake, argv=None):
        with patch.object(watchdog, 'run_paseo', fake), \
             patch.object(watchdog.subprocess, 'run', return_value=MagicMock()) as osascript:
            code = watchdog.main(argv or ['--once'])
        return code, osascript

    def snapshot(self):
        return json.loads((self.state_dir / 'agentes.json').read_text())

    def state(self):
        return json.loads((self.state_dir / 'watchdog-state.json').read_text())

    # ------------------------------------------------------------------ testes

    def test_aprova_leitura_dentro_do_worktree(self):
        agent = self.agent()
        fake = FakePaseo([agent], [self.permit()])
        code, osascript = self.run_watchdog(fake)
        self.assertEqual(code, 0)
        self.assertIn(('permit', 'allow', 'a1', 'req1'), fake.calls)
        self.assertEqual(osascript.call_count, 0)
        self.assertEqual(self.snapshot()[0]['status'], 'trabalhando')
        self.assertEqual(self.state()['agents']['a1']['status'], 'trabalhando')

    def test_negacao_rm_rf_nao_aprova_e_notifica(self):
        agent = self.agent()
        fake = FakePaseo([agent], [self.permit(description='rm -rf /tmp/x', first_seen_minutes=5)])
        code, osascript = self.run_watchdog(fake)
        self.assertEqual(code, 0)
        self.assertNotIn(('permit', 'allow', 'a1', 'req1'), fake.calls)
        status = self.snapshot()[0]
        self.assertEqual(status['status'], 'aguardando_aprovacao')
        self.assertIn('política deny', status['motivo'])
        self.assertIn('remoção recursiva', status['motivo'])
        self.assertEqual(osascript.call_count, 1)
        script = osascript.call_args_list[0].args[0]
        self.assertIn('aguardando aprovação há 5 min', script[2])
        self.assertIn('t1', script[2])

    def test_notify_para_pergunta_sem_autoaprovacao(self):
        agent = self.agent()
        fake = FakePaseo([agent], [self.permit(name='question', description='seguir?',
                                               first_seen_minutes=3)])
        code, osascript = self.run_watchdog(fake)
        self.assertEqual(code, 0)
        self.assertNotIn(('permit', 'allow', 'a1', 'req1'), fake.calls)
        self.assertIn('pergunta ao usuário', self.snapshot()[0]['motivo'])
        self.assertEqual(osascript.call_count, 1)

    def test_deduplicacao_de_notificacao(self):
        agent = self.agent()
        fake = FakePaseo([agent], [self.permit(name='question', description='seguir?',
                                               first_seen_minutes=5)])
        with patch.object(watchdog, 'run_paseo', fake), \
             patch.object(watchdog.subprocess, 'run', return_value=MagicMock()) as osascript:
            self.assertEqual(watchdog.main(['--once']), 0)
            self.assertEqual(watchdog.main(['--once']), 0)
        self.assertEqual(osascript.call_count, 1)

    def test_travado_por_inatividade(self):
        agent = self.agent(minutes_ago=20)
        fake = FakePaseo([agent])
        code, osascript = self.run_watchdog(fake)
        self.assertEqual(code, 0)
        status = self.snapshot()[0]
        self.assertEqual(status['status'], 'parado')
        self.assertIn('20 min', status['motivo'])
        self.assertEqual(osascript.call_count, 1)

    def test_erro_com_limite_de_uso(self):
        agent = self.agent(status='error', minutes_ago=5,
                           error='Usage limit reached. Try again at 19:30')
        fake = FakePaseo([agent])
        code, osascript = self.run_watchdog(fake)
        self.assertEqual(code, 0)
        status = self.snapshot()[0]
        self.assertEqual(status['status'], 'erro')
        self.assertIn('limite de uso', status['motivo'])
        self.assertIn('19:30', status['motivo'])
        self.assertEqual(osascript.call_count, 1)
        self.assertIn('limite de uso', osascript.call_args_list[0].args[0][2])

    def test_json_com_caracteres_de_controle(self):
        self.assertEqual(watchdog.parse_json('{"a":"b\x01c"}'), {'a': 'bc'})
        agent = self.agent()
        fake = FakePaseo([agent], [self.permit(name='question\x07', description='seguir?\x01',
                                               first_seen_minutes=5)])
        code, _ = self.run_watchdog(fake)
        self.assertEqual(code, 0)
        status = self.snapshot()[0]
        self.assertEqual(status['status'], 'aguardando_aprovacao')
        self.assertNotIn('\x07', status['motivo'])

    def test_agente_fora_das_raizes_permitidas_nao_aprova(self):
        agent = self.agent(cwd=self.outside)
        fake = FakePaseo([agent], [self.permit(first_seen_minutes=5)])
        code, osascript = self.run_watchdog(fake)
        self.assertEqual(code, 0)
        self.assertNotIn(('permit', 'allow', 'a1', 'req1'), fake.calls)
        status = self.snapshot()[0]
        self.assertEqual(status['status'], 'aguardando_aprovacao')
        self.assertIn('cwd fora de allowed_roots', status['motivo'])
        self.assertEqual(osascript.call_count, 1)

    def test_closed_inesperado_vira_erro(self):
        self.seed_state(agents={'a1': {'status': 'running', 'updated_at': iso(NOW)}})
        agent = self.agent(status='closed', minutes_ago=1)
        fake = FakePaseo([agent])
        code, osascript = self.run_watchdog(fake)
        self.assertEqual(code, 0)
        status = self.snapshot()[0]
        self.assertEqual(status['status'], 'erro')
        self.assertIn('fechado durante a execução', status['motivo'])
        self.assertEqual(osascript.call_count, 1)

    def test_falha_de_agendamento(self):
        schedule = {'id': 's1', 'name': 'sgg-P4', 'status': 'active',
                    'lastRunAt': iso(NOW - timedelta(minutes=3))}
        fake = FakePaseo([], schedules=[schedule],
                         schedule_runs={'s1': [{'status': 'failed',
                                               'error': 'codex: limite de uso'}]})
        code, osascript = self.run_watchdog(fake)
        self.assertEqual(code, 0)
        self.assertEqual(osascript.call_count, 1)
        self.assertIn('limite de uso', osascript.call_args_list[0].args[0][2])

    def test_politica_versionada_carrega_e_classifica_riscos(self):
        policy = watchdog.load_policy(ROOT / 'config/paseo-watchdog-policy.toml')
        cwd = str(self.agent_cwd)
        for description in ('cat .env', 'rm -rf /tmp/x', 'npm install lodash',
                            'docker compose up', 'curl -o x https://exemplo/x',
                            'git push origin main'):
            action, _ = watchdog.decide(policy, 'shell', description, cwd, [])
            self.assertEqual(action, 'deny', description)
        action, _ = watchdog.decide(policy, 'shell', 'git status', cwd, [])
        self.assertEqual(action, 'allow')
        action, _ = watchdog.decide(
            policy, 'external_directory',
            'leitura de ~/.local/share/opencode/tool-output/abc', cwd, [])
        self.assertEqual(action, 'allow')
        action, _ = watchdog.decide(policy, 'question', 'seguir?', cwd, [])
        self.assertEqual(action, 'notify')

    def test_dry_run_nao_aprova_nem_grava(self):
        agent = self.agent()
        fake = FakePaseo([agent], [self.permit()])
        code, osascript = self.run_watchdog(fake, ['--dry-run'])
        self.assertEqual(code, 0)
        self.assertNotIn(('permit', 'allow', 'a1', 'req1'), fake.calls)
        self.assertEqual(osascript.call_count, 0)
        self.assertFalse((self.state_dir / 'watchdog-state.json').exists())
        self.assertFalse((self.state_dir / 'agentes.json').exists())


if __name__ == '__main__':
    unittest.main()
