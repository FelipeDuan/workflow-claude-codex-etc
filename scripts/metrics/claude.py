"""Uso de tokens do Claude Code (~/.claude/projects/**/*.jsonl).

Só lê campos de contagem (timestamp, modelo, usage, ids). Dedup global por
message.id; principal vs subagente por isSidechain ou caminho /subagents/.
"""
import collections
import glob
import json
import os

from metrics_common import parse_ts


def fam(m):
    m = (m or '').lower()
    for k in ('opus', 'sonnet', 'haiku', 'fable'):
        if k in m:
            return k
    return m or 'none'


def _add(c, r):
    c['msgs'] += 1
    c['in'] += r['i']
    c['out'] += r['o']
    c['cc'] += r['cc']
    c['cr'] += r['cr']


def collect(ctx, root):
    root = str(root).rstrip('/') + '/'
    files = sorted(glob.glob(root + '**/*.jsonl', recursive=True))
    raw = 0
    recs = {}
    nousage = 0
    diffs = 0
    dupe_lines = 0
    for f in files:
        rel = f[len(root):]
        proj = rel.split('/')[0]
        sub = '/subagents/' in rel
        sid = os.path.basename(f)[:-6] if not sub else rel.split('/')[1]
        for l in ctx.lines(f):
            try:
                d = _loads(l)
            except ValueError:
                continue
            if d.get('type') != 'assistant':
                continue
            ts = d.get('timestamp')
            if ts and ctx.after_until(parse_ts(ts)):
                continue
            raw += 1
            m = d.get('message') or {}
            u = m.get('usage')
            if not u:
                nousage += 1
                continue
            key = m.get('id') or d.get('requestId') or d.get('uuid')
            r = dict(ts=ts, model=m.get('model'), side=bool(d.get('isSidechain')) or sub,
                     i=u.get('input_tokens', 0) or 0, o=u.get('output_tokens', 0) or 0,
                     cc=u.get('cache_creation_input_tokens', 0) or 0,
                     cr=u.get('cache_read_input_tokens', 0) or 0,
                     proj=ctx.project_label(proj), sid=sid)
            if key in recs:
                dupe_lines += 1
                p = recs[key]
                if (p['i'], p['o'], p['cc'], p['cr']) != (r['i'], r['o'], r['cc'], r['cr']):
                    diffs += 1
                if r['o'] >= p['o']:
                    r['side'] = p['side'] or r['side']
                    recs[key] = r
            else:
                recs[key] = r
    agg = collections.defaultdict(collections.Counter)
    bydm = collections.defaultdict(collections.Counter)
    bydt = collections.defaultdict(collections.Counter)
    sess = collections.defaultdict(lambda: collections.defaultdict(set))
    for r in recs.values():
        if not r['ts']:
            continue
        d = ctx.day(r['ts'])
        p = ctx.per(d)
        f = fam(r['model'])
        if f == 'none' or r['model'] == '<synthetic>':
            f = 'synthetic'
        kind = 'sub' if r['side'] else 'main'
        _add(agg[(p, f, kind)], r)
        _add(agg[(p, f, 'all')], r)
        _add(bydm[(d, f)], r)
        _add(bydt[(d, kind)], r)
        sess[p][r['proj']].add(r['sid'])
    out = dict(files=len(files), raw_assistant_lines=raw, no_usage=nousage, dedup_msgs=len(recs),
               dupe_lines=dupe_lines, dupes_with_diff_usage=diffs, tz=str(ctx.tz),
               agg={f'{k[0]}|{k[1]}|{k[2]}': dict(v) for k, v in agg.items()},
               bydaymodel={f'{k[0]}|{k[1]}': dict(v) for k, v in sorted(bydm.items())},
               bydaytype={f'{k[0]}|{k[1]}': dict(v) for k, v in sorted(bydt.items())},
               sessions={p: {pr: len(s) for pr, s in v.items()} for p, v in sess.items()})
    for p in ('S1', 'S2', 'outro'):
        tot = sum(v['msgs'] for k, v in agg.items() if k[0] == p and k[2] == 'all')
        out.setdefault('sanity', {})[p] = tot
    return out


def _loads(l):
    d = json.loads(l)
    if not isinstance(d, dict):
        raise ValueError('linha não é objeto')
    return d
