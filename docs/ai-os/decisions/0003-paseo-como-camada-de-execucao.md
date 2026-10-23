# ADR-0003: Paseo como camada de execução (provisória)

**Status:** aceita em 23/10/2026 após a POC no laboratório. Revisar se aparecer um problema que a POC não pegou.

## Contexto

Até aqui o orquestrador (Claude) disparava Codex e OpenCode por script, conferia se a sessão começou e coletava o resultado. Funcionou, mas de forma artesanal: o I-01 (Codex parado 20 min sem ninguém ver) veio daí. A comparação em `ORQUESTRADORES.md` indicou o Paseo para o primeiro teste. A auditoria `AUDITORIA-CONTINUITY.md` recomendou não instalar o plugin Continuity.

## Decisão

Adotar o **Paseo 0.12.0** (Homebrew cask, versão estável) como camada de execução: agentes, worktrees, aprovações, mensagens e cockpit. O Felipe AI OS continua dono de:

- instruções, skills, agents e hooks (`workflow-ai`);
- memória e handoff (ai-memory);
- sensores de franquia (quota-guard, `quota_codex.py`) e política de roteamento (ADR-0002);
- telemetria, incidentes e ADRs.

**Continuity: não instalar.** O handoff continua pelo ai-memory. Um failover automático, se vier, será uma integração pequena nas APIs oficiais do Paseo, com os requisitos de segurança listados na auditoria.

## Evidências da POC (23/10/2026, laboratório)

| Critério | Resultado |
|---|---|
| Instalação/daemon | `brew install --cask paseo` → 0.12.0; daemon só em `127.0.0.1:6767`, relay desligado, sem conflito de porta |
| Três harnesses | Claude e Codex detectados de cara; OpenCode depois do override de comando (I-12) |
| Paralelismo | Claude (Haiku) e OpenCode (DeepSeek free) em 2 worktrees do Paseo, ao mesmo tempo; cada um só com o próprio arquivo, branches separadas |
| AGENTS.md e skills | Os dois responderam "Felipe, pt-BR" e encontraram `memory-backfill` |
| Aprovações | O modo padrão pediu aprovação para shell/escrita; `paseo permit ls/allow` funcionou; `paseo wait` mostra "waiting for permission" (I-16) |
| ai-memory | Sessões dos worktrees do Paseo associadas ao projeto `laboratorio` (estratégia repo-root); handoff Claude → Codex funcionou pelo hook de SessionStart; MCP do Codex funcionou depois do I-13 |
| Claude-Mem | Sem dupla captura depois do I-14 (181 → 181 sessões) |
| quota-guard | Arquivo de franquia atualizado durante sessão Claude lançada pelo Paseo (indício; não comparado em detalhe) |
| Encerramento | `paseo delete` + remoção dos worktrees: nenhum processo órfão |
| Recursos | ~1,1 GB de RAM com o app aberto (UI Electron ~600 MB, daemon ~370 MB); 514 MB do app + ~1 GB de modelos de voz baixados sozinho (I-15) |

## Não testado ainda

- Travamento por stdin (I-01) dentro do Paseo; queda real por quota; `paseo usage` comparado aos nossos sensores; skills de orquestração do Paseo (`/paseo-handoff`, committee) e onde elas são instaladas; uso pelo celular.

## Consequências

- O Claude passa a delegar via `paseo run` (com worktree e aprovação) em vez de scripts com `codex exec`.
- Configurações do Paseo ficam em `~/.paseo/config.json` (máquina local), documentadas em `USO-DIARIO.md`.
- Se o Paseo falhar num critério importante, o próximo candidato é Superset; Orca só em modo Manual.
