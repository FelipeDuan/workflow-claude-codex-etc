#!/usr/bin/env python3
"""hygiene.py — higiene do AI OS em modo diagnóstico (somente leitura).

Subcomandos:
  scan  [--out ARQ] [--repo DIR]      inventário em JSON (stdout se --out "-")
  plan  [--scan ARQ] [--days N] [--out ARQ]
                                      plano em Markdown: PRESERVAR / CANDIDATO /
                                      DESCONHECIDO para cada recurso

REGRA: esta ferramenta nunca apaga, move, poda, mata processo, descarrega
launchd nem roda git gc/prune/worktree remove/paseo delete. Ela só lê e
imprime. Os comandos que aparecem no plano são sugestões para o Felipe rodar
à mão, depois de conferir.

# ponytail: a execução (--apply) fica para um PR futuro, com aprovação por
# classe (worktrees, agentes, ...) e com o plano congelado em arquivo.

Classificação (qualquer dúvida preserva):
  PRESERVAR     alterado/untracked, commit sem equivalente em outra ref, lock,
                agente ativo/aguardando/recente, checkout principal, restrito.
  CANDIDATO     worktree limpa, sem commit exclusivo (ou patch já integrado em
                outra ref), parada há mais de N dias; agente closed/idle sem
                pendência há mais de N dias.
  DESCONHECIDO  falha de leitura, Paseo indisponível, status inédito, symlink...

Privacidade: caminhos de projeto restrito saem como "restrito/<n>", sem
branch; títulos de agentes nunca são coletados.

Só biblioteca padrão, Python >= 3.11. Git e Paseo por subprocess sem shell.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

if sys.version_info < (3, 11):  # paseo_watchdog usa tomllib; no macOS use /opt/homebrew/bin/python3
    sys.exit("hygiene: requer Python >= 3.11 (tomllib). Rode com /opt/homebrew/bin/python3, como o launchd do vigia.")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paseo_watchdog as wd  # noqa: E402  (reuso de _state_dir, is_restricted, _git...)

SCHEMA_VERSION = 1
DEFAULT_DAYS = 7
MAX_CHERRY_REFS = 40
DU_TIMEOUT = 180
PRESERVAR, CANDIDATO, DESCONHECIDO = "PRESERVAR", "CANDIDATO", "DESCONHECIDO"


class HygieneError(Exception):
    pass


# ------------------------------------------------------------------ utilidades


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _git(cwd: str, *args: str) -> str | None:
    return wd._git(cwd, *args)  # somente leitura; fsmonitor desligado, sem locks opcionais


def paseo_json(args: list[str]):
    return wd.paseo_json(args)


def walk_size(path: str) -> tuple[int, float | None]:
    """(bytes em disco, mtime mais recente). Não segue symlinks."""
    total, newest, stack = 0, None, [path]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as it:
                for entry in it:
                    try:
                        st = entry.stat(follow_symlinks=False)
                        total += getattr(st, "st_blocks", 0) * 512 or st.st_size
                        newest = st.st_mtime if newest is None else max(newest, st.st_mtime)
                        if entry.is_dir(follow_symlinks=False):
                            stack.append(entry.path)
                    except OSError:
                        continue
        except OSError:
            continue
    return total, newest


def du_bytes(path: Path) -> int | None:
    if not path.exists():
        return None
    try:
        # -P: não segue symlinks (um link para fora não soma o alvo); -k: KiB; -s: total
        out = subprocess.run(["du", "-sPk", str(path)], capture_output=True, text=True, timeout=DU_TIMEOUT)
        return int(out.stdout.split()[0]) * 1024
    except (OSError, subprocess.TimeoutExpired, ValueError, IndexError):
        return None


def dir_sizes(home: Path, state_dir: Path) -> dict:
    paseo = du_bytes(home / ".paseo")
    paseo_wt = du_bytes(home / ".paseo" / "worktrees")
    return {
        "paseo_fora_worktrees": None if paseo is None else paseo - (paseo_wt or 0),
        "paseo_worktrees_du": paseo_wt,
        "claude": du_bytes(home / ".claude"),
        "codex": du_bytes(home / ".codex"),
        "ai_os_state": du_bytes(state_dir),
        "gemini": du_bytes(home / ".gemini"),
        "library_caches_informativo": du_bytes(home / "Library" / "Caches"),
    }


def memory_info() -> dict:
    info = {"pressure_level": None, "free_percentage": None, "swap_total_bytes": None, "swap_used_bytes": None}

    def run(cmd):
        try:
            return subprocess.run(cmd, capture_output=True, text=True, timeout=10).stdout
        except (OSError, subprocess.TimeoutExpired):
            return ""

    m = re.search(r"free percentage:\s*(\d+)%", run(["memory_pressure", "-Q"]))
    if m:
        info["free_percentage"] = int(m.group(1))
    m = re.search(r":\s*(\d+)", run(["sysctl", "kern.memorystatus_vm_pressure_level"]))
    if m:
        info["pressure_level"] = {1: "normal", 2: "aviso", 4: "critica"}.get(int(m.group(1)), "desconhecida")
    swap = run(["sysctl", "vm.swapusage"])
    units = {"M": 1 << 20, "G": 1 << 30, "K": 1 << 10}
    for key, name in (("swap_total_bytes", "total"), ("swap_used_bytes", "used")):
        m = re.search(name + r"\s*=\s*([\d.,]+)([KMG])", swap)
        if m:
            info[key] = int(float(m.group(1).replace(",", ".")) * units[m.group(2)])
    return info


def launchctl_list() -> list[dict]:
    try:
        out = subprocess.run(["launchctl", "list"], capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.TimeoutExpired):
        return []
    jobs = []
    for line in out.splitlines()[1:]:
        parts = line.split("\t")
        if len(parts) == 3 and parts[2].startswith("com.felipe"):
            jobs.append({"label": parts[2], "pid": None if parts[0] == "-" else parts[0], "last_exit": parts[1]})
    return jobs


# ------------------------------------------------------------------ scan


def registered_worktrees(repo: str) -> list[dict]:
    out = _git(repo, "worktree", "list", "--porcelain")
    if out is None:
        raise HygieneError("git worktree list falhou no repo informado")
    entries, current = [], None
    for line in out.splitlines():
        if line.startswith("worktree "):
            current = {"path": line[9:], "main": not entries}
            entries.append(current)
        elif current is not None and line.startswith("branch "):
            current["branch"] = line[7:].removeprefix("refs/heads/")
    return entries


def _other_refs(cwd: str, own_branch: str | None) -> list[str] | None:
    """Refs do repositório de origem (branches, remotes, tags...) menos a branch do worktree."""
    out = _git(cwd, "for-each-ref", "--format=%(refname)")
    if out is None:
        return None
    own = f"refs/heads/{own_branch}" if own_branch else None
    return [r for r in out.splitlines() if r and r != own and not r.endswith("/HEAD")]


def _sibling_heads(cwd: str, self_path: str) -> list[str]:
    """HEADs das outras worktrees do mesmo repo (cobre worktrees em HEAD destacado)."""
    out = _git(cwd, "worktree", "list", "--porcelain")
    heads, current, self_real = [], None, os.path.realpath(self_path)
    for line in (out or "").splitlines():
        if line.startswith("worktree "):
            current = line[9:]
        elif line.startswith("HEAD ") and current and os.path.realpath(current) != self_real:
            heads.append(line[5:].strip())
    return heads


def inspect_worktree(path: str, branch_hint: str | None, is_main: bool) -> dict:
    item = {"path": path, "is_main": is_main, "branch": branch_hint, "head": None, "tracked_changes": None,
            "untracked": None, "exclusive_commits": None, "unintegrated_commits": None, "locked": None,
            "age_days": None, "size_bytes": None, "main_checkout": None, "error": None}
    if os.path.islink(path):
        item["error"] = "symlink (não seguido)"
        return item
    if not os.path.isdir(path):
        item["error"] = "diretório ausente"
        return item
    head = _git(path, "rev-parse", "HEAD")
    status = _git(path, "status", "--porcelain=v1", "--untracked-files=all")
    gitdir = _git(path, "rev-parse", "--absolute-git-dir")
    common = _git(path, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if head is None or status is None or gitdir is None or common is None:
        item["error"] = "leitura do git falhou"
        return item
    item["head"] = head.strip()[:12]
    lines = [ln for ln in status.splitlines() if ln]
    item["untracked"] = sum(1 for ln in lines if ln.startswith("??"))
    item["tracked_changes"] = len(lines) - item["untracked"]
    try:  # ausente = sem lock; qualquer outro erro = desconhecido (None)
        os.stat(os.path.join(gitdir.strip(), "locked"))
        item["locked"] = True
    except FileNotFoundError:
        item["locked"] = False
    except OSError:
        item["locked"] = None
    item["main_checkout"] = str(Path(common.strip()).parent)
    if branch_hint is None:
        sym = _git(path, "symbolic-ref", "--short", "-q", "HEAD")
        item["branch"] = sym.strip() if sym and sym.strip() else None
    branch = item["branch"]

    refs = _other_refs(path, branch)
    if refs is None:
        item["error"] = "for-each-ref falhou"
        return item
    heads = _sibling_heads(path, path)
    rev = _git(path, "rev-list", "HEAD", "--not", *refs, *heads)
    if rev is None:
        item["error"] = "rev-list falhou"
        return item
    exclusive = rev.split()
    item["exclusive_commits"] = len(exclusive)
    pending = set(exclusive)
    if pending:
        # só branches e remotes do repo de origem (e HEADs de outras worktrees) provam integração
        eligible = [r for r in refs if r.startswith(("refs/heads/", "refs/remotes/"))] + heads
        for ref in eligible[:MAX_CHERRY_REFS]:
            out = _git(path, "cherry", ref, "HEAD")
            if out is None:
                continue
            for line in out.splitlines():
                if line.startswith("- "):
                    pending.discard(line[2:].strip())
            if not pending:
                break
        if pending and not eligible:
            item["unintegrated_commits"] = None
            item["error"] = "sem refs elegíveis para comparar os patches"
        elif pending and len(eligible) > MAX_CHERRY_REFS:
            item["unintegrated_commits"] = None
            item["error"] = f"busca de patch truncada (> {MAX_CHERRY_REFS} refs)"
        else:
            item["unintegrated_commits"] = len(pending)
    else:
        item["unintegrated_commits"] = 0

    if not is_main:  # o checkout principal inclui .git; não vale a caminhada
        size, newest = walk_size(path)
        item["size_bytes"] = size
        if newest is not None:
            item["age_days"] = round((time.time() - newest) / 86400, 2)
    return item


def collect_worktrees(repo: str, paseo_root: Path) -> list[dict]:
    reg = registered_worktrees(repo)
    seen = {os.path.realpath(e["path"]) for e in reg}
    items = [inspect_worktree(e["path"], e.get("branch"), e["main"]) for e in reg]
    if paseo_root.is_dir():
        for group in sorted(paseo_root.iterdir()):
            if group.is_symlink() or not group.is_dir():
                continue
            for entry in sorted(group.iterdir()):
                real = os.path.realpath(entry)
                if real in seen and not entry.is_symlink():
                    continue
                if entry.is_symlink():
                    items.append(inspect_worktree(str(entry), None, False))
                elif entry.is_dir() and (entry / ".git").exists():
                    seen.add(real)
                    items.append(inspect_worktree(str(entry), None, False))
    return items


def mask_restricted(items: list[dict], agents: list[dict], roots: list[Path]) -> None:
    """Liga agentes a worktrees e troca caminho/branch de restritos por 'restrito/<n>'.

    Falha de política ou de leitura conta como restrito (fail-closed).
    """
    def restricted(cwd: str | None) -> bool:
        if not cwd:
            return False
        try:
            return wd.is_restricted(cwd, roots)
        except Exception:
            return True

    reals = [os.path.realpath(i["path"]) for i in items]
    for item in items:
        item["restricted"] = restricted(item["path"]) or restricted(item["main_checkout"])
    for agent in agents:
        cwd = agent.pop("_cwd", "")
        real = os.path.realpath(cwd) if cwd else ""
        match = None
        for idx, rp in enumerate(reals):
            if real and (real == rp or real.startswith(rp + os.sep)) and (match is None or len(rp) > len(reals[match])):
                match = idx
        agent["restricted"] = restricted(cwd) or (match is not None and items[match]["restricted"])
        agent["_match"] = match
    count = 0
    for item in items:
        if item["restricted"]:
            count += 1
            item["path"], item["branch"], item["main_checkout"] = f"restrito/{count}", None, None
    for agent in agents:
        match = agent.pop("_match")
        agent["worktree"] = items[match]["path"] if match is not None else None


def collect_agents(now: datetime) -> tuple[list[dict], str | None]:
    try:
        listed = paseo_json(["ls", "-a", "--json"])
        if not isinstance(listed, list):
            raise ValueError("ls não devolveu lista")
    except Exception as exc:  # PaseoError, ValueError...
        return [], wd._clean(str(exc))
    agents = []
    for raw in listed:
        agent_id = str(wd._field(raw, "id", "Id"))
        agent = {"id": agent_id, "provider": str(wd._field(raw, "provider", "Provider")),
                 "status": str(wd._field(raw, "status", "Status")), "age_days": None, "archived": None,
                 "pending_permissions": None, "_cwd": str(wd._field(raw, "cwd", "Cwd"))}
        try:
            info = paseo_json(["inspect", agent_id, "--json"])
            updated = wd._parse_ts(wd._field(info, "UpdatedAt", "updatedAt"))
            if updated is not None:
                agent["age_days"] = round((now - updated).total_seconds() / 86400, 2)
            agent["archived"] = wd._bool(wd._field(info, "Archived", "archived", default=False))
            pend = wd._field(info, "PendingPermissions", "pendingPermissions", default=None)
            agent["pending_permissions"] = len(pend) if isinstance(pend, list) else None
            agent["status"] = str(wd._field(info, "Status", "status", default=agent["status"]))
            agent["_cwd"] = str(wd._field(info, "Cwd", "cwd", default=agent["_cwd"]))
        except Exception:
            pass  # campos ficam None → plano marca DESCONHECIDO
        agents.append(agent)
    return agents, None


def build_scan(repo: str, home: Path, state_dir: Path, restricted_roots: list[Path]) -> dict:
    started = time.monotonic()
    now = _now()
    items = collect_worktrees(repo, home / ".paseo" / "worktrees")
    agents, paseo_error = collect_agents(now)
    mask_restricted(items, agents, restricted_roots)
    sizes = dir_sizes(home, state_dir)
    sizes["worktrees_escaneadas"] = sum(i["size_bytes"] or 0 for i in items if not i["is_main"])
    usage = shutil.disk_usage(home)
    return {
        "version": SCHEMA_VERSION,
        "generated_at": wd._iso(now),
        "paseo_ok": paseo_error is None,
        "paseo_error": paseo_error,
        "worktrees": items,
        "agents": agents,
        "launchd": launchctl_list(),
        "sizes_bytes": sizes,
        "disk": {"total_bytes": usage.total, "free_bytes": usage.free},
        "memory": memory_info(),
        "scan_seconds": round(time.monotonic() - started, 2),
    }


# ------------------------------------------------------------------ plano


WT_SCHEMA = {"path": "str", "is_main": "bool", "restricted": "bool", "branch": "str?", "tracked_changes": "int?",
             "untracked": "int?", "exclusive_commits": "int?", "unintegrated_commits": "int?", "locked": "bool?",
             "age_days": "num?", "size_bytes": "int?", "main_checkout": "str?", "error": "str?"}
AGENT_SCHEMA = {"id": "str", "provider": "str", "status": "str", "age_days": "num?", "pending_permissions": "int?",
                "restricted": "bool", "worktree": "str?"}
TOP_SCHEMA = {"generated_at": "str", "paseo_ok": "bool", "worktrees": "list", "agents": "list", "launchd": "list",
              "disk": "dict", "memory": "dict", "sizes_bytes": "dict"}
DISK_SCHEMA = {"free_bytes": "int", "total_bytes": "int"}
MEMORY_SCHEMA = {"pressure_level": "str?", "free_percentage": "int?", "swap_total_bytes": "int?", "swap_used_bytes": "int?"}
SIZES_SCHEMA = {k: "int?" for k in ("worktrees_escaneadas", "paseo_fora_worktrees", "claude", "codex", "ai_os_state",
                                    "gemini", "library_caches_informativo")}


def _kind_ok(value, kind: str) -> bool:
    nullable = kind.endswith("?")
    kind = kind.rstrip("?")
    if value is None:
        return nullable
    if kind in ("int", "num", "bool") and isinstance(value, bool) != (kind == "bool"):
        return False  # bool não vale como número e vice-versa
    return isinstance(value, {"str": str, "int": int, "num": (int, float), "bool": bool, "list": list,
                              "dict": dict}[kind])


def schema_problem(obj, schema: dict) -> str | None:
    if not isinstance(obj, dict):
        return "item não é objeto"
    for field, kind in schema.items():
        if field not in obj:
            return f"campo ausente: {field}"
        if not _kind_ok(obj[field], kind):
            return f"campo com tipo inválido: {field}"
    return None


def validate_scan(scan) -> None:
    """Falha com erro claro se a estrutura geral do scan não é a esperada. Itens ruins são tratados em classify."""
    if not isinstance(scan, dict):
        raise HygieneError("scan inválido: não é um objeto JSON")
    if scan.get("version") != SCHEMA_VERSION:
        raise HygieneError(f"scan inválido: versão {scan.get('version')!r} (esperada {SCHEMA_VERSION})")
    for name, schema in (("topo", TOP_SCHEMA),):
        problem = schema_problem(scan, schema)
        if problem:
            raise HygieneError(f"scan inválido ({name}): {problem}")
    for name in ("disk", "memory", "sizes_bytes"):
        problem = schema_problem(scan[name], {"disk": DISK_SCHEMA, "memory": MEMORY_SCHEMA, "sizes_bytes": SIZES_SCHEMA}[name])
        if problem:
            raise HygieneError(f"scan inválido ({name}): {problem}")


def _severity(klass: str) -> int:
    return {PRESERVAR: 2, DESCONHECIDO: 1, CANDIDATO: 0}[klass]


def classify_agent(agent: dict, days: float) -> tuple[str, str]:
    if agent["restricted"]:
        return PRESERVAR, "cwd restrito"
    status = agent["status"]
    if status == "running":
        return PRESERVAR, "agente ativo"
    if agent["pending_permissions"]:
        return PRESERVAR, "aguardando permissão"
    if status == "error":
        return DESCONHECIDO, "agente em erro: confira antes de decidir"
    if status not in ("idle", "closed"):
        return DESCONHECIDO, f"status '{wd._clean(status, 30)}' não reconhecido"
    if agent["age_days"] is None or agent["pending_permissions"] is None:
        return DESCONHECIDO, "inspect indisponível (idade ou pendências desconhecidas)"
    if agent["age_days"] <= days:
        return PRESERVAR, f"{status} há {agent['age_days']:.1f} d (<= {days:g} d)"
    return CANDIDATO, f"{status} há {agent['age_days']:.1f} d"


def classify_worktree(item: dict, linked: list[tuple[str, str]], paseo_ok: bool, days: float) -> tuple[str, list[str]]:
    why: list[str] = []
    if item["restricted"]:
        return PRESERVAR, ["projeto restrito"]
    if item["is_main"]:
        return PRESERVAR, ["checkout principal"]
    if item["locked"]:
        why.append("lock")
    if item["tracked_changes"]:
        why.append(f"{item['tracked_changes']} arquivo(s) alterado(s)")
    if item["untracked"]:
        why.append(f"{item['untracked']} arquivo(s) untracked")
    if item["unintegrated_commits"]:
        why.append(f"{item['unintegrated_commits']} commit(s) sem equivalente em outra ref")
    if why:
        return PRESERVAR, why
    if item["error"]:
        return DESCONHECIDO, [item["error"]]
    for field in ("locked", "tracked_changes", "untracked", "unintegrated_commits", "main_checkout"):
        if item[field] is None:  # não dá para provar: nunca vira candidato
            return DESCONHECIDO, [f"não foi possível verificar: {field}"]
    if not paseo_ok:
        return DESCONHECIDO, ["Paseo indisponível: não dá para saber se há agente usando"]
    for klass, reason in linked:
        if klass == PRESERVAR:
            return PRESERVAR, [f"agente vinculado: {reason}"]
    for klass, reason in linked:
        if klass == DESCONHECIDO:
            return DESCONHECIDO, [f"agente vinculado: {reason}"]
    if item["age_days"] is None:
        return DESCONHECIDO, ["idade desconhecida"]
    if item["age_days"] <= days:
        return PRESERVAR, [f"modificada há {item['age_days']:.1f} d (<= {days:g} d)"]
    return CANDIDATO, ["limpa, sem commit exclusivo, parada há %.1f d" % item["age_days"]]


def classify(scan: dict, days: float = DEFAULT_DAYS) -> list[dict]:
    """Itens malformados viram DESCONHECIDO, sem comando sugerido."""
    agents = scan["agents"]
    agent_bad = [schema_problem(a, AGENT_SCHEMA) for a in agents]
    own = [(DESCONHECIDO, f"item inconsistente no scan ({bad})") if bad else classify_agent(a, days)
           for a, bad in zip(agents, agent_bad)]
    results = []
    for n, item in enumerate(scan["worktrees"], 1):
        bad = schema_problem(item, WT_SCHEMA)
        if bad:
            results.append({"kind": "worktree", "name": f"<worktree #{n} inválida>", "class": DESCONHECIDO,
                            "why": [f"item inconsistente no scan ({bad})"], "commands": [], "bytes": 0, "size": None})
            continue
        linked = [own[i] for i, a in enumerate(agents) if not agent_bad[i] and a["worktree"] == item["path"]]
        linked += [own[i] for i, a in enumerate(agents) if agent_bad[i] and isinstance(a, dict) and a.get("worktree") == item["path"]]
        klass, why = classify_worktree(item, linked, scan["paseo_ok"], days)
        commands = []
        if klass == CANDIDATO:
            main = item["main_checkout"]
            commands.append(f"git -C {shlex.quote(main)} worktree remove {shlex.quote(item['path'])}")
            if item["branch"]:
                commands.append(f"git -C {shlex.quote(main)} branch -d {shlex.quote(item['branch'])}")
        results.append({"kind": "worktree", "name": item["path"], "class": klass, "why": why, "commands": commands,
                        "bytes": (item["size_bytes"] or 0) if klass == CANDIDATO else 0, "size": item["size_bytes"]})
    by_name = {r["name"]: r for r in results if r["kind"] == "worktree"}
    for n, (agent, (klass, reason)) in enumerate(zip(agents, own), 1):
        if agent_bad[n - 1]:
            results.append({"kind": "agente", "name": f"<agente #{n} inválido>", "class": klass, "why": [reason],
                            "commands": [], "bytes": 0, "provider": "?", "status": "?"})
            continue
        why = [reason]
        wk = by_name.get(agent["worktree"]) if agent["worktree"] else None
        if klass == CANDIDATO:
            if wk is not None:
                if wk["class"] != CANDIDATO:
                    klass, why = wk["class"], [f"worktree vinculada: {'; '.join(wk['why'])}"]
            else:
                klass, why = DESCONHECIDO, ["cwd fora das worktrees escaneadas: não dá para saber se há trabalho"]
        results.append({"kind": "agente", "name": agent["id"], "class": klass, "why": why,
                        "commands": [f"paseo delete {shlex.quote(agent['id'])}"] if klass == CANDIDATO else [],
                        "bytes": 0, "provider": agent["provider"], "status": agent["status"]})
    return results


def gb(value: int | None) -> str:
    return "n/d" if value is None else f"{value / (1 << 30):.2f} GB"


def render_plan(scan: dict, days: float = DEFAULT_DAYS) -> str:
    validate_scan(scan)
    results = classify(scan, days)
    count = {k: {PRESERVAR: 0, CANDIDATO: 0, DESCONHECIDO: 0} for k in ("worktree", "agente")}
    for r in results:
        count[r["kind"]][r["class"]] += 1
    est = sum(r["bytes"] for r in results)
    mem, disk, sizes = scan["memory"], scan["disk"], scan["sizes_bytes"]
    out = [f"# Plano de higiene (DRY-RUN) — {scan['generated_at']}", "",
           "> Nada foi apagado, movido ou podado. Os comandos abaixo são **sugestões**: confira cada um antes de rodar.", "",
           "## Resumo", "",
           f"Limite de idade: {days:g} dias. Paseo disponível: {'sim' if scan['paseo_ok'] else 'NÃO (worktrees ficam DESCONHECIDO)'}.", "",
           "| Recurso | PRESERVAR | CANDIDATO | DESCONHECIDO |", "|---|---|---|---|"]
    for kind in ("worktree", "agente"):
        c = count[kind]
        out.append(f"| {kind} | {c[PRESERVAR]} | {c[CANDIDATO]} | {c[DESCONHECIDO]} |")
    out += ["", f"Espaço recuperável **ESTIMADO** (soma das worktrees CANDIDATO, bytes em disco): {gb(est)} ({est} bytes).", "",
            "## Máquina", "",
            f"- Disco livre: {gb(disk['free_bytes'])} de {gb(disk['total_bytes'])}.",
            f"- Pressão de memória: {mem['pressure_level'] or 'n/d'}; memória livre: "
            f"{'n/d' if mem['free_percentage'] is None else str(mem['free_percentage']) + '%'}.",
            f"- Swap: {gb(mem['swap_used_bytes'])} usados de {gb(mem['swap_total_bytes'])}.",
            "", "Tamanho por classe:", "",
            f"- worktrees escaneadas (fora o checkout principal): {gb(sizes['worktrees_escaneadas'])}",
            f"- ~/.paseo fora de worktrees: {gb(sizes['paseo_fora_worktrees'])}",
            f"- ~/.claude: {gb(sizes['claude'])}", f"- ~/.codex: {gb(sizes['codex'])}",
            f"- estado do AI OS (inclui history): {gb(sizes['ai_os_state'])}", f"- ~/.gemini: {gb(sizes['gemini'])}",
            f"- ~/Library/Caches (só informativo, fora do escopo do AI OS): {gb(sizes['library_caches_informativo'])}",
            "", "Jobs launchd com.felipe: " + (", ".join(j["label"] for j in scan["launchd"]) or "nenhum"), ""]
    for klass in (CANDIDATO, DESCONHECIDO, PRESERVAR):
        rows = [r for r in results if r["class"] == klass]
        out += [f"## {klass} ({len(rows)})", ""]
        for r in rows:
            extra = f" [{r['provider']}, {r['status']}]" if r["kind"] == "agente" else ""
            size = ""
            if r["kind"] == "worktree":
                size = f" — {gb(r['size'])}"
            out.append(f"- {r['kind']} `{r['name']}`{extra}{size}: {'; '.join(r['why'])}")
            for cmd in r["commands"]:
                out.append(f"  - sugestão (NÃO executada): `{cmd}`")
        out.append("")
    return "\n".join(out)


# ------------------------------------------------------------------ CLI


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M")


def _write_private(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)


def _default_repo() -> str:
    common = _git(str(wd.REPO_ROOT), "rev-parse", "--path-format=absolute", "--git-common-dir")
    return str(Path(common.strip()).parent) if common else str(wd.REPO_ROOT)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_scan = sub.add_parser("scan", help="inventário em JSON")
    p_scan.add_argument("--out", help="arquivo de saída ('-' = stdout); padrão: <state>/higiene/scan-AAAAMMDD-HHMM.json")
    p_scan.add_argument("--repo", default=None, help="repo cujas worktrees registradas entram (padrão: este)")
    p_plan = sub.add_parser("plan", help="plano em Markdown")
    p_plan.add_argument("--scan", help="scan JSON existente (padrão: roda um scan novo, em memória)")
    p_plan.add_argument("--days", type=float, default=DEFAULT_DAYS, help="idade mínima em dias (padrão 7)")
    p_plan.add_argument("--out", help="arquivo de saída (padrão: stdout)")
    p_plan.add_argument("--repo", default=None)
    args = parser.parse_args(argv)

    home, state = Path.home(), wd._state_dir()
    try:
        if args.cmd == "plan" and args.scan:
            try:
                scan = json.loads(Path(args.scan).read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                raise HygieneError(f"não consegui ler o scan: {exc}") from exc
            validate_scan(scan)
        else:
            roots = wd.load_restricted_roots(wd.MEMORY_POLICY_PATH)
            scan = build_scan(args.repo or _default_repo(), home, state, roots)
        if args.cmd == "scan":
            text = json.dumps(scan, ensure_ascii=False, indent=2) + "\n"
            if args.out == "-":
                sys.stdout.write(text)
            else:
                target = Path(args.out) if args.out else state / "higiene" / f"scan-{_stamp()}.json"
                _write_private(target, text)
                print(f"scan salvo em {target}", file=sys.stderr)
        else:
            text = render_plan(scan, args.days) + "\n"
            if args.out:
                _write_private(Path(args.out), text)
                print(f"plano salvo em {args.out}", file=sys.stderr)
            else:
                sys.stdout.write(text)
    except (HygieneError, wd.PolicyError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"hygiene: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
