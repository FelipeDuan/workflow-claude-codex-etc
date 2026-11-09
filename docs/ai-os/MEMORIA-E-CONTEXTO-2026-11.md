# Memória, handoff e contexto: validação de 09/11/2026

Tarefa P5. Investigação somente leitura, sem mudança de configuração. Base: `v0.1.0` (`f0507a3`). Contagens e tamanhos são do dia 09/11/2026; tokens são estimados em caracteres ÷ 4 (erro provável de ±30%).

## 1. Claude-Mem: o que ainda está ativo

| Item | Evidência (comando → saída resumida) |
|---|---|
| Plugin habilitado | `claude plugin list` → `claude-mem@thedotmack 12.4.9 ✔ enabled` (também `enabledPlugins` em `~/.claude/settings.json`) |
| Hooks de captura | `hooks/hooks.json` do plugin: `SessionStart` (startup, clear, compact: sobe o worker e injeta contexto), `UserPromptSubmit` (session-init), `PostToolUse *` (observation), `PreToolUse Read` (file-context), `Stop` (summarize) |
| Worker | `curl 127.0.0.1:37701/api/health` → `ok`, v12.4.9, pid 8434, no ar desde 27/10 (`managed: false`, ou seja, sem LaunchAgent; quem sobe é o hook de SessionStart) |
| Banco | `~/.claude-mem/claude-mem.db`: 266 MB (+ WAL 4 MB); `chroma/` 68 MB; `logs/` 98 MB; total ≈ 440 MB |
| Conteúdo | `sqlite3 -readonly ... select count(*) from observations` → 940 observações, 195 sessões |
| Última escrita | 09/11 00:58 (projeto `Workspace`) |
| Captura desde 27/10 | 117 observações, **todas** no projeto `Workspace` (cwd na raiz `~/Workspace`). Nenhum outro projeto escreveu nesse período |
| Exclusões | `CLAUDE_MEM_EXCLUDED_PROJECTS` em `~/.claude-mem/settings.json` cobre os projetos que já têm marcador do ai-memory, o hub `tools/` e `~/.paseo/worktrees/**` |
| Transcript-watch do Codex | `CLAUDE_MEM_TRANSCRIPTS_ENABLED=false` (desligado, I-22) |
| Observador | `claude-sonnet-4-6` via CLI (`CLAUDE_MEM_CLAUDE_AUTH_METHOD=cli`), consome franquia Claude em cada sessão capturada |

**Injeção no SessionStart.** O endpoint que o hook usa (`GET /api/context/inject?project=<cwd>`, somente leitura) devolveu: `Workspace` 6.966 caracteres (~1.740 tokens), `tools` 7.714 (~1.930), `workflow-ai` 7.307 (~1.830), e 78 caracteres (vazio) para um worktree novo como `wt-p5`. O limite é `CLAUDE_MEM_CONTEXT_OBSERVATIONS=50`. Ou seja: ~1,7 a 1,9 mil tokens por sessão aberta nesses diretórios, mesmo nos projetos excluídos da captura. O conteúdo do bloco de `Workspace` inclui títulos de observações de projetos restritos (não reproduzidos aqui): a injeção traz para o contexto de uma sessão qualquer em `~/Workspace` coisas que o ai-memory manteria isoladas pelo workspace `restrito`.

