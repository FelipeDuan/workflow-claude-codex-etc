"""Vigia (watchdog.log), commits (git log), telemetria manual e snapshots de franquia.

Commits: agrega por período, repo (pseudonimizado) e família do trailer
Co-Authored-By. Só o snapshot privado separado guarda SHA e patch-id;
mensagens e autores não são gravados.
"""
import collections
import glob
import json
import os
import re
import subprocess

from paseo import read_watchdog
from metrics_common import parse_ts

# trailers que não casam com nenhuma família viram 'outro' (podem ser nomes de pessoas)
FAMILIAS = (('Opus', 'Claude Opus'), ('Sonnet', 'Claude Sonnet'), ('Haiku', 'Claude Haiku'),
            ('Gemini', 'Gemini'), ('Codex', 'Codex/GPT'), ('GPT', 'Codex/GPT'), ('Claude', 'Claude (genérico)'))


def family(name):
    for a, n in FAMILIAS:
        if a in name:
            return n
    return 'outro'


def vigia(ctx, watchdog_log, paseo_agents):
    pm = {a['Id']: a['pm'] for a in paseo_agents}
    W = collections.defaultdict(collections.Counter)
    first = last = None
    uniq = collections.defaultdict(set)
    pmap = collections.Counter()
    for ts, t, ag, det in read_watchdog(ctx, watchdog_log):
        p = ctx.per(ctx.day(ts))
        first = first or ts
        last = ts
        W[p][t] += 1
        uniq[(p, t)].add(ag)
        if t == 'erro' and re.search(r'usage limit|limite de uso', det, re.I):
            W[p]['erro_limite_uso'] += 1
        if ag:
            pmap[(p, t, pm.get(ag, 'agente_nao_identificado'))] += 1
    return dict(first=first, last=last, eventos={p: dict(v) for p, v in W.items()},
                agentes_distintos={f'{k[0]}|{k[1]}': len(v - {None}) for k, v in uniq.items()},
                por_provider_modelo={f'{k[0]}|{k[1]}|{k[2]}': v for k, v in sorted(pmap.items())})


def find_roots(workspace, depth=3):
    roots = set()
    for dp in range(0, depth + 1):
        for g in glob.glob(str(workspace) + '/*' * dp + '/.git'):
            roots.add(os.path.dirname(g))
    return roots


def commits(ctx, since, runner=None, dedup='patch-id', snapshot=None):
    """Deduplica por SHA e pelo conteúdo estável do patch dentro de cada repo."""
    if dedup not in ('patch-id', 'sha'):
        raise ValueError('dedup deve ser patch-id ou sha')
    def default_runner(cmd):
        ctx.reads['subprocessos'] += 1
        return subprocess.run(cmd, capture_output=True, text=True, errors='replace').stdout
    runner = runner or default_runner
    roots = find_roots(ctx.workspace)
    com = collections.defaultdict(collections.Counter)
    seen = set()
    seen_patches = set()
    repos = collections.Counter()
    until = ctx.until.isoformat()
    if dedup == 'patch-id':
        since = min(since, *(a for a, _ in ctx.periods.values()))
    candidates = []
    patch_id_failures = 0
    fallback_sha_count = 0
    for r in sorted(roots):
        o = runner(['git', '-C', r, 'log', '--all', f'--since={since}', f'--until={until}',
                    '--date=short', '--format=@@%H|%ad%n%B@@END' if dedup == 'sha'
                    else '--format=@@%H|%aI%n%B@@END'])
        patches = {}
        if dedup == 'patch-id':
            diff = runner(['git', '-C', r, 'log', '--all', f'--since={since}', f'--until={until}',
                           '--pretty=medium', '--patch', '--no-ext-diff', '--no-textconv', '--binary'])
            ctx.reads['subprocessos'] += 1
            try:
                stable = subprocess.run(['git', 'patch-id', '--stable'], input=diff,
                                        capture_output=True, text=True, check=True).stdout
                patches = {sha: patch for patch, sha in (line.split() for line in stable.splitlines())}
            except (OSError, subprocess.CalledProcessError, ValueError):
                patch_id_failures += 1
        for blk in o.split('@@END'):
            blk = blk.strip()
            if not blk.startswith('@@'):
                continue
            h, rest = blk[2:].split('\n', 1) if '\n' in blk else (blk[2:], '')
            sha, d = h.split('|')
            candidates.append((d, sha, r, rest, patches.get(sha)))
    # Buscar baseline antes de S1 evita atribuir à semana nova um patch antigo.
    if dedup == 'patch-id':
        candidates.sort(key=lambda c: (parse_ts(c[0]), c[1], c[2]))
    for d, sha, r, rest, patch in candidates:
        if sha in seen:
            continue
        seen.add(sha)
        if patch and (r, patch) in seen_patches:
            continue
        if patch:
            seen_patches.add((r, patch))
        elif dedup == 'patch-id':
            fallback_sha_count += 1
        repos[ctx.repo_label(r)] += 1
        day = d[:10]
        p = ctx.per(day) if dedup == 'sha' else next(
            (name for name, (a, b) in ctx.periods.items() if a <= day <= b), 'outro')
        if snapshot is not None:
            snapshot.append(dict(repo=ctx.repo_label(r), sha=sha, patch_id=patch,
                                 author_date=d, periodo=p))
        com[p]['total'] += 1
        co = set(re.findall(r'^Co-Authored-By:\s*([^<\n]+?)\s*<', rest, re.I | re.M))
        if not co:
            com[p]['sem_coautor'] += 1
        for c in co:
            fam_ = family(c.strip())
            com[p]['co:' + (c.strip() if fam_ != 'outro' else 'outro')] += 1
    return dict(dedup=dedup, patch_id_failures=patch_id_failures, fallback_sha_count=fallback_sha_count,
                repos_com_git=len(roots), repos_com_commits=len(repos), commits_por_repo=dict(repos),
                por_periodo={p: dict(v) for p, v in com.items()})


def telemetria(ctx, path):
    if not path or not os.path.exists(path):
        return dict(n=0)
    tel = [json.loads(l) for l in ctx.lines(path) if l.strip()]
    tel = [t for t in tel if t['date'] <= ctx.until_day]
    if not tel:
        return dict(n=0)
    return dict(n=len(tel), primeira=min(t['date'] for t in tel), ultima=max(t['date'] for t in tel),
                por_dia=dict(sorted(collections.Counter(t['date'] for t in tel).items())),
                por_harness=dict(collections.Counter(t['harness'] for t in tel)),
                por_outcome=dict(collections.Counter(t['outcome'] for t in tel)))


def quota(ctx, qdir):
    """Snapshot ATUAL da franquia (não depende de --until). Só campos numéricos."""
    out = {}
    for f in sorted(glob.glob(str(qdir) + '/*.json')):
        q = json.loads(ctx.text(f))
        out[os.path.basename(f)[:-5]] = dict(
            provider=q.get('provider'), fetched_at=q.get('fetched_at'), status=q.get('status'),
            windows=[{k: w.get(k) for k in ('kind', 'pool', 'used_percent', 'resets_at', 'window_minutes') if k in w}
                     for w in q.get('windows', [])])
    return out


def collect(ctx, watchdog_log, paseo_agents, since, telemetry_path, quota_dir, dedup='patch-id', snapshot=None):
    return dict(vigia=vigia(ctx, watchdog_log, paseo_agents),
                commits=commits(ctx, since, dedup=dedup, snapshot=snapshot),
                telemetria=telemetria(ctx, telemetry_path), quota=quota(ctx, quota_dir) if quota_dir else {})
