import importlib.util
import contextlib
import io
import json
import os
import shlex
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
NEW_PYTHON = sys.version_info >= (3, 11)
hygiene = None
if NEW_PYTHON:  # o módulo sai com mensagem clara em Python < 3.11 (tomllib); ver OldPython abaixo
    sys.path.insert(0, str(ROOT / 'scripts'))
    spec = importlib.util.spec_from_file_location('hygiene', ROOT / 'scripts/hygiene.py')
    hygiene = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = hygiene
    spec.loader.exec_module(hygiene)
needs_311 = unittest.skipUnless(NEW_PYTHON, 'hygiene requer Python >= 3.11 (testado em OldPython)')

GIT_ENV = {**os.environ, 'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@t', 'GIT_COMMITTER_NAME': 't',
           'GIT_COMMITTER_EMAIL': 't@t', 'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_CONFIG_SYSTEM': '/dev/null'}


def git(cwd, *args):
    return subprocess.run(['git', '-C', str(cwd), *args], env=GIT_ENV, check=True, capture_output=True, text=True).stdout


def old(path, days=30):
    """Envelhece todos os arquivos (exceto .git de diretório) para passar do limite de dias."""
    stamp = time.time() - days * 86400
    for dirpath, dirnames, filenames in os.walk(path):
        for name in filenames + dirnames:
            os.utime(os.path.join(dirpath, name), (stamp, stamp), follow_symlinks=False)
    os.utime(path, (stamp, stamp))


def agent(agent_id, status='closed', age=30.0, cwd='', pending=0):
    return {'id': agent_id, 'provider': 'codex/x', 'status': status, 'age_days': age, 'archived': False,
            'pending_permissions': pending, '_cwd': cwd}


@needs_311
class HygieneCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(os.path.realpath(self.tmp.name))
        self.home = base / 'home dir'  # espaço no nome de propósito
        self.paseo = self.home / '.paseo' / 'worktrees'
        self.paseo.mkdir(parents=True)
        self.repo = base / 'repo'
        self.repo.mkdir()
        git(self.repo, 'init', '-q', '-b', 'main')
        (self.repo / 'a.txt').write_text('1\n')
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-q', '-m', 'base')

    def wt(self, name, branch=None, group='g1'):
        path = self.paseo / group / name
        path.parent.mkdir(parents=True, exist_ok=True)
        git(self.repo, 'worktree', 'add', '-q', '-b', branch or name.replace(' ', '-'), str(path))
        return path

    def run_plan(self, agents=(), days=7, paseo_ok=True, roots=(), process_rows=()):
        agents_list = [dict(a) for a in agents]
        error = None if paseo_ok else 'paseo fora'
        with patch.object(hygiene, 'collect_agents', return_value=(agents_list, error)), \
                patch.object(hygiene, 'scan_processes', return_value=(list(process_rows), 1.0, None)), \
                patch.object(hygiene, 'launchctl_list', return_value=[{'label': 'com.felipe.x', 'pid': None, 'last_exit': '0'}]), \
                patch.object(hygiene, 'dir_sizes', return_value={k: 1 for k in (
                    'paseo_fora_worktrees', 'paseo_worktrees_du', 'claude', 'codex', 'ai_os_state', 'gemini',
                    'library_caches_informativo')}), \
                patch.object(hygiene, 'memory_info', return_value={
                    'pressure_level': 'normal', 'free_percentage': 40, 'swap_total_bytes': 1, 'swap_used_bytes': 0}):
            scan = hygiene.build_scan(str(self.repo), self.home, self.home / 'state', list(roots))
        return scan, {r['name']: r for r in hygiene.classify(scan, days)}

    def klass(self, results, path):
        return results[str(path)]['class']


