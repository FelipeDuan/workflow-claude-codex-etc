"""Leitura resumida de processos associados a worktrees; nunca encerra processos."""

from __future__ import annotations

import getpass
import os
import re
import subprocess
import time
from pathlib import Path


def _run(command: list[str], timeout: float = 3) -> str | None:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout,
                                env={**os.environ, "LC_ALL": "C"})
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode == 0:
        return result.stdout
    # lsof usa status 1 para "nenhum descritor encontrado"; saída/erro vazio
    # diferencia isso de permissões negadas, falha real ou timeout.
    if (Path(command[0]).name == "lsof" and result.returncode == 1
            and not result.stdout.strip() and not result.stderr.strip()):
        return ""
    return None


def _summary(command: str) -> str:
    """Retorna só nome do executável e, nos servidores conhecidos, subcomando."""
    tokens = re.findall(r"[^\s]+", command)
    if not tokens:
        return "desconhecido"
    names = [Path(token.strip("'\"" )).name for token in tokens]
    lowered = [name.lower() for name in names]
    for executable in ("astro", "next", "vite"):
        if executable in lowered:
            index = lowered.index(executable)
            if executable == "astro" and index + 1 < len(names) and names[index + 1] in {"dev", "preview"}:
                return f"astro {names[index + 1]}"
            if executable == "next" and index + 1 < len(names) and names[index + 1] in {"dev", "start"}:
                return f"next {names[index + 1]}"
            if executable == "vite" and index + 1 < len(names) and names[index + 1] == "build":
                return "vite build"
            if executable == "vite" and index + 1 < len(names) and names[index + 1] == "dev":
                return "vite dev"
            return executable
    return names[0]


def _parse_ps(output: str | None) -> dict[int, dict]:
    processes = {}
    if output is None:
        return processes
    # macOS ps lstart has five whitespace-delimited fields; the day may be padded.
    pattern = re.compile(r"^\s*(\d+)\s+(\d+)\s+(\w+\s+\w+\s+\d+\s+\d\d:\d\d:\d\d\s+\d{4})\s+(\d+)\s+(.*)$")
    for line in output.splitlines():
        match = pattern.match(line)
        if not match:
            continue
        pid, ppid, started, rss, command = match.groups()
        processes[int(pid)] = {"pid": int(pid), "ppid": int(ppid), "start_time": started.strip(),
                               "rss_bytes": int(rss) * 1024, "command": _summary(command)}
    return processes


def _parse_cwds(output: str | None) -> dict[int, str]:
    result, pid = {}, None
    if output is None:
        return result
    for line in output.splitlines():
        if line.startswith("p") and line[1:].isdigit():
            pid = int(line[1:])
        elif line.startswith("n") and pid is not None:
            result[pid] = line[1:]
            pid = None
    return result


def _parse_tcp(output: str | None) -> tuple[dict[int, set[int]], dict[int, int], dict[int, int | None]]:
    """Lê TST por fd. Sem TST num socket TCP, atividade é desconhecida."""
    listen: dict[int, set[int]] = {}
    established: dict[int, int] = {}
    active: dict[int, int | None] = {}
    if output is None:
        return listen, established, active
    pid: int | None = None
    fd: str | None = None
    name: str | None = None
    state: str | None = None
    socket_rows: list[tuple[int, str | None, str | None, str | None]] = []

    def finish_socket() -> None:
        nonlocal fd, name, state
        if pid is not None and fd is not None:
            socket_rows.append((pid, fd, name, state))
        fd, name, state = None, None, None

    for line in output.splitlines():
        if line.startswith("p") and line[1:].isdigit():
            finish_socket()
            pid = int(line[1:])
        elif line.startswith("f"):
            finish_socket()
            fd = line[1:]
        elif line.startswith("n") and pid is not None:
            name = line[1:]
        elif line.startswith("TST="):
            state = line[4:].strip().upper()
    finish_socket()

    # lsof pode listar o mesmo socket em mais de um fd (dup); conte sockets,
    # não descritores. Nome ausente e estado ausente nunca provam ociosidade.
    seen: set[tuple[int, str, str]] = set()
    unknown: set[int] = set()
    for socket_pid, socket_fd, socket_name, socket_state in socket_rows:
        if socket_state is None:
            unknown.add(socket_pid)
            continue
        key = (socket_pid, socket_name or f"fd:{socket_fd}", socket_state)
        if key in seen:
            continue
        seen.add(key)
        if socket_state == "LISTEN":
            match = re.search(r":(\d+)$", socket_name or "")
            if match:
                listen.setdefault(socket_pid, set()).add(int(match.group(1)))
        else:
            active[socket_pid] = active.get(socket_pid, 0) + 1
            if socket_state == "ESTABLISHED":
                established[socket_pid] = established.get(socket_pid, 0) + 1
    for socket_pid, _, _, _ in socket_rows:
        active.setdefault(socket_pid, 0)
    for socket_pid in unknown:
        active[socket_pid] = None
    return listen, established, active


