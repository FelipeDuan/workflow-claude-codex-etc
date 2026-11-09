#!/usr/bin/env python3
"""Relatório GQM v1; só agrega metadados e usa a biblioteca padrão.

Datas em --since/--until incluem o dia local; instantes ISO delimitam [since, until).
Sem argumentos, cobre os últimos sete dias. Histórico é lido somente nos meses
locais dessa janela; bordas sem observação ficam desconhecidas.
"""
import argparse
import collections
import datetime as dt
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys

if sys.version_info < (3, 11):
    raise SystemExit('requer Python >= 3.11; rode com /opt/homebrew/bin/python3')

from metrics_common import Ctx, load_restricted, parse_ts, parse_tz
from paseo import parse as parse_inspect

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paseo_watchdog import PolicyError, is_restricted

REPO = Path(__file__).resolve().parents[2]
UTC = dt.timezone.utc
TASK = re.compile(r'^\[(T-\d{8}-\d{2,})\](?:\s|$)')
LIMIT = re.compile(r'usage.?limit|limite de uso|rate.?limit|quota.?exceed|usage_limit', re.I)
TERMINAL = {'error', 'erro', 'closed', 'completed', 'concluido'}
WAITING = {'waiting_permission', 'aguardando_aprovacao'}
SYNTHETIC_PREFIXES = ('<local-command', '<command-name>', '<command-message>',
                      '<system-reminder>', '<task-notification>')
PROXY_NOTE = ('Proxy estimado: soma intervalos de até 10 min entre mensagens humanas na mesma sessão. '
              'Não mede esforço humano: o intervalo pode ser revisão, estudo ou café. '
              'Não sustenta sozinho uma afirmação de produtividade.')


def stamp(value):
    try:
        return parse_ts(value) if isinstance(value, str) else None
    except (ValueError, OverflowError):
        return None


def iso(value):
    return value.astimezone(UTC).isoformat().replace('+00:00', 'Z')


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def months(since, until):
    # O vigia nomeia os arquivos no fuso local do sistema, independente de --tz.
    day = since.astimezone().date().replace(day=1)
    last = (until - dt.timedelta(microseconds=1)).astimezone().date().replace(day=1)
    while day <= last:
        yield day.strftime('%Y-%m')
        day = (day.replace(day=28) + dt.timedelta(days=4)).replace(day=1)


def read_history(state, since, until, tz):
    rows, invalid, files = [], 0, 0
    for month in months(since, until):
        for group in ('tasks', 'quota', 'agents', 'collector'):
            path = Path(state) / 'history' / f'{group}-{month}.jsonl'
            if not path.is_file():
                continue
            files += 1
            with path.open(encoding='utf-8', errors='replace') as handle:
                for line in handle:
                    try:
                        row = json.loads(line)
                        if not isinstance(row, dict) or not isinstance(row.get('type'), str):
                            raise ValueError('registro inválido')
                        for key in ('to', 'from', 'provider', 'pool', 'window_kind', 'task_id', 'agent_id',
                                    'role', 'verdict', 'reason', 'reason_code', 'error_reason'):
                            if row.get(key) is not None and not isinstance(row[key], str):
                                raise ValueError('campo textual inválido')
                        if row.get('used_percent') is not None and not number(row['used_percent']):
                            raise ValueError('percentual inválido')
                        observed = stamp(row.get('observed_at'))
                        if observed is None:
                            raise ValueError('timestamp inválido')
                        if since <= observed < until:
                            rows.append((observed, row))
                    except (ValueError, TypeError):
                        invalid += 1
    return sorted(rows, key=lambda item: item[0]), {'files': files, 'invalid_lines': invalid}


def run(cmd):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, errors='replace', timeout=30)
        return result.stdout if result.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def field(row, *keys):
    return next((row[k] for k in keys if row.get(k) is not None), None)


