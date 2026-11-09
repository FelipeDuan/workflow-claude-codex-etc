import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InstallAntigravityTest(unittest.TestCase):
    def run_install(self, home, *extra):
        env = dict(os.environ, HOME=str(home))
        for var in ('CLAUDE_CONFIG_DIR', 'CODEX_HOME', 'XDG_DATA_HOME', 'XDG_CONFIG_HOME'):
            env.pop(var, None)
        return subprocess.run(['bash', str(ROOT / 'install.sh'), '--only', 'antigravity',
                               '--no-third-party', '--no-mcp', *extra],
                              env=env, capture_output=True, text=True, timeout=60)

    def test_alvo_antigravity_linka_agents_e_declara_skills_idempotente(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / '.agents' / 'skills').mkdir(parents=True)
            cfg = home / '.gemini' / 'config'

            dry = self.run_install(home, '--dry-run')
            self.assertEqual(dry.returncode, 0, dry.stdout + dry.stderr)
            self.assertFalse(cfg.exists())

            first = self.run_install(home)
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            self.assertEqual(os.readlink(cfg / 'AGENTS.md'), str(ROOT / 'AGENTS.md'))
            skills = json.loads((cfg / 'skills.json').read_text())
            self.assertEqual(skills, {'entries': [{'path': str(home / '.agents' / 'skills')}]})
            self.assertFalse((home / '.codex').exists())
            self.assertFalse((home / '.claude').exists())

            second = self.run_install(home)
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            self.assertIn('alterações: 0', second.stdout)

    def test_skills_json_existente_e_preservado(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            skills_dir = home / '.agents' / 'skills'
            skills_dir.mkdir(parents=True)
            cfg = home / '.gemini' / 'config'
            cfg.mkdir(parents=True)
            (cfg / 'skills.json').write_text(json.dumps({'entries': [{'path': '/outro/lugar'}]}))

            res = self.run_install(home)
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
            paths = [e['path'] for e in json.loads((cfg / 'skills.json').read_text())['entries']]
            self.assertEqual(paths, ['/outro/lugar', str(skills_dir)])

            again = self.run_install(home)
            self.assertIn('alterações: 0', again.stdout)

    def test_skills_json_invalido_fica_intocado(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / '.agents' / 'skills').mkdir(parents=True)
            cfg = home / '.gemini' / 'config'
            cfg.mkdir(parents=True)
            (cfg / 'skills.json').write_text('{quebrado')

            res = self.run_install(home)
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
            self.assertEqual((cfg / 'skills.json').read_text(), '{quebrado')


if __name__ == '__main__':
    unittest.main()