**O que o ai-memory já cobre e o que só o Claude-Mem tem.** Marcadores `.ai-memory.toml` achados até 4 níveis em `~/Workspace`: 18 (hub, workflow-ai e worktrees, laboratorio, phpi, dotfiles, financas, pesquisa-operacional, marketing-digital, painel-dados-deputado, gestao-projetos, bun-backend-foundation, felipeduan-site, atendimento-api, labs). Em projetos restritos: 0 marcadores (busca até 7 níveis; só contagem). O Claude-Mem tem observações históricas de projetos que **não** têm marcador e que o ai-memory nunca viu: `Workspace` 143, `artigo-ssp` 141, `portfolio` 133, `feliz-um-ano-amor` 80, `app-laesa` 65, `repeticao` 31, `superhero-universe-modern` 29, `cp-cpp` 20, `gastrono-back` 20, `03-funcoes` 17, `pacto-economia` 16, entre outros menores. Também há 67 observações com "projeto" `12.4.9` (lixo de nome de projeto). Só o `memory-backfill` traz esse histórico, e só sob demanda. Nada disso foi verificado quanto a valor: é o arquivo morto que o checklist abaixo pede para decidir.

### Checklist de aposentadoria do Claude-Mem (NÃO executado)

Ordem pensada para ser reversível até o passo 5. Comandos compatíveis com fish.

| # | Passo | Comando | Reverter | Verificar |
|---|---|---|---|---|
| 0 | Pré-condição: Felipe decide o que fazer com o histórico dos projetos sem marcador (backfill de páginas duráveis ou descartar) | `memory-backfill` (skill) por projeto escolhido | n/a | página no ai-memory (`memory_query`) |
| 1 | Backup consistente do banco | `mkdir -p ~/.ai-os-backup/claude-mem-20261115; and sqlite3 ~/.claude-mem/claude-mem.db ".backup '$HOME/.ai-os-backup/claude-mem-20261115/claude-mem.db'"` e `cp -R ~/.claude-mem/settings.json ~/.claude-mem/chroma ~/.ai-os-backup/claude-mem-20261115/` | apagar a pasta de backup | `sqlite3 -readonly <backup> "select count(*) from observations"` → 940 (ou mais) |
| 2 | Desabilitar o plugin (some hooks, MCP de busca e injeção) | `claude plugin disable claude-mem@thedotmack` | `claude plugin enable claude-mem@thedotmack` | `claude plugin list` mostra `disabled`; sessão nova sem bloco "recent context" |
| 3 | Parar o worker (não é LaunchAgent) | `kill (jq -r .pid ~/.claude-mem/worker.pid)` | reabilitar o plugin; o SessionStart sobe o worker de novo | `curl -s -m3 127.0.0.1:37701/api/health` sem resposta; `ps aux \| grep worker-service` vazio |
| 4 | Período de observação (2 semanas) usando só o ai-memory | n/a | passo 2 reverso | rodar o teste de retomada (seção 5) e checar que não houve pergunta sem resposta que o Claude-Mem teria dado |
| 5 | Desinstalar o plugin (só após o passo 4 e autorização do Felipe) | `claude plugin uninstall claude-mem@thedotmack` | `claude plugin install claude-mem@thedotmack` (o banco continua em `~/.claude-mem`) | `claude plugin list` sem a entrada; `ls ~/.claude/plugins/cache/thedotmack` |
| 6 | Dados em `~/.claude-mem` (440 MB): manter como arquivo morto ou remover | remoção só com autorização explícita do Felipe | restaurar do backup do passo 1 | `du -sh ~/.claude-mem` |

Observação: o STATUS prevê "desligar a captura do Claude-Mem (meados de novembro)". A captura já está quase inerte (117 observações em 13 dias, todas de um diretório), então o ganho real da aposentadoria é a injeção de ~1,8 mil tokens, o worker residente e a franquia do observador, não espaço em disco.

## 2. ai-memory