def inventory(archive, since, until, live=True, runner=run):
    """Títulos ficam só em memória até extrair o ID; nunca entram no resultado."""
    agents = {}
    pre_window = set()
    sources, unknown_date = 0, 0

    def add(row):
        nonlocal unknown_date
        if not isinstance(row, dict):
            return
        nested = row.get('agent')
        if isinstance(nested, dict):
            row = nested
        aid = field(row, 'id', 'Id', 'agentId')
        if not isinstance(aid, str) or not aid:
            return
        created = stamp(field(row, 'createdAt', 'CreatedAt', 'created_at'))
        if created is None:
            unknown_date += 1
            return
        if created < since:
            pre_window.add(aid)
            agents.pop(aid, None)
            return
        if created >= until or aid in pre_window:
            return
        title = field(row, 'title', 'Title', 'name', 'Name')
        match = TASK.match(title) if isinstance(title, str) else None
        previous = agents.get(aid, {})
        provider = field(row, 'provider', 'Provider')
        agents[aid] = {'task_id': match.group(1) if match else previous.get('task_id'),
                       'provider': provider if isinstance(provider, str) else previous.get('provider'),
                       'created_at': created, 'start_status': 'measured'}

    if archive and Path(archive).is_dir():
        for path in sorted(Path(archive).glob('**/*inspect*')):
            if not path.is_file() or path.suffix not in ('.json', '.txt'):
                continue
            try:
                text = path.read_text(encoding='utf-8', errors='replace')
                add(json.loads(text) if path.suffix == '.json' else parse_inspect(text))
                sources += 1
            except (OSError, ValueError):
                continue
    if live:
        text = runner(['paseo', 'ls', '--json', '-a'])
        try:
            listed = json.loads(text) if text else None
            if isinstance(listed, list):
                sources += 1
                for row in listed:
                    add(row)
        except ValueError:
            pass
    return agents, {'inventory_sources': sources, 'inventory_without_created_at': unknown_date}, pre_window


def interaction(ctx, root, since, until):
    """Só usa timestamps de user com texto humano; tool_result é descartado."""
    daily = collections.defaultdict(float)
    day_counts = collections.Counter()
    n, files, invalid = 0, 0, 0
    pairs = 0
    global_seen = set()
    restricted_cwds = {}
    for path in sorted(Path(root).glob('*/*.jsonl')):
        times, seen = [], set()
        restricted = False
        files += 1
        with path.open(encoding='utf-8', errors='replace') as handle:
            for line in handle:
                try:
                    row = json.loads(line)
                    if not isinstance(row, dict):
                        raise ValueError('registro inválido')
                except ValueError:
                    invalid += 1
                    continue
                cwd = row.get('cwd')
                if isinstance(cwd, str):
                    if cwd not in restricted_cwds:
                        try:
                            restricted_cwds[cwd] = is_restricted(cwd, [Path(p).resolve() for p in ctx.restricted])
                        except (PolicyError, OSError):
                            restricted_cwds[cwd] = True
                    restricted = restricted or restricted_cwds[cwd]
                if row.get('type') != 'user' or row.get('isMeta') or row.get('isSidechain') or row.get('isCompactSummary'):
                    continue
                message = row.get('message')
                content = message.get('content') if isinstance(message, dict) else None
                texts = [content] if isinstance(content, str) else (
                    [b['text'] for b in content if isinstance(b, dict) and b.get('type') == 'text'
                     and isinstance(b.get('text'), str)] if isinstance(content, list) else [])
                combined = '\n'.join(texts).strip()
                human = bool(combined) and not combined.startswith(SYNTHETIC_PREFIXES)
                when = stamp(row.get('timestamp'))
                if not human or when is None or not since <= when < until:
                    continue
                key = row.get('uuid') or iso(when)
                if key not in seen and (not row.get('uuid') or row['uuid'] not in global_seen):
                    times.append(when)
                    seen.add(key)
                    if row.get('uuid'):
                        global_seen.add(row['uuid'])
        label = 'restrito' if restricted else ctx.project_label(path.parent.name)
        times.sort()
        n += len(times)
        for when in times:
            key = (when.astimezone(ctx.tz).date().isoformat(), label)
            daily[key] += 0
            day_counts[key] += 1
        for start, end in zip(times, times[1:]):
            pairs += 1
            if end - start > dt.timedelta(minutes=10):
                continue
            # Distribui intervalos que cruzam meia-noite entre os dias locais.
            while start < end:
                day = start.astimezone(ctx.tz).date()
                boundary = dt.datetime.combine(day + dt.timedelta(days=1), dt.time(), ctx.tz)
                stop = min(end, boundary)
                daily[(day.isoformat(), label)] += (stop - start).total_seconds() / 60
                start = stop
    return {'n': n, 'files': files, 'invalid_lines': invalid,
            'minutes': round(sum(daily.values()), 3) if n >= 2 and pairs else None,
            'reason': ('menos de duas mensagens humanas na janela' if n < 2 else
                       'nenhum par de mensagens humanas na mesma sessão' if not pairs else None),
            'by_day_project': [{'date': d, 'project': p, 'minutes': round(v, 3) if day_counts[(d, p)] >= 2 else None,
                                'n': day_counts[(d, p)], 'status': 'estimated' if day_counts[(d, p)] >= 2 else 'unknown',
                                'reason': None if day_counts[(d, p)] >= 2 else 'menos de duas mensagens humanas no dia e projeto'}
                               for (d, p), v in sorted(daily.items())]}


