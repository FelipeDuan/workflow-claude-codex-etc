"""Agentes Paseo: inspect/logs arquivados + estado vivo (paseo ls/inspect) + vigia.

Só extrai campos de metadado (provider, modelo, status, datas) e flags de regex
(limite de uso, hash de commit). O texto dos logs nunca vai para a saída, e o
título do agente (Name) é descartado por poder citar projetos.
"""
import collections
import glob
import json
import os
import re
import subprocess

from metrics_common import parse_ts

KEYS = ('Id', 'Name', 'Provider', 'Model', 'Thinking', 'Status', 'Mode', 'CreatedAt', 'UpdatedAt',
        'ParentAgentId', 'LastUsage')
LIMITE = re.compile(r'usage limit|limite de uso|Free usage limit', re.I)
WD_LINE = re.compile(r'(\S+) (\S+)(?: agente=(\S+))?(?: detalhe=(.*))?')


def parse(txt):
    """Saída de `paseo inspect` (linhas 'Chave valor') -> dict."""
    r = {}
    for l in txt.splitlines():
        p = l.split(None, 1)
        if len(p) == 2 and p[0] in KEYS:
            r[p[0]] = p[1].strip()
    return r


def read_watchdog(ctx, path):
    """Itera (ts, tipo, agente, detalhe) do watchdog.log até o instante de corte."""
    if not path or not os.path.exists(path):
        return
    for l in ctx.lines(path):
        m = WD_LINE.match(l)
        if not m:
            continue
        ts, t, ag, det = m.groups()
        try:
            if ctx.after_until(parse_ts(ts)):
                continue
        except ValueError:
            continue
        yield ts, t, ag, det or ''


def run_cmd(ctx, cmd):
    ctx.reads['subprocessos'] += 1
    r = subprocess.run(cmd, capture_output=True, text=True, errors='replace')
    return r.stdout


def collect(ctx, archive_dir, watchdog_log, agents_json, live=True, runner=None):
    runner = runner or (lambda cmd: run_cmd(ctx, cmd))
    wd = collections.defaultdict(collections.Counter)
    wdlim = collections.defaultdict(int)
    for _ts, t, ag, det in read_watchdog(ctx, watchdog_log):
        if ag:
            wd[ag][t] += 1
            if t == 'erro' and LIMITE.search(det):
                wdlim[ag] += 1
    agents = []
    A = str(archive_dir).rstrip('/') + '/' if archive_dir else None
    if A and os.path.isdir(A):
        for f in sorted(glob.glob(A + '*.inspect.txt')):
            r = parse(ctx.text(f))
            r['fonte'] = 'arquivado'
            lg = f.replace('.inspect.txt', '.log.txt')
            t = ctx.text(lg) if os.path.exists(lg) else ''
            r['log_chars'] = len(t)
            r['log_limite'] = bool(LIMITE.search(t))
            r['log_commit_hash'] = _commit_hash(t)
            agents.append(r)
        for f in sorted(glob.glob(A + '*.log.txt')):
            b = os.path.basename(f)[:-8]
            if os.path.exists(A + b + '.inspect.txt'):
                continue
            t = ctx.text(f)
            agents.append(dict(Id=b, Provider='desconhecido', Model='desconhecido', Status='sem_inspect',
                               fonte='arquivado_sem_inspect', log_chars=len(t),
                               log_limite=bool(re.search(r'usage limit|limite de uso', t, re.I)),
                               log_commit_hash=_commit_hash(t, short=True)))
    if live:
        cur = {}
        if agents_json and os.path.exists(agents_json):
            cur = {a['id']: a for a in json.loads(ctx.text(agents_json))}
        try:
            ls = json.loads(runner(['paseo', 'ls', '-a', '--json']) or '[]')
        except ValueError:
            ls = []
        for a in ls:
            r = parse(runner(['paseo', 'inspect', a['id']]))
            r['fonte'] = 'atual'
            r['vigia_status'] = cur.get(a['id'], {}).get('status')
            r['log_limite'] = bool(re.search(r'usage limit|limite de uso', cur.get(a['id'], {}).get('motivo', ''), re.I))
            agents.append(r)
    # corte temporal: ignora agentes criados depois do instante de corte
    agents = [r for r in agents if not (r.get('CreatedAt') and ctx.after_until(parse_ts(r['CreatedAt'])))]
    for r in agents:
        ca = r.get('CreatedAt')
        r['dia'] = ctx.day(ca) if ca else None
        r['periodo'] = ctx.per(r['dia']) if r['dia'] else 'sem_data'
        r['pm'] = r.get('Provider', '?') + '/' + r.get('Model', '?')
        full = r.get('Id')
        w = wd.get(full, {})
        r['wd'] = dict(w)
        st = r.get('Status')
        vs = r.get('vigia_status')
        if st == 'error' or vs == 'erro':
            d = 'erro'
        elif vs == 'aguardando_aprovacao':
            d = 'aguardando_aprovacao'
        elif st in ('closed', 'idle'):
            d = 'concluido(closed/idle)'
        else:
            d = 'desconhecido'
        r['ev_erro'] = bool(w.get('erro'))
        r['ev_parado'] = bool(w.get('parado'))
        r['ev_pendente'] = bool(w.get('pendente'))
        r['desfecho'] = d
        r['erro_limite'] = bool(r.get('log_limite') or wdlim.get(full))
    agg = collections.defaultdict(collections.Counter)
    for r in agents:
        for key in ((r['periodo'], r['pm']), (r['periodo'], 'TOTAL')):
            agg[key]['n'] += 1
            agg[key][r['desfecho']] += 1
            if r['erro_limite']:
                agg[key]['com_erro_limite'] += 1
            for e in ('ev_erro', 'ev_parado', 'ev_pendente'):
                if r[e]:
                    agg[key][e] += 1
            if r.get('log_commit_hash'):
                agg[key]['log_cita_commit'] += 1
    slim = [{k: r.get(k) for k in ('Id', 'pm', 'Thinking', 'Mode', 'dia', 'periodo', 'Status', 'fonte',
                                   'desfecho', 'erro_limite', 'ev_erro', 'ev_parado', 'ev_pendente',
                                   'log_commit_hash', 'wd')} for r in agents]
    return dict(n=len(agents), n_archived=sum(r['fonte'].startswith('arq') for r in agents),
                n_current=sum(r['fonte'] == 'atual' for r in agents),
                agg={f'{k[0]}|{k[1]}': dict(v) for k, v in sorted(agg.items())}, agents=slim)


def _commit_hash(t, short=False):
    if short:
        return bool(re.search(r'commit[^\n]{0,80}\b[0-9a-f]{7,40}\b', t, re.I))
    return bool(re.search(r'commit[^\n]{0,80}\b[0-9a-f]{7,40}\b|\b[0-9a-f]{7,40}\b[^\n]{0,40}commit', t, re.I))
