#!/usr/bin/env python3
"""Ponto de entrada das métricas do AI OS (Claude, Codex, Paseo, vigia, commits).

Uso (reproduz o briefing de 09/11/2026):
    python3 scripts/metrics/build.py --until 2026-11-09T16:03:00Z \\
        --archive-dir ~/.local/state/ai-os/arquivo-agentes/20261109 --out DIR

Padrão de saída: ~/.local/state/ai-os/metricas/<AAAAMMDD do --until>/ (fora do repo).
Só stdlib. Só agrega contagens; projetos restritos saem como "restrito".
"""
import argparse
import collections
import datetime
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import claude  # noqa: E402
import codex  # noqa: E402
import misc  # noqa: E402
import paseo  # noqa: E402
import sanity  # noqa: E402
from metrics_common import (DEFAULT_PERIODS, Ctx, load_restricted, parse_range, parse_tz,  # noqa: E402
                            parse_until)

REPO = Path(__file__).resolve().parents[2]


def days_between(a, b):
    f = datetime.date.fromisoformat
    return (f(b) - f(a)).days + 1


def add_days(d, n):
    return (datetime.date.fromisoformat(d) + datetime.timedelta(days=n)).isoformat()


def baseline_cmp(ctx, c, x):
    """Comparação com a linha de base (GESTAO-CONTEXTO.md): por faixa de dias, a partir dos agregados diários."""
    s1, s2, bl = ctx.periods['S1'], ctx.periods['S2'], ctx.periods['baseline']
    ranges = {'antes_08_21': bl, 'depois_22_25': (s1[0], add_days(s1[0], 3)), 'S1': s1, 'S2': s2,
              'S2_dias_completos': (s2[0], add_days(s2[1], -1))}
    out = {}
    for name, (a, b) in ranges.items():
        n = days_between(a, b)
        t = {k: collections.Counter() for k in ('main', 'sub')}
        for k, v in c['bydaytype'].items():
            d, kind = k.split('|')
            if a <= d <= b:
                t[kind].update(v)
        tot = lambda v: v['in'] + v['out'] + v['cc'] + v['cr']  # noqa: E731
        T = tot(t['main']) + tot(t['sub'])
        cr = t['main']['cr'] + t['sub']['cr']
        sem_cr = T - cr
        m = t['main']
        cx = sum(v['total_tokens'] for k, v in x['bydaymodel'].items() if a <= k.split('|')[0] <= b)
        out[name] = dict(claude=dict(
            days=n, M_dia_total=T / n / 1e6, M_dia_sem_cr=sem_cr / n / 1e6,
            sub_pct=100 * tot(t['sub']) / T if T else 0.0, cache_read_pct=100 * cr / T if T else 0.0,
            ctx_turno_main=(m['in'] + m['cc'] + m['cr']) / m['msgs'] if m['msgs'] else 0.0,
            msgs_main=m['msgs'], msgs_sub=t['sub']['msgs']), codex_M_dia=cx / n / 1e6)
    return out


def PC(x):
    return f'{x:.1f}%'.replace('.', ',')


def M(v):
    return f'{v / 1e6:,.1f}'.replace(',', '_').replace('.', ',').replace('_', '.')


def K(n):
    return f'{n:,}'.replace(',', '.')


