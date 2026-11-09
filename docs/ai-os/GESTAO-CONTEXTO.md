# Gestão de contexto: sessões curtas sem perder estado

Status: aprovado em 26/10/2026 (ADR-0004). Teste manual de continuidade aprovado em 26/10/2026; resultado na seção "Resultado do teste".

## Problema

Chats ficam abertos até ~800k tokens por medo de perder contexto. Isso custa caro (cada turno envia o contexto inteiro; a maior parte é lida do cache quando ele está quente) e piora a precisão: modelos perdem informação no meio de contextos longos ([Lost in the Middle](https://arxiv.org/abs/2307.03172), [Context Rot](https://www.trychroma.com/research/context-rot)), e a compactação automática descarta instruções antigas ([Claude Code](https://code.claude.com/docs/en/how-claude-code-works)).

O inventário de 26/10 mostrou por que fechar ainda dá medo:

- o ai-memory guarda o episódio (observações, trecho final da resposta e handoff). O inventário mediu esse trecho em 2 KB, mas o número ainda precisa ser confirmado na versão instalada. Página durável só nasce quando um agente a escreve de propósito, como a `decisions/design-director-main-conversation.md`. Não existe consolidação automática por LLM, e não há regras ativas;
- STATUS, ADRs e INCIDENTES só mudam quando alguém edita;
- queda por quota pode terminar sem handoff (I-11), e há 10 handoffs pendentes acumulados;
- o hub manda ler o STATUS em `workflow-ai/` e trabalhar em `workflow-ai-ai-os/` (`tools/CLAUDE.md`), então uma sessão nova podia ler um estado desatualizado (corrigido em 26/10: o hub aponta para `workflow-ai-ai-os`).

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
| Handoffs pendentes acumulados | Liste e identifique os obsoletos. Não aceite handoff para limpar, porque aceitar consome o handoff; cancelar só a pedido do Felipe. |

A coexistência com o Claude-Mem segue as proteções do I-14 e do I-22. O protocolo não cria captura nova.

## Sessões abertas e retomada

Medido nos transcripts do Claude Code (26/10 a 09/11, só mensagens do assistente na conversa principal, deduplicadas por message id). Mede o `cache_write` da primeira mensagem depois de uma pausa, agrupado pelo tamanho da pausa:

| Pausa antes da mensagem | n | Mediana de cache_write | Total |
|---|---:|---:|---:|
| < 5 min | 2394 | ~1 mil tokens | 4,47 M |
| 5 a 60 min | 148 | ~0,8 mil | 0,54 M |
| > 60 min | 44 | ~224 mil | 11,43 M |

Leitura: nas retomadas depois de mais de uma hora, o contexto inteiro aparece regravado no cache (associação observada). Explicação provável: o cache de prompt tem TTL (5 min por padrão, 1 h opcional, segundo a documentação da Anthropic) e expira durante a pausa. Hipótese quanto à causa exata no Claude Code: não verifiquei qual TTL ele usa. 44 retomadas longas custaram mais tokens de cache que as 2394 mensagens seguidas. Tokens de cache não são o custo exato da assinatura (o preço é fixo; o que pesa é o limite de uso), então isto indica tendência, não valor em reais.

Sessão parada não chama a API, mas ocupa memória: ~600 MB com os MCPs filhos (medido em 3 sessões, 587 a 621 MB cada).

Recomendação:

- Uma sessão por objetivo.
- Fechar depois de um checkpoint verificável (STATUS atualizado, handoff ou commit), e não no meio do trabalho. Nada de fechamento automático por tempo.
- Para retomar depois de mais de uma hora, preferir abrir sessão nova com briefing curto a reabrir uma sessão longa, até o experimento abaixo dizer o contrário.

Pendente no protocolo: experimento A/B/C com a mesma tarefa, comparando (A) retomar a sessão longa, (B) compactar e retomar, (C) sessão nova com briefing. Métricas: cache_write da primeira mensagem, tokens até o primeiro resultado útil e qualidade da retomada. Ainda não executado.

## Manutenção (sob demanda)

`memory_lint`, revisão dos handoffs pendentes, poda do STATUS e conferência do tamanho do CLAUDE.md e do AGENTS.md (CLAUDE.md abaixo de ~200 linhas, segundo a [doc de memória](https://code.claude.com/docs/en/memory)). Sem cadência fixa: faça quando o STATUS passar de uma página ou os handoffs pendentes atrapalharem. Escolha trivial não precisa de registro.

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

## Resultado do teste (26/10/2026)

Agentes Codex novos (gpt-6-luna), sem acesso ao chat original:

| Caso | Resultado |
|---|---|
| Decisão + pendência, lido a partir do hub | Passou: as 4 respostas certas, com arquivo:linha, lidas no checkout canônico |
| Queda sem handoff | Passou com ressalva: reconstruiu a sessão `d3bee63b` (tarefas, decisões, commits, pendência) por `memory_briefing` + `memory_read_session_observations`. Não viu o trabalho feito antes de a sessão entrar num projeto habilitado (`~/Workspace` não tem marcador) |
| Pendência de outra frente | Passou: o diff do STATUS só adicionou linhas; as pendências do SGG continuaram |

Limite do teste: ele comprovou a recuperação por leitura, mas não o ciclo completo encerrar → hook gera o handoff → sessão nova o recebe. Esse ciclo será observado no primeiro uso real da skill `sessao`. Edições concorrentes no STATUS também não foram testadas: um único responsável integra o STATUS.

Lição: só é capturado o que acontece dentro de um projeto com `.ai-memory.toml`. Para tarefas soltas (ex.: manutenção do Mac), abra a sessão num projeto habilitado ou registre o resultado no STATUS ao final.

## Linha de base de consumo (medida em 26/10/2026)

Medição feita pelo Codex (gpt-6.1-sol) nos logs do Claude Code e do Codex, com mensagens deduplicadas por ID e conferida contra o log bruto de uma sessão. Comparação de 08–21/10 (antes do AI OS) com 22–25/10 (depois), dias completos:

| Métrica | Antes | Depois |
|---|---:|---:|
| Claude, milhões de tokens/dia | 70,6 | 58,7 (−17%) |
| Codex, milhões de tokens/dia | 0 | 40,1 |
| Contexto por turno na conversa principal do Claude | 307 mil | 331 mil (+8%) |
| Parte dos tokens do Claude em subagentes | 58% | 4% |
| Leitura de cache no total do Claude | — | 96% |

Leitura:

- O volume total subiu (+40%), mas o Claude, que é a cota mais escassa, caiu. O trabalho migrou para o Codex, que tem cota própria. Isso é volume de tokens, não dinheiro: as assinaturas têm preço fixo, e o que importa é o limite de cada uma.
- O protocolo de sessões curtas ainda não entrou nesse período. O indicador que ele deve mover é o contexto por turno da conversa principal, que continua em ~300 mil, e quase tudo isso é a releitura do histórico (leitura de cache).
- São só 4 dias e com tarefas diferentes (antes era portfólio; depois, AI OS). Não dá para atribuir causa.
- Remedir depois de 2 semanas de uso do protocolo, com a mesma métrica. O script ficou em `/tmp/ai-os-economia/analisar.py`, que é temporário; trazê-lo para o repo está pendente.

## Decisões do Felipe (26/10/2026)

1. **Alerta de tamanho de contexto:** 200k tokens, como alerta experimental e não como regra. Não há número com base empírica.
2. **Aprovação de ADR:** o agente rascunha e o Felipe aprova toda decisão arquitetural ou normativa. Escolha operacional fica só no STATUS.
3. **Ordem:** itens 0 e 1 primeiro; a skill só entra depois que o teste manual passar.