| Item | Evidência |
|---|---|
| Versão e serviço | `ai-memory --version` → 3.2.0; LaunchAgent `com.github.akitaonrails.ai-memory` ativo (pid 792, `launchctl list`), servidor em `127.0.0.1:49374` |
| Volume global | `ai-memory status`: 135 páginas (172 versões), 141 sessões, 27.830 observações, banco de 42,5 MiB, FTS 100%, embeddings locais 170/170, LLM desabilitado, 0 descartes, 0 falhas |
| Spool | 16 a 23 eventos pendentes com o mais antigo em <20 s e 0 retries: fila normal em sessão ativa |
| Projetos com `.ai-memory.toml` | 18 (lista na seção 1); modo `allowlist` ("repositórios sem marcador não enviam nada") |
| Hooks Claude | `settings.json`: SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, PreCompact, Stop, SessionEnd, SubagentStart, SubagentStop, mais `StopFailure` (rate_limit/overloaded/billing_error) por script próprio |
| Hooks Codex | `~/.codex/hooks.json`: 7 comandos `ai-memory ... --agent codex`; `config.toml` registra o MCP |
| OpenCode | plugin `~/.config/opencode/plugins/ai-memory-opencode2.ts` + MCP no `opencode.json` |
| Antigravity | sem hook novo; fora da automação pela ADR-0006 (só uso direto). O `doctor` ainda lista 3 sessões antigas dele no workflow-ai (9 observações capturadas) |
| Captura do workflow-ai | `ai-memory doctor` no repo: `marker valid`; claude-code 2→3, codex 24→24, open-code 2→5, antigravity-cli 3→9 (sessões locais → capturadas); "Every harness ... is captured". O `doctor` rodado no diretório home acusa codex/open-code sem captura, o que é esperado (home não tem marcador) e não uma falha |
| Briefing do projeto | 41 páginas, 41 sessões em 30 dias, 4.706 observações, 14 sessões e 1.589 observações nos últimos 7 dias, 0 regras (`_rules/`), 1 decisão fixada (`design-director-main-conversation`) |
| Handoffs pendentes | **21** abertos no workflow-ai (`memory_handoff_list`): 10 de 23 a 26/10 e 11 de hoje. Entre os de hoje, 6 têm resumo de ~65 caracteres ("Single-prompt session") e 1 é só o prompt da tarefa. Nenhum foi aceito ou cancelado por esta tarefa |
| Sessões sem fim | o briefing marca 2 sessões `ended: false` (a atual e a do worktree `p2-task-ledger`) e uma do OpenCode `ended: false, handed_off: true` |

## 3. Teste de retomada (Q6): amostra n=1

Procedimento: `memory_briefing` (settled_first), `memory_handoff_list` (21 handoffs lidos por inteiro, em `jq`) e uma `memory_query` com os termos dos fatos, todos somente leitura, projeto `pessoal/workflow-ai`. Em paralelo, conferência do que sai só do STATUS/git neste checkout.

Critério: recuperado = o fato aparece com o identificador exato pedido (ADR, hash, caminho). Parcial = a ideia aparece sem o identificador. Resultado "memória" inclui as 3 chamadas acima; o arquivo de memória do Claude Code (`MEMORY.md`) é um terceiro canal e está separado.

| Fato | Briefing/handoffs/query do ai-memory | MEMORY.md do Claude | STATUS.md / git |
|---|---|---|---|
| (a) Antigravity fora da automação, ADR-0006 | Parcial: o handoff da tarefa P0a traz a decisão ("tirar o agy de TODA automação") mas nenhum texto cita "ADR-0006"; "ADR-0005" aparece em 2 prompts antigos sem marca de substituída | Sim, exato (`antigravity-no-ai-os.md` cita ADR-0006 e que substitui a 0005) | Sim: `decisions/0006-antigravity-fora-da-automacao.md` |
| (b) v0.1.0 = `f0507a3` em main | Não (0 ocorrências de `v0.1.0`/`f0507a3`) | Não | Sim: `git log`/`git tag`; `git branch --contains f0507a3` inclui `main` (o STATUS ainda descreve a integração como "próximo passo") |
| (c) vigia grava `history/*.jsonl` | Parcial: handoff da P1 descreve a série histórica e o contrato JSONL, sem o caminho `history/` | Não | Sim: `STATUS.md` linha 243 |
| (d) protocolo GQM em `docs/research/PROTOCOLO-GQM.md` | Não (a query por "GQM" não achou) | Não | Sim: arquivo e merge `f0507a3` |
| (e) a CLI do Paseo não expõe labels | Não (aparecem trechos de código sobre `labels`, não o achado) | Não | Sim: `STATUS.md` linha 250 |
| (f) próximos passos P2 a P5 | Fraco: só indícios (sessão rodando em `p2-task-ledger`); lista P2 a P5 ausente | Não | Sim: `STATUS.md` linha 252 |

