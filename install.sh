#!/usr/bin/env bash
# install.sh — instala este workflow de IA no Claude Code, no Codex e nas
# ferramentas que leem ~/.agents/skills (Gemini CLI, OpenCode etc.).
#
# Idempotente: rodar de novo só mexe no que mudou. Nada é apagado: qualquer
# arquivo/diretório existente que precise ser substituído vai antes para
# ~/.workflow-ai-backup/<timestamp>/<caminho relativo ao HOME>.
#
# Compatível com bash 3.2 (macOS) e Linux. Depende só de bash, coreutils,
# git, awk, sed, diff e cmp. Opcionais: uv (Graphify), claude/codex/npx (MCP).
#
# Nunca toca em: ~/.codex/auth.json, históricos, sessões, ~/.claude/plugins.
# MCP: `claude mcp add --scope user` grava em ~/.claude.json; no Codex, append
# em ~/.codex/config.toml. O settings.json do Claude recebe o hook StopFailure.
# Carrega mods/quota-guard via env.CLAUDE_CODE_PLUGIN_DIRS no settings do usuário.
# --harden acrescenta configurações por merge não destrutivo com backup
# (scripts/harden.py) no settings.json do Claude e config.toml do Codex.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
LOCK_FILE="$REPO_DIR/third-party.lock"
CONVERTER="$REPO_DIR/scripts/md-convert.awk"

PLAYWRIGHT_MCP_VERSION="0.0.82"
FIGMA_MCP_URL="https://mcp.figma.com/mcp"
FIGMA_MCP_DOCS="https://developers.figma.com/docs/figma-mcp-server/"

: "${HOME:?HOME não está definido}"
CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
CODEX_DIR="${CODEX_HOME:-$HOME/.codex}"
OPENCODE_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/opencode"
AGENTS_SKILLS_DIR="$HOME/.agents/skills"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/workflow-ai"
VENDOR_DIR="$DATA_DIR/vendor"
BACKUP_DIR="$HOME/.workflow-ai-backup/$(date +%Y%m%d-%H%M%S)"

DRY_RUN=0
UPDATE=0
THIRD_PARTY=1
MCP=1
HARDEN=0
ONLY_CLAUDE=0
ONLY_CODEX=0
ONLY_OPENCODE=0

N_OK=0
N_CHANGED=0
N_BACKUP=0
N_WARN=0

# ------------------------------------------------------------------ saída

say()  { printf '%s\n' "$*"; }
step() { printf '\n== %s\n' "$*"; }
ok()   { N_OK=$((N_OK + 1)); [ "${VERBOSE:-0}" = 1 ] && say "  ok        $*"; return 0; }
did()  { N_CHANGED=$((N_CHANGED + 1)); if [ "$DRY_RUN" = 1 ]; then say "  [dry-run] $*"; else say "  $*"; fi; }
warn() { N_WARN=$((N_WARN + 1)); printf '  AVISO: %s\n' "$*" >&2; printf '%s\n' "$*" >> "$STAGE/warnings.txt"; }
die()  { printf 'ERRO: %s\n' "$*" >&2; exit 1; }

usage() {
    cat <<'EOF'
Uso: ./install.sh [opções]

Instala AGENTS.md, agentes, skills e commands deste repo (via symlink) e as
skills/agentes de terceiros fixados em third-party.lock (via cópia).
Claude: carrega mods/quota-guard via env.CLAUDE_CODE_PLUGIN_DIRS no settings do usuário.

Opções:
  --dry-run          Mostra o que seria feito, sem alterar nada.
  --only ALVO        Instala só para "claude", "codex" ou "opencode". Pode repetir.
                     codex inclui ~/.agents/skills (lido também por Gemini CLI,
                     OpenCode etc.).
  --update           Baixa de novo as fontes de terceiros (no SHA fixado),
                     descartando o cache atual (o cache antigo vai para backup).
  --no-third-party   Não instala nada de third-party.lock (nem o Graphify).
  --no-mcp           Não configura servidores MCP.
  --harden           Opt-in. Claude: acrescenta env de privacidade e
                     permissions.deny (impeccable install/update/hooks on) no
                     settings.json. Codex: env em shell_environment_policy.set
                     e ~/.codex/rules/workflow-ai.rules. Merge não destrutivo,
                     com backup; requer python3 (tomllib, >= 3.11, no Codex).
  -v, --verbose      Lista também o que já estava correto.
  -h, --help         Mostra esta ajuda.

Variáveis respeitadas: CLAUDE_CONFIG_DIR, CODEX_HOME, XDG_DATA_HOME, XDG_CONFIG_HOME.
Backups: ~/.workflow-ai-backup/<timestamp>/
EOF
}

# ------------------------------------------------------------------ argumentos

while [ $# -gt 0 ]; do
    case "$1" in
        --dry-run) DRY_RUN=1 ;;
        --update) UPDATE=1 ;;
        --no-third-party) THIRD_PARTY=0 ;;
        --no-mcp) MCP=0 ;;
        --harden) HARDEN=1 ;;
        -v|--verbose) VERBOSE=1 ;;
        -h|--help) usage; exit 0 ;;
        --only|--only=*)
            if [ "$1" = "--only" ]; then
                [ $# -ge 2 ] || die "--only precisa de um valor (claude|codex|opencode)"
                target="$2"; shift
            else
                target="${1#--only=}"
            fi
            case "$target" in
                claude) ONLY_CLAUDE=1 ;;
                codex) ONLY_CODEX=1 ;;
                opencode) ONLY_OPENCODE=1 ;;
                *) die "--only aceita claude, codex ou opencode (recebido: $target)" ;;
            esac
            ;;
        *) usage >&2; die "opção desconhecida: $1" ;;
    esac
    shift
