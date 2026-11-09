"""Utilitários comuns das métricas do AI OS (somente stdlib).

Contexto (Ctx): fuso, instante de corte (until), períodos, pastas de origem,
projetos restritos e contadores de leitura (arquivos/bytes/subprocessos).
Os scripts só agregam contagens: nenhum prompt, mensagem, e-mail ou caminho
completo vai para a saída.
"""
import datetime
import os
import re
import time
from contextlib import contextmanager
from pathlib import Path

RESTRITO = 'restrito'

DEFAULT_PERIODS = {
    'baseline': ('2026-10-08', '2026-10-21'),
    'S1': ('2026-10-22', '2026-11-01'),
    'S2': ('2026-11-02', None),  # None = dia do --until
}


def parse_tz(s):
    """None -> fuso local; '-03', '-03:00', '+0530' ou 'UTC' -> offset fixo."""
    if not s:
        return datetime.datetime.now().astimezone().tzinfo
    if s.upper() in ('UTC', 'Z'):
        return datetime.timezone.utc
    m = re.fullmatch(r'([+-])(\d{2}):?(\d{2})?', s)
    if not m:
        raise ValueError(f'fuso inválido: {s}')
    off = datetime.timedelta(hours=int(m.group(2)), minutes=int(m.group(3) or 0))
    return datetime.timezone(off if m.group(1) == '+' else -off)


def parse_ts(ts):
    """ISO 8601 (aceita 'Z') -> datetime com fuso. Sem fuso = UTC."""
    d = datetime.datetime.fromisoformat(ts.replace('Z', '+00:00'))
    return d if d.tzinfo else d.replace(tzinfo=datetime.timezone.utc)


def parse_until(s, tz):
    if not s:
        return datetime.datetime.now(datetime.timezone.utc)
    d = datetime.datetime.fromisoformat(s.replace('Z', '+00:00'))
    return d if d.tzinfo else d.replace(tzinfo=tz)


def parse_range(spec, default):
    """'A..B' ou 'A..' -> (A, B|None). None -> default."""
    if not spec:
        return default
    a, _, b = spec.partition('..')
    return (a, b or None)


def expand_home(p, home):
    p = str(p)
    return str(home / p[2:]) if p.startswith('~/') else p


def load_restricted(toml_path, home):
    """Lê [restricted].paths do toml; devolve lista de caminhos absolutos."""
    if not toml_path or not Path(toml_path).is_file():
        return []
    import tomllib
    with open(toml_path, 'rb') as f:
        cfg = tomllib.load(f)
    return [expand_home(p, home).rstrip('/') for p in (cfg.get('restricted') or {}).get('paths', [])]


def encode_path(p):
    """Mesma codificação do Claude Code para nome de pasta de projeto."""
    return re.sub(r'[^A-Za-z0-9]', '-', str(p))


class Ctx:
    def __init__(self, tz=None, until=None, periods=None, home=None, restricted=(), workspace=None):
        self.tz = tz or parse_tz(None)
        self.until = until or datetime.datetime.now(datetime.timezone.utc)
        self.until_day = self.until.astimezone(self.tz).strftime('%Y-%m-%d')
        self.home = Path(home) if home else Path.home()
        self.workspace = Path(workspace) if workspace else self.home / 'Workspace'
        self.restricted = [str(r).rstrip('/') for r in restricted]
        self._restricted_enc = [encode_path(r) for r in self.restricted]
        self.periods = {}
        for k, (a, b) in (periods or DEFAULT_PERIODS).items():
            self.periods[k] = (a, b or self.until_day)
        self.reads = {'files': 0, 'bytes': 0, 'subprocessos': 0}
        self.stages = {}

    # --- tempo e períodos ---
    def day(self, ts):
        return parse_ts(ts).astimezone(self.tz).strftime('%Y-%m-%d')

    def per(self, d):
        for p in ('S1', 'S2'):
            a, b = self.periods[p]
            if a <= d <= b:
                return p
        return 'outro'

    def after_until(self, dt):
        return dt > self.until

    # --- restritos / pseudonimização ---
    def path_restricted(self, path):
        p = str(path).rstrip('/')
        return any(p == r or p.startswith(r + '/') for r in self.restricted)

    def project_label(self, name):
        """Nome de pasta de projeto do Claude Code -> rótulo seguro.

        Restrito -> 'restrito'; worktree do Paseo -> 'paseo-worktree' (a origem
        não é identificável pelo nome); demais perdem o prefixo da home.
        """
        home_enc = encode_path(self.home)
        wt_enc = encode_path(self.home / '.paseo' / 'worktrees')
        for r in self._restricted_enc:
            if name == r or name.startswith(r + '-'):
                return RESTRITO
        if name == wt_enc or name.startswith(wt_enc + '-'):
            return 'paseo-worktree'
        if name.startswith(home_enc + '-'):
            return name[len(home_enc) + 1:]
        return name

    def repo_label(self, path):
        """Caminho de repositório -> 'restrito' ou caminho relativo ao workspace."""
        if self.path_restricted(path):
            return RESTRITO
        try:
            return str(Path(path).relative_to(self.workspace))
        except ValueError:
            return Path(path).name

    # --- leitura com contagem ---
    def lines(self, path):
        """Itera linhas de texto contando arquivo e bytes lidos."""
        self.reads['files'] += 1
        self.reads['bytes'] += os.path.getsize(path)
        with open(path, errors='replace') as f:
            yield from f

    def text(self, path):
        self.reads['files'] += 1
        self.reads['bytes'] += os.path.getsize(path)
        with open(path, errors='replace') as f:
            return f.read()

    @contextmanager
    def stage(self, name):
        r0, t0 = dict(self.reads), time.perf_counter()
        try:
            yield
        finally:
            self.stages[name] = {'segundos': round(time.perf_counter() - t0, 2),
                                 **{k: self.reads[k] - r0[k] for k in r0}}
