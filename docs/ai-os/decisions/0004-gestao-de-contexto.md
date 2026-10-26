# ADR-0004: Gestão de contexto por sessões curtas

**Status:** aceita em 26/10/2026. Teste manual de continuidade aprovado no mesmo dia (ver `../GESTAO-CONTEXTO.md`).

## Contexto

Felipe mantinha chats abertos até ~800k tokens por medo de perder contexto. Isso custa caro, já que todo turno reenvia o histórico. Também piora a precisão: a degradação em contexto longo é documentada, e a compactação automática descarta instruções antigas.

O inventário de 26/10 mostrou que o ai-memory guarda o episódio (observações, trecho final das respostas e handoff). Ele não transforma decisões em conhecimento durável sem ação explícita. Hoje, fechar a sessão preserva o contexto só em parte. Os detalhes e as fontes estão em `../GESTAO-CONTEXTO.md`.

## Decisão

Adotar sessões curtas, uma por objetivo. O estado fica fora do chat, em três camadas:

- **viva:** `STATUS.md`. Cada sessão atualiza só a própria frente e não apaga pendência sem resolução explícita;
- **estável:** ADRs, `INCIDENTES.md` e páginas duráveis do ai-memory. O ADR é a fonte canônica de cada decisão, e a memória só aponta para ele;
- **episódica:** observações e handoff do ai-memory, que continuam automáticos.

Regras aprovadas pelo Felipe:

1. **Tamanho da sessão:** 200k tokens funciona como alerta experimental, não como limite rígido.
2. **ADRs:** o agente rascunha e o Felipe aprova toda decisão arquitetural ou normativa. Escolhas operacionais ficam só no STATUS.
3. **Ordem de implementação:** primeiro o checkout canônico, depois o teste manual e, só se ele passar, a skill `sessao`.

O checkout canônico do AI OS é `workflow-ai-ai-os` (`feat/ai-os-v2`). O hub (`~/Workspace/tools/AGENTS.md`) aponta para ele.

## Consequências

- Encerrar uma sessão passa a ter um custo pequeno: atualizar o STATUS e rascunhar o ADR. Em troca, a sessão seguinte começa com poucos tokens e com o estado conferível.
- Fica fora de escopo, por enquanto, a consolidação automática por LLM e a extração automática de ADR. Os motivos são custo, latência e risco de memória envenenada.
- O GPT-6-Astra revisou a proposta ("aprovar com mudanças"), e os quatro achados de severidade alta foram incorporados.