done

if [ "$ONLY_CLAUDE" = 0 ] && [ "$ONLY_CODEX" = 0 ] && [ "$ONLY_OPENCODE" = 0 ]; then
    DO_CLAUDE=1; DO_CODEX=1; DO_OPENCODE=1
else
    DO_CLAUDE=$ONLY_CLAUDE; DO_CODEX=$ONLY_CODEX; DO_OPENCODE=$ONLY_OPENCODE
fi

want_target() { # $1 = claude|codex|opencode
    case "$1" in
        claude) [ "$DO_CLAUDE" = 1 ] ;;
        codex) [ "$DO_CODEX" = 1 ] ;;
        opencode) [ "$DO_OPENCODE" = 1 ] ;;
        *) return 1 ;;
    esac
}

# ------------------------------------------------------------------ pré-checagens

for tool in git awk sed diff cmp mktemp; do
    command -v "$tool" >/dev/null 2>&1 || die "comando obrigatório ausente: $tool"
done
[ -f "$REPO_DIR/AGENTS.md" ] || die "AGENTS.md não encontrado em $REPO_DIR"
[ -f "$CONVERTER" ] || die "conversor não encontrado: $CONVERTER"
[ -f "$LOCK_FILE" ] || die "manifesto não encontrado: $LOCK_FILE"

STAGE="$(mktemp -d "${TMPDIR:-/tmp}/workflow-ai.XXXXXX")"
# Remove só o diretório temporário criado acima.
trap 'rm -rf "$STAGE"' EXIT
: > "$STAGE/warnings.txt"
PLAN="$STAGE/plan.tsv"
: > "$PLAN"

