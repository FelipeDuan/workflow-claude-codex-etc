---
name: academic-style
description: "Revisar concisão, coesão e precisão de escrita científica sem alterar evidências."
---

# academic-style

**Ativar quando:** há pedido de polimento, padronização, tradução ou reescrita textual.

**Fundamentação:** Wazlawick, §10.11 e princípios do agente original. O conteúdo abaixo é operacionalização do agente, não transcrição literal do livro.

## Entradas
- Texto original, público, idioma e grau de intervenção solicitado.

## Procedimento
1. Preservar significado, números, qualificadores, referências e modalidade epistêmica.
2. Remover redundância sem perder distinções conceituais.
3. Alternar construções sintáticas quando houver repetição, não apenas trocar palavras.
4. Detectar muletas como repetidos dois-pontos de "afirmação: explicação"; manter pontuação quando funcional.
5. Ajustar tempo verbal, paralelismo, conexão lógica, termos técnicos e impessoalidade quando pertinente.
6. Evitar afirmações categóricas mais fortes que as originais.
7. Sinalizar contradições científicas sem resolvê-las por conjectura.
8. Oferecer versão revisada e explicação breve de mudanças substantivas.

## Saída esperada
- Texto revisado; notas sobre ambiguidades, afirmações frágeis e pendências, somente quando necessário.

## Critérios de conclusão
- Preserva dados e significado.
- Melhora ritmo e precisão, não só substituições vocabulares.
- Não remove ressalvas importantes.

## Regras
- Não inventar dados, fontes, citações, resultados nem validações. Marcar o que falta com [FONTE PENDENTE], [DADO PENDENTE], [RESULTADO NÃO DISPONÍVEL] ou [DECISÃO METODOLÓGICA PENDENTE].
- Deixar explícito o que é fato com fonte, resultado documentado, hipótese, interpretação ou decisão proposta.
- Não apresentar ferramenta ou implementação como contribuição científica sem a pergunta e a evidência que a sustentam.
- Encaminhamento: depois da revisão, passar pela `humanizer`; alegação sem lastro encontrada no texto vai para `scientific-integrity`.
