---
name: scientific-writing
description: "Redigir seções cientificamente coerentes e proporcionais à evidência."
---

# scientific-writing

**Ativar quando:** é pedido escrever ou reescrever introdução, resumo, relacionados, método ou conclusão.

**Fundamentação:** Wazlawick, caps. 10–11. O conteúdo abaixo é operacionalização do agente, não transcrição literal do livro.

## Entradas
- Esqueleto, fatos, fontes verificadas, evidências, veículo e extensão desejada.

## Procedimento
1. Determinar função da seção; não antecipar detalhes desnecessários.
2. Introdução: contexto→problema→lacuna documentada→pergunta/objetivo→proposta→contribuições/organização quando pertinente.
3. Relacionados: critérios de comparação e síntese crítica, sem descrever trabalhos como inventário solto.
4. Metodologia: operações replicáveis no tempo verbal coerente com execução.
5. Resultados: fatos observados e unidades; discussão: interpretações e confronto com literatura.
6. Conclusão: responder à pergunta com escopo consistente; sem novo resultado.
7. Resumo: problema, abordagem, avaliação, resultados reais e contribuição; se não há resultados, usar formulação de proposta, não resumo de estudo concluído.
8. Revisar coerência local e global, citações pendentes e densidade informacional.
9. Passar o texto final pela skill `humanizer` antes de entregar, eliminando os vícios conhecidos (dois-pontos "afirmação: interpretação" como muleta, "não é X, é Y", tríades forçadas, travessões, frases de efeito, negrito decorativo, inflação e repetição sintática). Preservar números, citações, pendências e qualificadores que expressam o grau de certeza da evidência.

## Saída esperada
- Texto pronto por seção, com marcações discretas de pendência e quadro de afirmações a validar quando necessário.

## Critérios de conclusão
- Nenhum dado ou literatura inventado.
- Alegações se restringem ao suporte fornecido.
- Não há inflação retórica nem extrapolação.

## Regras
- Não inventar dados, fontes, citações, resultados nem validações. Marcar o que falta com [FONTE PENDENTE], [DADO PENDENTE], [RESULTADO NÃO DISPONÍVEL] ou [DECISÃO METODOLÓGICA PENDENTE].
- Deixar explícito o que é fato com fonte, resultado documentado, hipótese, interpretação ou decisão proposta.
- Não apresentar ferramenta ou implementação como contribuição científica sem a pergunta e a evidência que a sustentam.
- Encaminhamento: polimento vai para `academic-style` e depois `humanizer`; afirmação sem fonte vai para `citation-management`.
