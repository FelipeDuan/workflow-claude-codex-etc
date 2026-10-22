#!/usr/bin/env python3
"""Finaliza só a sessão que falhou; --dry-run imprime o comando sem executá-lo."""

import json
from pathlib import Path
import subprocess
import sys


def main():
    if sys.argv[1:] not in ([], ["--dry-run"]):
        return 64
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            return 0
        if payload.get("hook_event_name") != "StopFailure" or payload.get("error") not in (
            "rate_limit", "overloaded", "billing_error"
        ):
            return 0
        cwd, session_id = payload.get("cwd"), payload.get("session_id")
        if not isinstance(cwd, str) or not Path(cwd).is_absolute():
            return 0
        if not isinstance(session_id, str) or not session_id.strip():
            return 0
        directory = Path(cwd).resolve(strict=True)
        if not directory.is_dir() or not any(
            (parent / ".ai-memory.toml").is_file()
            for parent in (directory, *directory.parents)
        ):
            return 0
        command = ["ai-memory", "finalize-session", "--agent", "claude-code",
                   "--session-id", session_id]
        if "--dry-run" in sys.argv:
            print(json.dumps({"cwd": str(directory), "argv": command}))
            return 0
        # Sem shell: nenhum campo do payload é interpretado como comando.
        return subprocess.run(command, cwd=directory, timeout=20, check=False).returncode
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        print("StopFailure: não foi possível finalizar a sessão: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
