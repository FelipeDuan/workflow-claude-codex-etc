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
| OpenCode | 2.0.32 (fixada; npm com integridade sha512, em `~/.opencode`) | CONFIRMADO FUNCIONAL (laboratório) | serviço movido para a porta 49375 (conflito com o ai-memory em 49374); plugin + MCP do ai-memory; descobre as skills de `~/.claude/skills` e `~/.agents/skills`; modelos `opencode/*-free` sem login | política de permissões; AGENTS.md global; provedor econômico com login |
| Paseo | — | PENDENTE | não instalado | verificar procedência e instalação oficial |
| AI-Memory | 3.2.0 (fixada) | EXPERIMENTAL: handoff Claude→Codex ok, Codex→Claude parcial | binário em `~/.local/lib/ai-memory`; LaunchAgent `com.github.akitaonrails.ai-memory` em 127.0.0.1:49374 com bearer token; hooks Claude+Codex em **allowlist** (só repos com `.ai-memory.toml`), `--project-strategy repo-root`; MCP Claude via `mcp-bridge` conectado | resolver lacunas do T2 |
| Antigravity / Gemini | — | EXPERIMENTAL (opcional) | não instalado | fora do caminho crítico |
| DeepSeek Harness | — | PENDENTE | não instalado | só com justificativa |
| Handoff entre harnesses | ai-memory 3.2.0 | CONFIRMADO FUNCIONAL (laboratório) | Claude → Codex → OpenCode → Claude, ver T2 | testar parada abrupta |
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

## T2 completo — Claude → Codex → OpenCode → Claude, 22/10/2026: CONFIRMADO
- Ligado `capture_assistant` (servidor + hooks Claude/Codex/OpenCode). A última mensagem de cada agente agora vai no handoff automático.
- Etapa 3, OpenCode 2.0.32 com `opencode/deepseek-v4.1-flash-free`: resumiu as etapas 1 e 2 e a decisão vigente só pelo ai-memory. Entregou `--max` com argparse, 11 testes e o commit `a050054`, em 1:15.
- Retorno ao Claude (Haiku, só ai-memory): identificou o OpenCode como último agente, o que ele entregou e o próximo passo. Também avisou que havia uma sessão posterior que ele não leu.
- Gotchas:
  1. O OpenCode 2 usa por padrão a mesma porta do ai-memory, resolvido com `opencode service set port 49375`.
  2. Um `opencode run` disparado junto com `service restart` trava. É preciso esperar o serviço subir.
  3. O agente `build` do OpenCode vem com a permissão `*` liberada.
  4. O OpenCode não lê o AGENTS.md global (`~/.config/opencode/AGENTS.md` não existe).

## PRÓXIMOS PASSOS (aprovados pelo Felipe em 22/10/2026). Retomar daqui
Trabalhar no worktree `~/Workspace/tools/workflow-ai-ai-os`, branch `feat/ai-os-v2`. A pasta `~/Workspace/tools/workflow-ai` é a config ao vivo (branch de design): NÃO fazer checkout nela antes do merge. A implementação vai para um agente; o orquestrador verifica.

