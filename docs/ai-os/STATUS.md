# STATUS — Felipe AI OS

Legenda: CONFIRMADO FUNCIONAL · INSTALADO MAS NÃO VALIDADO · EXPERIMENTAL · PENDENTE · BLOQUEADO

## Componentes (auditoria somente leitura de 22/10/2026)

| Componente | Versão | Estado | Evidência | Próxima ação |
|---|---|---|---|---|
| Claude Code | 2.1.308 | CONFIRMADO FUNCIONAL | sessão atual rodando | — |
| Codex CLI | 0.163.0 | CONFIRMADO FUNCIONAL | Etapa 2 do T2 executada | — |
| workflow-ai (instalação) | branch `feat/design-workflow-v1` | CONFIRMADO FUNCIONAL | `install.sh --dry-run`: 0 alterações, 214 corretos, 0 avisos; Claude 83 skills/15 agents/6 commands; Codex 89 skills/13 agents | — |
| Claude-Mem | 12.4.9 (plugin; 14.0.1 disponível) | CONFIRMADO FUNCIONAL (Claude) · EXPERIMENTAL (Codex) | 727 observações; sessões: 173 claude, 2 codex (transcript-watch ativo); observador usa `claude-sonnet-4-6` via CLI (consome franquia Claude) | comparar com ai-memory |
| Figma MCP (Claude) | plugin oficial | INSTALADO MAS NÃO VALIDADO | autenticado pelo Felipe em 22/10; ferramentas do MCP disponíveis na sessão | teste de leitura num arquivo real |
| Figma MCP (Codex) | — | PENDENTE | não consta em `~/.codex/config.toml` | decidir se precisa |
| Playwright MCP | plugin (Claude) + config.toml (Codex) | INSTALADO MAS NÃO VALIDADO | conectado nos dois | — |
| OpenCode | — | PENDENTE | não instalado | verificar canal oficial e versão |
| Paseo | — | PENDENTE | não instalado | verificar procedência e instalação oficial |
| AI-Memory | 3.2.0 (fixada) | EXPERIMENTAL: handoff Claude→Codex ok, Codex→Claude parcial | binário em `~/.local/lib/ai-memory`; LaunchAgent `com.github.akitaonrails.ai-memory` em 127.0.0.1:49374 com bearer token; hooks Claude+Codex em **allowlist** (só repos com `.ai-memory.toml`), `--project-strategy repo-root`; MCP Claude via `mcp-bridge` conectado | resolver lacunas do T2 |
| Antigravity / Gemini | — | EXPERIMENTAL (opcional) | não instalado | fora do caminho crítico |
| DeepSeek Harness | — | PENDENTE | não instalado | só com justificativa |
| Handoff entre harnesses | ai-memory 3.2.0 | EXPERIMENTAL | ver T2 abaixo | handoff de volta |
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

**Etapa 2, Codex 0.163.0 (`ai-memory run codex exec`), 22/10/2026: CONFIRMADO (com ressalvas)**
- O hook de SessionStart injetou o handoff sozinho. A primeira fala do Codex resumiu corretamente a Etapa 1 e a decisão vigente. Ele não reimplementou nada.
- Resultado: 10 testes passaram, só biblioteca padrão. Tempo de 1:05 e 37k tokens.
- O commit foi bloqueado pelo sandbox `workspace-write` do Codex, que protege o `.git`. O Claude orquestrador fez o commit (`6f57a69`). Isso é comportamento do Codex, não do ai-memory.

**Retorno ao Claude (`claude -p`, Haiku, só ai-memory): PARCIAL**
- O agente sabia da Etapa 1 e de que houve uma sessão do Codex depois. **Não sabia o que o Codex entregou**: a captura do Codex trouxe prompts e chamadas de ferramenta, mas não as saídas, e o Codex não deixou handoff de volta ao terminar.
- O modelo não inventou nada: apontou o commit desconhecido e pediu para conferir.

**Medições**
- ai-memory em `laboratorio`: claude-code 3 sessões capturadas, codex 1. No spool ficou 1 evento em trânsito.
- Claude-Mem em `laboratorio`: 2 sessões claude e 2 codex (transcript-watch), 6 observações. Captura duplicada nos dois harnesses.
- Ficou 1 handoff automático do claude-code ainda aberto (órfão), porque o explícito foi o que o Codex consumiu.

**Lacunas a resolver**
1. Retorno Codex → Claude: exigir handoff explícito no fim de cada sessão (skill/regra), ou ver se o `codex exec` dispara SessionEnd.
2. Política de handoff: um só por sessão. Hoje convivem o explícito e o automático.
3. Captura duplicada com o Claude-Mem: decidir o papel de cada um (proposta: ai-memory captura, Claude-Mem fica como arquivo consultável).
4. Commits em `codex exec`: usar `--sandbox` adequado ou deixar o commit para o orquestrador.

## Rollback do AI-Memory
- `ai-memory uninstall --apply`: remove hooks, MCP, skills e LaunchAgent instalados por ele.
- Backups anteriores à instalação: `~/.ai-os-backup/<timestamp>-pre-ai-memory/`, além dos backups com timestamp que o próprio ai-memory grava ao lado de cada arquivo alterado.
- Os dados ficam em `~/Library/Application Support/ai-memory`. Remover só com autorização.

## Skill `memory-backfill` (Claude-Mem → AI-Memory sob demanda), 22/10/2026: CONFIRMADO
- Projeto: workflow-ai, que passou a ser capturado pelo ai-memory (`.ai-memory.toml`, commit 4156752) e saiu do Claude-Mem (`CLAUDE_MEM_EXCLUDED_PROJECTS`).
- Pergunta: "por que o design-director roda na conversa principal?". O ai-memory não tinha a resposta. O Claude-Mem tinha na observação #405. O fato foi conferido em `skills/design-director/SKILL.md:10,66,69,95`, `agents/frontend-ux-ui.md:22`, `docs/design-workflow.md:11` e no commit `eb1e8db`. Uma página foi gravada: `decisions/design-director-main-conversation.md`.
- Na segunda pergunta, feita só ao ai-memory (Haiku), a resposta veio da página gravada. O Claude-Mem não foi consultado.
- Decisão do Felipe: a skill grava sem pedir confirmação. Os limites são 5 páginas por execução, gravar só fatos conferidos e registrar a proveniência.
- Aposentadoria do Claude-Mem: em fases. Cada projeto que entra no ai-memory sai do Claude-Mem; em 3–4 semanas avaliamos a frequência do backfill; o plugin só é removido no fim.
