#!/usr/bin/env python3
"""paseo_watchdog.py — vigia dos agentes do Paseo.

Uma execução (one-shot; o agendamento é do launchd). Lê `paseo ls -a --json`,
`paseo inspect <id> --json`, `paseo permit ls --json` e `paseo schedule
ls/logs`, e detecta:

  aguardando_aprovacao  pedido pendente há mais de PENDING_MIN (padrão 2 min).
                        O `permit ls` não traz horário, então o primeiro
                        avistamento fica em watchdog-state.json.
  parado                status "running" com UpdatedAt do inspect há mais de
                        STUCK_MIN (padrão 10 min). Critério: `paseo logs --json`
                        não devolve JSON (sai em texto), então o sinal
                        confiável de atividade é o UpdatedAt do inspect, que o
                        Paseo atualiza a cada evento do agente.
  erro                  status "error" (captura a mensagem, inclusive limite de
                        uso com horário de retorno) ou "closed" quando o agente
                        estava "running" na execução anterior (I-21: daemon
                        reiniciado no meio da tarefa).
  concluido             "idle"/"closed" normal, arquivado é ignorado.

Autoaprovação: primeira regra que casar em config/paseo-watchdog-policy.toml.
`deny` nunca aprova; `allow` só aprova com cwd em allowed_roots e fora de
projeto restrito (config/ai-os-memory.toml e marcador .ai-memory.toml). O resto
vira `notify`. Nada é autoaprovado sem regra.

Notificação: `osascript -e 'display notification ...'`, no máximo uma vez a
cada DEDUP_MIN (10 min) por chave. Estado: ~/.local/state/ai-os/
(watchdog-state.json, agentes.json, watchdog.log).

Uso:
  python3 scripts/paseo_watchdog.py [--dry-run] [--once]

  --dry-run  não aprova, não notifica e não grava estado; só mostra.
  --once     uma execução (padrão; existe para deixar o LaunchAgent explícito).

Só biblioteca padrão, Python >= 3.11 (tomllib). A CLI `paseo` roda por
subprocess com timeout, sem shell=True.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = REPO_ROOT / "config" / "paseo-watchdog-policy.toml"
MEMORY_POLICY_PATH = REPO_ROOT / "config" / "ai-os-memory.toml"

PENDING_MIN = 2
STUCK_MIN = 10
DEDUP_MIN = 10
CMD_TIMEOUT = 20
DESC_LIMIT = 200
STATE_KEEP_DAYS = 7

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")
_SECRET = re.compile(
    r"(?i)\b(token|password|passwd|secret|api[_-]?key|authorization)\b"
    r"(\s*[=:]\s*)(\"[^\"]*\"|'[^']*'|\S+)"
)
_STATUS_PRIORITY = {
    "aguardando_aprovacao": 0,
    "erro": 1,
    "parado": 2,
    "trabalhando": 3,
    "concluido": 4,
}


class PaseoError(RuntimeError):
    """Falha ao rodar ou interpretar a CLI do Paseo."""


class PolicyError(RuntimeError):
    """Política ausente ou inválida; nada deve ser aprovado."""


@dataclass
class Rule:
    action: str
    name: re.Pattern | None
    description: re.Pattern | None
    reason: str


@dataclass
class Policy:
    rules: list[Rule]
    allowed_roots: list[Path]


# ------------------------------------------------------------------ utilidades


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse_ts(value) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def _clean(value, limit: int = DESC_LIMIT) -> str:
    """Remove controles, colapsa espaços, mascara segredos e corta em `limit`."""
    text = _CONTROL.sub("", str(value if value is not None else ""))
    text = re.sub(r"\s+", " ", text).strip()
    text = _SECRET.sub(lambda m: f"{m.group(1)}{m.group(2)}***", text)
    return text[:limit]


def _age_text(delta: timedelta | None) -> str:
    if delta is None:
        return "—"
    minutes = max(0, int(delta.total_seconds() // 60))
    if minutes < 60:
        return f"{minutes} min"
    hours, minutes = divmod(minutes, 60)
    if hours < 24:
        return f"{hours} h" + (f" {minutes} min" if minutes else "")
    days, hours = divmod(hours, 24)
    return f"{days} d" + (f" {hours} h" if hours else "")


def parse_json(text: str):
    """json.loads depois de remover caracteres de controle (já vimos JSON sujo)."""
    cleaned = _CONTROL.sub("", str(text or "")).lstrip("\ufeff")
    return json.loads(cleaned)


def _field(data, *names, default=""):
    if isinstance(data, dict):
        for name in names:
            if name in data and data[name] is not None:
                return data[name]
    return default


def _bool(value) -> bool:
    return value is True or str(value).lower() in {"true", "1", "yes"}


# ------------------------------------------------------------------ CLI paseo


def run_paseo(args: list[str], check: bool = True) -> str:
    """Roda `paseo` sem shell, com timeout. Devolve stdout."""
    cmd = ["paseo", *args]
    try:
        completed = subprocess.run(
            cmd, capture_output=True, text=True, timeout=CMD_TIMEOUT
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        if check:
            raise PaseoError(f"{' '.join(cmd)}: {exc}") from exc
        return ""
    if check and completed.returncode != 0:
        detail = _clean(completed.stderr or completed.stdout)
        raise PaseoError(f"{' '.join(cmd)}: rc={completed.returncode} {detail}")
    return completed.stdout


def paseo_json(args: list[str]):
    try:
        return parse_json(run_paseo(args))
    except ValueError as exc:
        raise PaseoError(f"{' '.join(args)}: JSON inválido ({exc})") from exc


# ------------------------------------------------------------------ política


def load_policy(path: Path) -> Policy:
    try:
        with open(path, "rb") as handle:
            data = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise PolicyError(f"política {path}: {exc}") from exc

    rules: list[Rule] = []
    for index, raw in enumerate(data.get("rules") or [], start=1):
        action = str(raw.get("action", "")).strip().lower()
        if action not in {"allow", "deny", "notify"}:
            raise PolicyError(f"política {path}: regra {index} com action inválida '{action}'")
        try:
            name = re.compile(str(raw["name"]), re.IGNORECASE) if raw.get("name") else None
            description = (
                re.compile(str(raw["description"]), re.IGNORECASE | re.DOTALL)
                if raw.get("description")
                else None
            )
        except re.error as exc:
            raise PolicyError(f"política {path}: regra {index} com regex inválida ({exc})") from exc
        rules.append(Rule(action, name, description, _clean(raw.get("reason", ""))))

    roots = [
        Path(os.path.expanduser(str(item))).resolve()
        for item in (data.get("allowed_roots") or [])
        if str(item).strip()
    ]
    if not rules:
        raise PolicyError(f"política {path}: nenhuma regra")
    return Policy(rules, roots)


def load_restricted_roots(path: Path) -> list[Path]:
    """Raízes restritas de config/ai-os-memory.toml; política ilegível falha fechado."""
    if not path.exists():
        return []
    try:
        with open(path, "rb") as handle:
            data = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise PolicyError(f"projetos restritos {path}: {exc}") from exc
    paths = (data.get("restricted") or {}).get("paths") or []
    return [Path(os.path.expanduser(str(item))).resolve() for item in paths if str(item).strip()]


def _within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _marker_restricted(cwd: Path) -> bool:
    """Marcador .ai-memory.toml entre o cwd e a raiz do usuário."""
    home = Path.home().resolve()
    current = cwd
    for _ in range(8):
        marker = current / ".ai-memory.toml"
        if marker.is_file():
            try:
                with open(marker, "rb") as handle:
                    data = tomllib.load(handle)
            except (OSError, tomllib.TOMLDecodeError):
                return False
            return str(data.get("workspace", "")).lower() == "restrito"
        if current == home or current.parent == current:
            break
        current = current.parent
    return False


def cwd_allowed(cwd: str, policy: Policy, restricted: list[Path]) -> tuple[bool, str]:
    if not cwd:
        return False, "cwd desconhecido"
    path = Path(os.path.expanduser(cwd))
    try:
        resolved = path.resolve()
    except OSError:
        resolved = path.absolute()
    for root in restricted:
        if _within(resolved, root):
            return False, "projeto restrito (config/ai-os-memory.toml)"
    if _marker_restricted(resolved):
        return False, "projeto restrito (.ai-memory.toml)"
    for root in policy.allowed_roots:
        if _within(resolved, root):
            return True, str(root)
    return False, "cwd fora de allowed_roots"


def match_rule(policy: Policy, name: str, description: str) -> Rule | None:
    for rule in policy.rules:
        if rule.name and not rule.name.search(name):
            continue
        if rule.description and not rule.description.search(description):
            continue
        return rule
    return None


def decide(policy: Policy, name: str, description: str, cwd: str, restricted: list[Path]) -> tuple[str, str]:
    """Primeira regra que casa; allow exige cwd permitido."""
    rule = match_rule(policy, name, description)
    if rule is None:
        return "notify", "sem regra na política: decisão humana"
    if rule.action != "allow":
        return rule.action, rule.reason or f"regra {rule.action}"
    allowed, why = cwd_allowed(cwd, policy, restricted)
    if not allowed:
        return "notify", f"{rule.reason or 'allow'}, mas {why}"
    return "allow", rule.reason or "leitura/inspeção"


# ------------------------------------------------------------------ estado


def _state_dir() -> Path:
    override = os.environ.get("AI_OS_STATE_DIR")
    if override:
        return Path(os.path.expanduser(override))
    return Path.home() / ".local" / "state" / "ai-os"


def _empty_state() -> dict:
    return {"version": 1, "permissions": {}, "notifications": {}, "agents": {}}


def load_state(path: Path) -> dict:
    try:
        data = parse_json(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("estado não é objeto")
    except (OSError, ValueError):
        return _empty_state()
    for key in ("permissions", "notifications", "agents"):
        if not isinstance(data.get(key), dict):
            data[key] = {}
    return data


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp{os.getpid()}")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def prune_state(state: dict, now: datetime) -> None:
    cutoff = now - timedelta(days=STATE_KEEP_DAYS)
    state["notifications"] = {
        key: value
        for key, value in state["notifications"].items()
        if (_parse_ts(value) or cutoff) >= cutoff
    }


# ------------------------------------------------------------------ notificação / log


def _applescript_string(text: str) -> str:
    return _clean(text, 220).replace("\\", "\\\\").replace('"', '\\"')


def notify(state: dict, now: datetime, key: str, title: str, message: str, dry_run: bool) -> bool:
    """Notifica no macOS respeitando a janela de dedup. return: notificou agora?"""
    last = _parse_ts(state["notifications"].get(key))
    if last is not None and now - last < timedelta(minutes=DEDUP_MIN):
        return False
    title = _clean(title, 60)
    message = _clean(message, 200)
    if dry_run:
        print(f"[dry-run] notificaria: {title} — {message}")
        return False
    script = f'display notification "{_applescript_string(message)}" with title "{_applescript_string(title)}"'
    try:
        subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return False
    state["notifications"][key] = _iso(now)
    return True


def log_event(path: Path, now: datetime, event: str, **fields) -> None:
    parts = [_iso(now), event]
    parts += [f"{key}={_clean(value)}" for key, value in fields.items() if value not in (None, "")]
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(" ".join(parts) + "\n")
    except OSError:
        pass


# ------------------------------------------------------------------ leitura do Paseo


def _provider_label(inspect: dict, listed: dict) -> str:
    provider = str(_field(inspect, "Provider", "provider", default=""))
    model = str(_field(inspect, "Model", "model", default=""))
    if model and provider and not model.startswith(f"{provider}/"):
        return f"{provider}/{model}"
    return model or provider or str(_field(listed, "provider", default=""))


def _error_message(inspect: dict) -> str:
    for key in ("Error", "LastError", "error", "lastError", "StatusMessage", "statusMessage", "Message", "message"):
        value = inspect.get(key) if isinstance(inspect, dict) else None
        if isinstance(value, dict):
            value = _field(value, "message", "Message", "detail", "Detail")
        if value:
            return _clean(value)
    return ""


def _limit_hint(message: str) -> str:
    if re.search(r"(?i)usage limit|limit reached|quota|rate limit|resets?|try again|retry after", message):
        return "limite de uso"
    return ""


def _permit_name(permit: dict) -> str:
    return _clean(_field(permit, "name", "Name", "tool", "Tool"), 80)


def _permit_description(permit: dict) -> str:
    return _clean(_field(permit, "description", "Description"))


def _schedule_failure(entry: dict) -> str:
    if not isinstance(entry, dict):
        return ""
    status = str(_field(entry, "status", "state", "result", "lastRunStatus", default="")).lower()
    success = _field(entry, "success", "ok", default=None)
    error = _field(entry, "error", "Error", "lastError", default="")
    if success is False:
        return _clean(error or f"status {status or 'falhou'}") or "run falhou"
    if status in {"failed", "failure", "error", "errored", "timeout", "cancelled", "canceled"}:
        return _clean(error or f"status {status}") or "run falhou"
    if error and status not in {"success", "ok", "completed", "finished", "done"}:
        return _clean(error)
    return ""


def _run_entries(payload) -> list:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("runs", "logs", "entries", "items", "history"):
            if isinstance(payload.get(key), list):
                return payload[key]
    return []


def _error_status_from_logs(agent_id: str) -> str:
    """Mensagem de erro: inspect não traz; `logs --json` sai texto, então usa tail."""
    text = run_paseo(["logs", agent_id, "--tail", "20"], check=False)
    lines = [_clean(line) for line in _CONTROL.sub("", text).splitlines() if line.strip()]
    return lines[-1] if lines else ""


# ------------------------------------------------------------------ execução


def _classify(inspect: dict, pending: list[dict], now: datetime, previous: str) -> tuple[str, str, datetime | None]:
    """Devolve (status real, motivo, instante de referência para 'há quanto tempo')."""
    raw = str(_field(inspect, "Status", "status", default="")).lower()
    updated = _parse_ts(_field(inspect, "UpdatedAt", "updatedAt", default=""))
    if pending:
        oldest = min((_parse_ts(item["first_seen"]) or now for item in pending), default=now)
        first = pending[0]
        detail = _permit_name(first) or "permissão"
        description = _permit_description(first)
        if description and description != "-":
            detail = f"{detail}: {description}"
        extra = f" (+{len(pending) - 1})" if len(pending) > 1 else ""
        decision = str(first.get("_decision", ""))
        why = str(first.get("_reason", ""))
        if decision == "deny":
            tail = f" — política deny: {why}" if why else " — política deny"
        elif why:
            tail = f" — {why}"
        else:
            tail = ""
        return "aguardando_aprovacao", f"pedido pendente {detail}{extra}{tail}", oldest
    if raw == "error":
        agent_id = str(_field(inspect, "Id", "id", default=""))
        message = _error_message(inspect) or (_error_status_from_logs(agent_id) if agent_id else "")
        hint = _limit_hint(message)
        reason = f"{hint}: {message}" if hint and message else (message or "status error sem mensagem")
        return "erro", reason, updated
    if raw == "closed":
        if previous in {"running", "trabalhando"} and not _bool(_field(inspect, "Archived", "archived", default=False)):
            return "erro", "fechado durante a execução (possível reinício do daemon); conferir o worktree", updated
        return "concluido", "encerrado", updated
    if raw == "running":
        if updated is not None and (now - updated) >= timedelta(minutes=STUCK_MIN):
            return "parado", f"running sem atividade nova há {_age_text(now - updated)}", updated
        return "trabalhando", "atividade recente", updated
    if raw in {"idle", "completed", "done", "finished"}:
        return "concluido", "sem tarefa em andamento", updated
    if raw in {"stopped", "paused", "paused_waiting"}:
        return "parado", f"status {raw}", updated
    return "parado", f"status desconhecido '{raw or '?'}'", updated


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Vigia dos agentes do Paseo.")
    parser.add_argument("--dry-run", action="store_true", help="não aprova, não notifica, não grava estado")
    parser.add_argument("--once", action="store_true", help="uma execução (padrão)")
    args = parser.parse_args(argv)

    now = _now()
    state_dir = _state_dir()
    state_path = state_dir / "watchdog-state.json"
    snapshot_path = state_dir / "agentes.json"
    log_path = state_dir / "watchdog.log"
    state = load_state(state_path)

    try:
        policy = load_policy(POLICY_PATH)
        restricted = load_restricted_roots(MEMORY_POLICY_PATH)
    except PolicyError as exc:
        message = _clean(str(exc))
        print(f"paseo_watchdog: {message}", file=sys.stderr)
        if not args.dry_run:
            log_event(log_path, now, "policy_error", detalhe=message)
            notify(state, now, "policy:error", "Paseo · vigia", f"política inválida: {message}", False)
            write_json(state_path, state)
        return 1

    try:
        listed = paseo_json(["ls", "-a", "--json"])
        if not isinstance(listed, list):
            raise PaseoError("paseo ls: JSON não é lista")
        permits = paseo_json(["permit", "ls", "--json"])
        if not isinstance(permits, list):
            raise PaseoError("paseo permit ls: JSON não é lista")
    except PaseoError as exc:
        message = _clean(str(exc))
        print(f"paseo_watchdog: {message}", file=sys.stderr)
        if not args.dry_run:
            log_event(log_path, now, "paseo_error", detalhe=message)
            notify(state, now, "paseo:error", "Paseo · vigia", f"CLI falhou: {message}", False)
            write_json(state_path, state)
        return 1

    inspects: dict[str, dict] = {}
    for item in listed:
        agent_id = str(_field(item, "Id", "id", "shortId", default=""))
        if not agent_id:
            continue
        try:
            inspect = paseo_json(["inspect", agent_id, "--json"])
            if not isinstance(inspect, dict):
                raise PaseoError("inspect: JSON não é objeto")
        except PaseoError as exc:
            inspect = {
                "Id": agent_id,
                "Name": _field(item, "name", default=agent_id),
                "Status": _field(item, "status", default=""),
                "Cwd": _field(item, "cwd", default=""),
                "_inspect_error": _clean(str(exc)),
            }
        if _bool(_field(inspect, "Archived", "archived", default=False)):
            continue
        inspects[str(_field(inspect, "Id", "id", default=agent_id))] = inspect

    # -- permissões: primeiro avistamento, então autoaprovação ---------------
    approved: set[str] = set()
    pending_permissions: list[dict] = []
    for permit in permits:
        request_id = str(_field(permit, "id", "Id", default=""))
        if not request_id:
            continue
        entry = state["permissions"].get(request_id)
        if not isinstance(entry, dict) or _parse_ts(entry.get("first_seen")) is None:
            entry = {"first_seen": _iso(now), "agent": str(_field(permit, "agentId", "AgentId", default=""))}
            state["permissions"][request_id] = entry
        pending_permissions.append({**permit, "first_seen": entry["first_seen"]})
    keep = {str(_field(permit, "id", "Id", default="")) for permit in permits}
    state["permissions"] = {key: value for key, value in state["permissions"].items() if key in keep}

    for permit in pending_permissions:
        request_id = str(_field(permit, "id", "Id", default=""))
        agent_id = str(_field(permit, "agentId", "AgentId", default=""))
        inspect = inspects.get(agent_id)
        name = _permit_name(permit)
        description = _permit_description(permit)
        if inspect is None:
            permit["_decision"] = "notify"
            permit["_reason"] = "agente fora da lista (arquivado?)"
            continue
        cwd = str(_field(inspect, "Cwd", "cwd", default=""))
        action, reason = decide(policy, name, description, cwd, restricted)
        permit["_decision"] = action
        permit["_reason"] = reason
        if action != "allow":
            continue
        label = f"{_field(inspect, 'Name', 'name', default=agent_id)} [{name}]"
        if args.dry_run:
            print(f"[dry-run] aprovaria {label}: {description or name} ({reason})")
            approved.add(request_id)
            continue
        try:
            run_paseo(["permit", "allow", agent_id, request_id])
        except PaseoError as exc:
            message = _clean(str(exc))
            log_event(log_path, now, "permit_error", agente=agent_id, pedido=request_id, detalhe=message)
            notify(state, now, f"permit-error:{request_id}", "Paseo · vigia", f"falhou ao aprovar {label}: {message}", False)
            continue
        approved.add(request_id)
        print(f"paseo_watchdog: aprovado {label}: {description or name}")
        log_event(log_path, now, "permit_allow", agente=agent_id, pedido=request_id, ferramenta=name,
                  detalhe=description, motivo=reason)

    pending_by_agent: dict[str, list[dict]] = {}
    for permit in pending_permissions:
        request_id = str(_field(permit, "id", "Id", default=""))
        if request_id in approved:
            continue
        pending_by_agent.setdefault(str(_field(permit, "agentId", "AgentId", default="")), []).append(permit)

    # -- agentes ------------------------------------------------------------
    snapshot: list[dict] = []
    agents_state: dict[str, dict] = {}
    for agent_id, inspect in inspects.items():
        previous = str((state["agents"].get(agent_id) or {}).get("status", ""))
        status, reason, reference = _classify(inspect, pending_by_agent.get(agent_id, []), now, previous)
        age = now - reference if reference is not None else None
        name = str(_field(inspect, "Name", "name", default=agent_id))
        cwd = str(_field(inspect, "Cwd", "cwd", default=""))
        if inspect.get("_inspect_error"):
            status, reason = "erro", f"inspect falhou: {inspect['_inspect_error']}"
        snapshot.append({
            "id": agent_id,
            "titulo": name,
            "provider_model": _provider_label(inspect, {}),
            "status": status,
            "ha_quanto": _age_text(age),
            "cwd": cwd,
            "motivo": reason,
            "verificado_em": _iso(now),
        })
        agents_state[agent_id] = {"status": status, "updated_at": _iso(reference) if reference else ""}

        if status == "aguardando_aprovacao" and age is not None and age >= timedelta(minutes=PENDING_MIN):
            notified = notify(
                state, now, f"pending:{agent_id}", f"Paseo · {name}",
                f"aguardando aprovação há {_age_text(age)}: {reason}", args.dry_run,
            )
            if notified:
                log_event(log_path, now, "pendente", agente=agent_id, detalhe=reason, espera=_age_text(age))
        elif status == "parado":
            notified = notify(
                state, now, f"stuck:{agent_id}", f"Paseo · {name}",
                f"parado há {_age_text(age)}: {reason}", args.dry_run,
            )
            if notified:
                log_event(log_path, now, "parado", agente=agent_id, detalhe=reason, espera=_age_text(age))
        elif status == "erro":
            notified = notify(
                state, now, f"error:{agent_id}:{_clean(reason, 40)}", f"Paseo · {name}",
                f"erro: {reason}", args.dry_run,
            )
            if notified:
                log_event(log_path, now, "erro", agente=agent_id, detalhe=reason)

    state["agents"] = agents_state

    # -- agendamentos -------------------------------------------------------
    schedule_lines: list[str] = []
    try:
        schedules = paseo_json(["schedule", "ls", "--json"])
        if not isinstance(schedules, list):
            raise PaseoError("schedule ls: JSON não é lista")
    except PaseoError as exc:
        schedules = []
        log_event(log_path, now, "schedule_error", detalhe=str(exc))

    for schedule in schedules:
        schedule_id = str(_field(schedule, "id", "Id", default=""))
        name = str(_field(schedule, "name", "Name", default=schedule_id))
        last_run = _field(schedule, "lastRunAt", "LastRunAt", default="")
        failure = _schedule_failure(schedule)
        if last_run and not failure:
            try:
                runs = _run_entries(paseo_json(["schedule", "logs", schedule_id, "--json"]))
            except PaseoError as exc:
                runs = []
                log_event(log_path, now, "schedule_error", agendamento=schedule_id, detalhe=str(exc))
            if runs:
                failure = _schedule_failure(runs[-1])
        if not failure:
            continue
        schedule_lines.append(f"agendamento {name}: run falhou — {failure}")
        key = f"schedule:{schedule_id}:{last_run or 'run'}"
        if notify(state, now, key, f"Paseo · {name}", f"run do agendamento falhou: {failure}", args.dry_run):
            log_event(log_path, now, "schedule_falhou", agendamento=schedule_id, detalhe=failure)

    prune_state(state, now)
    snapshot.sort(key=lambda item: (_STATUS_PRIORITY.get(item["status"], 9), item["titulo"].lower()))

    if args.dry_run:
        print(f"Paseo watchdog (dry-run): {len(snapshot)} agentes, {len(pending_permissions)} pedidos, {len(schedules)} agendamentos")
        for item in snapshot:
            print(f"  {item['status']:<20} {item['titulo']} — {item['ha_quanto']} — {item['motivo']}")
        for line in schedule_lines:
            print(f"  {line}")
        return 0

    write_json(state_path, state)
    if snapshot:
        write_json(snapshot_path, snapshot)
    for line in schedule_lines:
        print(f"paseo_watchdog: {line}")
    for item in snapshot:
        if item["status"] in {"aguardando_aprovacao", "parado", "erro"}:
            print(f"paseo_watchdog: {item['status']} {item['titulo']} ({item['ha_quanto']}) — {item['motivo']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