1. **CONCLUÍDO NO REPO (instalação pendente): install.sh ganha o alvo `opencode`**, no mesmo padrão dos alvos claude/codex. Symlink `~/.config/opencode/AGENTS.md` → `AGENTS.md` do repo. As skills já são descobertas via `~/.claude/skills` e `~/.agents/skills`, então não duplicar. Testar com `install.sh --dry-run` e rodar `scripts/check.sh`.
2. **CONCLUÍDO NA CONFIG LOCAL: Política de permissões do OpenCode 2.** O agente `build` vem com `*`. Ler a doc oficial de permissions da v2 (https://opencode.ai/v2/docs). Configurar `bash` e edição fora do projeto como "ask"; manter o MCP ai-memory. Arquivo: `~/.config/opencode/opencode.json` (fazer backup antes).
3. **CONCLUÍDO NO REPO (instalação pendente): Hook `StopFailure` no Claude:** quando `error` for `rate_limit`, `overloaded` ou `billing_error`, rodar `ai-memory finalize-session --agent claude-code`, que gera handoff com a última mensagem. Versionar no repo (o install.sh aplica) e testar simulando o payload pelo stdin.
4. **Mod "quota-guard" no Claude** (skill plugin-authoring): em `session.measure`, quando `rateLimits` `five_hour` ≥ 85%, status line + toast com `resetsAt` e um pedido para o agente escrever a nota de estado. Decidir onde o mod mora no repo e como o install.sh o instala.
5. **CONCLUÍDO COM RESSALVAS: Comparar provedores econômicos para o OpenCode.** Pesquisa oficial de 22/10/2026 em [PROVEDORES.md](PROVEDORES.md): DeepSeek, GLM/Z.ai, Kimi/Moonshot, Model Studio internacional e NVIDIA, com preços, modelos/IDs, coding, dados e integração v2. Lacunas marcadas como "não confirmado", inclusive catálogo nominal da v2 e preços que as páginas não expuseram. Nenhum cadastro, chave ou contratação.
6. **Merge de `feat/ai-os-v2` → `feat/design-workflow-v1`** depois de 1–3, e reaplicar `install.sh` com dry-run antes. Só com aprovação do Felipe.
7. Depois: Paseo (fase de orquestração e failover automático) e SGG.

Já validado (não refazer): ai-memory 3.2.0, OpenCode 2.0.32, handoff Claude→Codex→OpenCode→Claude, skill memory-backfill, Claude-Mem excluído de laboratorio e workflow-ai.

## Execução dos passos 1–3 (Codex, 22/10/2026)

- Passo 1: alvo `opencode` incluído no padrão de `--only`, também selecionado por padrão. Planeja apenas o symlink de `AGENTS.md`, respeita `XDG_CONFIG_HOME` e não duplica skills. O symlink ainda não foi instalado.
- Passo 2: consultada a [documentação oficial de permissions v2](https://opencode.ai/v2/docs/permissions). O formato é `permissions` com `action/resource/effect`; o comando Bash usa a ação `shell`. Configuradas `shell: * → ask` e `external_directory: * → ask` em `~/.config/opencode/opencode.json`. A segunda pede confirmação também para leituras externas, conforme o limite de diretório da v2. O MCP e os demais valores foram preservados, conferidos contra o backup `~/.config/opencode/opencode.json.bak-20261022-165841`. Pela documentação, regras do agente vêm depois das globais; o `build` padrão só acrescenta permissão para perguntas. Regras específicas de agentes e aprovações persistidas podem alterar o resultado.
- Passo 3: `scripts/stop-failure.py` lê JSON pelo stdin, filtra os três erros aprovados, exige `cwd`, `session_id` e marcador `.ai-memory.toml` no diretório ou ancestral. Executa `ai-memory finalize-session --agent claude-code --session-id <id>` no `cwd` do payload, sem shell. O instalador planeja o symlink do script e faz merge aditivo e idempotente no `settings.json` com backup. O hook ainda não foi instalado.
- Fonte do payload e matcher: [referência oficial de hooks do Claude](https://code.claude.com/docs/en/hooks#stopfailure). `last_assistant_message` nesse evento contém o erro da API; o hook não o usa como nota. O `finalize-session --help` local confirmou `--session-id` e resolução de projeto/workspace pelo diretório. A geração de handoff com a última mensagem não foi confirmada em falha real.

Validação:

- `python3 -m unittest discover -s tests`: 2 testes passaram. Cobrem stdin com os três erros, dry-run e execução com `ai-memory` falso no PATH, conferindo argv/cwd/id; payloads ignorados/inválidos e projeto sem marcador; merge preservando hooks existentes, idempotência e JSON inválido. Nenhum `finalize-session` real foi executado.
- `bash scripts/check.sh`: passou. A validação TOML com `tomllib` foi pulada pelo Python disponível; a conversão via awk passou.
- `./install.sh --dry-run --only opencode --no-third-party --no-mcp`: passou, 1 symlink planejado, 0 avisos.
- `./install.sh --dry-run`: executado, código 2 na etapa Graphify. A consulta do `uv` ao ambiente instalado foi bloqueada pelo sandbox; o instalador não chegou ao resumo. O fluxo existente não foi alterado por isso.
- `UV_TOOL_DIR=/tmp/workflow-ai-uv-tools ./install.sh --dry-run`: passou, 76 alterações planejadas, 143 corretos, 70 backups planejados, 0 avisos. A variável isola a consulta de ferramentas do `uv`; não instala nada. `./install.sh --dry-run --no-third-party --no-mcp` também passou (75 alterações planejadas, 0 avisos).
- `opencode` não está no PATH desta sessão. Pelo caminho absoluto, `--version` e `--help` foram bloqueados ao abrir o log fora do sandbox. O `package.json` local confirma 2.0.32. Não foi possível confirmar a configuração carregada pelo runtime nem observar os prompts de permissão; o formato foi confirmado pela documentação oficial v2.

Estado: alterados `install.sh`, `scripts/harden.py`, `scripts/stop-failure.py`, `tests/test_stop_failure.py`, este STATUS e a config local do OpenCode (com backup). Nenhum commit, instalação real ou alteração na pasta `~/Workspace/tools/workflow-ai`. Passos 4 em diante não executados. Próximo passo: o orquestrador revisar o diff e os testes; aplicação dos links/hook fica para a instalação aprovada após o merge do passo 6.

## Gotcha: `ai-memory run` retoma por padrão
`ai-memory run codex exec ...` vira `codex exec resume <sessão>` quando o workstream já tem uma sessão do Codex, e as flags como `--sandbox` são rejeitadas. Para tarefa nova, usar `ai-memory run --fresh codex exec ...`. Para continuar o trabalho, `ai-memory run codex`.

## Rodada de 22–23/10/2026 (pós-reset): concluído
- Passo 4: mod `quota-guard` (5h + semana) validado em sessão real; o install.sh o carrega via `CLAUDE_CODE_PLUGIN_DIRS`.
- Leitor oficial da franquia do Codex: `scripts/quota_codex.py` (App Server). Rodar fora do sandbox (I-06).
- Modelos gratuitos do OpenCode (GLM-5.3-Flash e DeepSeek V4.1 Flash) testados em worktrees paralelos: os dois ok. Isso fecha o T3.
- ADR-0002 (roteamento por franquia), `telemetria.jsonl` (5 tarefas), `PESQUISA-ROTEAMENTO.md` e `INCIDENTES.md` (11 itens).
- Próximo: merge em `feat/design-workflow-v1` + install.sh; depois, teste do Paseo Desktop no laboratório (sem o Continuity), se o Felipe aprovar.

## 23/10/2026: Paseo adotado (ADR-0003)
- POC no laboratório aprovada: 3 harnesses, paralelismo em worktrees, aprovações, ai-memory, sem dupla captura no Claude-Mem, sem processos órfãos. Detalhes no ADR-0003; incidentes I-12 a I-16.
- Correções feitas: OpenCode no Paseo (override de comando); MCP do ai-memory no Codex via `mcp-bridge` (vale também fora do Paseo); `~/.paseo/worktrees/**` excluído do Claude-Mem; voz/ditado desligados.
- Guia: `docs/ai-os/USO-DIARIO.md`.

## PRÓXIMOS PASSOS (rodada seguinte)
1. Backlog de ferramentas (pesquisa delegada ao Codex → `docs/ai-os/BACKLOG-FERRAMENTAS.md`): Claude Code Setup (diagnóstico somente leitura), Skill Creator (já instalado como plugin: usar em A/B das skills), Task Observer, Serena, Headroom (só em teste isolado, por causa do proxy), Context7 (já instalado como plugin), OmniRoute/OpenRouter (ver PESQUISA-ROTEAMENTO), Ponytail 5.x × SHA do third-party.lock.
2. Remover `~/.paseo/models` (~1 GB de voz em inglês): **aguarda autorização do Felipe**.
3. POC D pendente: travamento por stdin dentro do Paseo; comparar `paseo usage` com os sensores; skills de orquestração do Paseo (ver onde instalam antes).
4. Política de roteamento aplicada no Paseo: perfis (Architecture/Implementation/Economy) + o coordenador consultando os arquivos de franquia.
5. Depois: SGG como primeiro projeto real.