@needs_311
class WorktreeMatrix(HygieneCase):
    def test_clean_integrated_is_candidate_with_commands(self):
        path = self.wt('limpa')
        old(path)
        scan, res = self.run_plan()
        self.assertEqual(self.klass(res, path), hygiene.CANDIDATO)
        cmds = res[str(path)]['commands']
        self.assertIn('worktree remove', cmds[0])
        self.assertIn('branch -d limpa', cmds[1])
        text = hygiene.render_plan(scan)
        self.assertIn('NÃO executada', text)
        self.assertIn('ESTIMADO', text)

    def test_recent_clean_is_preserved(self):
        path = self.wt('nova')
        _, res = self.run_plan()
        self.assertEqual(self.klass(res, path), hygiene.PRESERVAR)

    def test_tracked_change_preserved(self):
        path = self.wt('suja')
        (path / 'a.txt').write_text('mudou\n')
        old(path)
        _, res = self.run_plan()
        self.assertEqual(self.klass(res, path), hygiene.PRESERVAR)

    def test_untracked_preserved(self):
        path = self.wt('untracked')
        (path / 'novo.txt').write_text('x')
        old(path)
        _, res = self.run_plan()
        self.assertEqual(self.klass(res, path), hygiene.PRESERVAR)

    def test_exclusive_commit_preserved(self):
        path = self.wt('exclusivo')
        (path / 'b.txt').write_text('b')
        git(path, 'add', '.')
        git(path, 'commit', '-q', '-m', 'so aqui')
        old(path)
        scan, res = self.run_plan()
        self.assertEqual(self.klass(res, path), hygiene.PRESERVAR)
        item = next(w for w in scan['worktrees'] if w['path'] == str(path))
        self.assertEqual((item['exclusive_commits'], item['unintegrated_commits']), (1, 1))

    def test_cherry_picked_patch_is_candidate(self):
        path = self.wt('picked')
        (path / 'c.txt').write_text('c')
        git(path, 'add', '.')
        git(path, 'commit', '-q', '-m', 'feature')
        sha = git(path, 'rev-parse', 'HEAD').strip()
        (self.repo / 'd.txt').write_text('d')  # a main avança, senão o cherry-pick repete o mesmo SHA
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-q', '-m', 'avanca')
        git(self.repo, 'cherry-pick', sha)  # mesmo patch, SHA diferente na main
        old(path)
        scan, res = self.run_plan()
        item = next(w for w in scan['worktrees'] if w['path'] == str(path))
        self.assertEqual((item['exclusive_commits'], item['unintegrated_commits']), (1, 0))
        self.assertEqual(self.klass(res, path), hygiene.CANDIDATO)

    def test_lock_preserved(self):
        path = self.wt('travada')
        git(self.repo, 'worktree', 'lock', str(path))
        old(path)
        _, res = self.run_plan()
        self.assertEqual(self.klass(res, path), hygiene.PRESERVAR)
        self.assertIn('lock', res[str(path)]['why'])

    def test_space_in_name_candidate_and_quoted_command(self):
        path = self.wt('com espaco')
        old(path)
        _, res = self.run_plan()
        self.assertEqual(self.klass(res, path), hygiene.CANDIDATO)
        self.assertIn("'" + str(path) + "'", res[str(path)]['commands'][0])

    def test_symlink_outside_not_followed(self):
        outside = Path(self.tmp.name) / 'fora'
        outside.mkdir()
        (outside / 'grande.bin').write_bytes(b'x' * 200_000)
        path = self.wt('com-link')
        os.symlink(outside, path / 'link')
        old(path)
        scan, res = self.run_plan()
        item = next(w for w in scan['worktrees'] if w['path'] == str(path))
        self.assertLess(item['size_bytes'], 150_000)  # não contou o alvo do link
        # symlink no lugar de uma worktree do Paseo: listado, não seguido, DESCONHECIDO
        link = self.paseo / 'g1' / 'atalho'
        os.symlink(outside, link)
        scan, res = self.run_plan()
        self.assertEqual(res[str(link)]['class'], hygiene.DESCONHECIDO)
        self.assertEqual(next(w for w in scan['worktrees'] if w['path'] == str(link))['head'], None)

    def test_scan_does_not_modify_worktree(self):
        path = self.wt('intacta')
        (path / 'u.txt').write_text('u')
        old(path)
        before = git(path, 'status', '--porcelain=v1', '--untracked-files=all')
        self.run_plan()
        self.assertEqual(before, git(path, 'status', '--porcelain=v1', '--untracked-files=all'))
        self.assertTrue((path / 'u.txt').exists())

    def test_main_checkout_always_preserved(self):
        _, res = self.run_plan()
        self.assertEqual(self.klass(res, self.repo), hygiene.PRESERVAR)


