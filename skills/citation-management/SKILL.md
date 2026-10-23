---
name: citation-management
description: "Gerir citações, fontes, BibTeX e rastreabilidade de alegações."
---

# citation-management

**Ativar quando:** o usuário pede referências, literatura citada, BibTeX, revisão de citações ou LaTeX.

**Fundamentação:** Wazlawick, cap. 7, §10.10 e cap. 12. O conteúdo abaixo é operacionalização do agente, não transcrição literal do livro.

## Entradas
- Fontes efetivamente fornecidas/acessadas, estilo requerido, texto com afirmações.

## Procedimento
1. Extrair metadados exclusivamente de fonte verificável; nunca deduzir DOI, volume ou paginação.
2. Construir registro fonte↔alegação e marcar afirmações sem lastro.
3. Distinguir citação direta, paráfrase, interpretação e conhecimento do autor.
4. Verificar que todas as citações em texto correspondem à bibliografia e vice-versa conforme estilo.
5. Produzir entradas BibTeX somente com campos confirmados; registrar campos ausentes sem inventar.
6. Verificar integridade de URLs, DOI e metadados apenas se fontes e ferramentas permitirem.
7. Evitar citação decorativa ou empilhamento de referências que não sustentam a afirmação.
8. Respeitar normas de atribuição e direitos autorais.

## Saída esperada
- Matriz alegação→fonte→status; bibliografia/BibTeX confiável; lista de campos e citações pendentes.

## Critérios de conclusão
- Todas as entradas são rastreáveis.
- Fontes não acessadas são rotuladas como não verificadas.
- Nenhum dado bibliográfico é fabricado.

## Regras
- Não inventar dados, fontes, citações, resultados nem validações. Marcar o que falta com [FONTE PENDENTE], [DADO PENDENTE], [RESULTADO NÃO DISPONÍVEL] ou [DECISÃO METODOLÓGICA PENDENTE].
- Deixar explícito o que é fato com fonte, resultado documentado, hipótese, interpretação ou decisão proposta.
- Não apresentar ferramenta ou implementação como contribuição científica sem a pergunta e a evidência que a sustentam.
- Encaminhamento: afirmação que nenhuma fonte sustenta vai para `scientific-integrity`, sem buscar citação que a justifique a posteriori.