def _within(path: str, root: str) -> bool:
    try:
        return os.path.commonpath((os.path.realpath(path), os.path.realpath(root))) == os.path.realpath(root)
    except (OSError, ValueError):
        return False


def _ancestor_pids(processes: dict[int, dict], pid: int) -> set[int]:
    parents = {proc_id: row["ppid"] for proc_id, row in processes.items()}
    result, current = {pid}, pid
    while current in parents:
        parent = parents[current]
        if parent <= 1 or parent in result:
            break
        result.add(parent)
        current = parent
    return result


def scan_processes(worktrees: list[dict], *, target: str | None = None, exclude_pid: int | None = None,
                   include_tcp: bool = True, timeout: float = 3) -> tuple[list[dict], float, str | None]:
    """Escaneia processos do usuário em worktrees. O retorno inclui custo em ms e erro."""
    started = time.perf_counter()
    uid = str(os.getuid())
    ps = _run(["ps", "-U", uid, "-o", "pid=,ppid=,lstart=,rss=,command="], timeout)
    # Uma chamada global de cwd evita uma invocação lsof por PID.
    user = getpass.getuser()
    cwd_out = _run(["lsof", "-nP", "-a", "-u", user, "-d", "cwd", "-Fpcn"], timeout)
    tcp_out = _run(["lsof", "-nP", "-a", "-u", user, "-iTCP", "-FpnfT"], timeout) if include_tcp else None
    rows, cwds = _parse_ps(ps), _parse_cwds(cwd_out)
    listen, established, active = _parse_tcp(tcp_out) if include_tcp else ({}, {}, {})
    error = None if ps is not None and cwd_out is not None and (not include_tcp or tcp_out is not None) else "ps/lsof indisponível"
    excluded = _ancestor_pids(rows, exclude_pid) if exclude_pid is not None else set()
    result = []
    for pid, row in rows.items():
        cwd = cwds.get(pid)
        if not cwd:
            continue
        matches = [wt for wt in worktrees
                   if not os.path.islink(wt.get("raw_path", wt["path"]))
                   and _within(cwd, wt.get("raw_path", wt["path"]))]
        owner = max(matches, key=lambda wt: len(wt.get("raw_path", wt["path"]))) if matches else None
        if owner is None or (target and not _within(cwd, target)) or pid in excluded:
            continue
        result.append({**row, "cwd": cwd, "worktree": owner.get("display_path", owner.get("path")),
                       "listen_ports": sorted(listen.get(pid, set())),
                       "established_connections": established.get(pid, 0) if include_tcp and error is None else None,
                       "active_connections": active.get(pid, 0) if include_tcp and error is None else None,
                       "is_main": owner.get("is_main", False),
                       "is_paseo_worktree": owner.get("is_paseo_worktree", False)})
    return result, round((time.perf_counter() - started) * 1000, 3), error


def process_start_times(pids: set[int]) -> tuple[dict[int, str] | None, float]:
    """Revalida identidade de PIDs de um scan salvo antes de montar o plano."""
    started = time.perf_counter()
    output = _run(["ps", "-U", str(os.getuid()), "-o", "pid=,ppid=,lstart=,rss=,command="])
    if output is None:
        return None, round((time.perf_counter() - started) * 1000, 3)
    current = _parse_ps(output)
    return {pid: row["start_time"] for pid, row in current.items() if pid in pids}, round((time.perf_counter() - started) * 1000, 3)
