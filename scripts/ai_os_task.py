#!/usr/bin/env python3
"""Registro local de tarefas do AI OS, somente acréscimos e biblioteca padrão."""

import argparse
import fcntl
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

if sys.version_info < (3, 11):
    sys.exit("requer Python >= 3.11; rode com /opt/homebrew/bin/python3")

from paseo_watchdog import PolicyError, _clean, is_restricted, load_restricted_roots

VERSION = "1.0.0"
REPO = Path(__file__).resolve().parents[1]
TASK_ID = re.compile(r"T-\d{8}-\d{2,}")


def read_events(history):
    """Ignora linhas interrompidas; a próxima escrita preserva a separação."""
    events = []
    for path in sorted(history.glob("tasks-????-??.jsonl")):
        with path.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                if isinstance(event, dict) and TASK_ID.fullmatch(str(event.get("task_id", ""))):
                    events.append(event)
    return events


def task_states(events):
    tasks = {}
    for event in events:
        task_id = event["task_id"]
        kind = event.get("type")
        if kind == "task.opened":
            tasks[task_id] = {**event, "status": "open", "agents": []}
        elif task_id in tasks:
            task = tasks[task_id]
            if kind == "task.linked":
                task["agents"].append({"agent_id": event.get("agent_id"), "role": event.get("role")})
            elif kind == "task.closed":
                task.update(status="closed", verdict=event.get("verdict"))
            elif kind == "task.reopened":
                task.update(status="em_reavaliacao", verdict=None)
    return tasks


def append_event(history, now, event):
    """Mesma proteção do vigia: separa a linha parcial antes do append."""
    path = history / f"tasks-{now.astimezone():%Y-%m}.jsonl"
    line = (json.dumps(event, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    with path.open("a+b") as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell():
            handle.seek(-1, os.SEEK_END)
            if handle.read(1) != b"\n":
                line = b"\n" + line
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())


def parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--cwd", default=argparse.SUPPRESS, help="projeto da tarefa (obrigatório em open)")
    common.add_argument("--state-dir", default=argparse.SUPPRESS, help="estado local do AI OS")
    common.add_argument("--restricted-config", default=argparse.SUPPRESS, help="política de caminhos restritos")
    ap = argparse.ArgumentParser(description=__doc__, parents=[common])
    subs = ap.add_subparsers(dest="command", required=True)
    op = subs.add_parser("open", parents=[common], help="abre tarefa")
    op.add_argument("objective")
    op.add_argument("--risk", choices=("low", "medium", "high"), default="low")
    op.add_argument("--category")
    link = subs.add_parser("link", parents=[common], help="vincula agente")
    link.add_argument("task_id")
    link.add_argument("agent_id")
    link.add_argument("--role", choices=("exec", "review", "fix"), default="exec")
    close = subs.add_parser("close", parents=[common], help="registra veredito do orquestrador")
    close.add_argument("task_id")
    close.add_argument("verdict", choices=("aceito", "retrabalho", "rejeitado"))
    close.add_argument("--nota")
    reopen = subs.add_parser("reopen", parents=[common], help="reabre tarefa")
    reopen.add_argument("task_id")
    reopen.add_argument("--motivo", required=True)
    ls = subs.add_parser("list", parents=[common], help="lista tarefas em JSON")
    ls.add_argument("--open", action="store_true")
    return ap


def main(argv=None):
    ap = parser()
    args = ap.parse_args(argv)
    state = Path(getattr(args, "state_dir", os.environ.get("AI_OS_STATE_DIR", "~/.local/state/ai-os"))).expanduser()
    history = state / "history"
    try:
        if args.command == "open":
            if not getattr(args, "cwd", "").strip():
                raise ValueError("open requer --cwd do projeto da tarefa")
            policy = Path(getattr(args, "restricted_config", REPO / "config/ai-os-memory.toml")).expanduser()
            if not policy.is_file():
                raise PolicyError("configuração de caminhos restritos ausente ou ilegível")
            cwd = Path(args.cwd).expanduser().resolve()
            restricted = is_restricted(str(cwd), load_restricted_roots(policy))
        history.mkdir(parents=True, exist_ok=True)
        # Um lock protege a sequência diária e as transições entre processos.
        with (history / ".tasks.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            events = read_events(history)
            tasks = task_states(events)
            if args.command == "list":
                print(json.dumps([tasks[k] for k in sorted(tasks)
                                  if not args.open or tasks[k]["status"] != "closed"], ensure_ascii=False))
                return 0
            now = datetime.now(timezone.utc)
            stamp = now.isoformat(timespec="seconds").replace("+00:00", "Z")
            fields = {}
            if args.command == "open":
                objective = "restrito" if restricted else _clean(args.objective, 120)
                if not objective:
                    raise ValueError("objetivo vazio")
                prefix = f"T-{now.astimezone():%Y%m%d}-"
                seq = max((int(k[len(prefix):]) for k in tasks if k.startswith(prefix)), default=0) + 1
                task_id = f"{prefix}{seq:02d}"
                fields = {"objective": objective, "risk": args.risk,
                          "category": "restrito" if restricted and args.category else _clean(args.category, 120) or None,
                          "project": "restrito" if restricted else _clean(cwd.name, 120)}
            else:
                task_id = args.task_id
                if not TASK_ID.fullmatch(task_id) or task_id not in tasks:
                    raise ValueError("tarefa inexistente")
                task = tasks[task_id]
                closed = task["status"] == "closed"
                if args.command == "reopen":
                    if not closed:
                        raise ValueError("tarefa já está aberta")
                    reason = "restrito" if task.get("project") == "restrito" else _clean(args.motivo, 120)
                    if not reason:
                        raise ValueError("motivo vazio")
                    fields = {"reason": reason}
                elif closed:
                    raise ValueError("tarefa encerrada; use reopen antes")
                elif args.command == "link":
                    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,199}", args.agent_id):
                        raise ValueError("agent_id inválido")
                    if any(agent["agent_id"] == args.agent_id for agent in task["agents"]):
                        raise ValueError("agente já vinculado a esta tarefa")
                    if any(other["status"] != "closed" and any(
                            agent["agent_id"] == args.agent_id for agent in other["agents"])
                           for other in tasks.values()):
                        raise ValueError("agente já vinculado a outra tarefa aberta")
                    fields = {"agent_id": args.agent_id, "role": args.role}
                elif args.command == "close":
                    fields = {"verdict": args.verdict}
                    if args.nota:
                        fields["note"] = "restrito" if task.get("project") == "restrito" else _clean(args.nota, 120)
            kind = {"open": "opened", "link": "linked", "close": "closed", "reopen": "reopened"}[args.command]
            event = {"schema_version": 1, "type": f"task.{kind}", "occurred_at": stamp,
                     "observed_at": stamp, "source": "ai-os-task", "source_version": VERSION,
                     "confidence": "observed", "task_id": task_id, **fields}
            if args.command == "open" and fields["category"] is None:
                event["reason"] = "categoria não informada"
            append_event(history, now, event)
        print(task_id)
        return 0
    except (OSError, ValueError, PolicyError) as exc:
        ap.exit(2, f"erro: {exc}\n")


if __name__ == "__main__":
    sys.exit(main())
