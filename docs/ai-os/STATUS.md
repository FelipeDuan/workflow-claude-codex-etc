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
| AI-Memory | — | PENDENTE | não instalado | só se Claude-Mem não cobrir a necessidade |
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