@needs_311
class AgentMatrix(HygieneCase):
    def test_closed_agent_with_dirty_worktree_preserved(self):
        path = self.wt('dirty-agent')
        (path / 'a.txt').write_text('alterado')
        old(path)
        _, res = self.run_plan([agent('ag1', 'closed', 30, str(path))])
        self.assertEqual(res['ag1']['class'], hygiene.PRESERVAR)
        self.assertEqual(res['ag1']['commands'], [])
        self.assertEqual(self.klass(res, path), hygiene.PRESERVAR)

    def test_closed_old_agent_with_clean_worktree_is_candidate(self):
        path = self.wt('ok-agent')
        old(path)
        _, res = self.run_plan([agent('ag2', 'closed', 30, str(path))])
        self.assertEqual(res['ag2']['class'], hygiene.CANDIDATO)
        self.assertEqual(res['ag2']['commands'], ['paseo delete ag2'])
        self.assertEqual(self.klass(res, path), hygiene.CANDIDATO)

    def test_running_and_pending_agents_preserve_worktree(self):
        path = self.wt('ativo')
        old(path)
        _, res = self.run_plan([agent('r1', 'running', 0.0, str(path))])
        self.assertEqual(res['r1']['class'], hygiene.PRESERVAR)
        self.assertEqual(self.klass(res, path), hygiene.PRESERVAR)
        _, res = self.run_plan([agent('p1', 'idle', 30, str(path), pending=1)])
        self.assertEqual(res['p1']['class'], hygiene.PRESERVAR)

    def test_recent_idle_agent_preserved(self):
        path = self.wt('recente')
        old(path)
        _, res = self.run_plan([agent('i1', 'idle', 2.0, str(path))])
        self.assertEqual(res['i1']['class'], hygiene.PRESERVAR)
        self.assertEqual(self.klass(res, path), hygiene.PRESERVAR)

    def test_unknown_status_is_desconhecido(self):
        path = self.wt('estranho')
        old(path)
        _, res = self.run_plan([agent('u1', 'banana', 30, str(path))])
        self.assertEqual(res['u1']['class'], hygiene.DESCONHECIDO)
        self.assertEqual(self.klass(res, path), hygiene.DESCONHECIDO)
        self.assertEqual(res['u1']['commands'], [])

    def test_agent_without_inspect_data_is_desconhecido(self):
        _, res = self.run_plan([agent('n1', 'closed', None, '')])
        self.assertEqual(res['n1']['class'], hygiene.DESCONHECIDO)

    def test_agent_outside_known_worktrees_is_desconhecido(self):
        _, res = self.run_plan([agent('o1', 'closed', 30, str(self.home))])
        self.assertEqual(res['o1']['class'], hygiene.DESCONHECIDO)

    def test_paseo_down_makes_worktrees_desconhecido(self):
        path = self.wt('sem-paseo')
        old(path)
        _, res = self.run_plan(paseo_ok=False)
        self.assertEqual(self.klass(res, path), hygiene.DESCONHECIDO)

    def test_broken_git_fails_closed_as_restricted(self):
        # a política não consegue resolver a origem: trata como restrito (mascarado) e nunca vira candidato
        broken = self.paseo / 'g2' / 'quebrada'
        broken.mkdir(parents=True)
        (broken / '.git').write_text('gitdir: /nao/existe\n')
        scan, res = self.run_plan()
        self.assertNotIn(str(broken), res)
        self.assertEqual(res['restrito/1']['class'], hygiene.PRESERVAR)


@needs_311
class Privacy(HygieneCase):
    def test_restricted_paths_masked_and_agent_title_never_collected(self):
        path = self.wt('segredo')
        old(path)
        scan, res = self.run_plan([agent('rs1', 'closed', 30, str(path))], roots=[self.repo])
        text = hygiene.render_plan(scan) + json.dumps(scan)
        self.assertNotIn('segredo', text)
        self.assertNotIn(str(self.repo), text)
        self.assertIn('restrito/', text)
        self.assertEqual(res['rs1']['class'], hygiene.PRESERVAR)
        self.assertEqual(res['restrito/2']['commands'], [])


@needs_311
class ProcessOwnership(HygieneCase):
    def test_checkout_principal_sem_agente_nao_e_orfao(self):
        process = {'pid': 2468, 'ppid': 1, 'start_time': 'Mon Nov  9 10:00:00 2026',
                   'command': 'astro dev', 'cwd': str(self.repo), 'worktree': str(self.repo), 'rss_bytes': 1024,
                   'listen_ports': [4321], 'established_connections': 0, 'active_connections': 0}
        scan, _ = self.run_plan(process_rows=[process])
        row = scan['processes']['items'][0]
        self.assertTrue(row['is_main'])
        result = next(item for item in hygiene.classify(scan) if item['kind'] == 'process')
        self.assertEqual(result['class'], hygiene.DESCONHECIDO)

    def test_dono_ambiguo_em_mesma_worktree_nao_e_orfao(self):
        path = self.wt('duplo')
        process = {'pid': 2468, 'ppid': 1, 'start_time': 'Mon Nov  9 10:00:00 2026',
                   'command': 'astro dev', 'cwd': str(path), 'worktree': str(path), 'rss_bytes': 1024,
                   'listen_ports': [], 'established_connections': 0, 'active_connections': 0}
        owners = [agent('a1', status='closed', cwd=str(path)), agent('a2', status='closed', cwd=str(path))]
        scan, _ = self.run_plan(agents=owners, process_rows=[process])
        row = scan['processes']['items'][0]
        self.assertFalse(row['owner_known'])
        result = next(item for item in hygiene.classify(scan) if item['kind'] == 'process')
        self.assertEqual(result['class'], hygiene.DESCONHECIDO)