def collect(ctx, state, since, until, archive=None, claude_root=None, live=True, runner=run):
    window = {'since': iso(since), 'until': iso(until), 'timezone': str(ctx.tz), 'end_exclusive': True}
    insufficient = []

    def metric(name, value, n, status='measured', reason=None, **extra):
        if value is None:
            status = 'unknown'
            reason = reason or 'sem observações suficientes na janela'
        result = {'value': value, 'n': n, 'window': window, 'status': status, **extra}
        if reason:
            result['reason'] = reason
        if status == 'unknown':
            insufficient.append({'metric': name, 'reason': reason})
        return result

    def ratio(name, num, den, **extra):
        return metric(name, num / den if den else None, den, numerator=num, **extra)

    rows, reads = read_history(state, since, until, ctx.tz)
    agents, sources, pre_window = inventory(archive, since, until, live, runner)
    reads.update(sources)
    opened, events, links, transitions = {}, collections.defaultdict(list), {}, collections.defaultdict(list)
    quota = collections.defaultdict(list)
    daily, gaps = {}, []
    for when, row in rows:
        kind, tid, aid = row['type'], row.get('task_id'), row.get('agent_id')
        if kind.startswith('task.') and isinstance(tid, str):
            events[tid].append(row)
            if kind == 'task.opened':
                opened[tid] = row
            elif kind == 'task.linked' and isinstance(aid, str):
                links[aid] = (tid, row.get('role', 'exec'))
        elif kind == 'agent.transition' and isinstance(aid, str):
            transitions[aid].append((when, row))
            if aid not in pre_window and (row.get('reason_code') == 'first_seen' or row.get('from') is None):
                agents.setdefault(aid, {'task_id': None, 'provider': row.get('provider'),
                                       'created_at': when, 'start_status': 'estimated'})
        elif kind == 'quota.sample':
            key = tuple(row.get(k) if isinstance(row.get(k), str) else None
                        for k in ('provider', 'pool', 'window_kind'))
            quota[key].append((when, row))
        elif kind == 'collector.daily':
            try:
                date = dt.date.fromisoformat(row['date'])
                start = dt.datetime.combine(date, dt.time(), ctx.tz)
                end = dt.datetime.combine(date + dt.timedelta(days=1), dt.time(), ctx.tz)
                if since <= start and end <= until:
                    daily[row['date']] = row
            except (ValueError, KeyError, TypeError):
                pass
        elif kind == 'collector.gap':
            start, end = stamp(row.get('start_at')), stamp(row.get('end_at'))
            if start and end and max(start, since) < min(end, until):
                gaps.append((max(start, since), min(end, until)))

    for aid, (tid, role) in links.items():
        # Um vínculo registra presença na janela, mas não prova início nela.
        agents.setdefault(aid, {'task_id': tid, 'provider': None, 'created_at': None, 'start_status': 'unknown'})
        agents[aid]['task_id'] = tid
    task_agents = collections.defaultdict(set)
    exec_agents = collections.defaultdict(set)
    for aid, agent in agents.items():
        tid = agent['task_id']
        if tid in opened:
            task_agents[tid].add(aid)
            if aid in links and links[aid][1] == 'exec':
                exec_agents[tid].add(aid)
    # Links explícitos também vinculam agentes antigos/sem data sem inferir início.
    for aid, (tid, role) in links.items():
        if tid not in opened:
            continue
        task_agents[tid].add(aid)
        if role == 'exec':
            exec_agents[tid].add(aid)
    latest, first_verdict, reworked, reevaluating = {}, {}, set(), set()
    for tid in opened:
        for row in events[tid]:
            if row['type'] == 'task.reopened':
                latest.pop(tid, None)
                reevaluating.add(tid)
            elif row['type'] == 'task.closed' and row.get('verdict') in ('aceito', 'retrabalho', 'rejeitado'):
                latest[tid] = row['verdict']
                reevaluating.discard(tid)
                first_verdict.setdefault(tid, row['verdict'])
                if row['verdict'] == 'retrabalho':
                    reworked.add(tid)
    first = sum(v == 'aceito' and first_verdict[t] == 'aceito' and t not in reworked
                and len(exec_agents[t]) <= 1 for t, v in latest.items())
    missing_roles = any(aid not in links for tid in task_agents for aid in task_agents[tid])
    q1 = {'first_delivery_acceptance': ratio('Q1.first_delivery_acceptance', first, len(latest),
                status='estimated' if missing_roles else 'measured',
                reason='agentes com prefixo sem papel conhecido podem ocultar relançamentos' if missing_roles else None),
          'rework_rate': ratio('Q1.rework_rate', sum(t in reworked for t in latest), len(latest)),
          'evaluation_coverage': ratio('Q1.evaluation_coverage', len(latest), len(opened))}
    q2 = {'quota_windows': [], 'saturations_per_100': []}
    for (provider, pool, kind), samples in sorted(quota.items(), key=lambda x: str(x[0])):
        valid = [(t, r['used_percent']) for t, r in samples
                 if r.get('confidence') != 'unknown' and number(r.get('used_percent')) and 0 <= r['used_percent'] <= 100]
        unknown_seconds = (until - since).total_seconds()
        for index, (when, row) in enumerate(samples):
            used = row.get('used_percent')
            if row.get('confidence') == 'unknown' or not number(used) or not 0 <= used <= 100:
                continue
            # Nunca estende leitura por uma lacuna inteira; validade segue os sensores.
            fetched = stamp(row.get('occurred_at')) or when
            expires = fetched + dt.timedelta(minutes=15 if provider == 'claude' else 10)
            end = min(until, samples[index + 1][0] if index + 1 < len(samples) else until, expires)
            unknown_seconds -= max(0, (end - when).total_seconds())
        prefix = f'Q2.quota.{provider}.{pool}.{kind}'
        last_time, last_row = samples[-1]
        last_value = last_row.get('used_percent')
        last_value = last_value if last_row.get('confidence') != 'unknown' and number(last_value) and 0 <= last_value <= 100 else None
        q2['quota_windows'].append({'provider': provider, 'pool': pool, 'window_kind': kind,
            'last_reading': metric(prefix + '.last', last_value, len(samples), observed_at=iso(last_time)),
            'maximum': metric(prefix + '.maximum', max((v for _, v in valid), default=None), len(samples)),
            'sample_count': metric(prefix + '.samples', len(samples), len(samples)),
            'unknown_minutes': metric(prefix + '.unknown_minutes', round(max(0, unknown_seconds) / 60, 3),
                                      len(samples), 'estimated', reason='bordas e leituras expiradas são desconhecidas; sem interpolação')})
    if not quota:
        q2['quota_data'] = metric('Q2.quota_data', None, 0, reason='nenhuma amostra de quota na janela')
    providers = {a.get('provider') for a in agents.values()} | {r.get('provider') for ts in transitions.values() for _, r in ts}
    providers.discard(None)
    for provider in sorted(providers, key=str):
        started = {a for a, r in agents.items() if r.get('provider') == provider and r.get('created_at') is not None}
        estimated_start = any(agents[a]['start_status'] == 'estimated' for a in started)
        limited, missing_reason = set(), set()
        for aid, changes in transitions.items():
            if aid not in started:
                continue
            for _, row in changes:
                if row.get('provider') != provider or row.get('to') not in ('error', 'erro'):
                    continue
                reason = ' '.join(str(row.get(k) or '') for k in ('reason_code', 'reason', 'error_reason'))
                if LIMIT.search(reason):
                    limited.add(aid)
                elif not row.get('error_reason') and row.get('reason_code') not in ('network_error', 'process_failed', 'permission_denied', 'crash'):
                    missing_reason.add(aid)
        name = f'Q2.saturations.{provider}'
        value = len(limited & started) * 100 / len(started) if started and not missing_reason else None
        q2['saturations_per_100'].append({'provider': provider,
            **metric(name, value, len(started), numerator=len(limited & started),
                     status='estimated' if estimated_start else 'measured',
                     reason=('motivo de erro não disponível ou nenhum início observado' if value is None else
                             'primeiro avistamento pode incluir agentes iniciados antes da janela' if estimated_start else None))})
    if not providers:
        q2['saturations_per_100'].append(metric('Q2.saturations', None, 0, reason='nenhum início de agente observado'))
    q2['unavailable_minutes'] = metric('Q2.unavailable_minutes', None, len(rows),
        reason='amostras esparsas e transições não identificam continuamente pool e agentes esperando')

    tasks = set(opened)
    relaunches = sum(max(0, len(exec_agents[t]) - 1) for t in tasks)
    linked = sum(a['task_id'] in opened for a in agents.values())
    proxy = interaction(ctx, claude_root or ctx.home / '.claude/projects', since, until)
    reads['transcript_files'] = proxy['files']
    reads['transcript_invalid_lines'] = proxy['invalid_lines']
    by_task = []
    for tid in sorted(tasks):
        incomplete = any(aid not in links for aid in task_agents[tid])
        unknown = incomplete and not exec_agents[tid]
        by_task.append({'task_id': tid, 'agents': len(task_agents[tid]), 'n': len(task_agents[tid]),
                        'window': window, 'evaluation_status': 'em_reavaliacao' if tid in reevaluating else latest.get(tid, 'aberta'),
                        'relaunches': None if unknown else max(0, len(exec_agents[tid]) - 1),
                        'relaunch_status': 'unknown' if unknown else 'estimated' if incomplete else 'measured',
                        'reason': 'papéis ausentes; somente exec explícito permite contar relançamentos' if incomplete else None})
    q3 = {'agents_per_task': ratio('Q3.agents_per_task', sum(len(task_agents[t]) for t in tasks), len(tasks)),
          'relaunches': metric('Q3.relaunches', relaunches if tasks and (not missing_roles or any(exec_agents.values())) else None,
                              len(tasks), 'estimated' if missing_roles else 'measured',
                              reason='papéis ausentes; conta somente agentes extras com role exec explícito' if missing_roles else None),
          'link_coverage': ratio('Q3.link_coverage', linked, len(agents), status='estimated',
                                 reason='cobertura entre agentes encontrados no inventário, primeiro avistamento e vínculos explícitos'),
          'by_task': by_task,
          'interaction_time_proxy': metric('Q3.interaction_time_proxy', proxy['minutes'], proxy['n'], 'estimated',
                reason=PROXY_NOTE + (' ' + proxy['reason'] if proxy['reason'] else ''),
                confidence='estimated', unit='minutes', by_day_project=proxy['by_day_project'])}
    finals = {a: ts[-1][1]['to'] for a, ts in transitions.items() if ts[-1][1].get('to') in TERMINAL}
    waits, completed_waits, unknown_waits = 0, 0, 0
    for changes in transitions.values():
        start = None
        for when, row in changes:
            if row.get('to') in WAITING:
                start = start or when
            elif start:
                completed_waits += 1
                if any(start < b and a < when for a, b in gaps):
                    unknown_waits += 1
                else:
                    waits += when - start > dt.timedelta(minutes=10)
                start = None
        if start and until - start > dt.timedelta(minutes=10):
            if any(start < b and a < until for a, b in gaps):
                unknown_waits += 1
            else:
                waits += 1
            completed_waits += 1
    merged = []
    for start, end in sorted(gaps):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    collector_seen = bool(daily or gaps)
    q4 = {'technical_failure_rate': ratio('Q4.technical_failure_rate', sum(v in ('error', 'erro') for v in finals.values()), len(finals)),
          'permission_waits_over_10_minutes': metric('Q4.permission_waits_over_10_minutes', waits if transitions and not unknown_waits else None,
                                                   completed_waits, 'estimated', unknown_waits=unknown_waits,
                                                   reason='espera cruza collector.gap; continuidade desconhecida' if unknown_waits else
                                                   'duração entre observações; espera anterior à borda não é inferida'),
          'collector_gaps': metric('Q4.collector_gaps', len(merged) if collector_seen else None, len(gaps),
                                  reason='somente lacunas registradas; ausência de diário/lacunas não prova coleta contínua'),
          'collector_gap_minutes': metric('Q4.collector_gap_minutes', round(sum((b - a).total_seconds() for a, b in merged) / 60, 3) if collector_seen else None,
                                          len(gaps))}
    q5 = {'by_day': []}
    for day, row in sorted(daily.items()):
        cycles, total, maximum, size = (row.get(k) for k in ('cycles', 'total_ms', 'max_ms', 'bytes_appended'))
        count = cycles if number(cycles) and cycles > 0 else 0
        q5['by_day'].append({'date': day,
            'cycles': metric(f'Q5.{day}.cycles', cycles if number(cycles) else None, count),
            'mean_ms': metric(f'Q5.{day}.mean_ms', total / count if count and number(total) else None, count),
            'max_ms': metric(f'Q5.{day}.max_ms', maximum if number(maximum) else None, count),
            'bytes': metric(f'Q5.{day}.bytes', size if number(size) else None, count)})
    if not daily:
        q5['collector_cost'] = metric('Q5.collector_cost', None, 0,
            reason='nenhum collector.daily de dia completo na janela; resumo sai no dia seguinte, sem extrapolar bordas')
    sha = runner(['git', '-C', str(REPO), 'rev-parse', 'HEAD'])
    return {'window': window, 'metric_definition_version': 1, 'git_sha': sha.strip() if sha else None,
            'generated_at': iso(dt.datetime.now(UTC)), 'insufficient_data': insufficient,
            'read': reads, 'Q1': q1, 'Q2': q2, 'Q3': q3, 'Q4': q4, 'Q5': q5,
            'limitations': ['Coorte Q1: tarefas abertas na janela; eventos anteriores não são reconstruídos.',
                'Inventário Q3 usa agentes iniciados na janela; vínculos explícitos podem incluir agentes sem data.',
                'Primeiro avistamento não prova início; denominadores que o usam são estimados.',
                'Restrição de transcripts usa cwd, checkout principal do worktree e pasta codificada; falha ao resolver origem vira restrito.',
                'Somente arquivos mensais da janela são lidos; bordas não são preenchidas.',
                'P1 não registra motivo específico do erro: saturações podem ficar desconhecidas.', PROXY_NOTE]}


