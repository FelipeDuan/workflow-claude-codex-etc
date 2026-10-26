import importlib.util
import json
import os
import subprocess
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
        self.quota_patch = patch.object(watchdog, 'refresh_quota')
        self.quota_patch.start()
        self.addCleanup(self.quota_patch.stop)
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
             patch.object(watchdog.subprocess, 'run', return_value=MagicMock(returncode=0)) as osascript:
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
             patch.object(watchdog.subprocess, 'run', return_value=MagicMock(returncode=0)) as osascript:
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
        self.assertEqual(action, 'notify')
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


    def restricted_policy(self):
        self.memory.write_text(
            '[restricted]\npaths = ["' + str(self.worktrees) + '"]\n'
            'allowed_models = ["claude", "codex", "opencode/deepseek-v4.1-flash-free"]\n'
        )

    def test_modelos_permitidos_aprovam_em_projeto_restrito(self):
        self.restricted_policy()
        for provider, model in [('opencode', 'opencode/opencode/deepseek-v4.1-flash-free'),
                                ('claude', 'claude-opus'), ('codex', 'gpt-6.1-sol')]:
            with self.subTest(provider=provider):
                agent = self.agent()
                agent.update(Provider=provider, Model=model)
                fake = FakePaseo([agent], [self.permit()])
                self.run_watchdog(fake)
                self.assertIn(('permit', 'allow', 'a1', 'req1'), fake.calls)

    def test_modelo_proibido_alerta_alto_sem_aprovar(self):
        self.restricted_policy()
        agent = self.agent()
        agent['Model'] = 'outro-modelo'
        fake = FakePaseo([agent], [self.permit()])
        _, notifications = self.run_watchdog(fake)
        self.assertNotIn(('permit', 'allow', 'a1', 'req1'), fake.calls)
        self.assertIn('prioridade alta', notifications.call_args.args[0][2])
        self.assertIn('modelo não permitido em projeto restrito', notifications.call_args.args[0][2])
        self.assertTrue(self.state()['agents']['a1']['modelo_bloqueado'])
        self.assertIn('modelo_nao_permitido', (self.state_dir / 'watchdog.log').read_text())

    def test_modelo_proibido_e_detectado_sem_pedido(self):
        self.restricted_policy()
        agent = self.agent()
        agent['Model'] = 'outro'
        _, notifications = self.run_watchdog(FakePaseo([agent]))
        self.assertEqual(notifications.call_count, 1)
        self.assertTrue(self.snapshot()[0]['modelo_bloqueado'])

    def test_restricao_herdada_do_checkout_principal(self):
        main = self.outside / 'restrito'
        main.mkdir()
        (main / '.git').mkdir()
        (self.agent_cwd / '.git').write_text('gitdir: ignored')
        with patch.object(watchdog, '_git', return_value=str(main / '.git')):
            self.assertTrue(watchdog.is_restricted(str(self.agent_cwd), [main]))
        with patch.object(watchdog, '_git', return_value=None):
            with self.assertRaises(watchdog.PolicyError):
                watchdog.is_restricted(str(self.agent_cwd), [main])
            fake = FakePaseo([self.agent()], [self.permit()])
            self.run_watchdog(fake)
            self.assertNotIn(('permit', 'allow', 'a1', 'req1'), fake.calls)

    def test_marcador_restrito_ancestral_e_invalido(self):
        (self.worktrees / '.ai-memory.toml').write_text('workspace = "restrito"')
        (self.agent_cwd / '.ai-memory.toml').write_text('workspace = "pessoal"')
        self.assertTrue(watchdog.is_restricted(str(self.agent_cwd), []))
        (self.agent_cwd / '.ai-memory.toml').write_text('workspace = [')
        with self.assertRaises(watchdog.PolicyError):
            watchdog.is_restricted(str(self.agent_cwd), [])

    def test_allowed_roots_corrigidas_e_worktree_manual(self):
        policy = watchdog.load_policy(ROOT / 'config/paseo-watchdog-policy.toml')
        for relative in ['Workspace/projetos/sgg-controle/sgg-v3/sgg-v3-docs',
                         'Workspace/tools/laboratorio', '.paseo/worktrees/manual/repo']:
            self.assertTrue(watchdog.cwd_allowed(str(Path.home() / relative), policy, [])[0])
        self.assertFalse(watchdog.cwd_allowed(str(Path.home() / 'Workspace/projetos/sgg-v3-docs'), policy, [])[0])

    def test_fantasmas_nao_repetem_nem_apos_desaparecer(self):
        for failure in ['handler_error', '404', 'unconfirmed']:
            with self.subTest(failure=failure):
                self.seed_state()
                fake = FakePaseo([self.agent()], [self.permit()])
                def failing(args, check=True):
                    if args[:2] == ['permit', 'allow']:
                        fake.calls.append(tuple(args))
                        raise watchdog.PaseoError(failure)
                    return fake(args, check)
                _, notifications = self.run_watchdog(failing)
                self.assertEqual(notifications.call_count, 1)
                self.assertIn('pedido fantasma', notifications.call_args.args[0][2])
                self.assertEqual(self.snapshot()[0]['status'], 'pedido_fantasma')
                self.assertTrue(self.state()['permissions']['req1']['ghost'])
                with patch.object(watchdog, '_now', return_value=NOW + timedelta(hours=1)):
                    self.run_watchdog(FakePaseo([]))
                    _, again = self.run_watchdog(failing)
                self.assertEqual(again.call_count, 0)
                self.assertEqual(fake.calls.count(('permit', 'allow', 'a1', 'req1')), 1)

    def test_resposta_unconfirmed_com_exit_zero_vira_fantasma(self):
        fake = FakePaseo([self.agent()], [self.permit()])
        def unconfirmed(args, check=True):
            return 'unconfirmed' if args[:2] == ['permit', 'allow'] else fake(args, check)
        self.run_watchdog(unconfirmed)
        self.assertTrue(self.state()['permissions']['req1']['ghost'])

    def test_cli_detecta_fantasma_em_stderr_ou_stdout_com_allow_e_deny(self):
        for action in ['allow', 'deny']:
            for channel in ['stdout', 'stderr']:
                for rc in [0, 1]:
                    with self.subTest(action=action, channel=channel, rc=rc):
                        result = subprocess.CompletedProcess([], rc, stdout='', stderr='')
                        setattr(result, channel, 'x' * 300 + ' handler_error 404')
                        with patch.object(watchdog.subprocess, 'run', return_value=result):
                            with self.assertRaises(watchdog.PhantomPermission):
                                watchdog.run_paseo(['permit', action, 'a1', 'req1'])

    def test_question_imediata_mesmo_com_allow_generico_e_tipo_separado(self):
        self.policy.write_text('allowed_roots = ["' + str(self.worktrees) + '"]\n'
                               '[[rules]]\naction = "allow"\nname = "bash"\n')
        permit = self.permit(description='ls')
        permit['type'] = 'question'
        fake = FakePaseo([self.agent()], [permit])
        _, notifications = self.run_watchdog(fake)
        self.assertNotIn(('permit', 'allow', 'a1', 'req1'), fake.calls)
        self.assertEqual(notifications.call_count, 1)
        self.assertIn('prioridade alta', notifications.call_args.args[0][2])

    def test_estados_sem_entrega_notificam(self):
        for raw in ['idle', 'closed', 'error']:
            with self.subTest(status=raw):
                self.seed_state()
                with patch.object(watchdog, 'no_delivery', return_value=True):
                    _, notifications = self.run_watchdog(FakePaseo([self.agent(status=raw)]))
                self.assertEqual(self.snapshot()[0]['status'], 'parado_sem_entrega')
                self.assertEqual(notifications.call_count, 1)

    def test_no_delivery_exige_worktree_limpo_sem_commit_e_git_confiavel(self):
        agent = self.agent(status='idle')
        (self.agent_cwd / '.git').write_text('gitdir: ignored')
        answers = ['/repo/.git/worktrees/w', '/repo/.git', '', '']
        with patch.object(watchdog, '_git', side_effect=answers):
            self.assertTrue(watchdog.no_delivery(agent))
        for changes, commits in [('?? novo.py', ''), (' M x.py', ''), ('', 'sha'), (None, ''), ('', None)]:
            with self.subTest(changes=changes, commits=commits):
                with patch.object(watchdog, '_git', side_effect=answers[:2] + [changes, commits]):
                    self.assertFalse(watchdog.no_delivery(agent))
        with patch.object(watchdog, '_git', return_value='/repo/.git'):
            self.assertFalse(watchdog.no_delivery(agent))
        agent.pop('CreatedAt')
        self.assertFalse(watchdog.no_delivery(agent))

    def test_no_delivery_com_git_real(self):
        repo = self.outside / 'repo'
        repo.mkdir()
        def git(*args):
            return subprocess.run(['git', '-C', str(repo), *args], check=True,
                                  capture_output=True, text=True).stdout
        git('init')
        git('-c', 'user.name=Teste', '-c', 'user.email=teste@example.invalid',
            'commit', '--allow-empty', '-m', 'base')
        git('worktree', 'add', '-b', 'teste', str(self.agent_cwd))
        agent = self.agent(status='idle')
        agent['CreatedAt'] = iso(watchdog.datetime.now(timezone.utc) + timedelta(seconds=2))
        self.assertTrue(watchdog.no_delivery(agent))
        (self.agent_cwd / 'novo.txt').write_text('entrega')
        self.assertFalse(watchdog.no_delivery(agent))
        subprocess.run(['git', '-C', str(self.agent_cwd), 'add', 'novo.txt'], check=True, capture_output=True)
        subprocess.run(['git', '-C', str(self.agent_cwd), '-c', 'user.name=Teste',
                        '-c', 'user.email=teste@example.invalid', 'commit', '-m', 'entrega'],
                       check=True, capture_output=True)
        agent['CreatedAt'] = iso(watchdog.datetime.now(timezone.utc) - timedelta(seconds=2))
        self.assertFalse(watchdog.no_delivery(agent))

    def test_quota_cada_cinco_minutos_e_dry_run_sem_sensor(self):
        self.quota_patch.stop()
        state = watchdog._empty_state()
        log = self.state_dir / 'watchdog.log'
        with patch.object(watchdog.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '{"status":"ok"}', '')) as run:
            watchdog.refresh_quota(state, NOW, False, log)
            watchdog.refresh_quota(state, NOW + timedelta(minutes=4, seconds=59), False, log)
            self.assertEqual(run.call_count, 1)
            self.assertEqual(run.call_args.args[0], ['python3', str(ROOT / 'scripts/quota_codex.py'), '--write'])
            self.assertGreater(run.call_args.kwargs['timeout'], 20)
            watchdog.refresh_quota(state, NOW + timedelta(minutes=5), False, log)
            self.assertEqual(run.call_count, 2)
            before = dict(state)
            watchdog.refresh_quota(state, NOW + timedelta(minutes=10), True, log)
            self.assertEqual(run.call_count, 2)
            self.assertEqual(state, before)

    def test_quota_falha_ainda_tenta_so_a_cada_cinco_minutos(self):
        self.quota_patch.stop()
        state = watchdog._empty_state()
        with patch.object(watchdog.subprocess, 'run', side_effect=subprocess.TimeoutExpired('quota', 30)) as run:
            watchdog.refresh_quota(state, NOW, False, self.state_dir / 'watchdog.log')
            watchdog.refresh_quota(state, NOW + timedelta(minutes=1), False, self.state_dir / 'watchdog.log')
        self.assertEqual(run.call_count, 1)
        self.assertIn('quota_error', (self.state_dir / 'watchdog.log').read_text())

    def test_quota_e_chamada_mesmo_quando_paseo_falha(self):
        with patch.object(watchdog, 'run_paseo', side_effect=watchdog.PaseoError('offline')), \
             patch.object(watchdog.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '', '')):
            self.assertEqual(watchdog.main(['--once']), 1)
        self.assertEqual(watchdog.refresh_quota.call_count, 1)

    def test_decisao_usa_descricao_inteira_sem_mascarar_segredos(self):
        for description in ['ls ' + 'x' * 210 + '; rm -rf x',
                            'ls secret="rm -rf x"', 'ls\npython3 maligno.py']:
            with self.subTest(description=description):
                fake = FakePaseo([self.agent()], [self.permit(description=description)])
                self.run_watchdog(fake)
                self.assertNotIn(('permit', 'allow', 'a1', 'req1'), fake.calls)

    def test_inspect_falho_nunca_aprova_pelo_cwd_da_listagem(self):
        agent = self.agent()
        fake = FakePaseo([agent], [self.permit()])
        def broken(args, check=True):
            if args[:1] == ['inspect']:
                raise watchdog.PaseoError('offline')
            return fake(args, check)
        self.run_watchdog(broken)
        self.assertNotIn(('permit', 'allow', 'a1', 'req1'), fake.calls)

    def test_comandos_compostos_opacos_e_caminhos_externos_ficam_humanos(self):
        policy = watchdog.load_policy(ROOT / 'config/paseo-watchdog-policy.toml')
        (self.agent_cwd / 'link').symlink_to(self.outside)
        (self.agent_cwd / '123').symlink_to(self.outside / 'segredo.txt')
        (self.agent_cwd / 'normal').symlink_to(self.agent_cwd / '.env')
        descriptions = ['ls; python3 ataque.py', 'ls > entrega', 'ls $(touch entrega)',
                        'ls `touch entrega`', 'cat /etc/passwd', 'cat ../fora', 'cat link/x',
                        'cat 123', 'cat *', 'cat normal', 'cat .e""nv', 'git diff --output=arquivo', 'git commit -m x',
                        "sed -n '1e touch x' arquivo", 'rg --pre=ataque x', 'ls && echo x']
        for description in descriptions:
            with self.subTest(description=description):
                self.assertNotEqual(watchdog.decide(policy, 'shell', description, str(self.agent_cwd), [])[0], 'allow')

    def test_dry_run_nao_grava_logs_em_falha_de_schedule(self):
        fake = FakePaseo([self.agent()])
        def broken(args, check=True):
            if args[:2] == ['schedule', 'ls']:
                raise watchdog.PaseoError('offline')
            return fake(args, check)
        self.run_watchdog(broken, ['--dry-run', '--once'])
        self.assertFalse((self.state_dir / 'watchdog.log').exists())
        self.assertFalse((self.state_dir / 'watchdog-state.json').exists())

    def test_snapshot_vazio_substitui_agentes_anteriores(self):
        self.run_watchdog(FakePaseo([self.agent()]))
        self.run_watchdog(FakePaseo([]))
        self.assertEqual(self.snapshot(), [])


    def test_dry_run_nao_grava_logs_em_falha_dos_logs_de_schedule(self):
        fake = FakePaseo([], schedules=[{'id': 's1', 'lastRunAt': iso(NOW)}])
        def broken(args, check=True):
            if args[:2] == ['schedule', 'logs']:
                raise watchdog.PaseoError('offline')
            return fake(args, check)
        self.run_watchdog(broken, ['--dry-run', '--once'])
        self.assertFalse((self.state_dir / 'watchdog.log').exists())
        self.assertFalse((self.state_dir / 'watchdog-state.json').exists())

    def test_instalador_dry_run_nao_chama_uv_graphify(self):
        bindir = Path(self.tmp.name) / 'bin'
        bindir.mkdir()
        marker = Path(self.tmp.name) / 'uv-called'
        uv = bindir / 'uv'
        uv.write_text('#!/bin/sh\ntouch "' + str(marker) + '"\nexit 93\n')
        uv.chmod(0o755)
        env = dict(os.environ, PATH=str(bindir) + ':/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin')
        result = subprocess.run(['bash', str(ROOT / 'install.sh'), '--dry-run', '--no-mcp', '--only', 'codex'],
                                env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(marker.exists())
        self.assertIn('Graphify', result.stdout)

    def test_notify_nao_marca_sucesso_se_osascript_falhar(self):
        state = watchdog._empty_state()
        with patch.object(watchdog.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, '', 'erro')):
            self.assertFalse(watchdog.notify(state, NOW, 'key', 'titulo', 'msg', False))
        self.assertEqual(state['notifications'], {})


    def test_git_do_vigia_desativa_fsmonitor_do_repositorio(self):
        result = subprocess.CompletedProcess([], 0, '', '')
        with patch.object(watchdog.subprocess, 'run', return_value=result) as run:
            self.assertEqual(watchdog._git(str(self.agent_cwd), 'status', '--porcelain'), '')
        self.assertEqual(run.call_args.args[0], [
            'git', '-c', 'core.fsmonitor=false', '--no-optional-locks',
            '-C', str(self.agent_cwd), 'status', '--porcelain',
        ])


if __name__ == '__main__':
    unittest.main()
