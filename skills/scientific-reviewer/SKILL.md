---
name: scientific-reviewer
description: "Revisar manuscrito como parecerista com diagnóstico verificável."
---

# scientific-reviewer

**Ativar quando:** é pedido parecer, avaliação de qualidade, preparação para submissão ou revisão crítica.

**Fundamentação:** Wazlawick, caps. 5, 9, 11 e 13. O conteúdo abaixo é operacionalização do agente, não transcrição literal do livro.

## Entradas
- Manuscrito completo/parcial, normas do veículo se houver e evidências anexas.

## Procedimento
1. Classificar tipo, objetivo e contribuição alegada.
2. Identificar e avaliar problema, novidade sustentada, relação com estado da arte, objetivos e justificativa.
3. Auditar métodos, controles, baselines, evidências, validade, reprodutibilidade e ética.
4. Checar coerência entre resumo, introdução, método, resultados e conclusão.
5. Avaliar cobertura das 20 perguntas conforme pertinência, não por checklist mecânico.
6. Separar problemas fatais, maiores, menores e questões estilísticas, citando trechos/locais.
7. Recomendar correções acionáveis e proporcionalidade das alegações.
8. Não prever aceitação ou atribuir notas sem rubrica explícita.

## Saída esperada
- Parecer estruturado com pontos fortes, problemas por gravidade, evidências do manuscrito e plano de revisão priorizado, seguindo o modelo `templates/parecer-cientifico.md` (nesta pasta da skill).

## Critérios de conclusão
- Críticas apontam localização e fundamento.
- Ausência de dados é descrita como insuficiência de evidência, não como fraude.
- Não confunde preferências editoriais com erros metodológicos.

## Regras
- Não inventar dados, fontes, argumentos empíricos nem resultados.
- Indicar claramente hipóteses, decisões propostas e lacunas de informação.
- Preservar distinção entre proposta técnica e contribuição científica.
- Encaminhar a `scientific-integrity` se houver alegações sem lastro; a `scientific-reviewer` se for solicitada avaliação completa.
