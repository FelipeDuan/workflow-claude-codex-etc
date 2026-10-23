import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('harden', ROOT / 'scripts/harden.py')
harden = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harden)


class PluginDirsTests(unittest.TestCase):
    def test_missing_value_and_empty_string(self):
        for original in (None, {}, {'env': {'OTHER': '1'}},
                         {'env': {'CLAUDE_CODE_PLUGIN_DIRS': ''}}):
            with self.subTest(original=original), tempfile.TemporaryDirectory() as tmp:
                settings = Path(tmp) / 'settings.json'
                if original is not None:
                    settings.write_text(json.dumps(original))
                before = settings.read_bytes() if settings.exists() else None
                args = ['harden.py', 'claude-plugin-dirs', str(settings), '/repo/quota guard']
                self.assertEqual(harden.main(args + ['--check']), harden.CHANGED)
                self.assertEqual(settings.read_bytes() if settings.exists() else None, before)
                self.assertEqual(harden.main(args + ['--apply']), harden.CHANGED)
                merged = json.loads(settings.read_text())
                self.assertEqual(merged['env']['CLAUDE_CODE_PLUGIN_DIRS'], '/repo/quota guard')
                if original and original.get('env', {}).get('OTHER'):
                    self.assertEqual(merged['env']['OTHER'], '1')

    def test_existing_dirs_preserved_and_idempotent(self):
        for existing in ('/other', '/other:', '/one:/two'):
            with self.subTest(existing=existing), tempfile.TemporaryDirectory() as tmp:
                settings = Path(tmp) / 'settings.json'
                original = {'env': {'CLAUDE_CODE_PLUGIN_DIRS': existing, 'OTHER': '1'},
                            'hooks': {'Stop': []}, 'permissions': {'deny': ['existing']}}
                settings.write_text(json.dumps(original))
                self.assertEqual(harden.claude_plugin_dirs(str(settings), '/quota', True), harden.CHANGED)
                merged = json.loads(settings.read_text())
                expected = existing + ('' if existing.endswith(':') else ':') + '/quota'
                self.assertEqual(merged['env']['CLAUDE_CODE_PLUGIN_DIRS'], expected)
                merged['env']['CLAUDE_CODE_PLUGIN_DIRS'] = existing
                self.assertEqual(merged, original)
                before = settings.read_bytes()
                for apply in (False, True):
                    self.assertEqual(harden.claude_plugin_dirs(str(settings), '/quota', apply), harden.NOTHING)
                    self.assertEqual(settings.read_bytes(), before)

    def test_already_present_in_middle_is_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = Path(tmp) / 'settings.json'
            settings.write_text('{"env":{"CLAUDE_CODE_PLUGIN_DIRS":"/one:/quota:/two"}}')
            before = settings.read_bytes()
            self.assertEqual(harden.claude_plugin_dirs(str(settings), '/quota', True), harden.NOTHING)
            self.assertEqual(settings.read_bytes(), before)

    def test_invalid_types_and_json_are_untouched(self):
        invalid = ['{broken', '[]']
        invalid += [json.dumps({'env': value}) for value in (None, [], 'wrong', 1)]
        invalid += [json.dumps({'env': {'CLAUDE_CODE_PLUGIN_DIRS': value}})
                    for value in (None, [], {}, 1, True)]
        for raw in invalid:
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as tmp:
                settings = Path(tmp) / 'settings.json'
                settings.write_text(raw)
                before = settings.read_bytes()
                for apply in (False, True):
                    output = io.StringIO()
                    with contextlib.redirect_stdout(output):
                        result = harden.claude_plugin_dirs(str(settings), '/quota', apply)
                    self.assertEqual(result, harden.UNSAFE)
                    self.assertTrue(output.getvalue().startswith('WARN '))
                    self.assertEqual(settings.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