@needs_311
class CliAndParsers(unittest.TestCase):
    def test_no_apply_flag(self):
        with self.assertRaises(SystemExit):
            hygiene.main(['plan', '--apply'])

    def test_plan_from_scan_file_and_private_perms(self):
        with tempfile.TemporaryDirectory() as tmp:
            scan = {'version': 1, 'generated_at': 'x', 'paseo_ok': True, 'worktrees': [], 'agents': [],
                    'launchd': [], 'disk': {'free_bytes': 1, 'total_bytes': 2},
                    'memory': {'pressure_level': None, 'free_percentage': None, 'swap_total_bytes': None,
                               'swap_used_bytes': None},
                    'sizes_bytes': {k: None for k in ('worktrees_escaneadas', 'paseo_fora_worktrees', 'claude', 'codex',
                                                      'ai_os_state', 'gemini', 'library_caches_informativo')}}
            src, dst = Path(tmp) / 's.json', Path(tmp) / 'out' / 'p.md'
            src.write_text(json.dumps(scan))
            self.assertEqual(hygiene.main(['plan', '--scan', str(src), '--out', str(dst)]), 0)
            self.assertIn('DRY-RUN', dst.read_text())
            self.assertEqual(dst.stat().st_mode & 0o777, 0o600)

    def test_memory_parsing(self):
        outputs = {
            'memory_pressure': 'System-wide memory free percentage: 35%\n',
            'sysctl': 'vm.swapusage: total = 12288,00M  used = 11555,38M  free = 732,62M  (encrypted)\n',
        }

        def fake_run(cmd, **kwargs):
            text = outputs['memory_pressure'] if cmd[0] == 'memory_pressure' else (
                'kern.memorystatus_vm_pressure_level: 2\n' if 'kern.memorystatus_vm_pressure_level' in cmd else outputs['sysctl'])
            return subprocess.CompletedProcess(cmd, 0, stdout=text, stderr='')

        with patch.object(hygiene.subprocess, 'run', fake_run):
            info = hygiene.memory_info()
        self.assertEqual((info['free_percentage'], info['pressure_level']), (35, 'aviso'))
        self.assertEqual(info['swap_total_bytes'], 12288 * 1024 * 1024)


@needs_311
class FailClosed(HygieneCase):
    def test_more_than_40_refs_without_proof_is_desconhecido(self):
        path = self.wt('muitas-refs')
        (path / 'b.txt').write_text('b')
        git(path, 'add', '.')
        git(path, 'commit', '-q', '-m', 'exclusivo')
        for n in range(45):
            git(self.repo, 'branch', f'ref{n:02d}')
        old(path)
        scan, res = self.run_plan()
        self.assertEqual(self.klass(res, path), hygiene.DESCONHECIDO)
        self.assertIn('truncada', ' '.join(res[str(path)]['why']))
        self.assertEqual(res[str(path)]['commands'], [])

    def test_many_refs_but_ancestry_proves_it_is_still_candidate(self):
        path = self.wt('muitas-refs-ok')
        for n in range(45):
            git(self.repo, 'branch', f'ref{n:02d}')
        old(path)
        _, res = self.run_plan()
        self.assertEqual(self.klass(res, path), hygiene.CANDIDATO)

    def test_no_eligible_refs_is_desconhecido(self):
        path = self.wt('sem-refs')
        (path / 'b.txt').write_text('b')
        git(path, 'add', '.')
        git(path, 'commit', '-q', '-m', 'exclusivo')
        old(path)
        with patch.object(hygiene, '_other_refs', return_value=[]), patch.object(hygiene, '_sibling_heads', return_value=[]):
            scan, res = self.run_plan()
        self.assertEqual(self.klass(res, path), hygiene.DESCONHECIDO)
        self.assertIn('sem refs elegíveis', ' '.join(res[str(path)]['why']))

    def test_patch_in_sibling_detached_worktree_counts(self):
        path = self.wt('picked2')
        (path / 'c.txt').write_text('c')
        git(path, 'add', '.')
        git(path, 'commit', '-q', '-m', 'feature')
        sha = git(path, 'rev-parse', 'HEAD').strip()
        det = self.paseo / 'g1' / 'detached'
        git(self.repo, 'worktree', 'add', '-q', '--detach', str(det))
        (det / 'x.txt').write_text('x')
        git(det, 'add', '.')
        git(det, 'commit', '-q', '-m', 'outra')
        git(det, 'cherry-pick', sha)
        old(path)
        scan, _ = self.run_plan()
        item = next(w for w in scan['worktrees'] if w['path'] == str(path))
        self.assertEqual((item['exclusive_commits'], item['unintegrated_commits']), (1, 0))

    def test_lock_permission_error_is_desconhecido(self):
        path = self.wt('lock-perm')
        old(path)
        real_stat = os.stat

        def fake_stat(target, *a, **k):
            if str(target).endswith('locked'):
                raise PermissionError('negado')
            return real_stat(target, *a, **k)

        with patch.object(hygiene.os, 'stat', fake_stat):
            scan, res = self.run_plan()
        item = next(w for w in scan['worktrees'] if w['path'] == str(path))
        self.assertIsNone(item['locked'])
        self.assertEqual(self.klass(res, path), hygiene.DESCONHECIDO)
        self.assertEqual(res[str(path)]['commands'], [])

    def test_du_does_not_follow_symlinks(self):
        calls = []

        def fake_run(cmd, **k):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, stdout='4\tx\n', stderr='')

        with patch.object(hygiene.subprocess, 'run', fake_run):
            hygiene.du_bytes(self.home)
        self.assertEqual(calls[0][:2], ['du', '-sPk'])


