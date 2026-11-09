import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('quota_antigravity', ROOT / 'scripts/quota_antigravity.py')
quota = importlib.util.module_from_spec(spec)
spec.loader.exec_module(quota)

REAL_SAMPLE = (
    "Gemini Models\tWeekly Limit Remaining\t100%\t2026-11-16T14:06:53Z\n"
    "Gemini Models\tFive Hour Limit Remaining\t100%\t2026-11-09T19:06:53Z\n"
    "Claude and GPT models\tWeekly Limit Remaining\t100%\t2026-11-16T14:10:20Z\n"
    "Claude and GPT models\tFive Hour Limit Remaining\t100%\t2026-11-09T19:10:20Z\n"
    "Gemini 4 Argon\tGemini 4 Argon Weekly Limit\t100%\t2026-11-16T14:10:20Z\n"
)


class QuotaAntigravityTests(unittest.TestCase):
    def test_parse_valido_exemplo_real(self):
        result = subprocess.CompletedProcess(
            args=['agy', '-p', '/usage'],
            returncode=0,
            stdout=REAL_SAMPLE,
            stderr='',
        )
        with patch.object(quota.subprocess, 'run', return_value=result) as run_mock:
            output = quota.fetch_quota()

        run_mock.assert_called_once_with(
            ['agy', '-p', '/usage'],
            capture_output=True,
            text=True,
            timeout=30.0,
        )
        self.assertEqual(output['provider'], 'antigravity')
        self.assertEqual(output['source'], 'agy-usage')
        self.assertEqual(output['status'], 'ok')
        self.assertEqual(output['note'], '')
        self.assertTrue(output['fetched_at'].endswith('Z'))

        windows = output['windows']
        self.assertEqual(len(windows), 5)

        self.assertEqual(windows[0], {
            'kind': 'weekly',
            'pool': 'Gemini Models',
            'used_percent': 0.0,
            'resets_at': '2026-11-16T14:06:53Z',
            'window_minutes': 10080,
        })
        self.assertEqual(windows[1], {
            'kind': 'five_hour',
            'pool': 'Gemini Models',
            'used_percent': 0.0,
            'resets_at': '2026-11-09T19:06:53Z',
            'window_minutes': 300,
        })
        self.assertEqual(windows[2], {
            'kind': 'weekly',
            'pool': 'Claude and GPT models',
            'used_percent': 0.0,
            'resets_at': '2026-11-16T14:10:20Z',
            'window_minutes': 10080,
        })
        self.assertEqual(windows[3], {
            'kind': 'five_hour',
            'pool': 'Claude and GPT models',
            'used_percent': 0.0,
            'resets_at': '2026-11-09T19:10:20Z',
            'window_minutes': 300,
        })
        self.assertEqual(windows[4], {
            'kind': 'weekly',
            'pool': 'Gemini 4 Argon',
            'used_percent': 0.0,
            'resets_at': '2026-11-16T14:10:20Z',
            'window_minutes': 10080,
        })

    def test_conversao_porcentagem_restante_para_usada(self):
        casos = [
            ('100%', 0.0),
            ('75%', 25.0),
            ('65.5%', 34.5),
            ('0%', 100.0),
        ]
        for pct_str, esperado in casos:
            with self.subTest(pct=pct_str):
                texto = f"Pool Teste\tFive Hour Limit\t{pct_str}\t2026-11-09T19:00:00Z\n"
                result = subprocess.CompletedProcess(['agy', '-p', '/usage'], 0, texto, '')
                with patch.object(quota.subprocess, 'run', return_value=result):
                    output = quota.fetch_quota()
                self.assertEqual(output['status'], 'ok')
                self.assertEqual(output['windows'][0]['used_percent'], esperado)

    def test_reconhecimento_de_variacoes_de_janela(self):
        casos = [
            ('Five Hour Limit Remaining', 'five_hour', 300),
            ('5 Hour Limit', 'five_hour', 300),
            ('Janela 5h', 'five_hour', 300),
            ('Weekly Limit Remaining', 'weekly', 10080),
            ('Week Quota', 'weekly', 10080),
            ('Limite Semanal', 'weekly', 10080),
        ]
        for janela_str, kind_esperado, mins_esperado in casos:
            with self.subTest(janela=janela_str):
                texto = f"Pool\t{janela_str}\t50%\t2026-11-09T19:00:00Z\n"
                result = subprocess.CompletedProcess(['agy', '-p', '/usage'], 0, texto, '')
                with patch.object(quota.subprocess, 'run', return_value=result):
                    output = quota.fetch_quota()
                self.assertEqual(output['status'], 'ok')
                self.assertEqual(output['windows'][0]['kind'], kind_esperado)
                self.assertEqual(output['windows'][0]['window_minutes'], mins_esperado)

    def test_linha_desconhecida_ignorada_com_note_mantendo_ok(self):
        texto = (
            "Pool Normal\tFive Hour Limit\t80%\t2026-11-09T19:00:00Z\n"
            "Pool Especial\tJanela Mensal Desconhecida\t90%\t2026-11-09T19:00:00Z\n"
        )
        result = subprocess.CompletedProcess(['agy', '-p', '/usage'], 0, texto, '')
        with patch.object(quota.subprocess, 'run', return_value=result):
            output = quota.fetch_quota()

        self.assertEqual(output['status'], 'ok')
        self.assertEqual(len(output['windows']), 1)
        self.assertEqual(output['windows'][0]['pool'], 'Pool Normal')
        self.assertIn('Linha desconhecida ignorada: Janela Mensal Desconhecida', output['note'])

    def test_todas_linhas_desconhecidas_vira_error(self):
        texto = "Pool Especial\tJanela Mensal Desconhecida\t90%\t2026-11-09T19:00:00Z\n"
        result = subprocess.CompletedProcess(['agy', '-p', '/usage'], 0, texto, '')
        with patch.object(quota.subprocess, 'run', return_value=result):
            output = quota.fetch_quota()

        self.assertEqual(output['status'], 'error')
        self.assertEqual(output['windows'], [])
        self.assertIn('Linha desconhecida ignorada', output['note'])

    def test_linhas_invalidas_geram_error_e_windows_vazio(self):
        casos_invalidos = [
            ('colunas faltantes', "Pool\tWeekly\t100%\n"),
            ('coluna vazia', "Pool\t\t100%\t2026-11-09T19:00:00Z\n"),
            ('porcentagem sem %', "Pool\tWeekly\t100\t2026-11-09T19:00:00Z\n"),
            ('porcentagem nao numerica', "Pool\tWeekly\tabc%\t2026-11-09T19:00:00Z\n"),
            ('porcentagem negativa', "Pool\tWeekly\t-10%\t2026-11-09T19:00:00Z\n"),
            ('porcentagem maior que 100', "Pool\tWeekly\t105%\t2026-11-09T19:00:00Z\n"),
            ('data invalida', "Pool\tWeekly\t100%\tdata-invalida\n"),
        ]
        for descricao, texto in casos_invalidos:
            with self.subTest(descricao=descricao):
                result = subprocess.CompletedProcess(['agy', '-p', '/usage'], 0, texto, '')
                with patch.object(quota.subprocess, 'run', return_value=result):
                    output = quota.fetch_quota()
                self.assertEqual(output['status'], 'error')
                self.assertEqual(output['windows'], [])
                self.assertTrue(len(output['note']) > 0)

    def test_saida_vazia_gera_error(self):
        for vazio in ['', '   \n\n  \t  ']:
            with self.subTest(vazio=vazio):
                result = subprocess.CompletedProcess(['agy', '-p', '/usage'], 0, vazio, '')
                with patch.object(quota.subprocess, 'run', return_value=result):
                    output = quota.fetch_quota()
                self.assertEqual(output['status'], 'error')
                self.assertEqual(output['windows'], [])
                self.assertIn('Saída do agy vazia', output['note'])

    def test_executavel_ausente_gera_error(self):
        with patch.object(quota.subprocess, 'run', side_effect=FileNotFoundError):
            output = quota.fetch_quota()
        self.assertEqual(output['status'], 'error')
        self.assertEqual(output['windows'], [])
        self.assertEqual(output['note'], 'Executável agy não encontrado.')

    def test_timeout_gera_error(self):
        with patch.object(quota.subprocess, 'run', side_effect=subprocess.TimeoutExpired(['agy'], 30.0)):
            output = quota.fetch_quota()
        self.assertEqual(output['status'], 'error')
        self.assertEqual(output['windows'], [])
        self.assertEqual(output['note'], 'Tempo limite na consulta ao agy.')

    def test_returncode_diferente_de_zero_gera_error(self):
        result = subprocess.CompletedProcess(['agy', '-p', '/usage'], 127, '', 'erro')
        with patch.object(quota.subprocess, 'run', return_value=result):
            output = quota.fetch_quota()
        self.assertEqual(output['status'], 'error')
        self.assertEqual(output['windows'], [])
        self.assertEqual(output['note'], 'Comando agy retornou código 127.')

    def test_escrita_atomica_com_write(self):
        output = {
            'provider': 'antigravity',
            'source': 'agy-usage',
            'fetched_at': quota.iso(),
            'status': 'ok',
            'windows': [{'kind': 'weekly', 'pool': 'P', 'used_percent': 10.0, 'resets_at': None, 'window_minutes': 10080}],
            'note': '',
        }
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(quota.Path, 'home', return_value=Path(directory)), \
             patch.object(quota, 'fetch_quota', return_value=output), \
             patch.object(quota.sys, 'argv', ['quota_antigravity.py', '--write']), \
             patch('sys.stdout', new_callable=io.StringIO) as stdout:
            quota.main()
            saved = Path(directory) / '.local/state/ai-os/quota/antigravity.json'
            self.assertTrue(saved.exists())
            self.assertEqual(json.loads(saved.read_text()), output)
            self.assertEqual(json.loads(stdout.getvalue()), output)
            self.assertEqual(list(saved.parent.iterdir()), [saved])

    def test_stdout_sem_write_nao_salva_arquivo(self):
        output = {
            'provider': 'antigravity',
            'source': 'agy-usage',
            'fetched_at': quota.iso(),
            'status': 'ok',
            'windows': [],
            'note': '',
        }
        with patch.object(quota, 'fetch_quota', return_value=output), \
             patch.object(quota, 'write_quota') as write_mock, \
             patch.object(quota.sys, 'argv', ['quota_antigravity.py']), \
             patch('sys.stdout', new_callable=io.StringIO) as stdout:
            quota.main()
        write_mock.assert_not_called()
        self.assertEqual(json.loads(stdout.getvalue()), output)

    def test_falha_de_escrita_gera_error_no_stdout(self):
        output = {
            'provider': 'antigravity',
            'source': 'agy-usage',
            'fetched_at': quota.iso(),
            'status': 'ok',
            'windows': [{'kind': 'five_hour', 'pool': 'P', 'used_percent': 0.0, 'resets_at': None, 'window_minutes': 300}],
            'note': '',
        }
        with patch.object(quota, 'fetch_quota', return_value=output), \
             patch.object(quota, 'write_quota', side_effect=PermissionError), \
             patch.object(quota.sys, 'argv', ['quota_antigravity.py', '--write']), \
             patch('sys.stdout', new_callable=io.StringIO) as stdout:
            quota.main()
        impresso = json.loads(stdout.getvalue())
        self.assertEqual(impresso['status'], 'error')
        self.assertEqual(impresso['windows'], [])
        self.assertEqual(impresso['note'], 'Não foi possível salvar a franquia.')

    def test_argumentos_invalidos_geram_error(self):
        for args in [['--invalid'], ['--write', 'extra'], ['foo']]:
            with self.subTest(args=args):
                with patch.object(quota.sys, 'argv', ['quota_antigravity.py', *args]), \
                     patch('sys.stdout', new_callable=io.StringIO) as stdout:
                    quota.main()
                impresso = json.loads(stdout.getvalue())
                self.assertEqual(impresso['status'], 'error')
                self.assertEqual(impresso['windows'], [])
                self.assertEqual(impresso['note'], 'Argumentos inválidos. Use --write para salvar.')


if __name__ == '__main__':
    unittest.main()
