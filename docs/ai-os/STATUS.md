# STATUS — Felipe AI OS

Legenda: CONFIRMADO FUNCIONAL · INSTALADO MAS NÃO VALIDADO · EXPERIMENTAL · PENDENTE · BLOQUEADO

## Componentes (auditoria somente leitura de 22/10/2026)

| Componente | Versão | Estado | Evidência | Próxima ação |
|---|---|---|---|---|
| Claude Code | 2.1.308 | CONFIRMADO FUNCIONAL | sessão atual rodando | — |
| Codex CLI | 0.154.0 | INSTALADO MAS NÃO VALIDADO | `codex login status` → "Logged in using ChatGPT" | tarefa real pequena |
| workflow-ai (instalação) | branch `feat/design-workflow-v1` | CONFIRMADO FUNCIONAL | `install.sh --dry-run`: 0 alterações, 214 corretos, 0 avisos; Claude 83 skills/15 agents/6 commands; Codex 89 skills/13 agents | — |
| Claude-Mem | 12.4.9 (plugin; 14.0.1 disponível) | CONFIRMADO FUNCIONAL (Claude) · EXPERIMENTAL (Codex) | 727 observações; sessões: 173 claude, 2 codex (transcript-watch ativo); observador usa `claude-sonnet-4-6` via CLI (consome franquia Claude) | comparar com ai-memory |
| Figma MCP (Claude) | plugin oficial | INSTALADO MAS NÃO VALIDADO | autenticado pelo Felipe em 22/10; ferramentas do MCP disponíveis na sessão | teste de leitura num arquivo real |
| Figma MCP (Codex) | — | PENDENTE | não consta em `~/.codex/config.toml` | decidir se precisa |
| Playwright MCP | plugin (Claude) + config.toml (Codex) | INSTALADO MAS NÃO VALIDADO | conectado nos dois | — |
| OpenCode | — | PENDENTE | não instalado | verificar canal oficial e versão |
| Paseo | — | PENDENTE | não instalado | verificar procedência e instalação oficial |
| AI-Memory | 3.2.0 (fixada) | INSTALADO MAS NÃO VALIDADO (Claude ok, Codex pendente) | binário em `~/.local/lib/ai-memory`; LaunchAgent `com.github.akitaonrails.ai-memory` em 127.0.0.1:49374 com bearer token; hooks Claude+Codex em **allowlist** (só repos com `.ai-memory.toml`), `--project-strategy repo-root`; MCP Claude via `mcp-bridge` conectado | Felipe aprovar hooks no Codex (`/hooks`); testar Etapa 2 no Codex |
| Antigravity / Gemini | — | EXPERIMENTAL (opcional) | não instalado | fora do caminho crítico |
| DeepSeek Harness | — | PENDENTE | não instalado | só com justificativa |
| Handoff entre harnesses | — | PENDENTE | — | teste Claude → Codex |
| Failover automático | — | PENDENTE | — | só depois do handoff manual |

## Git do workflow

- `origin` = FelipeDuan/workflow-claude-codex-etc, `upstream` = whosbea/workflow-claude-codex-etc.
- `main` = `origin/main` = `upstream/main` (3e2518b). É a versão com a identidade da Beatriz. Não fazer checkout dela em `~/Workspace/tools/workflow-ai`.
- `feat/design-workflow-v1`: publicada em `origin` em 22/10/2026 (antes só existia localmente).
- `feat/ai-os-v2`: criada a partir da branch de design, no worktree `~/Workspace/tools/workflow-ai-ai-os`.
- `~/.claude/CLAUDE.md` e `~/.codex/AGENTS.md` são symlinks para `~/Workspace/tools/workflow-ai/AGENTS.md`. A branch com checkout nessa pasta é a config global ativa.

## Conflitos e observações

- As skills do kit (`.agents/skills/*`) usam `summary:` no frontmatter em vez de `description:`, por isso não seriam descobertas. A `handoff` do kit também colide com a `handoff` do Matt Pocock, que já está instalada (aquela grava em diretório temporário, esta grava no repo).
- A shell de login é `/bin/zsh`, o fish é usado de forma interativa. Por isso o diagnóstico mostra zsh.
- O `dokploy-mcp` está registrado globalmente no Claude, fora do workflow. Ele carrega muitas ferramentas em todas as sessões.
- O Codex tem memória nativa (`~/.codex/memories_1.sqlite`). Ainda falta avaliar como ela se relaciona com o Claude-Mem.

## Registro de última sessão

- Agente executor: Claude Code (Opus 5.5)
- Data: 22/10/2026
- Pasta e worktree: `~/Workspace/tools/workflow-ai-ai-os` (`feat/ai-os-v2`)
- Última ação comprovada: commit 9cd2b96 (remove referências restantes à Beatriz)
- Testes: `install.sh --dry-run` ok; `python3 -m unittest discover -s tests` (kit) ok, 4 testes
- Próximo passo: verificar canais oficiais de OpenCode/Paseo/AI-Memory e pedir autorização de instalação

> Nunca registrar chaves/tokens/credenciais neste arquivo.

## Teste T2 — handoff (laboratório `~/Workspace/tools/laboratorio`)

**Etapa 1, Claude (`claude -p`, Sonnet), 22/10/2026: CONFIRMADO**
- Commit `eeeb803`. `python3 -m unittest` passou (4 testes). Nenhuma dependência externa.
- AI-Memory: 31 observações, 2 sessões, 1 página no escopo `laboratorio/laboratorio`.
- Handoffs abertos: **2**. Um foi registrado de forma explícita pelo agente via MCP (atribuído como `other`) e o outro foi gerado sozinho pelo hook de fim de sessão (`claude-code`). O próximo agente assume um deles e o outro fica pendurado. Ainda falta definir a política: só o automático, ou só o explícito.
- Claude-Mem capturou a mesma sessão (1 observação, 1 sessão). **A captura duplicada foi confirmada.**

**Etapa 2, Codex: PENDENTE**
- Os hooks do Codex estão "untrusted" até o Felipe rodar `/hooks` no Codex.
- O MCP do Codex usa `bearer_token_env_var` (`AI_MEMORY_AUTH_TOKEN`). Falta testar se `ai-memory run codex` injeta essa variável sozinho.

## Rollback do AI-Memory
- `ai-memory uninstall --apply`: remove hooks, MCP, skills e LaunchAgent instalados por ele.
- Backups anteriores à instalação: `~/.ai-os-backup/<timestamp>-pre-ai-memory/`, além dos backups com timestamp que o próprio ai-memory grava ao lado de cada arquivo alterado.
- Os dados ficam em `~/Library/Application Support/ai-memory`. Remover só com autorização.