@needs_311
class ScanValidation(unittest.TestCase):
    def good(self):
        wt = {'path': '/x/wt', 'is_main': False, 'restricted': False, 'branch': 'b', 'tracked_changes': 0,
              'untracked': 0, 'exclusive_commits': 0, 'unintegrated_commits': 0, 'locked': False,
              'age_days': 30.0, 'size_bytes': 10, 'main_checkout': '/x/main', 'error': None}
        ag = {'id': 'a1', 'provider': 'p', 'status': 'closed', 'age_days': 30.0, 'pending_permissions': 0,
              'restricted': False, 'worktree': '/x/wt'}
        return {'version': 1, 'generated_at': 'x', 'paseo_ok': True, 'worktrees': [wt], 'agents': [ag],
                'launchd': [], 'disk': {'free_bytes': 1, 'total_bytes': 2},
                'memory': {'pressure_level': None, 'free_percentage': None, 'swap_total_bytes': None,
                           'swap_used_bytes': None},
                'sizes_bytes': {k: None for k in hygiene.SIZES_SCHEMA}}

    def test_valid_scan_gives_candidates(self):
        res = {r['name']: r for r in hygiene.classify(self.good())}
        self.assertEqual(res['/x/wt']['class'], hygiene.CANDIDATO)
        self.assertEqual(res['a1']['class'], hygiene.CANDIDATO)

    def test_missing_field_in_worktree_is_desconhecido_without_command(self):
        scan = self.good()
        del scan['worktrees'][0]['untracked']
        res = hygiene.classify(scan)
        wt = next(r for r in res if r['kind'] == 'worktree')
        self.assertEqual((wt['class'], wt['commands']), (hygiene.DESCONHECIDO, []))
        ag = next(r for r in res if r['kind'] == 'agente')
        self.assertEqual((ag['class'], ag['commands']), (hygiene.DESCONHECIDO, []))
        self.assertIn('DESCONHECIDO (2)', hygiene.render_plan(scan))

    def test_non_numeric_count_is_desconhecido(self):
        scan = self.good()
        scan['worktrees'][0]['unintegrated_commits'] = 'zero'
        scan['agents'][0]['age_days'] = True  # bool não vale como número
        res = hygiene.classify(scan)
        self.assertTrue(all(r['class'] == hygiene.DESCONHECIDO and not r['commands'] for r in res))

    def test_bad_agent_blocks_linked_worktree(self):
        scan = self.good()
        del scan['agents'][0]['status']
        wt = next(r for r in hygiene.classify(scan) if r['kind'] == 'worktree')
        self.assertEqual(wt['class'], hygiene.DESCONHECIDO)

    def test_null_proof_fields_never_candidate(self):
        for field in ('locked', 'unintegrated_commits', 'tracked_changes'):
            scan = self.good()
            scan['worktrees'][0][field] = None
            wt = next(r for r in hygiene.classify(scan) if r['kind'] == 'worktree')
            self.assertEqual((wt['class'], wt['commands']), (hygiene.DESCONHECIDO, []), field)

    def test_invalid_file_gives_clear_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / 'bad.json'
            for content in ('nao e json', '[]', '{"version": 2}', json.dumps({**self.good(), 'disk': {}})):
                bad.write_text(content)
                self.assertEqual(hygiene.main(['plan', '--scan', str(bad)]), 2, content)
            self.assertEqual(hygiene.main(['plan', '--scan', str(Path(tmp) / 'nao-existe.json')]), 2)

    def test_plan_scan_com_lstart_diferente_fica_desconhecido(self):
        scan = self.good()
        scan["processes"] = {"scan_ms": 2.0, "error": None, "items": [{
            "pid": 2468, "ppid": 1, "start_time": "Mon Nov  9 10:00:00 2026", "command": "astro dev",
            "worktree": "/x/wt", "rss_bytes": 1024, "owner_agent": None, "owner_status": None,
            "owner_known": True, "established_connections": 0, "listen_ports": [], "age_hours": 48,
            "restricted": False, "pid_reused": False,
            "astro_locks": {"dev": {"present": False, "pid_matches": None},
                            "preview": {"present": False, "pid_matches": None}},
        }]}
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "scan.json"
            source.write_text(json.dumps(scan))
            output = io.StringIO()
            with patch.object(hygiene, "process_start_times", return_value=({2468: "Tue Nov 10 10:00:00 2026"}, 1.2)) as check, \
                    contextlib.redirect_stdout(output):
                self.assertEqual(hygiene.main(["plan", "--scan", str(source)]), 0)
            self.assertEqual(check.call_count, 1)
            self.assertIn("DESCONHECIDO", output.getvalue())
            self.assertIn("não corresponde mais ao horário de início", output.getvalue())


