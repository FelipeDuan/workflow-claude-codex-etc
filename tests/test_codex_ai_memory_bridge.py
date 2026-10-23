import contextlib
import builtins
import importlib.util
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

try:
    import tomllib
except ImportError:
    tomllib = None

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('harden', ROOT / 'scripts/harden.py')
harden = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harden)


class MissingTomllibTests(unittest.TestCase):
    def test_missing_parser_warns_and_preserves_file(self):
        original_import = builtins.__import__

        def without_tomllib(name, *args, **kwargs):
            if name == 'tomllib':
                raise ImportError('sem tomllib')
            return original_import(name, *args, **kwargs)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'config.toml'
            original = b'[mcp_servers.ai-memory]\nurl = "old"\n'
            path.write_bytes(original)
            output = io.StringIO()
            with mock.patch('builtins.__import__', side_effect=without_tomllib), contextlib.redirect_stdout(output):
                self.assertEqual(harden.codex_ai_memory_bridge(str(path), True), harden.UNSAFE)
            self.assertTrue(output.getvalue().startswith('WARN '))
            self.assertEqual(path.read_bytes(), original)


@unittest.skipUnless(tomllib, 'requer Python >= 3.11 (tomllib)')
class CodexAiMemoryBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'config.toml'
        self.binary = Path(self.tmp.name) / 'ai-memory'
        self.binary.write_text('#!/bin/sh\n')
        self.binary.chmod(0o755)
        patch = mock.patch.object(harden.shutil, 'which', return_value=str(self.binary))
        patch.start()
        self.addCleanup(patch.stop)

    def run_mode(self, apply=True):
        return harden.main(['harden.py', 'codex-ai-memory-bridge', str(self.path),
                            '--apply' if apply else '--check'])

    def test_url_to_bridge_check_apply_and_idempotence(self):
        original = b'[mcp_servers.ai-memory]\nurl = "http://localhost/mcp"\nbearer_token_env_var = "AI_MEMORY_AUTH_TOKEN"\n'
        self.path.write_bytes(original)
        self.path.chmod(0o640)
        self.assertEqual(self.run_mode(False), harden.CHANGED)
        self.assertEqual(self.path.read_bytes(), original)
        self.assertEqual(self.run_mode(), harden.CHANGED)
        self.assertEqual(tomllib.loads(self.path.read_text())['mcp_servers']['ai-memory'], {
            'command': str(self.binary), 'args': ['mcp-bridge', '--no-session-id',
            '--server-url', 'http://127.0.0.1:49374/mcp']})
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o640)
        merged = self.path.read_bytes()
        self.assertEqual(self.run_mode(), harden.NOTHING)
        self.assertEqual(self.path.read_bytes(), merged)

    def test_already_bridge_no_table_and_missing_file(self):
        for original in (b'[mcp_servers.ai-memory]\ncommand = "/old/ai-memory"\nargs = ["mcp-bridge"]\n',
                         b'model = "test"\n[mcp_servers.other]\nurl = "other"\n'):
            with self.subTest(original=original):
                self.path.write_bytes(original)
                self.assertEqual(self.run_mode(), harden.NOTHING)
                self.assertEqual(self.path.read_bytes(), original)
        self.path.unlink()
        self.assertEqual(self.run_mode(), harden.NOTHING)
        self.assertFalse(self.path.exists())

    def test_invalid_toml_warns_without_writing(self):
        original = b'[mcp_servers.ai-memory]\nurl = "unterminated\n'
        self.path.write_bytes(original)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(self.run_mode(), harden.UNSAFE)
        self.assertTrue(output.getvalue().startswith('WARN '))
        self.assertEqual(self.path.read_bytes(), original)

    def test_other_tables_crlf_and_multiline_headers_preserved(self):
        prefix = b'# comentario\r\nmodel = "test"\r\nnote = """\r\n[mcp_servers.ai-memory]\r\nurl = "fake"\r\n"""\r\n'
        suffix = b'[mcp_servers.other] # manter\r\nurl = "other"\r\n[projects."/a b"]\r\ntrust_level = "trusted"\r\n'
        self.path.write_bytes(prefix + b'[mcp_servers."ai-memory"] # alvo\r\nurl = "old"\r\n' + suffix)
        self.assertEqual(self.run_mode(), harden.CHANGED)
        merged = self.path.read_bytes()
        self.assertTrue(merged.startswith(prefix))
        self.assertTrue(merged.endswith(suffix))
        self.assertNotIn(b'\n', merged.replace(b'\r\n', b''))

    def test_missing_binary_and_local_bin_fallback(self):
        original = b'[mcp_servers.ai-memory]\nurl = "old"\n'
        self.path.write_bytes(original)
        fallback = Path(self.tmp.name) / '.local/bin/ai-memory'
        with mock.patch.object(harden.shutil, 'which', return_value=None), mock.patch.dict(os.environ, HOME=self.tmp.name):
            self.assertEqual(self.run_mode(), harden.NOTHING)
            self.assertEqual(self.path.read_bytes(), original)
            fallback.parent.mkdir(parents=True)
            fallback.write_text('#!/bin/sh\n')
            self.assertEqual(self.run_mode(), harden.NOTHING)
            fallback.chmod(0o755)
            self.assertEqual(self.run_mode(), harden.CHANGED)
        self.assertEqual(tomllib.loads(self.path.read_text())['mcp_servers']['ai-memory']['command'], str(fallback))

    def test_subtable_is_not_silently_changed(self):
        original = b'[mcp_servers.ai-memory]\nurl = "old"\n[mcp_servers.ai-memory.headers]\nx = "keep"\n'
        self.path.write_bytes(original)
        self.assertEqual(self.run_mode(), harden.UNSAFE)
        self.assertEqual(self.path.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
