---
name: scientific-outline
description: "Criar esqueleto de artigo adaptativo e cobrir 20 perguntas geradoras."
---

# scientific-outline

**Ativar quando:** há pedido de estrutura, sumário, seções ou preparação de manuscrito a partir de tema.

**Fundamentação:** Wazlawick, caps. 10–11 + 20 perguntas geradoras do agente. O conteúdo abaixo é operacionalização do agente, não transcrição literal do livro.

## Entradas
- Tema ou pergunta de pesquisa; tipo de artigo; contribuição; evidências já disponíveis; normas do veículo se fornecidas.

## Procedimento
1. Propor 2–3 títulos provisórios específicos sem superlativos.
2. Identificar tipo de artigo (teórico, método, empírico, relato etc.) antes de escolher estrutura.
3. Criar seções e subseções proporcionais ao tipo; esquema padrão: resumo, introdução, relacionados/fundamentação, metodologia/proposta, avaliação/resultados, discussão, conclusão, referências.
4. Para cada seção indicar: função retórica, tópicos indispensáveis, insumos, evidências, figuras/tabelas úteis, questões geradoras e critérios de completude.
5. Usar o catálogo em `references/20-perguntas-geradoras.md` (nesta pasta da skill) e partir do modelo `templates/esqueleto-artigo.md`; garantir cobertura integral sem forçar uma pergunta em seção inadequada.
6. Construir matriz pergunta→seção→evidência necessária→status. Uma pergunta pode estar em várias seções.
7. Identificar buracos de conhecimento; nunca escrever "resultados demonstram" sem resultados.
8. Indicar ordem recomendada de escrita separada da ordem de leitura.

## Saída esperada
- Título(s), sumário hierárquico, roteiro tópico por seção, matriz das 20 perguntas, figuras/tabelas propostas e pendências.

## Critérios de conclusão
- Todas as 20 perguntas têm destino, evidência requerida e status.
- Problema, objetivo, método e conclusão pretendida estão alinhados.
- Seções não prometem achados inexistentes.

## Regras
- Não inventar dados, fontes, citações, resultados nem validações. Marcar o que falta com [FONTE PENDENTE], [DADO PENDENTE], [RESULTADO NÃO DISPONÍVEL] ou [DECISÃO METODOLÓGICA PENDENTE].
- Deixar explícito o que é fato com fonte, resultado documentado, hipótese, interpretação ou decisão proposta.
- Não apresentar ferramenta ou implementação como contribuição científica sem a pergunta e a evidência que a sustentam.
- Encaminhamento: redação das seções segue para `scientific-writing`; pergunta geradora sem evidência fica como pendência, sem texto de preenchimento.