**Resultado (n=1, sem generalizar):** ai-memory sozinho recupera 0 de 6 fatos completos, 2 parciais (a, c) e 1 indício (f). Com o `MEMORY.md` do Claude Code sobe para 1 de 6 completo (a). STATUS.md + git recuperam 6 de 6. Nenhum fato apareceu **errado**; o risco encontrado foi de **desatualização**: a ADR-0005 segue em 2 handoffs pendentes de outubro sem sinal de substituição, e o `STATUS.md` (seção marcada "atualizado em 26/10/2026") não diz que a integração e a tag `v0.1.0` já aconteceram.

Por que o briefing recupera tão pouco: ele traz contagens e títulos de sessão, que são o prompt da tarefa truncado em 80 caracteres. Os handoffs guardam o prompt original e a última resposta do agente, não as decisões do dia. Só uma página durável (1 decisão) está fixada. A consolidação por LLM está desligada por decisão (ADR-0004), então ninguém transforma sessões em fatos.

Limitações: (1) o bloco de SessionStart do ai-memory nesta sessão não foi medido, só os dados que ele usa; (2) uma sessão nova real poderia usar `memory_read_session_observations` e achar mais, o que não foi testado; (3) n=1, avaliador único, fatos escolhidos por quem já os conhecia.

## 4. Contexto fixo por sessão neste diretório

| Fonte | Tamanho | Tokens (≈) |
|---|---|---|
| Lista de skills + descrições (281 `SKILL.md` instalados; a lista enviada à sessão é truncada) | 73 mil caracteres só em nome+descrição nos arquivos | 6 a 18 mil (a lista real do prompt não foi medida) |
| `~/.claude/CLAUDE.md` (link para `workflow-ai/AGENTS.md`) | 20.262 caracteres | ~5.070 |
| Bloco do claude-mem | ~7.000 a 7.700 caracteres | ~1.700 a 1.900 |
| Bloco do ai-memory (handoff de SessionStart) | não medido; o maior handoff aberto tem 3,5 mil caracteres | até ~900 |
| `CLAUDE.md` do hub | 1.594 caracteres | ~400 |
| `MEMORY.md` do projeto (só o índice; os 2 arquivos ligados têm 2,5 mil caracteres) | 234 caracteres | ~60 |
| `AGENTS.md` do repo | não é carregado pelo Claude Code neste diretório (o hub tem `CLAUDE.md`; o `AGENTS.md` do hub é cópia dele) | 0 |

Total fixo estimado: ~14 a 27 mil tokens, dominado pela lista de skills. Estimativa de tokens das ferramentas MCP diferidas (nomes de ~700 ferramentas, a maioria do `dokploy-mcp`) não foi medida, mas pesa na lista.

**Os 3 maiores:** (1) lista de skills; (2) `~/.claude/CLAUDE.md`, dos quais 6.824 caracteres (34%) são a seção "Agents, skills and commands", que repete o que as descrições dos próprios agentes e skills já dizem; (3) bloco do claude-mem.

**O que sairia sem perda (sugestões, nada aplicado):** o bloco do claude-mem (aposentar, seção 1); a seção de agentes e skills do CLAUDE.md global, reduzida às regras de ordem (cadeias de revisão, design, pesquisa), cortando ~1,2 mil tokens; skills de domínio que não são do Felipe e aparecem em todo projeto (`astronomer-data:*`, ~25 itens, e as de Figma fora de projetos de design), via plugin habilitado por projeto; plugin `data-engineering` e MCP do Dokploy fora de projetos sem Dokploy.

