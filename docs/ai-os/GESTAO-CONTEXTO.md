# Gestão de contexto: sessões curtas sem perder estado

Status: aprovado em 26/10/2026 (ADR-0004). Em validação: o teste manual de continuidade (item 1 da implementação) ainda não rodou.

## Problema

Chats ficam abertos até ~800k tokens por medo de perder contexto. Isso custa caro (todo turno reenvia o histórico) e piora a precisão: modelos perdem informação no meio de contextos longos ([Lost in the Middle](https://arxiv.org/abs/2307.03172), [Context Rot](https://www.trychroma.com/research/context-rot)), e a compactação automática descarta instruções antigas ([Claude Code](https://code.claude.com/docs/en/how-claude-code-works)).

O inventário de 26/10 mostrou por que fechar ainda dá medo:

- o ai-memory guarda o episódio (observações, trecho final da resposta e handoff). O inventário mediu esse trecho em 2 KB, mas o número ainda precisa ser confirmado na versão instalada. Página durável só nasce quando um agente a escreve de propósito, como a `decisions/design-director-main-conversation.md`. Não existe consolidação automática por LLM, e não há regras ativas;
- STATUS, ADRs e INCIDENTES só mudam quando alguém edita;
- queda por quota pode terminar sem handoff (I-11), e há 10 handoffs pendentes acumulados;
- o hub manda ler o STATUS em `workflow-ai/` e trabalhar em `workflow-ai-ai-os/` (`tools/CLAUDE.md`), então uma sessão nova pode ler um estado desatualizado.

## Princípio

O chat é bancada de trabalho e pode ser descartado. O estado mora em três camadas:

| Camada | Onde | Muda quando | Quem escreve |
|---|---|---|---|
| Viva | `STATUS.md`, seção "ESTADO ATUAL E PENDÊNCIAS" | fim de toda sessão que mudou algo | agente, só no trecho da própria frente |
| Estável | ADRs, `INCIDENTES.md`, páginas duráveis do ai-memory | quando nasce uma decisão ou regra | agente rascunha; Felipe aprova o que for arquitetural ou normativo |
| Episódica | observações e handoff do ai-memory | sempre | automático (já existe) |

A fonte canônica de cada decisão é o ADR. A memória só aponta para ele, sem manter uma segunda cópia. O `memory-backfill` continua podendo gravar fatos verificados, como hoje.

Quando houver divergência, separe o comportamento observado (código, git, testes) do comportamento autorizado (ADR, regra aprovada). O código mostra o que acontece, não o que deveria acontecer. Investigue antes de corrigir o código ou expirar a memória.

## Regras para o STATUS

- Edite só a seção de estado atual e só a frente em que você trabalhou.
- Releia o arquivo imediatamente antes de salvar, porque outra sessão pode ter mudado.
- Pendência só sai com resolução explícita (feita, descartada ou movida).
- Confira o diff antes de encerrar. Histórico e evidências antigas saem da seção de estado atual, mas ficam referenciados (git, INCIDENTES).

## Ciclo de uma sessão

1. **Abrir.** O handoff já chega pelo hook. O agente lê o STATUS do checkout canônico e confere checkout e branch (`git worktree list`, I-31). Em cliente sem sessão (MCP estático), passe workspace e projeto explicitamente.
2. **Trabalhar.** Um objetivo por sessão. Toda decisão é registrada na hora: linha no STATUS ou rascunho de ADR. Exploração e saída verbosa vão para subagente.
3. **Encerrar a sessão** (não confundir com o fim de um turno: são os hooks `SessionEnd` e `Stop`, respectivamente). Os gatilhos são:
   - objetivo concluído;
   - troca de assunto;
   - mais de duas correções falhas no mesmo problema ([best practices](https://code.claude.com/docs/en/best-practices));
   - pausa longa;
   - alerta de tamanho de contexto.

   No encerramento: STATUS atualizado pelas regras acima, rascunho de ADR para decisão nova e a nota de estado de sempre. Não crie handoff explícito, porque o automático já cobre (`AGENTS.md`).

## Contingências

| Situação | O que fazer |
|---|---|
| Chat gigante já existente | Destilar uma vez, dentro do próprio chat: atualizar o STATUS (pelas regras), rascunhar os ADRs pendentes, listar as perguntas abertas. Revisar e fechar. |
| Sessão caiu sem handoff | Ache a sessão no `memory_briefing` e leia `memory_read_session_observations` em ordem decrescente. Depois confira checkout, arquivos não rastreados, `git diff` e `git log`. Só o diff não recupera decisões nem perguntas. |
| Compactação no meio do trabalho | Seção "Compact Instructions" no CLAUDE.md dizendo o que preservar. Prefira `/compact <foco>` manual a esperar o automático. |
| Memória diverge do código | Classifique a divergência como observado × autorizado antes de mexer (ver Princípio). |
| Handoffs pendentes acumulados | Aceite ou cancele na manutenção. |

A coexistência com o Claude-Mem segue as proteções do I-14 e do I-22. O protocolo não cria captura nova.

## Manutenção (cadência a medir)

`memory_lint`, revisão dos handoffs pendentes, poda do STATUS e conferência do tamanho do CLAUDE.md e do AGENTS.md (CLAUDE.md abaixo de ~200 linhas, segundo a [doc de memória](https://code.claude.com/docs/en/memory)). Comece semanal e ajuste pelo uso real.

## Implementação, em ordem

0. **Caminho canônico do STATUS.** Resolver a contradição do `tools/CLAUDE.md`: definir qual checkout é a fonte e apontar o hub para ele.
1. **Teste manual de continuidade** antes de codificar qualquer coisa, com três casos:
   - fechar e reabrir com uma decisão e uma pendência verificáveis;
   - queda sem handoff;
   - uma pendência de outra frente que precisa sobreviver à atualização do STATUS. A leitura parte do hub.
2. **Skill `sessao`** (abrir, encerrar, recuperar, destilar). Ela codifica o checklist já testado e reaproveita as skills de retrieval, handoff e backfill, sem mecanismo novo.
3. **Seção "Compact Instructions"** no CLAUDE.md do hub.
4. Opcional: hook `SessionStart` que avisa ao abrir `tools/workflow-ai/` fora do worktree (I-31).

Fora de escopo por enquanto: ligar consolidação por LLM no ai-memory (custo, latência e risco de memória envenenada, ver [Unit 42](https://unit42.paloaltonetworks.com/indirect-prompt-injection-poisons-ai-longterm-memory/)) e extração automática de ADR.

## Decisões do Felipe (26/10/2026)

1. **Alerta de tamanho de contexto:** 200k tokens, como alerta experimental e não como regra. Não há número com base empírica.
2. **Aprovação de ADR:** o agente rascunha e o Felipe aprova toda decisão arquitetural ou normativa. Escolha operacional fica só no STATUS.
3. **Ordem:** itens 0 e 1 primeiro; a skill só entra depois que o teste manual passar.
