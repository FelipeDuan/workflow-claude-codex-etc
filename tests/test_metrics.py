"""Testes das métricas (scripts/metrics) com fixtures sintéticas. Nada de dados reais."""
import contextlib
import datetime
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/metrics'))

import build  # noqa: E402
import claude  # noqa: E402
import codex  # noqa: E402
import metrics_common as mc  # noqa: E402
import misc  # noqa: E402
import paseo  # noqa: E402

UTC = datetime.timezone.utc
SEGREDO = 'SEGREDO-NAO-VAZAR'  # texto de prompt sintético: nunca pode aparecer em saída


def ctx_for(home, until='2026-11-09T16:00:00Z', restricted=()):
    tz = mc.parse_tz('-03:00')
    return mc.Ctx(tz=tz, until=mc.parse_until(until, tz), periods={
        'baseline': ('2026-10-08', '2026-10-21'), 'S1': ('2026-10-22', '2026-11-01'), 'S2': ('2026-11-02', None)},
        home=home, restricted=restricted)


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(r) + '\n' for r in rows))


def asst(mid, ts, model='claude-opus-5-5', out=10, side=False, **extra):
    return {'type': 'assistant', 'timestamp': ts, 'isSidechain': side,
            'message': {'id': mid, 'model': model, 'content': SEGREDO,
                        'usage': {'input_tokens': 1, 'output_tokens': out,
                                  'cache_creation_input_tokens': 2, 'cache_read_input_tokens': 100}}, **extra}


class CommonTests(unittest.TestCase):
    def test_tz_range_e_until(self):
        self.assertEqual(mc.parse_tz('-03:00').utcoffset(None), datetime.timedelta(hours=-3))
        self.assertEqual(mc.parse_tz('-03').utcoffset(None), datetime.timedelta(hours=-3))
        self.assertEqual(mc.parse_range('2026-11-02..', None), ('2026-11-02', None))
        self.assertEqual(mc.parse_range(None, ('a', 'b')), ('a', 'b'))
        self.assertEqual(mc.parse_until('2026-11-09T16:00:00Z', None), datetime.datetime(2026, 11, 9, 16, tzinfo=UTC))

    def test_dia_local_e_periodo(self):
        ctx = ctx_for(Path('/h'))
        self.assertEqual(ctx.day('2026-11-02T01:00:00Z'), '2026-11-01')  # -03: ainda 01/11
        self.assertEqual(ctx.per('2026-11-01'), 'S1')
        self.assertEqual(ctx.per('2026-11-02'), 'S2')
        self.assertEqual(ctx.per('2026-10-10'), 'outro')
        self.assertEqual(ctx.periods['S2'][1], '2026-11-09')  # fim aberto = dia do until

    def test_pseudonimiza_projeto_restrito(self):
        home = Path('/home/u')
        ctx = ctx_for(home, restricted=['/home/u/Workspace/cliente-x', '/home/u/Workspace/area/sigilo'])
        self.assertEqual(ctx.project_label('-home-u-Workspace-cliente-x'), 'restrito')
        self.assertEqual(ctx.project_label('-home-u-Workspace-cliente-x-sub'), 'restrito')
        self.assertEqual(ctx.project_label('-home-u-Workspace-area-sigilo-v2'), 'restrito')
        self.assertEqual(ctx.project_label('-home-u-Workspace-publico'), 'Workspace-publico')
        self.assertEqual(ctx.project_label('-home-u--paseo-worktrees-abc-nome'), 'paseo-worktree')
        self.assertEqual(ctx.repo_label('/home/u/Workspace/cliente-x/api'), 'restrito')
        self.assertEqual(ctx.repo_label('/home/u/Workspace/publico/api'), 'publico/api')

    def test_load_restricted_expande_til(self):
        with tempfile.TemporaryDirectory() as d:
            t = Path(d) / 'p.toml'
            t.write_text('[restricted]\npaths = ["~/Workspace/x", "/abs/y/"]\n')
            self.assertEqual(mc.load_restricted(t, Path('/home/u')), ['/home/u/Workspace/x', '/abs/y'])
            self.assertEqual(mc.load_restricted(Path(d) / 'nao-existe.toml', Path('/h')), [])


