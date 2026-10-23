import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

try:
    import tomllib
except ImportError:
    tomllib = None

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/ai_memory_autoenable.py'
spec = importlib.util.spec_from_file_location('harden_memory', ROOT / 'scripts/harden.py')
harden = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harden)


@unittest.skipUnless(tomllib, 'requer Python >= 3.11 (tomllib)')
class AutoenableTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name).resolve()
        self.workspace = self.home / 'Workspace'
        self.workspace.mkdir()
        self.policy = self.home / 'policy.toml'
        self.policy.write_text('roots = ["~/Workspace", "~/.paseo/worktrees"]\n'
                               '[restricted]\npaths = ["~/Workspace/seplan", "~/Workspace/projetos/sgg-controle"]\n'
                               'workspace = "restrito"\nallowed_models = ["claude", "codex", "opencode/glm-5.3-flash-free", "opencode/deepseek-v4.1-flash-free"]\n')
        self.env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
        self.env['HOME'] = str(self.home)
        self.env['GIT_CONFIG_NOSYSTEM'] = '1'
        self.settings = self.home / '.claude-mem/settings.json'

    def git(self, cwd, *args):
        return subprocess.run(['git', '-C', str(cwd), *args], env=self.env,
                              capture_output=True, text=True, check=True).stdout.strip()

    def repo(self, relative='Workspace/pessoal'):
        repo = self.home / relative
        repo.mkdir(parents=True)
        self.git(repo, 'init', '-q')
        return repo

    def hook(self, cwd, *args, raw=None, env=None):
        return subprocess.run([sys.executable, str(SCRIPT), '--config', str(self.policy), *args],
                              env=env or self.env, capture_output=True, text=True,
                              input=raw if raw is not None else json.dumps({'cwd': str(cwd)}))

    def test_personal_marker_and_shared_exclude_idempotent(self):
        repo = self.repo()
        nested = repo / 'subdir'
        nested.mkdir()
        result = self.hook(nested)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, '')
        marker = repo / '.ai-memory.toml'
        self.assertEqual(tomllib.loads(marker.read_text()), {'workspace': 'pessoal', 'briefing': {
            'inject_on_session_start': True, 'max_chars': 4000}})
        exclude = repo / '.git/info/exclude'
        before = exclude.read_bytes()
        stamp = marker.stat().st_mtime_ns
        self.hook(repo)
        self.assertEqual(exclude.read_bytes(), before)
        self.assertEqual(marker.stat().st_mtime_ns, stamp)
        self.assertEqual(exclude.read_text().splitlines().count('.ai-memory.toml'), 1)
        self.assertEqual(self.git(repo, 'status', '--porcelain'), '')

    def test_restricted_notice_and_derived_project(self):
        for relative in ('Workspace/seplan/repo', 'Workspace/projetos/sgg-controle'):
            with self.subTest(relative=relative):
                repo = self.repo(relative)
                result = self.hook(repo)
                self.assertEqual(tomllib.loads((repo / '.ai-memory.toml').read_text())['workspace'], 'restrito')
                notice = json.loads(result.stdout)['hookSpecificOutput']
                self.assertEqual(notice['hookEventName'], 'SessionStart')
                self.assertIn('Projeto restrito', notice['additionalContext'])
                self.assertIn('Nunca delegar', notice['additionalContext'])
                self.assertIn('opencode/deepseek-v4.1-flash-free', notice['additionalContext'])
                self.assertNotIn('project', tomllib.loads((repo / '.ai-memory.toml').read_text()))

    def test_worktree_inherits_main_checkout(self):
        repo = self.repo('Workspace/seplan/repo')
        self.git(repo, '-c', 'user.name=Teste', '-c', 'user.email=teste@example.invalid',
                 '-c', 'commit.gpgsign=false', 'commit', '--allow-empty', '-qm', 'inicial')
        worktree = self.home / '.paseo/worktrees/task/repo'
        worktree.parent.mkdir(parents=True)
        self.git(repo, 'worktree', 'add', '-q', '--detach', str(worktree))
        self.settings.parent.mkdir()
        self.settings.write_text('{}')
        result = self.hook(worktree)
        self.assertIn('Projeto restrito', result.stdout)
        self.assertEqual(tomllib.loads((worktree / '.ai-memory.toml').read_text())['workspace'], 'restrito')
        self.assertFalse((repo / '.ai-memory.toml').exists())
        self.assertIn('.ai-memory.toml', (repo / '.git/info/exclude').read_text())
        self.assertFalse((worktree / '.git/info/exclude').exists())
        self.assertEqual(json.loads(self.settings.read_text())['CLAUDE_MEM_EXCLUDED_PROJECTS'],
                         str(repo) + ',' + str(repo) + '/**')

    def test_existing_and_tracked_marker_preserved(self):
        repo = self.repo()
        marker = repo / '.ai-memory.toml'
        original = b'# versionado\nworkspace = "outro"\nproject = "fixo"\n'
        marker.write_bytes(original)
        self.hook(repo)
        self.assertEqual(marker.read_bytes(), original)
        self.git(repo, 'add', '-f', '.ai-memory.toml')
        exclude = repo / '.git/info/exclude'
        exclude.write_text('# original\n')
        self.hook(repo)
        self.assertEqual(exclude.read_text(), '# original\n')
        self.assertEqual(marker.read_bytes(), original)

    def test_outside_roots_non_git_and_path_boundary(self):
        for repo in (self.repo('fora/repo'), self.repo('Workspace-other/repo'), self.workspace):
            result = self.hook(repo)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, '')
            self.assertFalse((repo / '.ai-memory.toml').exists())
        repo = self.repo('Workspace/seplan-other')
        self.assertEqual(self.hook(repo).stdout, '')
        self.assertEqual(tomllib.loads((repo / '.ai-memory.toml').read_text())['workspace'], 'pessoal')

    def test_paseo_worktree_outside_main_root_is_ignored(self):
        repo = self.repo('fora/repo')
        self.git(repo, '-c', 'user.name=Teste', '-c', 'user.email=teste@example.invalid',
                 '-c', 'commit.gpgsign=false', 'commit', '--allow-empty', '-qm', 'inicial')
        worktree = self.home / '.paseo/worktrees/repo'
        worktree.parent.mkdir(parents=True)
        self.git(repo, 'worktree', 'add', '-q', '--detach', str(worktree))
        self.assertEqual(self.hook(worktree).stdout, '')
        self.assertFalse((worktree / '.ai-memory.toml').exists())

    def test_claude_mem_backup_private_idempotent_preserves_settings(self):
        repo = self.repo()
        self.settings.parent.mkdir()
        original = {'other': {'keep': True}, 'CLAUDE_MEM_EXCLUDED_PROJECTS': '/existing,/existing/**'}
        self.settings.write_text(json.dumps(original))
        self.settings.chmod(0o600)
        self.hook(repo)
        result = json.loads(self.settings.read_text())
        self.assertEqual(result['other'], original['other'])
        self.assertEqual(result['CLAUDE_MEM_EXCLUDED_PROJECTS'], '/existing,/existing/**,' + str(repo) + ',' + str(repo) + '/**')
        backups = list(self.settings.parent.glob('settings.json.backup-*'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(json.loads(backups[0].read_text()), original)
        for file in (self.settings, backups[0]):
            self.assertEqual(file.stat().st_mode & 0o777, 0o600)
        before = self.settings.read_bytes()
        self.hook(repo)
        self.assertEqual(self.settings.read_bytes(), before)
        self.assertEqual(list(self.settings.parent.glob('settings.json.backup-*')), backups)

    def test_dry_run_does_not_write(self):
        repo = self.repo()
        self.settings.parent.mkdir()
        self.settings.write_text('{}')
        before = (repo / '.git/info/exclude').read_bytes()
        result = self.hook(repo, '--dry-run')
        self.assertEqual(len(json.loads(result.stdout)['dry_run']), 3)
        self.assertFalse((repo / '.ai-memory.toml').exists())
        self.assertEqual((repo / '.git/info/exclude').read_bytes(), before)
        self.assertEqual(self.settings.read_text(), '{}')
        self.assertEqual(list(self.settings.parent.glob('settings.json.backup-*')), [])

    def test_errors_exit_zero_and_keep_bad_settings(self):
        repo = self.repo()
        for raw in ('{bad', '[]', '{}', '{"cwd":12}'):
            self.assertEqual(self.hook(repo, raw=raw).returncode, 0)
        self.settings.parent.mkdir()
        self.settings.write_text('{bad')
        result = self.hook(repo)
        self.assertEqual(result.returncode, 0)
        self.assertIn('ai-memory autoenable:', result.stderr)
        self.assertEqual(self.settings.read_text(), '{bad')
        self.assertFalse((repo / '.ai-memory.toml').exists())
        self.policy.write_text('invalid = [')
        self.assertEqual(self.hook(repo).returncode, 0)
        self.assertEqual(self.hook(repo, '--invalid').returncode, 0)

    def test_git_environment_does_not_override_cwd(self):
        repo = self.repo()
        other = self.repo('Workspace/seplan/other')
        env = dict(self.env, GIT_DIR=str(other / '.git'), GIT_WORK_TREE=str(other))
        self.assertEqual(self.hook(repo, env=env).stdout, '')
        self.assertEqual(tomllib.loads((repo / '.ai-memory.toml').read_text())['workspace'], 'pessoal')
        self.assertFalse((other / '.ai-memory.toml').exists())


class MemoryHookMergeTests(unittest.TestCase):
    def test_merge_preserves_ai_memory_and_idempotence(self):
        for filename in ('settings.json', 'hooks.json'):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / filename
                entry = {'matcher': 'startup|resume', 'hooks': [{'type': 'command', 'command': 'ai-memory hook session-start', 'timeout': 30}]}
                original = {'other': 123, 'hooks': {'SessionStart': [entry], 'SessionEnd': [{'hooks': []}]}}
                path.write_text(json.dumps(original))
                before = path.read_bytes()
                self.assertEqual(harden.memory_session_start(str(path), '/repo with space/script.py', '/python', False), 10)
                self.assertEqual(path.read_bytes(), before)
                self.assertEqual(harden.memory_session_start(str(path), '/repo with space/script.py', '/python', True), 10)
                merged = json.loads(path.read_text())
                self.assertEqual(merged['hooks']['SessionStart'][1:], original['hooks']['SessionStart'])
                self.assertEqual(merged['hooks']['SessionEnd'], original['hooks']['SessionEnd'])
                self.assertEqual(merged['other'], original['other'])
                self.assertEqual(merged['hooks']['SessionStart'][0]['hooks'][0]['command'], "/python '/repo with space/script.py'")
                before = path.read_bytes()
                self.assertEqual(harden.memory_session_start(str(path), '/repo with space/script.py', '/python', True), 0)
                self.assertEqual(path.read_bytes(), before)

    def test_missing_file_and_invalid_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'settings.json'
            self.assertEqual(harden.memory_session_start(str(path), '/script', '/python', True), 10)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            for raw in ('{bad', '[]', '{"hooks": []}', '{"hooks": {"SessionStart": {}}}'):
                path.write_text(raw)
                self.assertEqual(harden.memory_session_start(str(path), '/script', '/python', True), 2)
                self.assertEqual(path.read_text(), raw)


if __name__ == '__main__':
    unittest.main()