# Protege contra destinos que resolvem para dentro do próprio repo (ex.:
# ~/.claude/skills como symlink para o repo): mover "o antigo" para backup
# moveria arquivos do repo.
physical_dir() { (cd "$1" 2>/dev/null && pwd -P); }
for d in "$CLAUDE_DIR" "$CLAUDE_DIR/agents" "$CLAUDE_DIR/skills" "$CLAUDE_DIR/commands" "$CLAUDE_DIR/hooks" \
         "$CODEX_DIR" "$CODEX_DIR/agents" "$AGENTS_SKILLS_DIR" "$OPENCODE_DIR"; do
    [ -d "$d" ] || continue
    p="$(physical_dir "$d")"
    case "$p/" in
        "$REPO_DIR"/*) die "destino $d aponta para dentro do repo ($p); corrija antes de instalar" ;;
    esac
done

mdc() { LC_ALL=C awk -f "$CONVERTER" "$@"; }
fm_get() { mdc -v mode=get -v key="$1" "$2"; } # $1 = chave, $2 = arquivo

# ------------------------------------------------------------------ primitivas (únicas que alteram o HOME)

# Move $1 para o backup do run atual, preservando o caminho relativo ao HOME.
backup_move() {
    local path="$1" rel dest
    case "$path" in
        "$HOME"/*) rel="${path#"$HOME"/}" ;;
        *) rel="_abs${path}" ;;
    esac
    dest="$BACKUP_DIR/$rel"
    N_BACKUP=$((N_BACKUP + 1))
    if [ "$DRY_RUN" = 1 ]; then
        say "  [dry-run] backup  $path -> $dest"
        return 0
    fi
    mkdir -p "$(dirname "$dest")"
    [ -e "$dest" ] || [ -L "$dest" ] && dest="$dest.$$"
    mv "$path" "$dest"
    printf '%s\t%s\n' "$path" "$dest" >> "$BACKUP_DIR/MANIFEST.tsv"
    say "  backup    $path -> $dest"
}

# Copia $1 para o backup sem removê-lo (para arquivos que só recebem append).
backup_copy() {
    local path="$1" rel dest
    case "$path" in
        "$HOME"/*) rel="${path#"$HOME"/}" ;;
        *) rel="_abs${path}" ;;
    esac
    dest="$BACKUP_DIR/$rel"
    N_BACKUP=$((N_BACKUP + 1))
    if [ "$DRY_RUN" = 1 ]; then
        say "  [dry-run] backup (cópia)  $path -> $dest"
        return 0
    fi
    mkdir -p "$(dirname "$dest")"
    [ -e "$dest" ] && dest="$dest.$$"
    cp -p "$path" "$dest"
    LAST_BACKUP="$dest"
    printf '%s\t%s\n' "$path" "$dest" >> "$BACKUP_DIR/MANIFEST.tsv"
    say "  backup    $path -> $dest (cópia)"
}

exists_or_link() { [ -e "$1" ] || [ -L "$1" ]; }

ensure_symlink() { # $1 = origem (no repo), $2 = destino
    local src="$1" dst="$2"
    if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then ok "$dst"; return 0; fi
    exists_or_link "$dst" && backup_move "$dst"
    did "link      $dst -> $src"
    [ "$DRY_RUN" = 1 ] && return 0
    mkdir -p "$(dirname "$dst")"
    ln -s "$src" "$dst"
}

install_file() { # $1 = arquivo pronto (staging), $2 = destino
    local src="$1" dst="$2"
    if [ -f "$dst" ] && [ ! -L "$dst" ] && cmp -s "$src" "$dst"; then ok "$dst"; return 0; fi
    exists_or_link "$dst" && backup_move "$dst"
    did "arquivo   $dst"
    [ "$DRY_RUN" = 1 ] && return 0
    mkdir -p "$(dirname "$dst")"
    cp "$src" "$dst"
}

install_dir() { # $1 = diretório pronto (staging), $2 = destino
    local src="$1" dst="$2"
    if [ -d "$dst" ] && [ ! -L "$dst" ] && diff -r -q -x .DS_Store "$src" "$dst" >/dev/null 2>&1; then
        ok "$dst"; return 0
    fi
    exists_or_link "$dst" && backup_move "$dst"
    did "cópia     $dst/"
    [ "$DRY_RUN" = 1 ] && return 0
    mkdir -p "$(dirname "$dst")"
    cp -R "$src" "$dst"
}

# ------------------------------------------------------------------ plano
# Cada linha do plano: op<TAB>arg1<TAB>...<TAB>destino (destino sempre por
# último, para detectar colisões antes de alterar qualquer coisa).

plan() { local IFS=$'\t'; printf '%s\n' "$*" >> "$PLAN"; }

plan_own_content() {
    local f d name
    if want_target opencode; then
        plan link "$REPO_DIR/AGENTS.md" "$OPENCODE_DIR/AGENTS.md"
    fi
    if want_target claude; then
        plan link "$REPO_DIR/AGENTS.md" "$CLAUDE_DIR/CLAUDE.md"
        plan link "$REPO_DIR/scripts/stop-failure.py" "$CLAUDE_DIR/hooks/stop-failure.py"
        for f in "$REPO_DIR"/agents/*.md; do
            [ -f "$f" ] || continue
            plan link "$f" "$CLAUDE_DIR/agents/$(basename "$f")"
        done
        for d in "$REPO_DIR"/skills/*/; do
            d="${d%/}"
            [ -f "$d/SKILL.md" ] || continue
            plan link "$d" "$CLAUDE_DIR/skills/$(basename "$d")"
        done
        for f in "$REPO_DIR"/commands/*.md; do
            [ -f "$f" ] || continue
            plan link "$f" "$CLAUDE_DIR/commands/$(basename "$f")"
        done
    fi
    if want_target codex; then
        plan link "$REPO_DIR/AGENTS.md" "$CODEX_DIR/AGENTS.md"
        for f in "$REPO_DIR"/agents/*.md; do
            [ -f "$f" ] || continue
            name="$(fm_get name "$f")"
            [ -n "$name" ] || name="$(basename "$f" .md)"
            plan agent-toml "$f" "$name" "agents/$(basename "$f")" "$CODEX_DIR/agents/$name.toml"
        done
        for d in "$REPO_DIR"/skills/*/; do
            d="${d%/}"
            [ -f "$d/SKILL.md" ] || continue
            plan link "$d" "$AGENTS_SKILLS_DIR/$(basename "$d")"
        done
        for f in "$REPO_DIR"/commands/*.md; do
            [ -f "$f" ] || continue
            name="$(basename "$f" .md)"
            plan command-skill "$f" "$name" "commands/$(basename "$f")" "$AGENTS_SKILLS_DIR/$name"
        done
    fi
}

# ------------------------------------------------------------------ terceiros

lock_lines() { # imprime as linhas úteis do lock com o tipo pedido
    awk -v kind="$1" '$0 !~ /^[ \t]*(#|$)/ && $1 == kind' "$LOCK_FILE"
}

repo_field() { # $1 = id, $2 = 3 (url) | 4 (sha)
    lock_lines repo | awk -v id="$1" -v f="$2" '$2 == id { print $f; exit }'
}

# Garante $VENDOR_DIR/<id> no SHA fixado. Retorna 1 se indisponível (dry-run sem cache).
fetch_repo() {
    local id="$1" url="$2" sha="$3" dir="$VENDOR_DIR/$1" head refetch=1
    if [ -d "$dir/.git" ] && [ "$UPDATE" = 0 ]; then
        head="$(git -C "$dir" rev-parse HEAD 2>/dev/null || true)"
        if [ -z "$(git -C "$dir" status --porcelain 2>/dev/null || echo dirty)" ]; then
            if [ "$head" = "$sha" ]; then ok "vendor $id @ ${sha:0:12}"; return 0; fi
            # Cache limpo em outro commit: só troca de commit (nada local é perdido).
            did "vendor    $id: ${head:0:12} -> ${sha:0:12}"
            [ "$DRY_RUN" = 1 ] && return 1
            git -C "$dir" fetch -q --depth 1 origin "$sha" </dev/null
            git -C "$dir" -c advice.detachedHead=false checkout -q --detach FETCH_HEAD
            refetch=0
        else
            warn "cache de $id tem alterações locais ou está corrompido; será baixado de novo (o atual vai para backup)"
        fi
    fi
    if [ "$refetch" = 1 ]; then
        exists_or_link "$dir" && backup_move "$dir"
        did "download  $url @ ${sha:0:12} -> $dir"
        [ "$DRY_RUN" = 1 ] && return 1
        mkdir -p "$dir"
        git -C "$dir" init -q
        git -C "$dir" remote add origin "$url"
        git -C "$dir" fetch -q --depth 1 origin "$sha" </dev/null
        git -C "$dir" -c advice.detachedHead=false checkout -q --detach FETCH_HEAD
    fi
    head="$(git -C "$dir" rev-parse HEAD)"
    [ "$head" = "$sha" ] || die "vendor $id: HEAD $head difere do SHA fixado $sha"
}

fetch_all_repos() {
    local kind id url sha rest
    AVAILABLE=" "
    while read -r kind id url sha rest <&3; do
        [ -n "$kind" ] || continue
        [ -n "$sha" ] || die "linha repo inválida no lock: $kind $id $url"
        case "$sha" in *[!0-9a-f]*) die "SHA inválido para $id: $sha" ;; esac
        [ "${#sha}" = 40 ] || die "SHA de $id precisa ter 40 caracteres: $sha"
        if fetch_repo "$id" "$url" "$sha"; then AVAILABLE="$AVAILABLE$id "; fi
    done 3<<EOF
$(lock_lines repo)
EOF
}

repo_available() { case "$AVAILABLE" in *" $1 "*) return 0 ;; esac; return 1; }

plan_third_party() {
    local kind id src dest targets extra base name target srcpath fmname ext
    while read -r kind id src dest targets extra <&3; do
        [ -n "$kind" ] || continue
        [ -n "$targets" ] || die "linha inválida no lock: $kind $id $src $dest"
        [ -n "$(repo_field "$id" 3)" ] || die "repo '$id' não declarado no lock"
        base="$VENDOR_DIR/$id"
        srcpath="$base/${src#./}"
        [ "$src" = "." ] && srcpath="$base"
        if ! repo_available "$id"; then
            did "pendente  $kind $id:$src ($targets) — depende do download"
            continue
        fi
        case "$kind" in
            skill)
                [ -f "$srcpath/SKILL.md" ] || die "SKILL.md não encontrado em $id:$src"
                case "$extra" in
                    "") extra="-" ;;
                    include=*) extra="${extra#include=}" ;;
                    *) die "campo extra inválido em $id:$src: $extra" ;;
                esac
                [ "$src" = "." ] && [ "$extra" = "-" ] && die "$id:. exige include= (não copiar o repo inteiro)"
                fmname="$(fm_get name "$srcpath/SKILL.md")"
                if [ "$dest" = "-" ]; then name="${fmname:-$(basename "$srcpath")}"; else name="$dest"; fi
                for target in $(printf '%s' "$targets" | tr ',' ' '); do
                    want_target "$target" || continue
                    case "$target" in
                        claude) plan skill "$srcpath" "$name" "$extra" "$CLAUDE_DIR/skills/$name" ;;
                        codex) plan skill "$srcpath" "$name" "$extra" "$AGENTS_SKILLS_DIR/$name" ;;
                        *) die "alvo inválido em $id:$src: $target" ;;
                    esac
                done
                ;;
            agent)
                [ -f "$srcpath" ] || die "agente não encontrado: $id:$src"
                ext="${srcpath##*.}"
                for target in $(printf '%s' "$targets" | tr ',' ' '); do
                    want_target "$target" || continue
                    if [ "$ext" = "toml" ]; then
                        [ "$target" = codex ] || die "$id:$src é .toml; só vale para o alvo codex"
                        [ "$dest" = "-" ] || die "$id:$src: renomear .toml não é suportado"
                        plan copy-file "$srcpath" "$CODEX_DIR/agents/$(basename "$srcpath")"
                        continue
                    fi
                    [ "$ext" = "md" ] || die "$id:$src: agente precisa ser .md ou .toml"
                    fmname="$(fm_get name "$srcpath")"
                    if [ "$dest" = "-" ]; then name="${fmname:-$(basename "$srcpath" .md)}"; else name="$dest"; fi
                    case "$target" in
                        claude) plan agent-md "$srcpath" "$name" "$CLAUDE_DIR/agents/$name.md" ;;
                        codex) plan agent-toml "$srcpath" "$name" "$id:$src" "$CODEX_DIR/agents/$name.toml" ;;
                        *) die "alvo inválido em $id:$src: $target" ;;
                    esac
                done
                ;;
        esac
    done 3<<EOF
$(lock_lines skill; lock_lines agent)
EOF
}

# ------------------------------------------------------------------ execução do plano

stage_skill() { # $1 = origem, $2 = nome, $3 = include|-, $4 = staging de saída
    local src="$1" name="$2" include="$3" out="$4" rel fmname
    mkdir -p "$out"
    if [ "$include" = "-" ]; then
        cp -R "$src/." "$out/"
        rm -rf "$out/.git"   # dentro do staging temporário
    else
        for rel in $(printf '%s' "$include" | tr ',' ' '); do
            [ -e "$src/$rel" ] || die "include inexistente: $src/$rel"
            mkdir -p "$out/$(dirname "$rel")"
            cp -R "$src/$rel" "$out/$rel"
        done
    fi
    find "$out" -name .DS_Store -exec rm -f {} + 2>/dev/null || true
    fmname="$(fm_get name "$out/SKILL.md")"
    if [ "$fmname" != "$name" ]; then
        mdc -v mode=set-name -v newname="$name" "$out/SKILL.md" > "$out/SKILL.md.tmp"
        mv "$out/SKILL.md.tmp" "$out/SKILL.md"
    fi
}

check_collisions() {
    local dups
    dups="$(awk -F '\t' '{ print $NF }' "$PLAN" | sort | uniq -d)"
    [ -z "$dups" ] || die "dois itens instalariam no mesmo destino (ajuste o lock ou renomeie):
$dups"
}

apply_plan() {
    local op a b c d n=0 out
    while IFS=$'\t' read -r op a b c d <&3; do
        n=$((n + 1))
        out="$STAGE/item$n"
        case "$op" in
            link) ensure_symlink "$a" "$b" ;;
            agent-toml) # a=origem b=nome c=rótulo d=destino
                mdc -v mode=agent-toml -v name="$b" -v label="$c" "$a" > "$out"
                install_file "$out" "$d" ;;
            command-skill) # a=origem b=nome c=rótulo d=destino(dir)
                mkdir -p "$out"
                mdc -v mode=command-skill -v name="$b" -v label="$c" "$a" > "$out/SKILL.md"
                install_dir "$out" "$d" ;;
            skill) # a=origem b=nome c=include d=destino(dir)
                stage_skill "$a" "$b" "$c" "$out/$b"
                install_dir "$out/$b" "$d" ;;
            agent-md) # a=origem b=nome c=destino
                if [ "$(fm_get name "$a")" = "$b" ]; then cp "$a" "$out"
                else mdc -v mode=set-name -v newname="$b" "$a" > "$out"; fi
                install_file "$out" "$c" ;;
            copy-file) install_file "$a" "$b" ;;
            *) die "operação desconhecida no plano: $op" ;;
        esac
    done 3< "$PLAN"
}

# ------------------------------------------------------------------ motores binários (impeccable)
# O launcher da impeccable (scripts/impeccable) procura, nesta ordem:
# $IMPECCABLE_BIN, bin/<os>-<arch>/ ao lado dele, ~/.impeccable/bin/impeccable,
# ${IMPECCABLE_HOME:-~/.impeccable}/bin/<VERSION>/impeccable e o PATH; só então
# baixa sozinho (confiando no .sha256 do próprio release). Pré-instalando no cache
# versionado, com sha256 fixado no lock, a skill nunca chega ao download.
# O binário NÃO é executado aqui.

sha256_of() {
    if command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | awk '{ print $1 }'
    elif command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{ print $1 }'
    else return 1
    fi
}

host_platform() { # imprime <os>-<arch> com os mesmos nomes do launcher
    local os arch
    case "$(uname -s 2>/dev/null || echo unknown)" in
        Darwin) os=darwin ;; Linux) os=linux ;; *) os=unknown ;;
    esac
    case "$(uname -m 2>/dev/null || echo unknown)" in
        arm64|aarch64) arch=arm64 ;; x86_64|amd64) arch=x64 ;; *) arch=unknown ;;
    esac
    printf '%s-%s\n' "$os" "$arch"
}

install_engines() {
    local plat eid kind id ver p sha url dst vfile upstream tmp got
    plat="$(host_platform)"
    for eid in $(lock_lines engine | awk '{ print $2 }' | sort -u); do
        step "Motor $eid ($plat)"
        id="$eid" url=""
        read -r kind id ver p sha url <<EOF
$(lock_lines engine | awk -v id="$eid" -v p="$plat" '$2 == id && $4 == p { print; exit }')
EOF
        id="$eid"
        if [ -z "${url:-}" ]; then
            warn "sem digest no lock para $id em $plat; motor não pré-instalado (a skill tentaria baixar sozinha no primeiro uso)"
            continue
        fi
        case "$url" in https://*) ;; *) warn "URL do motor $id não é https; pulado"; continue ;; esac
        case "$sha" in *[!0-9a-f]*) die "sha256 inválido para $id/$plat: $sha" ;; esac
        [ "${#sha}" = 64 ] || die "sha256 de $id/$plat precisa ter 64 caracteres"
        # A versão do lock tem de bater com o VERSION do commit fixado.
        if repo_available "$id"; then
            for vfile in "$VENDOR_DIR/$id/plugin/skills/impeccable/scripts/VERSION" \
                         "$VENDOR_DIR/$id/.agents/skills/impeccable/scripts/VERSION"; do
                [ -f "$vfile" ] || continue
                upstream="$(tr -d '[:space:]' < "$vfile")"
                if [ "$upstream" != "$ver" ]; then
                    warn "motor $id: lock fixa $ver mas o launcher pede $upstream ($vfile); atualize o lock. Motor não instalado."
                    continue 2
                fi
            done
        fi
        dst="${IMPECCABLE_HOME:-$HOME/.impeccable}/bin/$ver/impeccable"
        if [ -f "$dst" ] && [ ! -L "$dst" ] && [ "$(sha256_of "$dst" || true)" = "$sha" ]; then
            ok "$dst"
            continue
        fi
        if [ "$DRY_RUN" = 1 ]; then
            exists_or_link "$dst" && backup_move "$dst"
            did "baixaria $url -> $dst (sha256 ${sha:0:12}…)"
            continue
        fi
        command -v curl >/dev/null 2>&1 || { warn "curl ausente; motor $id não instalado"; continue; }
        tmp="$STAGE/engine-$id-$plat"
        if ! curl -fsSL --proto '=https' --tlsv1.2 --retry 2 -o "$tmp" "$url" </dev/null; then
            warn "download do motor $id falhou ($url); nada instalado"
            continue
        fi
        got="$(sha256_of "$tmp" || true)"
        if [ "$got" != "$sha" ]; then
            warn "sha256 do motor $id NÃO confere (esperado $sha, obtido ${got:-?}); nada instalado"
            continue
        fi
        exists_or_link "$dst" && backup_move "$dst"
        did "motor     $dst (sha256 ok)"
        mkdir -p "$(dirname "$dst")"
        cp "$tmp" "$dst.part.$$"
        chmod 755 "$dst.part.$$"
        mv "$dst.part.$$" "$dst"
    done
}

# ------------------------------------------------------------------ Graphify (opcional)
# `graphify install` (v0.9.70, graphify/install.py) faz, no escopo global:
#   --platform claude: copia SKILL.md + references/ + .graphify_version para
#       ~/.claude/skills/graphify/ (ou $CLAUDE_CONFIG_DIR/skills/graphify/) E
#       acrescenta um bloco "# graphify" em ~/.claude/CLAUDE.md.
#   --platform agents: copia SKILL.md + references/ para ~/.agents/skills/graphify/
#       (não mexe em nenhum AGENTS.md).
#   (--platform codex usaria ~/.codex/skills/graphify, caminho antigo; não usamos.)
# Como ~/.claude/CLAUDE.md aqui é symlink para o AGENTS.md do repo, rodar o
# comando direto alteraria o repo. Por isso rodamos com HOME apontando para um
# staging temporário e copiamos só a pasta da skill; o bloco no CLAUDE.md é
# descartado (a skill é descoberta pelo diretório, o bloco é só um lembrete).
# Hooks do graphify (`graphify hook install`, `--project`) não são instalados.

install_graphify() {
    local pkg ver current bin gh
    read -r _ pkg ver _ <<EOF
$(lock_lines uvtool | head -n 1)
EOF
    [ -n "${ver:-}" ] || return 0
    step "Graphify ($pkg==$ver)"
    if ! command -v uv >/dev/null 2>&1; then
        warn "uv não encontrado; Graphify não instalado (instale uv e rode de novo, ou: uv tool install $pkg==$ver)"
        return 0
    fi
    # Consultas ao uv usam cache temporário para não criar ~/.cache/uv (dry-run = zero escrita).
    current="$(UV_CACHE_DIR="$STAGE/uv-cache" uv tool list 2>/dev/null | awk -v p="$pkg" '$1 == p { print $2; exit }')"
    if [ "$current" = "v$ver" ]; then
        ok "uv tool $pkg $current"
    else
        did "uv tool install $pkg==$ver${current:+ (atual: $current)}"
        if [ "$DRY_RUN" = 0 ] && ! uv tool install "$pkg==$ver"; then
            warn "falha em uv tool install $pkg==$ver"
            return 0
        fi
    fi
    bin="$(UV_CACHE_DIR="$STAGE/uv-cache" uv tool dir --bin 2>/dev/null)/graphify"
    if [ ! -x "$bin" ]; then
        [ "$DRY_RUN" = 1 ] && { did "graphify install (skill em staging e cópia)"; return 0; }
        warn "executável graphify não encontrado em $bin"
        return 0
    fi
    gh="$STAGE/graphify-home"
    mkdir -p "$gh"
    if want_target claude; then
        if env -u CLAUDE_CONFIG_DIR -u CODEX_HOME HOME="$gh" "$bin" install --platform claude >"$STAGE/graphify-claude.log" 2>&1 \
            && [ -f "$gh/.claude/skills/graphify/SKILL.md" ]; then
            install_dir "$gh/.claude/skills/graphify" "$CLAUDE_DIR/skills/graphify"
        else
            warn "graphify install --platform claude falhou: $(tail -n 3 "$STAGE/graphify-claude.log" | tr '\n' ' ')"
        fi
    fi
    if want_target codex; then
        if env -u CLAUDE_CONFIG_DIR -u CODEX_HOME HOME="$gh" "$bin" install --platform agents >"$STAGE/graphify-agents.log" 2>&1 \
            && [ -f "$gh/.agents/skills/graphify/SKILL.md" ]; then
            install_dir "$gh/.agents/skills/graphify" "$AGENTS_SKILLS_DIR/graphify"
        else
            warn "graphify install --platform agents falhou: $(tail -n 3 "$STAGE/graphify-agents.log" | tr '\n' ' ')"
        fi
    fi
}

# ------------------------------------------------------------------ MCP

has_tomllib() { command -v python3 >/dev/null 2>&1 && python3 -c 'import tomllib' 2>/dev/null; }

# Imprime present|absent|invalid. Usa tomllib (Python >= 3.11) se existir, por ser
# um parser real; senão cai num grep conservador (na dúvida, "present" = não mexe).
codex_playwright_state() {
    if has_tomllib; then
        python3 - "$1" <<'PY'
import sys, tomllib
try:
    with open(sys.argv[1], "rb") as f:
        data = tomllib.load(f)
except Exception:
    print("invalid"); sys.exit(0)
print("present" if "playwright" in (data.get("mcp_servers") or {}) else "absent")
PY
    elif grep -Eq '^[[:space:]]*\[[[:space:]]*mcp_servers[[:space:]]*\.[[:space:]]*"?playwright"?[[:space:]]*[].]|mcp_servers\.playwright|^[[:space:]]*"?playwright"?[[:space:]]*=' "$1"; then
        echo present
    else
        echo absent
    fi
}

append_codex_playwright() { # $1 = config.toml, $2 = pacote npx
    local cfg="$1" pw="$2"
    LAST_BACKUP=""
    [ -f "$cfg" ] && backup_copy "$cfg"
    did "append    [mcp_servers.playwright] em $cfg"
    [ "$DRY_RUN" = 1 ] && return 0
    mkdir -p "$(dirname "$cfg")"
    # Garante quebra de linha antes do bloco novo.
    if [ -s "$cfg" ] && [ -n "$(tail -c 1 "$cfg")" ]; then printf '\n' >> "$cfg"; fi
    {
        printf '\n# Adicionado pelo install.sh (workflow-ai)\n'
        printf '[mcp_servers.playwright]\n'
        printf 'command = "npx"\n'
        printf 'args = ["%s"]\n' "$pw"
    } >> "$cfg"
    if has_tomllib && [ "$(codex_playwright_state "$cfg")" != present ]; then
        if [ -n "$LAST_BACKUP" ]; then
            cp -p "$LAST_BACKUP" "$cfg"
            warn "append deixou $cfg inválido; conteúdo original restaurado de $LAST_BACKUP"
        else
            warn "append deixou $cfg inválido; revise o arquivo"
        fi
    fi
}

# O plugin oficial playwright@claude-plugins-official já expõe o Playwright MCP
# (aparece como plugin:playwright:playwright); `claude mcp get playwright` não o vê.
# Lê enabledPlugins do settings.json (python3 se existir, senão grep conservador).
# Só o settings.json de escopo user é lido; settings de projeto/local não são vistos.
claude_playwright_plugin_enabled() {
    local s="$CLAUDE_DIR/settings.json"
    [ -f "$s" ] || return 1
    if command -v python3 >/dev/null 2>&1; then
        python3 - "$s" <<'PY'
import json, sys
try:
    with open(sys.argv[1]) as f:
        plugins = json.load(f).get("enabledPlugins") or {}
    ok = isinstance(plugins, dict) and plugins.get("playwright@claude-plugins-official") is True
except Exception:
    sys.exit(1)
sys.exit(0 if ok else 1)
PY
    else
        grep -Eq '"playwright@claude-plugins-official"[[:space:]]*:[[:space:]]*true' "$s"
    fi
}

setup_mcp() {
    step "MCP"
    local pw="@playwright/mcp@$PLAYWRIGHT_MCP_VERSION" cfg="$CODEX_DIR/config.toml"
    if ! command -v npx >/dev/null 2>&1; then
        warn "npx não encontrado; Playwright MCP não configurado (instale Node.js e rode de novo)"
    else
        if want_target claude; then
            if ! command -v claude >/dev/null 2>&1; then
                warn "claude CLI não encontrado; Playwright MCP do Claude pulado"
            elif claude_playwright_plugin_enabled; then
                ok "claude mcp playwright (via plugin playwright@claude-plugins-official; não registrado de novo)"
                if [ -f "${CLAUDE_CONFIG_DIR:-$HOME}/.claude.json" ] \
                    && claude mcp get playwright </dev/null >/dev/null 2>&1; then
                    warn "Playwright MCP duplicado: plugin ativo e servidor manual em escopo user; remova com: claude mcp remove --scope user playwright"
                fi
            # `claude mcp get` cria ~/.claude.json se ele não existir; no dry-run,
            # sem esse arquivo o servidor com certeza não está configurado.
            elif { [ "$DRY_RUN" = 0 ] || [ -f "${CLAUDE_CONFIG_DIR:-$HOME}/.claude.json" ]; } \
                && claude mcp get playwright </dev/null >/dev/null 2>&1; then
                ok "claude mcp playwright"
            else
                did "claude mcp add --scope user playwright -- npx $pw"
                if [ "$DRY_RUN" = 0 ] && ! claude mcp add --scope user playwright -- npx "$pw"; then
                    warn "claude mcp add playwright falhou"
                fi
            fi
        fi
        if want_target codex; then
            if ! command -v codex >/dev/null 2>&1; then
                warn "codex CLI não encontrado; Playwright MCP do Codex pulado"
            else
                local state=absent
                [ -f "$cfg" ] && state="$(codex_playwright_state "$cfg")"
                case "$state" in
                    present) ok "codex mcp playwright" ;;
                    invalid) warn "$cfg não é TOML válido; Playwright MCP do Codex não configurado (arquivo intocado)" ;;
                    absent) append_codex_playwright "$cfg" "$pw" ;;
                esac
            fi
        fi
    fi
    say ""
    say "  Figma MCP (manual, não automatizado):"
    say "    Servidor remoto oficial: $FIGMA_MCP_URL (docs: $FIGMA_MCP_DOCS)"
    say "    Claude Code: recomendado: claude plugin install figma@claude-plugins-official"
    say "                 (mesmo servidor do conector do claude.ai, traz as skills do Figma e tem precedência)."
    say "                 Alternativa manual: claude mcp add --scope user --transport http figma $FIGMA_MCP_URL"
    say "                 Em ambos, autentique com /mcp dentro do Claude Code."
    say "    Codex:       codex mcp add figma --url $FIGMA_MCP_URL  e depois  codex mcp login figma"
}

# ------------------------------------------------------------------ hardening (--harden, opt-in)

# Roda scripts/harden.py em modo check; se houver mudanças, faz backup e aplica.
harden_merge() { # $1 = modo do harden.py, $2 = arquivo, demais = argumentos do modo
    local mode="$1" file="$2" out rc line
    shift 2
    if out="$(python3 "$REPO_DIR/scripts/harden.py" "$mode" "$file" "$@" --check)"; then rc=0; else rc=$?; fi
    while IFS= read -r line; do
        case "$line" in
            "CHANGE "*) did "merge     ${line#CHANGE }" ;;
            "WARN "*) warn "${line#WARN }" ;;
        esac
    done <<EOF
$out
EOF
    case "$rc" in
        0) ok "$file (harden)" ;;
        10)
            [ "$DRY_RUN" = 1 ] && return 0
            LAST_BACKUP=""
            [ -f "$file" ] && backup_copy "$file"
            if python3 "$REPO_DIR/scripts/harden.py" "$mode" "$file" "$@" --apply >/dev/null; then rc=0; else rc=$?; fi
            [ "$rc" = 10 ] || warn "harden.py $mode terminou com código $rc ao aplicar em $file"
            ;;
        2) ;; # harden.py já explicou o motivo em uma linha WARN; arquivo intocado
        *) warn "harden.py $mode falhou (código $rc); $file não alterado" ;;
    esac
}

setup_harden() {
    step "Hardening (--harden)"
    if ! command -v python3 >/dev/null 2>&1; then
        warn "python3 não encontrado; --harden pulado (nada alterado)"
        return 0
    fi
    if want_target claude; then
        harden_merge claude-settings "$CLAUDE_DIR/settings.json"
    fi
    if want_target codex; then
        harden_merge codex-env "$CODEX_DIR/config.toml"
        install_file "$REPO_DIR/harden/workflow-ai.rules" "$CODEX_DIR/rules/workflow-ai.rules"
    fi
}

# ------------------------------------------------------------------ relatório

count_entries() { # conta entradas (arquivos, dirs ou links) que casam com $2 em $1
    [ -d "$1" ] || { echo 0; return; }
    find "$1" -mindepth 1 -maxdepth 1 -name "$2" ! -name '.*' | wc -l | tr -d ' '
}

report() {
    step "Resumo"
    [ "$DRY_RUN" = 1 ] && say "  (dry-run: nada foi alterado)"
    say "  alterações: $N_CHANGED | já corretos: $N_OK | backups: $N_BACKUP | avisos: $N_WARN"
    if want_target claude; then
        say "  Claude: skills=$(count_entries "$CLAUDE_DIR/skills" '*') agents=$(count_entries "$CLAUDE_DIR/agents" '*.md') commands=$(count_entries "$CLAUDE_DIR/commands" '*.md')"
    fi
    if want_target codex; then
        say "  Codex:  skills(~/.agents/skills)=$(count_entries "$AGENTS_SKILLS_DIR" '*') agents=$(count_entries "$CODEX_DIR/agents" '*.toml')"
    fi
    if [ "$N_BACKUP" -gt 0 ] && [ "$DRY_RUN" = 0 ]; then
        say "  Backups em: $BACKUP_DIR (lista em MANIFEST.tsv)"
    fi
    local d broken="$STAGE/broken.txt"
    : > "$broken"
    for d in "$CLAUDE_DIR/agents" "$CLAUDE_DIR/skills" "$CLAUDE_DIR/commands" "$AGENTS_SKILLS_DIR"; do
        [ -d "$d" ] || continue
        find "$d" -mindepth 1 -maxdepth 1 -type l ! -exec test -e {} \; -print >> "$broken"
    done
    for d in "$CLAUDE_DIR/CLAUDE.md" "$CODEX_DIR/AGENTS.md" "$OPENCODE_DIR/AGENTS.md"; do
        if [ -L "$d" ] && [ ! -e "$d" ]; then printf '%s\n' "$d" >> "$broken"; fi
    done
    if [ -s "$broken" ]; then
        say "  Symlinks quebrados encontrados (não removidos; revise manualmente):"
        sed 's/^/    /' "$broken"
    fi
    if [ -s "$STAGE/warnings.txt" ]; then
        say "  Avisos:"
        sed 's/^/    - /' "$STAGE/warnings.txt"
    fi
}

# ------------------------------------------------------------------ main

say "workflow-ai: repo=$REPO_DIR"
say "  alvos: $( [ "$DO_CLAUDE" = 1 ] && printf 'claude ')$( [ "$DO_CODEX" = 1 ] && printf 'codex ')$( [ "$DO_OPENCODE" = 1 ] && printf 'opencode')"
[ "$DRY_RUN" = 1 ] && say "  modo: dry-run"

step "Conteúdo próprio (symlinks para o repo; toml/skills do Codex gerados)"
plan_own_content

if [ "$THIRD_PARTY" = 1 ]; then
    step "Terceiros: cache em $VENDOR_DIR"
    fetch_all_repos
    plan_third_party
fi

check_collisions

step "Aplicando"
apply_plan

if [ "$THIRD_PARTY" = 1 ]; then
    install_engines
    install_graphify
fi
if want_target claude; then
    if command -v python3 >/dev/null 2>&1; then
        harden_merge claude-stop-failure "$CLAUDE_DIR/settings.json"
        if [ -d "$REPO_DIR/mods/quota-guard" ]; then
            harden_merge claude-plugin-dirs "$CLAUDE_DIR/settings.json" "$REPO_DIR/mods/quota-guard"
        fi
    else
        warn "python3 ausente; hook StopFailure e env.CLAUDE_CODE_PLUGIN_DIRS não configurados"
    fi
fi
[ "$MCP" = 1 ] && setup_mcp
[ "$HARDEN" = 1 ] && setup_harden

report