class ClaudeTests(unittest.TestCase):
    def test_dedup_subagente_corte_e_restrito(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            root = home / '.claude/projects'
            enc = mc.encode_path
            pub = enc(home / 'Workspace/publico')
            res = enc(home / 'Workspace/sigilo')
            write_jsonl(root / pub / 's1.jsonl', [
                asst('m1', '2026-11-03T12:00:00Z'),
                asst('m1', '2026-11-03T12:00:01Z', out=30),            # duplicata: fica a de maior output
                asst('m2', '2026-11-03T13:00:00Z', model='claude-sonnet-5-5', side=True),
                asst('m3', '2026-11-09T17:00:00Z'),                    # depois do corte
                {'type': 'user', 'message': {'content': SEGREDO}},
            ])
            with (root / pub / 's1.jsonl').open('a') as f:
                f.write('linha quebrada\n')
            write_jsonl(root / pub / 's1' / 'subagents' / 'agent-a.jsonl', [asst('m4', '2026-10-30T12:00:00Z')])
            write_jsonl(root / res / 's2.jsonl', [asst('m5', '2026-11-04T12:00:00Z')])
            ctx = ctx_for(home, restricted=[str(home / 'Workspace/sigilo')])
            out = claude.collect(ctx, root)
            self.assertEqual(out['dedup_msgs'], 4)
            self.assertEqual(out['dupe_lines'], 1)
            self.assertEqual(out['dupes_with_diff_usage'], 1)
            self.assertEqual(out['raw_assistant_lines'], 5)  # m3 (após o corte) não conta
            s2 = out['agg']['S2|opus|all']
            self.assertEqual((s2['msgs'], s2['out']), (2, 30 + 10))
            self.assertEqual(out['agg']['S2|sonnet|sub']['msgs'], 1)
            self.assertEqual(out['agg']['S1|opus|sub']['msgs'], 1)  # arquivo em /subagents/
            self.assertEqual(out['sessions']['S2'], {'Workspace-publico': 1, 'restrito': 1})
            self.assertNotIn('sigilo', json.dumps(out))
            self.assertEqual(sum(v['msgs'] for k, v in out['agg'].items() if k.startswith('S2|') and k.endswith('|all')),
                             out['sanity']['S2'])


class CodexTests(unittest.TestCase):
    def ev(self, ts, total, model=None):
        rows = []
        if model:
            rows.append({'type': 'turn_context', 'payload': {'model': model}})
        rows.append({'timestamp': ts, 'type': 'event_msg', 'payload': {'type': 'token_count', 'info': {
            'total_token_usage': {'input_tokens': total, 'cached_input_tokens': 0, 'output_tokens': 0,
                                  'reasoning_output_tokens': 0, 'total_tokens': total}}}})
        return rows

    def test_delta_reset_modelo_e_corte(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rows = (self.ev('2026-11-03T12:00:00Z', 100, 'gpt-x') + self.ev('2026-11-03T12:01:00Z', 250)
                    + self.ev('2026-11-03T12:02:00Z', 40)                      # contador reiniciou
                    + self.ev('2026-11-09T18:00:00Z', 900))                    # após o corte
            sufixo = '-bbbb-cccc-dddd-' + 'e' * 12 + '.jsonl'
            write_jsonl(root / '2026/11/03' / ('rollout-x-' + 'a' * 8 + sufixo), rows)
            write_jsonl(root / '2026/09/01' / ('rollout-y-' + 'f' * 8 + sufixo), self.ev('2026-09-01T12:00:00Z', 5, 'velho'))
            out = codex.collect(ctx_for(Path(d)), root, since='2026-10-01')
            self.assertEqual(out['files'], 1)          # pasta anterior a --since é ignorada
            self.assertEqual(out['token_events'], 3)
            self.assertEqual(out['resets'], 1)
            self.assertEqual(out['agg']['S2|gpt-x']['total_tokens'], 100 + 150 + 40)
            self.assertEqual(out['sum_last_totals'], 40)
            self.assertEqual(out['agg']['S2|gpt-x']['sessions'], 1)


INSPECT = """Id           abc-1
Name         titulo-privado
Provider     codex
Model        gpt-x
Status       closed
CreatedAt    2026-11-04T12:00:00Z
Outra        ignorada
"""


class PaseoTests(unittest.TestCase):
    def test_parse(self):
        r = paseo.parse(INSPECT)
        self.assertEqual((r['Id'], r['Provider'], r['Status']), ('abc-1', 'codex', 'closed'))
        self.assertNotIn('Outra', r)

    def test_collect_arquivo_vigia_e_privacidade(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            arq = d / 'arq'
            arq.mkdir()
            (arq / 'abc-1.inspect.txt').write_text(INSPECT)
            (arq / 'abc-1.log.txt').write_text(f'{SEGREDO} commit realizado 1a2b3c4d5e6f\nFree usage limit reached\n')
            (arq / 'so-log.log.txt').write_text('nada\n')
            wd = d / 'watchdog.log'
            wd.write_text('2026-11-04T12:10:00Z erro agente=abc-1 detalhe=limite de uso: x\n'
                          '2026-11-04T12:20:00Z parado agente=abc-1 detalhe=y\n'
                          '2026-11-04T12:30:00Z paseo_error detalhe=paseo\n'
                          '2026-11-09T18:00:00Z erro agente=abc-1 detalhe=depois do corte\n')
            novo = INSPECT.replace('abc-1', 'vivo-9').replace('2026-11-04', '2026-11-09')

            def runner(cmd):
                if cmd[:3] == ['paseo', 'ls', '-a']:
                    return json.dumps([{'id': 'vivo-9'}])
                return novo
            ctx = ctx_for(d)
            out = paseo.collect(ctx, arq, wd, None, live=True, runner=runner)
            self.assertEqual((out['n'], out['n_archived'], out['n_current']), (3, 2, 1))
            a = {x['Id']: x for x in out['agents']}
            self.assertTrue(a['abc-1']['erro_limite'])
            self.assertTrue(a['abc-1']['log_commit_hash'])
            self.assertEqual(a['abc-1']['wd'], {'erro': 1, 'parado': 1})  # evento após o corte ignorado
            self.assertEqual(a['so-log']['periodo'], 'sem_data')
            self.assertEqual(a['vivo-9']['periodo'], 'S2')
            txt = json.dumps(out)
            self.assertNotIn('titulo-privado', txt)
            self.assertNotIn(SEGREDO, txt)
            sem_live = paseo.collect(ctx_for(d), arq, wd, None, live=False)
            self.assertEqual(sem_live['n_current'], 0)

    def test_agente_criado_apos_corte_e_ignorado(self):
        with tempfile.TemporaryDirectory() as d:
            ctx = ctx_for(Path(d), until='2026-11-04T00:00:00Z')
            runner = lambda cmd: json.dumps([{'id': 'abc-1'}]) if cmd[1] == 'ls' else INSPECT  # noqa: E731
            out = paseo.collect(ctx, None, None, None, runner=runner)
            self.assertEqual(out['n'], 0)


class MiscTests(unittest.TestCase):
    def test_family_nao_expoe_nome_de_pessoa(self):
        self.assertEqual(misc.family('Claude Opus 5.5'), 'Claude Opus')
        self.assertEqual(misc.family('Codex'), 'Codex/GPT')
        self.assertEqual(misc.family('Fulana de Tal'), 'outro')

    def test_commits_dedup_restrito_e_trailers(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            ws = home / 'Workspace'
            for p in ('publico', 'sigilo/api'):
                (ws / p / '.git').mkdir(parents=True)
            ctx = ctx_for(home, restricted=[str(ws / 'sigilo')])
            bloco = ('@@{sha}|{dia}\nfeat: x\n\nCo-Authored-By: Claude Opus 5.5 <a@b.c>\n'
                     'Co-Authored-By: Fulana de Tal <f@t.c>\n@@END\n')
            sem = '@@{sha}|{dia}\nfix: y\n@@END\n'

            def runner(cmd):
                if cmd[2].endswith('publico'):
                    return bloco.format(sha='a1', dia='2026-10-25') + sem.format(sha='a2', dia='2026-11-03')
                return bloco.format(sha='a1', dia='2026-10-25') + sem.format(sha='r1', dia='2026-11-03')  # a1 repetido
            out = misc.commits(ctx, '2026-10-22', runner=runner)
            self.assertEqual(out['repos_com_git'], 2)
            self.assertEqual(out['commits_por_repo'], {'publico': 2, 'restrito': 1})
            self.assertEqual(out['por_periodo']['S1']['total'], 1)
            self.assertEqual(out['por_periodo']['S2']['sem_coautor'], 2)
            self.assertEqual(out['por_periodo']['S1']['co:Claude Opus 5.5'], 1)
            self.assertEqual(out['por_periodo']['S1']['co:outro'], 1)
            self.assertNotIn('Fulana', json.dumps(out))
            self.assertNotIn('sigilo', json.dumps(out))

    def test_telemetria_e_quota(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            write_jsonl(d / 't.jsonl', [{'date': '2026-11-03', 'harness': 'h', 'outcome': 'success'},
                                        {'date': '2026-11-20', 'harness': 'h', 'outcome': 'failed'}])
            ctx = ctx_for(d)
            t = misc.telemetria(ctx, d / 't.jsonl')
            self.assertEqual((t['n'], t['por_outcome']), (1, {'success': 1}))
            (d / 'q').mkdir()
            (d / 'q/claude.json').write_text(json.dumps({
                'provider': 'claude', 'status': 'ok', 'conta': 'x@y.z', 'note': 'n',
                'windows': [{'kind': 'five_hour', 'used_percent': 5, 'resets_at': 'r', 'window_minutes': 300, 'extra': 1}]}))
            q = misc.quota(ctx, d / 'q')
            self.assertNotIn('x@y.z', json.dumps(q))
            self.assertEqual(q['claude']['windows'][0]['used_percent'], 5)

    def test_vigia_por_periodo_e_provider(self):
        with tempfile.TemporaryDirectory() as d:
            wd = Path(d) / 'w.log'
            wd.write_text('2026-10-27T12:00:00Z erro agente=a1 detalhe=Free usage limit\n'
                          '2026-11-03T12:00:00Z pendente agente=zz detalhe=p\n')
            v = misc.vigia(ctx_for(Path(d)), wd, [{'Id': 'a1', 'pm': 'codex/gpt-x'}])
            self.assertEqual(v['eventos']['S1'], {'erro': 1, 'erro_limite_uso': 1})
            self.assertEqual(v['por_provider_modelo']['S2|pendente|agente_nao_identificado'], 1)


class BuildEndToEndTests(unittest.TestCase):
    def test_saida_completa_sem_vazar_dados(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d) / 'home'
            out = Path(d) / 'out'
            enc = mc.encode_path
            write_jsonl(home / '.claude/projects' / enc(home / 'Workspace/sigilo') / 's.jsonl',
                        [asst('m1', '2026-11-03T12:00:00Z')])
            write_jsonl(home / '.claude/projects' / enc(home / 'Workspace/pub') / 's.jsonl',
                        [asst('m2', '2026-11-03T12:00:00Z'), asst('m3', '2026-10-23T12:00:00Z', side=True)])
            cfg = Path(d) / 'cfg.toml'
            cfg.write_text(f'[restricted]\npaths = ["{home}/Workspace/sigilo"]\n')
            (home / '.local/state/ai-os').mkdir(parents=True)
            with contextlib.redirect_stdout(io.StringIO()):
                rc = build.main(['--home', str(home), '--out', str(out), '--until', '2026-11-09T16:00:00Z',
                                 '--tz', '-03:00', '--no-paseo-live', '--restricted-config', str(cfg),
                                 '--telemetry', str(Path(d) / 'nada.jsonl')])
            self.assertEqual(rc, 0)
            for f in ('claude', 'codex', 'paseo', 'misc', 'sanity', 'baseline_cmp', 'metricas'):
                self.assertTrue((out / f'{f}.json').exists(), f)
            self.assertTrue((out / 'METRICAS.md').exists())
            m = json.loads((out / 'metricas.json').read_text())
            self.assertEqual(m['claude']['sessions']['S2'], {'restrito': 1, 'Workspace-pub': 1})
            self.assertEqual(m['execucao']['leitura']['files'] > 0, True)
            tudo = ''.join(p.read_text() for p in out.iterdir())
            for proibido in ('sigilo', SEGREDO, str(home), '/Users/'):
                self.assertNotIn(proibido, tudo)

    def test_baseline_cmp_formulas(self):
        ctx = ctx_for(Path('/h'))
        c = {'bydaytype': {'2026-11-03|main': {'msgs': 2, 'in': 10, 'out': 10, 'cc': 20, 'cr': 960},
                           '2026-11-03|sub': {'msgs': 1, 'in': 0, 'out': 0, 'cc': 0, 'cr': 1000}}}
        x = {'bydaymodel': {'2026-11-03|m': {'total_tokens': 4_000_000}}}
        r = build.baseline_cmp(ctx, c, x)['S2']
        self.assertEqual(r['claude']['days'], 8)  # 02/11..09/11
        self.assertAlmostEqual(r['claude']['sub_pct'], 100 * 1000 / 2000)
        self.assertAlmostEqual(r['claude']['cache_read_pct'], 100 * 1960 / 2000)
        self.assertAlmostEqual(r['claude']['ctx_turno_main'], (10 + 20 + 960) / 2)
        self.assertAlmostEqual(r['codex_M_dia'], 4 / 8)


if __name__ == '__main__':
    unittest.main()
