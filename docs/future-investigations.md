# Investigações futuras

Ideias avaliadas e adiadas de propósito. Cada item diz o que é, por que não agora, o que faria voltar a ele e como medir.

## Jev (TypeSafe AI)

O que: modelo "System One" da TypeSafe AI que devolve decisões tipadas, pensado para roteamento, gates e compactação de contexto. Acesso antecipado por waitlist desde por volta de 2026-09.

Por que não agora: não existe problema de roteamento medido neste workflow, e a ferramenta é nova demais para virar dependência.

Gatilho: skills ou agents sendo escolhidos errado com frequência, ou sessões longas perdendo contexto importante na compactação.

Como medir:
- J1, roteamento: acerto do Jev contra o roteamento nativo por `description:` num conjunto fixo de pedidos com rota esperada.
- J2, compactação: o que se perde e o que se preserva comparado com a compactação nativa, nas mesmas sessões.

Nunca usar para julgar qualidade de design. Isso continua sendo crítica heurística e decisão humana.

## Graphify como índice derivado

O que: usar o grafo do Graphify como índice para o agente navegar o projeto. Sempre derivado do código e dos docs, nunca fonte de verdade.

Por que não agora: nos projetos atuais, pequenos, ler os arquivos custa menos do que manter o índice. Compensaria em monorepo ou com muita documentação.

Gatilho: um projeto grande em que o agente abre dezenas de arquivos para responder perguntas de dependência.

Como medir: A/B com as mesmas tarefas, Claude sozinho contra Claude com Graphify. Métricas: tokens de entrada e saída, chamadas de ferramenta, arquivos abertos, tempo, dependências esquecidas, suposições erradas e correção da resposta.

Cuidados:
- Privacidade: o código é parseado localmente, mas docs e imagens vão para um backend de LLM. `--code-only` ou `--backend ollama` mantêm tudo local.
- Disco: numa máquina de 256 GB, conferir o tamanho do índice antes de adotar.

## MCPs pagos de referência (Mobbin, Refero)

O que: acesso a bibliotecas grandes de telas e fluxos de apps reais.

Por que não agora: não há evidência de que as fontes gratuitas deixem lacunas.

Gatilho: o benchmark do portfólio mostrar lacunas nas fontes gratuitas.

Como medir: relevância dos resultados, variedade, buscas sem resultado útil, profundidade dos fluxos e quanto trabalho manual ainda sobra.

## Benchmark do workflow

O que: comparar um pedido cru ("faça uma dashboard") com o mesmo pedido passando pelo workflow de design.

Por que não agora: o workflow acabou de ser montado; primeiro precisa rodar num caso real.

Gatilho: depois do benchmark do portfólio, ou antes de mudar o workflow de forma significativa.

Como medir: diversidade das propostas iniciais, número de iterações, findings de acessibilidade, erros de fluxo, consistência, avaliação de um revisor independente, defeitos de implementação, divergência entre design e código, tokens e custo.

## Portfólio como primeiro benchmark

O que: usar um portfólio pessoal como primeiro caso completo do workflow.

Por que ele: exercita quase todas as fases com risco baixo. Valida discovery, identidade, storytelling, pesquisa de referências, direção de arte divergente, anti-slop, tipografia, composição, design system, organização no Figma, prototipação, motion, acessibilidade, responsivo e fidelidade entre design e código.

Por que não agora: o workflow ainda está nesta branch e não foi usado de ponta a ponta.

Gatilho: workflow integrado à `main`. Este é o próximo passo planejado.

Como medir: as mesmas métricas do benchmark do workflow, registradas desde a primeira rodada para servir de base.