def render_md(ctx, c, x, p, m, b, s, until_iso):
    L = []
    A = L.append
    S1, S2 = ctx.periods['S1'], ctx.periods['S2']
    fmt = lambda d: f'{d[8:]}/{d[5:7]}'  # noqa: E731
    n1, n2 = days_between(*S1), days_between(*S2)
    A(f'# Métricas do AI OS: S1 ({fmt(S1[0])} a {fmt(S1[1])}, {n1} dias) vs S2 ({fmt(S2[0])} a {fmt(S2[1])}, {n2} dias)')
    A('')
    A(f'Corte temporal: {until_iso} (fuso {c["tz"]}). Só números e observações factuais. Dados completos: `metricas.json`. '
      'S2 termina no dia do corte (parcial). Tokens em milhões (M); "total" = input + output + cache creation + cache read.')
    A('')
    A('## 1. Claude Code (mensagens deduplicadas por `message.id`)')
    A('')
    A('| Período | Modelo | Msgs | Total M | Sem cache read M | % do total | % sem cache read | Output M |')
    A('|---|---|--:|--:|--:|--:|--:|--:|')
    for P in ('S1', 'S2'):
        rows = [(k.split('|')[1], v) for k, v in c['agg'].items() if k.startswith(P + '|') and k.endswith('|all') and v['msgs']]
        T = lambda v: v['in'] + v['out'] + v['cc'] + v['cr']  # noqa: E731
        N = lambda v: v['in'] + v['out'] + v['cc']  # noqa: E731
        tt = sum(T(v) for _, v in rows)
        tn = sum(N(v) for _, v in rows)
        for mo, v in sorted(rows, key=lambda r: -T(r[1])):
            A(f"| {P} | {mo} | {v['msgs']} | {M(T(v))} | {M(N(v))} | {PC(100 * T(v) / tt)} | {PC(100 * N(v) / tn)} | {M(v['out'])} |")
        A(f"| {P} | **soma** | {sum(v['msgs'] for _, v in rows)} | {M(tt)} | {M(tn)} | 100% | 100% | {M(sum(v['out'] for _, v in rows))} |")
    A('')
    A('Principal vs subagente (total M, sem cache read M):')
    A('')
    A('| Período | Modelo | Principal | Subagente |')
    A('|---|---|--:|--:|')
    for P in ('S1', 'S2'):
        for mo in ('opus', 'sonnet', 'haiku'):
            g = lambda t: c['agg'].get(f'{P}|{mo}|{t}', dict(msgs=0, **{'in': 0, 'out': 0, 'cc': 0, 'cr': 0}))  # noqa: E731
            f = lambda v: f"{M(v['in'] + v['out'] + v['cc'] + v['cr'])} / {M(v['in'] + v['out'] + v['cc'])} ({v['msgs']} msgs)"  # noqa: E731
            A(f"| {P} | {mo} | {f(g('main'))} | {f(g('sub'))} |")
    A('')
    ss = c['sessions']
    A('Sessões Claude Code com mensagens (pasta = projeto; restritos agrupados em "restrito"): '
      + '; '.join(f"{P}: {sum(v.values())} sessões em {len(v)} projetos" for P, v in ss.items() if P != 'outro')
      + '. Mais sessões em S2: '
      + ', '.join(f"{k} ({n})" for k, n in sorted(ss.get('S2', {}).items(), key=lambda z: -z[1])[:3])
      + f". Modelo `fable`: {c['agg'].get('S1|fable|all', {}).get('msgs', 0) + c['agg'].get('S2|fable|all', {}).get('msgs', 0)} mensagens.")
    A('')
    A('## 2. Codex (delta de `total_token_usage` por evento; input inclui cache)')
    A('')
    A('| Período | Modelo (turn_context) | Sessões | Total M | Cache lido M | Output M | % do total |')
    A('|---|---|--:|--:|--:|--:|--:|')
    for P in ('S1', 'S2'):
        tot = x['agg'].get(f'{P}|TOTAL', {}).get('total_tokens', 0)
        for k, v in sorted(x['agg'].items(), key=lambda z: -z[1]['total_tokens']):
            if k.startswith(P + '|') and not k.endswith('TOTAL'):
                A(f"| {P} | {k.split('|')[1]} | {v['sessions']} | {M(v['total_tokens'])} | {M(v['cached_input_tokens'])} | {M(v['output_tokens'])} | {PC(100 * v['total_tokens'] / tot)} |")
        tt = x['agg'].get(P + '|TOTAL', {})
        A(f"| {P} | **soma** | | {M(tot)} | {M(tt.get('cached_input_tokens', 0))} | {M(tt.get('output_tokens', 0))} | 100% |")
    A('')
    A('`codex-auto-review` é o modelo do revisor automático (modo auto-review do Codex).')
    A('')
    A(f"## 3. Agentes Paseo ({p['n']} fontes: {p['n_archived']} arquivados + {p['n_current']} atuais)")
    A('')
    A('Período = data de criação. Desfecho final = status do inspect/vigia (closed e idle = concluído; não prova entrega). '
      '"Evento vigia" = agente teve ao menos 1 evento daquele tipo. "Log cita commit" = log contém hash perto da palavra commit '
      '(heurística; só arquivados têm log).')
    A('')
    A('| Per. | Provider/modelo | N | Concl. | Erro | Aguard. aprov. | c/ limite de uso | ev. erro | ev. parado | Log cita commit |')
    A('|---|---|--:|--:|--:|--:|--:|--:|--:|--:|')
    for k, v in p['agg'].items():
        P, mo = k.split('|')
        if P == 'sem_data':
            P = 's/ data'
        A(f"| {P} | {mo.replace('opencode/opencode/', 'opencode/')} | {v['n']} | {v.get('concluido(closed/idle)', 0)} | {v.get('erro', 0)} | {v.get('aguardando_aprovacao', 0)} | {v.get('com_erro_limite', 0)} | {v.get('ev_erro', 0)} | {v.get('ev_parado', 0)} | {v.get('log_cita_commit', 0)} |")
    A('')
    A('Agentes "s/ data" têm só log (sem inspect): provider/modelo/data desconhecidos. Entrega real (commit/arquivos) por agente: desconhecida; só a heurística acima.')
    A('')
    vg = m['vigia']
    A(f"## 4. Vigia (`watchdog.log`, {vg['first']} a {vg['last']})")
    A('')
    w = vg['eventos']
    A('Eventos brutos (o vigia repete o mesmo alerta a cada ~10 min; entre parênteses, agentes distintos):')
    A('')
    A('| Tipo | S1 | S2 |')
    A('|---|--:|--:|')
    ad = vg['agentes_distintos']
    for t in ('erro', 'erro_limite_uso', 'parado', 'pendente', 'paseo_error', 'quota_error'):
        f = lambda P: f"{w.get(P, {}).get(t, 0)}" + (f" ({ad[P + '|' + t]})" if (P + '|' + t) in ad and t in ('erro', 'parado', 'pendente') else '')  # noqa: E731
        A(f"| {t}{' (subconjunto de erro)' if t == 'erro_limite_uso' else ''} | {f('S1')} | {f('S2')} |")
    A('')
    pm_ = vg['por_provider_modelo']
    for t in ('erro', 'parado'):
        A(f'Eventos `{t}` por modelo: S1 ' + ', '.join(f"{k.split('|')[2].replace('opencode/opencode/', '')} {v}" for k, v in pm_.items() if k.startswith(f'S1|{t}'))
          + '. S2 ' + ', '.join(f"{k.split('|')[2].replace('opencode/opencode/', '')} {v}" for k, v in pm_.items() if k.startswith(f'S2|{t}')) + '.')
    A('`paseo_error` = daemon indisponível na consulta do vigia.')
    A('')
    cm = m['commits']
    A(f"## 5. Commits ({cm['repos_com_git']} repos com .git até prof. 3 no workspace, `git log --all`, SHA deduplicado)")
    A('')
    cp = cm['por_periodo']
    fam = lambda k: misc.family(k[3:]) if k[3:] != 'outro' else 'outro'  # noqa: E731
    fm = {P: collections.Counter() for P in cp}
    for P in cp:
        for k, v in cp[P].items():
            if k.startswith('co:'):
                fm[P][fam(k)] += v
    g = lambda P, k: cp.get(P, {}).get(k, 0)  # noqa: E731
    A('| Coautor (trailer Co-Authored-By) | S1 | S2 |')
    A('|---|--:|--:|')
    A(f"| commits totais | {g('S1', 'total')} | {g('S2', 'total')} |")
    for n in ('Claude Opus', 'Claude Sonnet', 'Claude Haiku', 'Claude (genérico)', 'Codex/GPT', 'Gemini', 'outro'):
        A(f"| {n} | {fm.get('S1', {}).get(n, 0)} | {fm.get('S2', {}).get(n, 0)} |")
    A(f"| sem trailer | {g('S1', 'sem_coautor')} | {g('S2', 'sem_coautor')} |")
    top = sorted(cm['commits_por_repo'].items(), key=lambda z: -z[1])[:4]
    A('Repos com mais commits: ' + ', '.join(f'{k.split("/")[-1]} ({v})' for k, v in top)
      + '. Um commit com mais de um trailer conta em cada linha.')
    A('')
    A('## 6. Comparação com a linha de base (GESTAO-CONTEXTO.md, medida em 26/10)')
    A('')
    A('Mesmo método sobre os mesmos dados (valores do documento de 26/10 entre parênteses):')
    A('')
    A('| Métrica | Antes (baseline) | Depois 22-25/10 | S1 | S2 | S2 só dias completos |')
    A('|---|--:|--:|--:|--:|--:|')
    rows = [('Claude, M tokens/dia (com cache)', lambda r: f"{r['claude']['M_dia_total']:.1f}".replace('.', ','), '(70,6 / 58,7)'),
            ('Claude, M tokens/dia sem cache read', lambda r: f"{r['claude']['M_dia_sem_cr']:.2f}".replace('.', ','), '—'),
            ('Codex, M tokens/dia', lambda r: f"{r['codex_M_dia']:.1f}".replace('.', ','), '(0 / 40,1)'),
            ('Parte do Claude em subagentes', lambda r: PC(r['claude']['sub_pct']), '(58% / 4%)'),
            ('Cache read no total do Claude', lambda r: PC(r['claude']['cache_read_pct']), '(— / 96%)'),
            ('Contexto por turno, conversa principal (mil)', lambda r: f"{r['claude']['ctx_turno_main'] / 1e3:.0f}", '(307 / 331)')]
    for n, f, ref in rows:
        A(f"| {n} {ref} | {f(b['antes_08_21'])} | {f(b['depois_22_25'])} | {f(b['S1'])} | {f(b['S2'])} | {f(b['S2_dias_completos'])} |")
    A('')
    A('Contexto por turno = (input + cache creation + cache read) / msgs da conversa principal.')
    A('')
    A('## 7. Telemetria manual e snapshots de franquia')
    A('')
    t = m['telemetria']
    if t.get('n'):
        A(f"- `telemetria.jsonl`: {t['n']} registros ({', '.join(f'{v} em {d[8:]}/{d[5:7]}' for d, v in t['por_dia'].items())}). Desfechos: {t['por_outcome']}.")
    A('- Snapshots de franquia (valor atual no momento da execução, não filtrado pelo corte): '
      + '; '.join(f"{k}: " + ', '.join(f"{w.get('pool', '') + ' ' if w.get('pool') else ''}{w['kind']} {w['used_percent']:.0f}%" for w in v['windows']) for k, v in m['quota'].items()) + '.')
    A('')
    A('## 8. Checagens de sanidade')
    A('')
    cs = s['claude_dedup_vs_raw']
    A(f"- Claude: {K(cs[1])} linhas `assistant` brutas, {K(cs[0])} mensagens únicas, {K(cs[2])} linhas repetidas ({K(cs[0])} + {K(cs[2])} = {K(cs[0] + cs[2])}: {'confere' if cs[3] else 'NÃO confere'}). {c['dupes_with_diff_usage']} duplicatas tinham usage diferente entre linhas; mantida a linha com maior output.")
    A('- Soma por modelo = total (msgs): ' + ', '.join(f"{k} {v[0]}={v[1]}" for k, v in s['claude_soma_modelos_eq_total'].items()) + '.')
    A(f"- Codex: soma dos últimos totais por sessão = soma dos deltas = {K(s['codex_soma_ultimos_totais_vs_deltas'][0])} ({x['resets']} resets de contador).")
    A(f"- Paseo: {s['paseo_agentes'][0]} agentes no agregado = {s['paseo_agentes'][1]} arquivados + {s['paseo_agentes'][2]} atuais.")
    A('- Amostra de registros conferidos nas linhas brutas dos .jsonl:')
    for k, v in [(k, v) for k, v in s.items() if k.startswith('msg_')]:
        A(f"  - `{k}`: {len(v)} linha(s) bruta(s), output={v[0][2]}, in={v[0][3]}, cc={v[0][4]}, cr={v[0][5]}, modelo {v[0][6]}.")
    A('')
    A('## 9. Metodologia e limitações')
    A('')
    for l in ['Dia = data local do timestamp. Claude: dedup global por `message.id` entre todos os arquivos, incluindo `subagents/`; principal vs subagente por `isSidechain` ou caminho `/subagents/`.',
              'Tokens não são custo nem % de franquia. Os pesos de cada modelo na cota (Opus vs Sonnet; Codex vs Claude) não são comparáveis por contagem de tokens.',
              'Sem histórico de % da franquia: os snapshots em `quota/` são só o valor atual. Telemetria manual esparsa.',
              'S1 e S2 têm tamanhos diferentes e S2 termina parcial: compare por dia. O vigia só existe desde 26/10; agentes apagados antes da coleta não aparecem (viés de sobrevivência).',
              'Paseo: agentes apagados não estão na fonte. Status `closed` não distingue entrega de abandono. "Entregou" não é medido, só a heurística de hash de commit no log. O estado dos agentes vivos é o do momento da execução (não filtrado pelo corte, só a data de criação).',
              'Codex: modelo da sessão vem do último `turn_context`; sessão que troca de modelo fica toda no modelo vigente no evento. Forks/resumos que copiam histórico podem duplicar tokens (não verificado).',
              'Commits: author date; `--all` inclui branches e worktrees; commits sem trailer não têm autoria de modelo. Trailer indica coautoria declarada, não volume de trabalho.',
              'Claude Code só registra Opus/Sonnet/Haiku; execuções do Claude via Antigravity ou Paseo fora do Claude Code não entram na seção 1.']:
        A('- ' + l)
    return '\n'.join(L) + '\n'


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', help='diretório de saída (padrão: ~/.local/state/ai-os/metricas/<AAAAMMDD do until>/)')
    ap.add_argument('--until', help='instante de corte ISO 8601 (ex.: 2026-11-09T16:03:00Z); padrão: agora')
    ap.add_argument('--tz', help='fuso para definir o dia (ex.: -03:00); padrão: fuso local')
    for n in ('baseline', 'S1', 'S2'):
        a, b = DEFAULT_PERIODS[n]
        ap.add_argument(f'--{n.lower()}', metavar='INI..FIM', help=f'período {n} (padrão {a}..{b or "dia do --until"})')
    ap.add_argument('--home', help='home do usuário (padrão: Path.home())')
    ap.add_argument('--workspace', help='raiz dos repositórios (padrão: <home>/Workspace)')
    ap.add_argument('--state-dir', help='estado do AI OS (padrão: <home>/.local/state/ai-os)')
    ap.add_argument('--claude-dir', help='padrão: <home>/.claude/projects')
    ap.add_argument('--codex-dir', help='padrão: <home>/.codex/sessions')
    ap.add_argument('--codex-since', default='2026-10-01', help='só lê pastas de sessão Codex com data >= isto')
    ap.add_argument('--archive-dir', help='inspect/logs arquivados do Paseo (padrão: nenhum)')
    ap.add_argument('--no-paseo-live', action='store_true', help='não chama `paseo ls/inspect`')
    ap.add_argument('--watchdog-log', help='padrão: <state-dir>/watchdog.log')
    ap.add_argument('--agents-json', help='padrão: <state-dir>/agentes.json')
    ap.add_argument('--quota-dir', help='padrão: <state-dir>/quota')
    ap.add_argument('--telemetry', help='padrão: docs/ai-os/telemetria.jsonl do repo')
    ap.add_argument('--restricted-config', help='toml com [restricted].paths (padrão: config/ai-os-memory.toml do repo)')
    ap.add_argument('--commits-since', help='padrão: início de S1')
    a = ap.parse_args(argv)

    tz = parse_tz(a.tz)
    until = parse_until(a.until, tz)
    home = Path(a.home).expanduser() if a.home else Path.home()
    state = Path(a.state_dir).expanduser() if a.state_dir else home / '.local/state/ai-os'
    periods = {n: parse_range(getattr(a, n.lower()), DEFAULT_PERIODS[n]) for n in DEFAULT_PERIODS}
    restricted = load_restricted(a.restricted_config or REPO / 'config/ai-os-memory.toml', home)
    ctx = Ctx(tz=tz, until=until, periods=periods, home=home, restricted=restricted,
              workspace=Path(a.workspace).expanduser() if a.workspace else None)
    out = Path(a.out).expanduser() if a.out else state / 'metricas' / until.astimezone(tz).strftime('%Y%m%d')
    out.mkdir(parents=True, exist_ok=True)
    claude_dir = Path(a.claude_dir).expanduser() if a.claude_dir else home / '.claude/projects'
    codex_dir = Path(a.codex_dir).expanduser() if a.codex_dir else home / '.codex/sessions'
    wd = Path(a.watchdog_log).expanduser() if a.watchdog_log else state / 'watchdog.log'
    aj = Path(a.agents_json).expanduser() if a.agents_json else state / 'agentes.json'
    qd = Path(a.quota_dir).expanduser() if a.quota_dir else state / 'quota'
    tel = Path(a.telemetry).expanduser() if a.telemetry else REPO / 'docs/ai-os/telemetria.jsonl'
    t0 = time.perf_counter()

    with ctx.stage('claude'):
        c = claude.collect(ctx, claude_dir)
    with ctx.stage('codex'):
        x = codex.collect(ctx, codex_dir, a.codex_since)
    with ctx.stage('paseo'):
        p = paseo.collect(ctx, Path(a.archive_dir).expanduser() if a.archive_dir else None, wd, aj,
                          live=not a.no_paseo_live)
    with ctx.stage('misc'):
        m = misc.collect(ctx, wd, p['agents'], a.commits_since or ctx.periods['S1'][0], tel, qd)
    with ctx.stage('sanity'):
        s = sanity.collect(ctx, claude_dir, c, x, p)
    b = baseline_cmp(ctx, c, x)

    for name, obj in (('claude', c), ('codex', x), ('paseo', p), ('misc', m), ('sanity', s), ('baseline_cmp', b)):
        (out / f'{name}.json').write_text(json.dumps(obj, indent=1, ensure_ascii=False))
    until_iso = until.astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    execucao = dict(gerado_em=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                    segundos_total=round(time.perf_counter() - t0, 2), leitura=ctx.reads, etapas=ctx.stages)
    (out / 'metricas.json').write_text(json.dumps(dict(
        corte=until_iso, periodos={k: f'{v[0]}..{v[1]}' for k, v in ctx.periods.items()}, claude=c, codex=x, paseo=p,
        vigia=m['vigia'], commits=m['commits'], telemetria=m['telemetria'], quota=m['quota'],
        comparacao_linha_de_base=b, sanidade=s, execucao=execucao), indent=1, ensure_ascii=False))
    (out / 'METRICAS.md').write_text(render_md(ctx, c, x, p, m, b, s, until_iso))
    print(f'ok: {out} em {execucao["segundos_total"]}s; lidos {ctx.reads["files"]} arquivos, {ctx.reads["bytes"]} bytes, '
          f'{ctx.reads["subprocessos"]} subprocessos')
    return 0


if __name__ == '__main__':
    sys.exit(main())
