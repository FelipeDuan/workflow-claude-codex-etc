"""Uso de tokens do Codex (~/.codex/sessions/AAAA/MM/DD/*.jsonl).

Delta de total_token_usage por evento token_count. O modelo da sessão vem do
último turn_context visto (limitação conhecida: sessão que troca de modelo fica
toda no modelo vigente no evento). Só lê contagens e o nome do modelo.
"""
import collections
import glob
import json

from metrics_common import parse_ts

F = ('input_tokens', 'cached_input_tokens', 'output_tokens', 'reasoning_output_tokens', 'total_tokens')


def collect(ctx, root, since='2026-10-01'):
    """since: só lê pastas de sessão com data >= since (YYYY-MM-DD)."""
    root = str(root).rstrip('/')
    files = []
    for f in sorted(glob.glob(root + '/*/*/*/*.jsonl')):
        y, m, d = f[len(root) + 1:].split('/')[:3]
        if f'{y}-{m}-{d}' >= since:
            files.append(f)
    agg = collections.defaultdict(collections.Counter)
    bydm = collections.defaultdict(collections.Counter)
    nsess = collections.defaultdict(set)
    ev = 0
    resets = 0
    sess_last = {}
    for f in files:
        model = None
        prev = None
        sid = f.split('rollout-')[-1][-42:-6]
        for l in ctx.lines(f):
            try:
                d = json.loads(l)
            except ValueError:
                continue
            if not isinstance(d, dict):
                continue
            p = d.get('payload') or {}
            if d.get('type') == 'turn_context' and p.get('model'):
                model = p['model']
            if d.get('type') == 'session_meta' and not model:
                model = p.get('model')
            if p.get('type') == 'token_count' and p.get('info'):
                t = p['info'].get('total_token_usage')
                if not t:
                    continue
                if ctx.after_until(parse_ts(d['timestamp'])):
                    continue
                ev += 1
                cur = {k: t.get(k, 0) or 0 for k in F}
                if prev and cur['total_tokens'] < prev['total_tokens']:
                    resets += 1
                    delta = cur
                else:
                    delta = {k: cur[k] - (prev[k] if prev else 0) for k in F}
                prev = cur
                day = ctx.day(d['timestamp'])
                pr = ctx.per(day)
                m = model or 'desconhecido'
                for key in ((pr, m), (pr, 'TOTAL')):
                    for k in F:
                        agg[key][k] += delta[k]
                for k in F:
                    bydm[(day, m)][k] += delta[k]
                nsess[(pr, m)].add(sid)
        sess_last[sid] = prev
    tot_last = sum((v or {}).get('total_tokens', 0) for v in sess_last.values())
    tot_delta = sum(v['total_tokens'] for k, v in agg.items() if k[1] == 'TOTAL')
    return dict(files=len(files), token_events=ev, resets=resets, sum_last_totals=tot_last, sum_deltas=tot_delta,
                agg={f'{k[0]}|{k[1]}': dict(v, sessions=len(nsess[k]) if k[1] != 'TOTAL' else None)
                     for k, v in agg.items()},
                bydaymodel={f'{k[0]}|{k[1]}': dict(v) for k, v in sorted(bydm.items())})