## 5. Protocolo reaproveitável de teste de retomada (Q6)

1. **Escolher 6 fatos verdadeiros** do dia, de tipos diferentes: 2 decisões (com número de ADR), 2 estados de git (hash, tag, branch), 1 achado técnico, 1 próximo passo. Escrever a lista com a fonte de cada um **antes** de testar.
2. **Congelar** o estado (anotar data, `git rev-parse HEAD`, versão do ai-memory).
3. **Sessão nova**, no mesmo diretório, sem ler STATUS/git: rodar `memory_briefing` (`settled_first: true`), `memory_handoff_list` e uma `memory_query` por fato. Registrar o que cada chamada devolveu, sem interpretar.
4. **Pontuar** cada fato por canal (ai-memory, MEMORY.md, STATUS/git): 1 = fato com identificador exato; 0,5 = ideia sem identificador; 0 = ausente. Marcar separadamente: **errado** (contradiz a fonte) e **desatualizado** (era verdade, foi superado).
5. **Fidelidade** = soma dos pontos ÷ 6, por canal (a fórmula de Q6 do `PROTOCOLO-GQM.md` usa apenas "recuperado ÷ verificado"; aqui o 0,5 é um refinamento a validar).
6. **Onde registrar:** uma linha por rodada em `docs/ai-os/telemetria.jsonl` (feita pelo orquestrador, não por esta frente) e a tabela completa na seção de resultados do documento da rodada. Repetir em semanas diferentes e comparar antes e depois de mudanças (aposentar o claude-mem, ligar consolidação, escrever páginas duráveis).
7. **Não generalizar** de uma rodada: relatar n, avaliador e os fatos usados.

Rodada de 09/11/2026 (esta): n=1; ai-memory 0 completos + 2 parciais + 1 indício; MEMORY.md 1; STATUS/git 6.

## 6. Recomendações priorizadas

| # | Recomendação | Custo | Benefício |
|---|---|---|---|
| 1 | Atualizar o STATUS ao fechar cada sessão (já é a regra da ADR-0004) e registrar nele a integração, a tag `v0.1.0` e o P2 a P5. Hoje ele é o único canal que acerta 6/6, mas está marcado em 26/10 | baixo (orquestrador) | alto: é a fonte que a retomada realmente usa |
| 2 | Gravar 3 a 5 páginas duráveis (`decisions/`) para as decisões vigentes (ADR-0006, GQM, v0.1.0) por pedido explícito do Felipe, e marcar a ADR-0005 como substituída. É o único jeito de o briefing e a query recuperarem decisões | baixo a médio (escrita no ai-memory exige pedido) | alto: ataca a causa dos 0/6 |
| 3 | Cancelar, a pedido do Felipe, os handoffs obsoletos (10 de outubro, 6 sem conteúdo útil) para o handoff aberto ser confiável. Não aceitar para limpar | baixo | médio: reduz ruído e risco de ADR velha |
| 4 | Aposentar o Claude-Mem pelo checklist (passos 1 a 3 já economizam ~1,8 mil tokens por sessão, a franquia do observador e fecham a mistura com contexto de projetos restritos) | baixo, reversível até o passo 5 | médio |
| 5 | Enxugar a seção "Agents, skills and commands" do CLAUDE.md global e habilitar plugins de domínio por projeto | médio (mexe em config global, só com aprovação) | médio: de 3 a 8 mil tokens por sessão |
| 6 | Repetir o teste de retomada depois das ações 1 a 3 e comparar | baixo | valida Q6 com n>1 |
| 7 | Não ligar a consolidação por LLM agora (ADR-0004). Reavaliar depois do item 6, só se as páginas manuais não bastarem | n/a | evita custo e risco de memória envenenada |
