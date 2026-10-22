#!/usr/bin/env python3
"""harden.py — merge não destrutivo das configurações do install.sh --harden.

Por que Python: editar JSON/TOML com sed é frágil e jq não é garantido. Só usa
a biblioteca padrão (json; tomllib exige Python >= 3.11).

Uso:
  harden.py claude-settings <settings.json> --check|--apply
  harden.py codex-env       <config.toml>   --check|--apply
  harden.py claude-stop-failure <settings.json> --check|--apply

Saída (stdout), uma linha por item:
  CHANGE <descrição>   algo seria/foi acrescentado
  WARN <descrição>     conflito ou limitação; nada foi sobrescrito
Código de saída:
  0   nada a fazer
  10  há mudanças (aplicadas se --apply)
  2   arquivo inválido ou merge inseguro: NADA foi tocado
"""

import json
import os
import sys
import tempfile

ENV = {
    "IMPECCABLE_NO_TELEMETRY": "1",
    "IMPECCABLE_NO_UPDATE_CHECK": "1",
    "DO_NOT_TRACK": "1",
}

CLAUDE_DENY = [
    "Bash(npx impeccable install)",
    "Bash(npx impeccable install *)",
    "Bash(npx impeccable update)",
    "Bash(npx impeccable update *)",
    "Bash(* impeccable hooks on)",
    "Bash(* impeccable hooks on *)",
    "Bash(impeccable hooks on)",
]

NOTHING, CHANGED, UNSAFE = 0, 10, 2


def say(kind, msg):
    print(f"{kind} {msg}")


def write_atomic(path, text, default_mode=0o600):
    """Grava via arquivo temporário + rename, preservando o modo do original."""
    mode = os.stat(path).st_mode & 0o777 if os.path.exists(path) else default_mode
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".workflow-ai.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def claude_settings(path, apply):
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError) as exc:
            say("WARN", f"{path} não é JSON válido ({exc}); arquivo intocado")
            return UNSAFE
    else:
        data = {}
    if not isinstance(data, dict):
        say("WARN", f"{path}: raiz não é objeto JSON; arquivo intocado")
        return UNSAFE

    env = data.get("env", {})
    perms = data.get("permissions", {})
    if not isinstance(env, dict) or not isinstance(perms, dict):
        say("WARN", f"{path}: 'env' ou 'permissions' não é objeto; arquivo intocado")
        return UNSAFE
    deny = perms.get("deny", [])
    if not isinstance(deny, list):
        say("WARN", f"{path}: 'permissions.deny' não é lista; arquivo intocado")
        return UNSAFE

    changed = False
    for key, value in ENV.items():
        if key not in env:
            env[key] = value
            changed = True
            say("CHANGE", f"env.{key}={value} em {path}")
        elif env[key] != value:
            say("WARN", f"env.{key} já existe com valor {env[key]!r} em {path}; mantido (esperado {value!r})")
    for rule in CLAUDE_DENY:
        if rule not in deny:
            deny.append(rule)
            changed = True
            say("CHANGE", f"permissions.deny += {rule} em {path}")

    if not changed:
        return NOTHING
    if apply:
        # Só agora as chaves novas entram no objeto: chaves e ordem existentes são preservadas.
        data["env"] = env
        perms["deny"] = deny
        data["permissions"] = perms
        write_atomic(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return CHANGED


def claude_stop_failure(path, apply):
    import shlex

    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        data = {}
    except (OSError, ValueError):
        say("WARN", f"{path}: JSON inválido; arquivo intocado")
        return UNSAFE
    if not isinstance(data, dict) or not isinstance(data.get("hooks", {}), dict):
        say("WARN", f"{path}: hooks não é objeto; arquivo intocado")
        return UNSAFE
    hooks = data.get("hooks", {})
    entries = hooks.get("StopFailure", [])
    if not isinstance(entries, list):
        say("WARN", f"{path}: StopFailure não é lista; arquivo intocado")
        return UNSAFE
    script = os.path.join(os.path.dirname(os.path.abspath(path)), "hooks", "stop-failure.py")
    entry = {"matcher": "rate_limit|overloaded|billing_error", "hooks": [
        {"type": "command", "command": "python3 " + shlex.quote(script), "timeout": 25}
    ]}
    if entry in entries:
        return NOTHING
    say("CHANGE", f"hooks.StopFailure em {path}")
    if apply:
        hooks["StopFailure"] = entries + [entry]
        data["hooks"] = hooks
        write_atomic(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return CHANGED


def strip_added(data, had_policy):
    """Remove de uma cópia o que o append acrescenta, para comparar com o original."""
    import copy

    result = copy.deepcopy(data)
    policy = result.get("shell_environment_policy", {})
    policy.pop("set", None)
    if not had_policy and not policy:
        result.pop("shell_environment_policy", None)
    return result


def codex_env(path, apply):
    try:
        import tomllib
    except ImportError:
        say("WARN", "Python sem tomllib (< 3.11); shell_environment_policy do Codex não configurado")
        return UNSAFE

    text = ""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        say("WARN", f"{path} não é TOML válido ({exc}); arquivo intocado")
        return UNSAFE

    policy = data.get("shell_environment_policy")
    if policy is not None and not isinstance(policy, dict):
        say("WARN", f"{path}: shell_environment_policy não é tabela; arquivo intocado")
        return UNSAFE

    if policy is not None and "set" in policy:
        current = policy["set"]
        if not isinstance(current, dict):
            say("WARN", f"{path}: shell_environment_policy.set não é tabela; arquivo intocado")
            return UNSAFE
        missing = [k for k in ENV if k not in current]
        for key in ENV:
            if key in current and current[key] != ENV[key]:
                say("WARN", f"shell_environment_policy.set.{key} já existe com valor {current[key]!r}; mantido")
        if missing:
            lines = ", ".join(f'{k} = "{ENV[k]}"' for k in missing)
            say("WARN", f"{path} já tem shell_environment_policy.set; acrescente manualmente: {lines}")
            return UNSAFE
        return NOTHING

    block = "\n# Adicionado pelo install.sh (workflow-ai) --harden\n[shell_environment_policy.set]\n"
    block += "".join(f'{k} = "{v}"\n' for k, v in ENV.items())
    prefix = text if (not text or text.endswith("\n")) else text + "\n"
    candidate = prefix + block

    # Só aplica se o resultado for TOML válido, tiver as 3 vars e não mudar mais nada.
    try:
        parsed = tomllib.loads(candidate)
    except tomllib.TOMLDecodeError as exc:
        say("WARN", f"acrescentar [shell_environment_policy.set] deixaria {path} inválido ({exc}); arquivo intocado")
        return UNSAFE
    if parsed.get("shell_environment_policy", {}).get("set") != ENV or strip_added(parsed, policy is not None) != data:
        say("WARN", f"merge em {path} não pôde ser verificado; arquivo intocado")
        return UNSAFE

    for key, value in ENV.items():
        say("CHANGE", f"shell_environment_policy.set.{key}={value} em {path}")
    if apply:
        write_atomic(path, candidate)
    return CHANGED


def main(argv):
    if len(argv) != 4 or argv[1] not in ("claude-settings", "codex-env", "claude-stop-failure") or argv[3] not in ("--check", "--apply"):
        print(__doc__, file=sys.stderr)
        return 64
    handler = {"claude-settings": claude_settings, "codex-env": codex_env,
               "claude-stop-failure": claude_stop_failure}[argv[1]]
    return handler(argv[2], argv[3] == "--apply")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