def render_md(report):
    w = report['window']
    lines = ['# Relatório de métricas do AI OS', '', f"Janela: {w['since']} até {w['until']} (fim exclusivo); fuso {w['timezone']}.",
             f"metric_definition_version=1 · git sha: {report['git_sha'] or 'unknown'}", '', '## Dados insuficientes', '']
    lines.extend(f"- {r['metric']}: {r['reason']}" for r in report['insufficient_data'])
    if not report['insufficient_data']:
        lines.append('Nenhuma métrica desconhecida nas fontes disponíveis.')
    labels = {'first_delivery_acceptance': 'Aceite na primeira entrega', 'rework_rate': 'Taxa de retrabalho',
              'evaluation_coverage': 'Cobertura de avaliação', 'last_reading': 'Última leitura (%)',
              'maximum': 'Máximo (%)', 'sample_count': 'Amostras', 'unknown_minutes': 'Minutos desconhecidos',
              'quota_data': 'Dados de franquia', 'saturations_per_100': 'Saturações por 100 agentes iniciados',
              'unavailable_minutes': 'Minutos indisponíveis', 'agents_per_task': 'Agentes por tarefa',
              'relaunches': 'Relançamentos', 'link_coverage': 'Cobertura do vínculo',
              'interaction_time_proxy': 'Proxy estimado de interação (min)', 'technical_failure_rate': 'Falha técnica por tentativa',
              'permission_waits_over_10_minutes': 'Esperas por permissão acima de 10 min',
              'collector_gaps': 'Lacunas registradas do coletor', 'collector_gap_minutes': 'Lacunas do coletor (min)',
              'collector_cost': 'Custo do coletor', 'cycles': 'Ciclos', 'mean_ms': 'Média por ciclo (ms)',
              'max_ms': 'Máximo por ciclo (ms)', 'bytes': 'Bytes gravados'}
    rates = {'first_delivery_acceptance', 'rework_rate', 'evaluation_coverage', 'link_coverage', 'technical_failure_rate'}

    def table_rows(obj, prefix='', key=''):
        if isinstance(obj, dict) and 'status' in obj and 'value' in obj:
            context = ' / '.join(str(obj[k]) for k in ('provider', 'pool', 'window_kind', 'date') if obj.get(k) is not None)
            prefix = ' · '.join(filter(None, (context, prefix)))
            value = obj['value']
            shown = 'unknown' if value is None else (f'{value * 100:.1f}%' if key in rates else f'{value:g}' if number(value) else str(value))
            yield f"| {prefix} | {shown} | {obj['n']} | {obj['status']} |"
        elif isinstance(obj, dict):
            context = ' / '.join(str(obj[k]) for k in ('provider', 'pool', 'window_kind', 'date') if obj.get(k) is not None)
            for name, value in obj.items():
                if name in labels:
                    yield from table_rows(value, ' · '.join(filter(None, (context, labels[name]))), name)
                elif isinstance(value, list):
                    yield from table_rows(value, prefix, name)
        elif isinstance(obj, list):
            for value in obj:
                yield from table_rows(value, prefix, key)

    for question in ('Q1', 'Q2', 'Q3', 'Q4', 'Q5'):
        lines.extend(['', f'## {question}', '', '| Métrica | Valor | n | Status |', '|---|---:|---:|---|',
                      *table_rows(report[question])])
    lines.extend(['', 'Os detalhes por tarefa, dia e projeto estão em `relatorio.json`.', '', PROXY_NOTE])
    lines.extend(['', '## Limites de leitura', '', *('- ' + item for item in report['limitations']), '',
                  f"Linhas inválidas no histórico: {report['read']['invalid_lines']}; nos transcripts: {report['read']['transcript_invalid_lines']}.", ''])
    return '\n'.join(lines)


