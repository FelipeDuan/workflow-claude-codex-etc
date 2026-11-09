"""Checagens de sanidade: amostra independente de message.id nas linhas brutas
do Claude + consistência entre os agregados. Só ids, contagens e tipo (main/sub)."""
import collections
import glob
import json
import random

from metrics_common import parse_ts


def sample(ctx, root, desde='2026-11-05', seed=7):
    random.seed(seed)
    root = str(root).rstrip('/') + '/'
    lines = collections.defaultdict(list)
    for f in sorted(glob.glob(root + '**/*.jsonl', recursive=True)):
        kind = 'sub' if '/subagents/' in f[len(root):] else 'main'
        for n, l in enumerate(ctx.lines(f)):
            if '"type":"assistant"' not in l.replace('": "', '":"'):
                continue
            try:
                d = json.loads(l)
            except ValueError:
                continue
            m = d.get('message') or {}
            ts = d.get('timestamp') or ''
            if not m.get('id') or ts < desde or ctx.after_until(parse_ts(ts)):
                continue
            u = m.get('usage') or {}
            lines[m['id']].append((kind, n + 1, u.get('output_tokens'), u.get('input_tokens'),
                                   u.get('cache_creation_input_tokens'), u.get('cache_read_input_tokens'),
                                   m.get('model')))
    multi = [k for k, v in lines.items() if len(v) > 1]
    single = [k for k, v in lines.items() if len(v) == 1]
    pick = random.sample(multi, min(2, len(multi))) + random.sample(single, min(1, len(single)))
    return {k: lines[k] for k in pick}


def collect(ctx, root, claude, codex, paseo):
    out = sample(ctx, root)
    out['claude_soma_modelos_eq_total'] = {
        q: (sum(v['msgs'] for k, v in claude['agg'].items() if k.startswith(q + '|') and k.endswith('|all')),
            claude['sanity'][q]) for q in claude['sanity']}
    out['claude_dedup_vs_raw'] = (claude['dedup_msgs'], claude['raw_assistant_lines'], claude['dupe_lines'],
                                  claude['dedup_msgs'] + claude['dupe_lines'] + claude['no_usage'] == claude['raw_assistant_lines'])
    out['codex_soma_ultimos_totais_vs_deltas'] = (codex['sum_last_totals'], codex['sum_deltas'])
    out['paseo_agentes'] = (paseo['n'], paseo['n_archived'], paseo['n_current'])
    return out
