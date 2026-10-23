#!/usr/bin/env python3
"""SessionStart: ativa memória em projetos autorizados, sem rede (Python >= 3.11)."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def git(cwd, *args):
    result = subprocess.run(
        ["git", "-C", str(cwd), *args], capture_output=True, text=True,
        timeout=0.2, check=False,
        env={key: value for key, value in os.environ.items() if not key.startswith("GIT_")},
    )
    if result.returncode:
        return None
    return result.stdout.strip()


def expanded(value):
    return Path(value).expanduser().resolve()


def within(path, roots):
    return any(path.is_relative_to(expanded(root)) for root in roots)


def exclude_marker(common, dry_run, actions):
    path = common / "info" / "exclude"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if ".ai-memory.toml" in text.splitlines():
        return
    actions.append("Acrescentar .ai-memory.toml a " + str(path))
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(("\n" if text and not text.endswith("\n") else "") + ".ai-memory.toml\n")


def exclude_claude_mem(checkout, dry_run, actions):
    path = Path.home() / ".claude-mem" / "settings.json"
    if not path.exists():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("settings do Claude-Mem não são um objeto JSON")
    current = data.get("CLAUDE_MEM_EXCLUDED_PROJECTS", "")
    if not isinstance(current, str):
        raise ValueError("CLAUDE_MEM_EXCLUDED_PROJECTS não é string")
    entries = [value.strip() for value in current.split(",") if value.strip()]
    missing = [value for value in (str(checkout), str(checkout) + "/**") if value not in entries]
    if not missing:
        return
    actions.append("Excluir checkout e descendentes do Claude-Mem: " + str(checkout))
    if dry_run:
        return
    # Backup privado antes da alteração; mkstemp evita colisão entre sessões.
    fd, backup = tempfile.mkstemp(prefix="settings.json.backup-", dir=path.parent)
    with os.fdopen(fd, "wb") as stream, path.open("rb") as original:
        shutil.copyfileobj(original, stream)
    os.chmod(backup, 0o600)
    data["CLAUDE_MEM_EXCLUDED_PROJECTS"] = current + ("," if current and not current.endswith(",") else "") + ",".join(missing)
    fd, temporary = tempfile.mkstemp(prefix=".settings-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def run():
    import tomllib

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path(__file__).resolve().parents[1] / "config" / "ai-os-memory.toml")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    payload = json.load(sys.stdin)
    cwd = payload.get("cwd") if isinstance(payload, dict) else None
    if not isinstance(cwd, str) or not Path(cwd).is_absolute():
        return
    cwd = Path(cwd).resolve()
    if not cwd.is_dir():
        return
    with args.config.open("rb") as stream:
        policy = tomllib.load(stream)
    root = git(cwd, "rev-parse", "--show-toplevel")
    common = None
    if root is not None:
        common = git(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir")
        if common is None:
            raise ValueError("não foi possível descobrir git-common-dir")
        root, common = Path(root).resolve(), Path(common).resolve()
        checkout = common.parent
    else:
        if cwd.is_relative_to(expanded("~/.paseo/worktrees")):
            return  # Diretórios intermediários do Paseo não são projetos.
        roots = [expanded(value) for value in policy["roots"] if cwd.is_relative_to(expanded(value))]
        if not roots:
            return
        allowed_root = max(roots, key=lambda path: len(path.parts))
        parts = cwd.relative_to(allowed_root).parts
        if len(parts) < 2:
            return
        root = checkout = allowed_root.joinpath(*parts[:2])
    if not within(checkout, policy["roots"]):
        return
    restricted = policy["restricted"]
    is_restricted = within(checkout, restricted["paths"])
    workspace = restricted["workspace"] if is_restricted else "pessoal"
    allowed = restricted["allowed_models"]
    if not isinstance(workspace, str) or not isinstance(allowed, list) or not all(isinstance(item, str) for item in allowed):
        raise ValueError("workspace/allowed_models inválidos na política")
    actions = []
    marker = root / ".ai-memory.toml"
    inherited = None
    if not marker.exists() and not marker.is_symlink():
        for parent in root.parents:
            depths = [len(parent.relative_to(expanded(value)).parts)
                      for value in policy["roots"] if parent.is_relative_to(expanded(value))]
            candidate = parent / ".ai-memory.toml"
            if not depths or min(depths) == 0 or not candidate.is_file():
                continue
            # Primeiro nível só é projeto se for raiz Git, não mera categoria.
            if min(depths) >= 2 or git(parent, "rev-parse", "--show-toplevel") == str(parent):
                inherited = parent
                break
    tracked = common is not None and git(root, "ls-files", "--error-unmatch", "--", ".ai-memory.toml") is not None
    if common is not None and not tracked and inherited is None:
        exclude_marker(common, args.dry_run, actions)
    exclude_claude_mem(inherited or checkout, args.dry_run, actions)
    if inherited is None and not marker.exists() and not marker.is_symlink():
        actions.append("Criar " + str(marker) + " (workspace=" + workspace + ")")
        if not args.dry_run:
            try:
                with marker.open("x", encoding="utf-8") as stream:
                    # Chaves oficiais do marcador ai-memory v3.2.0, docs/marker-file.md.
                    stream.write("workspace = " + json.dumps(workspace, ensure_ascii=False) + "\n\n[briefing]\ninject_on_session_start = true\nmax_chars = 4000\n")
            except FileExistsError:
                pass  # Outro SessionStart criou o marcador; preservar seu conteúdo.
    output = {}
    if args.dry_run:
        output["dry_run"] = actions
    if is_restricted:
        # Claude Code e Codex documentam esta mesma saída de SessionStart.
        output["hookSpecificOutput"] = {
            "hookEventName": "SessionStart",
            "additionalContext": "Projeto restrito. Permitido só " + ", ".join(allowed) + ". Nunca delegar a modelos que coletam dados para treino. Claude/Codex: usar assinatura com treino desativado; Felipe deve verificar a configuração das contas.",
        }
    if output:
        print(json.dumps(output, ensure_ascii=False))


def main():
    try:
        run()
    except Exception as exc:
        print("ai-memory autoenable: " + str(exc), file=sys.stderr)
    except SystemExit as exc:
        if exc.code:
            print("ai-memory autoenable: argumentos inválidos", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