def boundary(value, tz, end=False):
    parsed = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=tz)
    if end and re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        parsed += dt.timedelta(days=1)
    return parsed


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--since', help='data local ou instante ISO; padrão: sete dias antes do corte')
    ap.add_argument('--until', help='data local inclusiva ou instante ISO exclusivo; padrão: agora')
    ap.add_argument('--tz', help='fuso, ex.: -03:00')
    ap.add_argument('--home', type=Path, default=Path.home())
    ap.add_argument('--state-dir', type=Path)
    ap.add_argument('--archive-dir', type=Path)
    ap.add_argument('--claude-dir', type=Path)
    ap.add_argument('--restricted-config', type=Path, default=REPO / 'config/ai-os-memory.toml')
    ap.add_argument('--no-paseo-live', action='store_true')
    ap.add_argument('--out', type=Path, help='diretório para RELATORIO.md e relatorio.json')
    a = ap.parse_args(argv)
    try:
        tz = parse_tz(a.tz)
        until = boundary(a.until, tz, end=True) if a.until else dt.datetime.now(UTC)
        since = boundary(a.since, tz) if a.since else until - dt.timedelta(days=7)
        if since >= until:
            raise ValueError('since deve vir antes de until')
    except ValueError as exc:
        ap.error(str(exc))
    state = a.state_dir or Path(os.environ.get('AI_OS_STATE_DIR', str(a.home / '.local/state/ai-os')))
    ctx = Ctx(tz=tz, until=until, home=a.home, restricted=load_restricted(a.restricted_config, a.home))
    report = collect(ctx, state, since, until, a.archive_dir or state / 'arquivo-agentes', a.claude_dir,
                     live=not a.no_paseo_live)
    out = a.out or state / 'relatorios' / f'{since.astimezone(tz):%Y%m%d}-{until.astimezone(tz):%Y%m%d}'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'relatorio.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    (out / 'RELATORIO.md').write_text(render_md(report), encoding='utf-8')
    print(f'ok: {out}; {report["read"]["files"]} arquivos mensais; {report["read"]["invalid_lines"]} linhas inválidas')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
