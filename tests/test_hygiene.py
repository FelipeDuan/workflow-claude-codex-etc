import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

if sys.version_info < (3, 11):
    raise unittest.SkipTest('hygiene requer Python >= 3.11')

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('hygiene', ROOT / 'scripts/hygiene.py')
hygiene = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = hygiene
spec.loader.exec_module(hygiene)

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

    def run_plan(self, agents=(), days=7, paseo_ok=True, roots=()):
        agents_list = [dict(a) for a in agents]
        error = None if paseo_ok else 'paseo fora'
        with patch.object(hygiene, 'collect_agents', return_value=(agents_list, error)), \
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


if __name__ == '__main__':
    unittest.main()
