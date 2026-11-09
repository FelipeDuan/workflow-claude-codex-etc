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
    def test_dicionario_env_tem_as_variaveis_do_astro(self):
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

    def _toml(self, text, apply=True):
        try:
            import tomllib
        except ImportError:
            self.skipTest('Python sem tomllib')
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / 'config.toml'
        path.write_text(text)
        return tomllib, path

    def test_codex_env_mescla_em_set_existente_e_e_idempotente(self):
        original = ('[shell_environment_policy.set]\n# privacidade\nIMPECCABLE_NO_TELEMETRY = "1"\n'
                    'IMPECCABLE_NO_UPDATE_CHECK = "1"\nDO_NOT_TRACK = "1"\n\n[outra]\nx = 1\n')
        tomllib, path = self._toml(original)
        self.assertEqual(harden.codex_env(str(path), True), 10)
        text = path.read_text()
        self.assertIn('# privacidade', text)
        self.assertIn('[outra]\nx = 1\n', text)
        policy = tomllib.loads(text)['shell_environment_policy']['set']
        self.assertEqual(policy, harden.ENV)
        self.assertEqual(harden.codex_env(str(path), True), 0)
        self.assertEqual(path.read_text(), text)

    def test_codex_env_set_existente_preserva_conflito(self):
        tomllib, path = self._toml('[shell_environment_policy.set]\nASTRO_DEV_BACKGROUND = "1"\n')
        harden.codex_env(str(path), True)
        policy = tomllib.loads(path.read_text())['shell_environment_policy']['set']
        self.assertEqual(policy['ASTRO_DEV_BACKGROUND'], '1')
        self.assertEqual(policy['ASTRO_PREVIEW_BACKGROUND'], '0')

    def test_codex_env_toml_real_com_hooks_state_aninhado(self):
        original = ('model = "x"\n\n[mcp_servers.ai-memory]\ncommand = "ai-memory"\n\n'
                    '[shell_environment_policy.set]\nDO_NOT_TRACK = "1"\n\n'
                    '[hooks.state]\n\n[hooks.state."/home/u/.codex/hooks.json:stop:0:0"]\ntrusted_hash = "abc"\n')
        tomllib, path = self._toml(original)
        antes = tomllib.loads(original)
        self.assertEqual(harden.codex_env(str(path), True), 10)
        depois = tomllib.loads(path.read_text())
        self.assertEqual(depois['hooks'], antes['hooks'])
        self.assertEqual(depois['mcp_servers'], antes['mcp_servers'])
        self.assertEqual(depois['shell_environment_policy']['set']['DO_NOT_TRACK'], '1')
        for key, value in ASTRO.items():
            self.assertEqual(depois['shell_environment_policy']['set'][key], value)

    def test_codex_env_set_inline_pede_acrescimo_manual(self):
        original = '[shell_environment_policy]\nset = { DO_NOT_TRACK = "1" }\n'
        tomllib, path = self._toml(original)
        self.assertEqual(harden.codex_env(str(path), True), 2)
        self.assertEqual(path.read_text(), original)


if __name__ == '__main__':
    unittest.main()
