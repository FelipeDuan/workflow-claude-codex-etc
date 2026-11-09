import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('harden', ROOT / 'scripts/harden.py')
harden = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harden)

ASTRO = {'ASTRO_DEV_BACKGROUND': '0', 'ASTRO_PREVIEW_BACKGROUND': '0'}


class AstroEnvTests(unittest.TestCase):
    def test_env_gerenciado_tem_as_variaveis_do_astro(self):
        for key, value in ASTRO.items():
            self.assertEqual(harden.ENV.get(key), value)

    def test_claude_settings_acrescenta_e_e_idempotente(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'settings.json'
            path.write_text(json.dumps({'env': {'OUTRA': 'x'}}))
            self.assertEqual(harden.claude_settings(str(path), True), 10)
            env = json.loads(path.read_text())['env']
            self.assertEqual(env['OUTRA'], 'x')
            for key, value in ASTRO.items():
                self.assertEqual(env[key], value)
            self.assertEqual(harden.claude_settings(str(path), True), 0)

    def test_claude_settings_nao_sobrescreve_valor_diferente(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'settings.json'
            path.write_text(json.dumps({'env': {'ASTRO_DEV_BACKGROUND': '1'}}))
            harden.claude_settings(str(path), True)
            env = json.loads(path.read_text())['env']
            self.assertEqual(env['ASTRO_DEV_BACKGROUND'], '1')
            self.assertEqual(env['ASTRO_PREVIEW_BACKGROUND'], '0')

    def test_codex_env_cria_bloco_com_as_variaveis(self):
        try:
            import tomllib
        except ImportError:
            self.skipTest('Python sem tomllib')
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'config.toml'
            path.write_text('model = "x"\n')
            self.assertEqual(harden.codex_env(str(path), True), 10)
            policy = tomllib.loads(path.read_text())['shell_environment_policy']['set']
            for key, value in ASTRO.items():
                self.assertEqual(policy[key], value)
            self.assertEqual(harden.codex_env(str(path), True), 0)

    def test_codex_env_set_existente_sem_astro_pede_acrescimo_manual(self):
        try:
            import tomllib  # noqa: F401
        except ImportError:
            self.skipTest('Python sem tomllib')
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'config.toml'
            original = '[shell_environment_policy.set]\nDO_NOT_TRACK = "1"\n'
            path.write_text(original)
            self.assertEqual(harden.codex_env(str(path), True), 2)
            self.assertEqual(path.read_text(), original)


if __name__ == '__main__':
    unittest.main()