@needs_311
class OrphanProcessPlan(unittest.TestCase):
    def row(self, **changes):
        return {'pid': 2468, 'ppid': 1, 'start_time': 'Mon Nov  9 10:00:00 2026',
                'command': 'astro dev', 'worktree': '/tmp/wt', 'rss_bytes': 1024,
                'owner_agent': 'a1', 'owner_status': 'closed', 'owner_known': True,
                'established_connections': 0, 'active_connections': 0, 'listen_ports': [4321], 'age_hours': 48,
                'is_main': False, 'is_paseo_worktree': True,
                'restricted': False, 'pid_reused': False, 'astro_locks': {'dev': {'present': True, 'pid_matches': True},
                'preview': {'present': False, 'pid_matches': None}}, **changes}

    def scan(self, row):
        return {'agents': [], 'worktrees': [], 'paseo_ok': True,
                'processes': {'items': [row], 'scan_ms': 2.5, 'error': None}}

    def test_classico_vira_orfao_com_comando_astro(self):
        result = hygiene.classify(self.scan(self.row()))[0]
        self.assertEqual(result['class'], 'ORFAO_CANDIDATO')
        self.assertIn('astro dev stop', result['commands'][0])
        self.assertNotIn('kill -9', result['commands'][0])

    def test_conexao_agente_ativo_ppid_e_pid_reutilizado_nao_sao_orfaos(self):
        for changes, klass in (({'established_connections': 1, 'active_connections': 1}, hygiene.PRESERVAR),
                               ({'owner_status': 'running'}, hygiene.PRESERVAR),
                               ({'ppid': 42}, 'RESIDUO_AGENTE'),
                               ({'active_connections': None}, hygiene.DESCONHECIDO),
                               ({'pid_reused': True}, hygiene.DESCONHECIDO)):
            with self.subTest(changes=changes):
                self.assertEqual(hygiene.classify(self.scan(self.row(**changes)))[0]['class'], klass)

    def test_lock_astro_com_pid_diferente_usa_guarda_de_inicio(self):
        row = self.row(astro_locks={'dev': {'present': True, 'pid_matches': False},
                                    'preview': {'present': False, 'pid_matches': None}})
        result = hygiene.classify(self.scan(row))[0]
        self.assertEqual(result['class'], 'ORFAO_CANDIDATO')
        self.assertIn('ps -o lstart=', result['commands'][0])
        self.assertIn('LC_ALL=C ps -o lstart= -p 2468', result['commands'][0])
        self.assertIn('kill -TERM 2468', result['commands'][0])

    def test_lock_astro_ausente_nao_usa_astro_stop(self):
        row = self.row(astro_locks={'dev': {'present': False, 'pid_matches': True},
                                    'preview': {'present': False, 'pid_matches': None}})
        result = hygiene.classify(self.scan(row))[0]
        self.assertNotIn('astro dev stop', result['commands'][0])
        self.assertIn('kill -TERM 2468', result['commands'][0])

    def test_restrito_fica_mascarado_e_preservado(self):
        row = self.row(restricted=True, worktree='restrito/1')
        result = hygiene.classify(self.scan(row))[0]
        self.assertEqual(result['class'], hygiene.PRESERVAR)
        self.assertEqual(result['process']['worktree'], 'restrito/1')

    def test_scanner_usa_ps_e_lsof_cwd_global_sem_lsof_por_pid(self):
        sys.path.insert(0, str(ROOT / 'scripts'))
        import process_scan
        calls = []
        def fake_run(command, **kwargs):
            calls.append(command)
            if command[0] == 'ps':
                stdout = '619 1 Mon Nov  9 10:00:00 2026 1234 astro dev --host\n'
            elif '-d' in command:
                stdout = 'p619\ncnode\nfcwd\nn/tmp/wt\n'
            else:
                stdout = (ROOT / 'tests/fixtures/lsof_tcp_FpnfT_real.txt').read_text()
            return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr='')
        with patch.object(process_scan.subprocess, 'run', side_effect=fake_run):
            rows, elapsed, error = process_scan.scan_processes([{'path': '/tmp/wt'}])
        self.assertEqual(error, None)
        self.assertEqual(rows[0]['command'], 'astro dev')
        self.assertEqual(rows[0]['listen_ports'], [5000, 7000])
        self.assertEqual(rows[0]['established_connections'], 0)
        self.assertEqual(rows[0]['active_connections'], 0)
        self.assertGreaterEqual(elapsed, 0)
        self.assertEqual(sum('-d' in command and 'cwd' in command for command in calls), 1)
        self.assertTrue(any('-FpnfT' in command for command in calls))

    def test_fixture_lsof_legado_sem_tst_nao_prova_zero(self):
        import process_scan
        output = (ROOT / 'tests/fixtures/lsof_tcp_Fpn_real.txt').read_text()
        listen, established, active = process_scan._parse_tcp(output)
        self.assertEqual(listen, {})
        self.assertIsNone(active[619])
        self.assertIsNone(active[658])
        self.assertIsNone(active[664])
        self.assertEqual(established, {})

    def test_estados_tcp_nao_established_tambem_contam_como_ativos(self):
        import process_scan
        output = ('p2468\nf3\nn127.0.0.1:4000->127.0.0.1:80\nTST=CLOSE_WAIT\n'
                  'f4\nn127.0.0.1:4001->127.0.0.1:80\nTST=SYN_SENT\n')
        _, established, active = process_scan._parse_tcp(output)
        self.assertEqual(established, {})
        self.assertEqual(active[2468], 2)

    def test_fixtures_lstart_e_comando_usam_locale_c(self):
        c = (ROOT / 'tests/fixtures/ps_lstart_C.txt').read_text().strip()
        pt = (ROOT / 'tests/fixtures/ps_lstart_ptBR.txt').read_text().strip()
        row = self.row(start_time=c, astro_locks={})
        command = hygiene.process_stop_command(row)[0]
        self.assertIn('LC_ALL=C ps -o lstart= -p 2468', command)
        self.assertIn(shlex.quote(c), command)
        self.assertNotEqual(c, pt)
        self.assertNotIn(pt, command)

    def test_so_roots_de_worktree_paseo_e_comando_de_servidor_podem_ser_orfao(self):
        cases = (({'is_main': True}, hygiene.DESCONHECIDO),
                 ({'is_paseo_worktree': False}, hygiene.DESCONHECIDO),
                 ({'command': 'tmux'}, hygiene.DESCONHECIDO),
                 ({'command': 'nohup', 'is_main': True}, hygiene.DESCONHECIDO),
                 ({'command': 'vite build'}, hygiene.DESCONHECIDO),
                 ({'command': 'node', 'listen_ports': []}, hygiene.DESCONHECIDO),
                 ({'command': 'node', 'listen_ports': [3000]}, 'ORFAO_CANDIDATO'))
        for changes, klass in cases:
            with self.subTest(changes=changes):
                self.assertEqual(hygiene.classify(self.scan(self.row(**changes)))[0]['class'], klass)

    def test_dono_ambiguo_nao_vira_orfao(self):
        process = self.row(owner_known=False)
        self.assertEqual(hygiene.classify(self.scan(process))[0]['class'], hygiene.DESCONHECIDO)

    def test_residuo_agente_agrupa_rss_sem_sugerir_kill(self):
        first = self.row(ppid=77, command='node', owner_agent='a1', active_connections=2)
        second = self.row(pid=2469, ppid=77, command='tmux', owner_agent='a1', rss_bytes=2048,
                          active_connections=1, astro_locks={})
        result = hygiene.classify({'agents': [], 'worktrees': [], 'paseo_ok': True,
                                   'processes': {'items': [first, second], 'scan_ms': 1, 'error': None}})
        residue = next(row for row in result if row['class'] == 'RESIDUO_AGENTE')
        self.assertEqual(residue['process']['pids'], [2468, 2469])
        self.assertEqual(residue['rss_bytes'], 3072)
        self.assertEqual(residue['process']['worktrees'], ['/tmp/wt'])
        self.assertIn('paseo delete a1 após conferir', residue['commands'][0])
        self.assertFalse(any('kill' in command for command in residue['commands']))

    def test_residuo_do_mesmo_agente_soma_rss_em_worktrees_diferentes(self):
        first = self.row(ppid=77, owner_agent='a1', worktree='/tmp/wt-a')
        second = self.row(pid=2470, ppid=77, owner_agent='a1', worktree='/tmp/wt-b', rss_bytes=2048)
        result = hygiene.classify({'agents': [], 'worktrees': [], 'paseo_ok': True,
                                   'processes': {'items': [first, second], 'scan_ms': 1, 'error': None}})
        residues = [row for row in result if row['class'] == 'RESIDUO_AGENTE']
        self.assertEqual(len(residues), 1)
        self.assertEqual(residues[0]['rss_bytes'], 3072)
        self.assertEqual(residues[0]['process']['worktrees'], ['/tmp/wt-a', '/tmp/wt-b'])

    def test_resumo_vite_build_nao_e_servidor_de_desenvolvimento(self):
        import process_scan
        self.assertEqual(process_scan._summary('/usr/local/bin/vite build'), 'vite build')
        self.assertEqual(process_scan._summary('/usr/local/bin/vite dev --host'), 'vite dev')

    def test_lsof_tcp_sem_matches_significa_zero_conexoes(self):
        import process_scan
        def fake_run(command, **kwargs):
            if command[0] == 'ps':
                stdout = '2468 1 Mon Nov  9 10:00:00 2026 1234 node astro dev\n'
                return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr='')
            if '-d' in command:
                return subprocess.CompletedProcess(command, 0, stdout='p2468\ncnode\nfcwd\nn/tmp/wt\n', stderr='')
            return subprocess.CompletedProcess(command, 1, stdout='', stderr='')
        with patch.object(process_scan.subprocess, 'run', side_effect=fake_run):
            rows, _, error = process_scan.scan_processes([{'path': '/tmp/wt'}])
        self.assertIsNone(error)
        self.assertEqual(rows[0]['established_connections'], 0)

    def test_lsof_tcp_com_erro_real_fica_desconhecido(self):
        import process_scan
        def fake_run(command, **kwargs):
            if command[0] == 'ps':
                return subprocess.CompletedProcess(command, 0,
                    stdout='2468 1 Mon Nov  9 10:00:00 2026 1234 node astro dev\n', stderr='')
            if '-d' in command:
                return subprocess.CompletedProcess(command, 0, stdout='p2468\ncnode\nfcwd\nn/tmp/wt\n', stderr='')
            return subprocess.CompletedProcess(command, 1, stdout='', stderr='permission denied')
        with patch.object(process_scan.subprocess, 'run', side_effect=fake_run):
            rows, _, error = process_scan.scan_processes([{'path': '/tmp/wt'}])
        self.assertIsNotNone(error)
        scan = {'agents': [], 'worktrees': [], 'paseo_ok': True,
                'processes': {'items': [dict(rows[0], owner_known=True, owner_status='closed', age_hours=48,
                                             restricted=False, pid_reused=False)], 'scan_ms': 1, 'error': error}}
        self.assertEqual(hygiene.classify(scan)[0]['class'], hygiene.DESCONHECIDO)

    def test_scanner_nao_confunde_prefixo_parecido_nem_segue_symlink_root(self):
        import process_scan
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / 'worktree'
            sibling = base / 'worktree-sibling'
            external = base / 'external'
            for path in (root, sibling, external):
                path.mkdir()
            link = base / 'linked-worktree'
            link.symlink_to(external)

            def fake_run(command, **kwargs):
                if command[0] == 'ps':
                    return subprocess.CompletedProcess(command, 0,
                        stdout='619 1 Mon Nov  9 10:00:00 2026 1234 astro dev\n', stderr='')
                if '-d' in command:
                    return subprocess.CompletedProcess(command, 0,
                        stdout=f'p619\ncnode\nfcwd\nn{sibling}\n', stderr='')
                return subprocess.CompletedProcess(command, 0,
                    stdout=(ROOT / 'tests/fixtures/lsof_tcp_FpnfT_real.txt').read_text(), stderr='')

            with patch.object(process_scan.subprocess, 'run', side_effect=fake_run):
                rows, _, error = process_scan.scan_processes([{'path': str(root)}])
                self.assertEqual(rows, [])
                rows, _, error = process_scan.scan_processes([{'path': str(link)}])
                self.assertEqual(rows, [])
            self.assertIsNone(error)


class OldPython(unittest.TestCase):
    def test_cli_fails_clearly_on_python_below_3_11(self):
        old_py = '/usr/bin/python3'
        if not os.path.exists(old_py):
            self.skipTest('sem /usr/bin/python3')
        version = subprocess.run([old_py, '-c', 'import sys;print(sys.version_info[:2] < (3, 11))'],
                                 capture_output=True, text=True).stdout.strip()
        if version != 'True':
            self.skipTest('/usr/bin/python3 já é >= 3.11')
        out = subprocess.run([old_py, str(ROOT / 'scripts/hygiene.py'), 'plan'], capture_output=True, text=True)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn('requer Python >= 3.11', out.stderr)
        self.assertIn('/opt/homebrew/bin/python3', out.stderr)


if __name__ == '__main__':
    unittest.main()
