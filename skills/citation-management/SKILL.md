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
- Não inventar dados, fontes, argumentos empíricos nem resultados.
- Indicar claramente hipóteses, decisões propostas e lacunas de informação.
- Preservar distinção entre proposta técnica e contribuição científica.
- Encaminhar a `scientific-integrity` se houver alegações sem lastro; a `scientific-reviewer` se for solicitada avaliação completa.
