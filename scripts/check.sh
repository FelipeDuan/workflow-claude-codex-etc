#!/usr/bin/env bash
# check.sh — validação estática do repo (frontmatter, nomes, conversão para o
# Codex, sintaxe do install.sh, symlinks e SHAs do lock). Não toca no HOME.
# Uso: scripts/check.sh   (sai com código != 0 se alguma checagem falhar)
set -u

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CONVERTER="$REPO_DIR/scripts/md-convert.awk"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
FAILED=0
ERRS=""

mdc() { LC_ALL=C awk -f "$CONVERTER" "$@"; }   # mesma chamada do install.sh
fm_get() { mdc -v mode=get -v key="$1" "$2"; }
err() { ERRS="$ERRS
    $*"; }
has_fm() { [ "$(head -n 1 "$1")" = "---" ] || { err "$1: sem frontmatter"; return 1; }; }
result() { # $1 = título
    if [ -z "$ERRS" ]; then printf 'PASS  %s\n' "$1"
    else printf 'FAIL  %s%s\n' "$1" "$ERRS"; FAILED=1; fi
    ERRS=""
}

cd "$REPO_DIR" || exit 1

# 1. skills/*/SKILL.md: name e description; name = nome da pasta
for f in skills/*/SKILL.md; do
    [ -f "$f" ] || continue
    has_fm "$f" || continue
    d="$(basename "$(dirname "$f")")"
    n="$(fm_get name "$f")"
    [ -n "$(fm_get description "$f")" ] || err "$f: description vazio"
    [ "$n" = "$d" ] || err "$f: name '$n' != pasta '$d'"
done
result "skills: frontmatter e name = pasta"

# 2. agents/*.md: name e description; name = arquivo e ^[a-z0-9-]+$
for f in agents/*.md; do
    [ -f "$f" ] || continue
    has_fm "$f" || continue
    n="$(fm_get name "$f")"
    [ -n "$(fm_get description "$f")" ] || err "$f: description vazio"
    [ "$n" = "$(basename "$f" .md)" ] || err "$f: name '$n' != nome do arquivo"
    printf '%s' "$n" | grep -Eq '^[a-z0-9-]+$' || err "$f: name '$n' fora de [a-z0-9-]"
done
result "agents: frontmatter, name = arquivo, formato do name"

# 3. commands/*.md: description
for f in commands/*.md; do
    [ -f "$f" ] || continue
    has_fm "$f" || continue
    [ -n "$(fm_get description "$f")" ] || err "$f: description vazio"
done
result "commands: description"

# 4. nomes únicos entre skills próprias e commands (commands viram skills no Codex)
dups="$( { for d in skills/*/; do [ -f "$d/SKILL.md" ] && basename "$d"; done
           for f in commands/*.md; do [ -f "$f" ] && basename "$f" .md; done; } | sort | uniq -d)"
[ -z "$dups" ] || err "duplicados: $(echo $dups)"
result "nomes únicos entre skills e commands"

# 5. conversão para o Codex (agent-toml e command-skill), como no install.sh
for f in agents/*.md; do
    [ -f "$f" ] || continue
    n="$(fm_get name "$f")"; [ -n "$n" ] || n="$(basename "$f" .md)"
    out="$TMP/$n.toml"
    mdc -v mode=agent-toml -v name="$n" -v label="agents/$(basename "$f")" "$f" > "$out" 2>"$TMP/err" \
        && [ -s "$out" ] || err "$f: agent-toml falhou $(cat "$TMP/err")"
done
for f in commands/*.md; do
    [ -f "$f" ] || continue
    n="$(basename "$f" .md)"
    mdc -v mode=command-skill -v name="$n" -v label="commands/$(basename "$f")" "$f" > "$TMP/$n.SKILL.md" 2>"$TMP/err" \
        && [ -s "$TMP/$n.SKILL.md" ] || err "$f: command-skill falhou $(cat "$TMP/err")"
done
if command -v python3 >/dev/null 2>&1 && python3 -c 'import tomllib' 2>/dev/null; then
    for t in "$TMP"/*.toml; do
        [ -f "$t" ] || continue
        msg="$(python3 -c 'import sys,tomllib; tomllib.load(open(sys.argv[1],"rb"))' "$t" 2>&1)" \
            || err "$(basename "$t"): TOML inválido: $(printf '%s' "$msg" | tail -n 1)"
    done
    result "conversão para o Codex (TOML validado com tomllib)"
else
    result "conversão para o Codex (sem tomllib; TOML não validado)"
fi

# 6. sintaxe do install.sh
msg="$(bash -n install.sh 2>&1)" || err "$msg"
result "bash -n install.sh"

# 7. symlinks quebrados no repo
broken="$(find . -path ./.git -prune -o -type l ! -exec test -e {} \; -print)"
[ -z "$broken" ] || err "$(echo $broken)"
result "sem symlinks quebrados"

# 8. third-party.lock: linhas repo com SHA de 40 hex
bad="$(awk '$0 !~ /^[ \t]*(#|$)/ && $1 == "repo" && $4 !~ /^[0-9a-f]{40}$/ { print $2 }' third-party.lock)"
[ -z "$bad" ] || err "repos sem SHA de 40 hex: $(echo $bad)"
result "third-party.lock: SHAs dos repos"

exit "$FAILED"
