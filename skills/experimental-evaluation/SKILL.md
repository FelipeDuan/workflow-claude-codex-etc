---
name: experimental-evaluation
description: "Planejar avaliação de computação com baselines e validade."
---

# experimental-evaluation

**Ativar quando:** pesquisa exige avaliação experimental, benchmark, simulação, estudo de usuário ou comparação.

**Fundamentação:** Aplicação operacional dos critérios de avaliação de Wazlawick, caps. 5–6; práticas específicas dependem da subárea. O conteúdo abaixo é operacionalização do agente, não transcrição literal do livro.

## Entradas
- Método/proposta, dados e métricas possíveis; recursos, cenários e alegações de desempenho.

## Procedimento
1. Transformar alegações em questões/hipóteses avaliáveis.
2. Escolher baselines adequados (estado da arte, prática corrente e/ou ablação), justificando ausência quando inevitável.
3. Definir datasets, divisão treino/validação/teste quando pertinente e proteção contra vazamento.
4. Definir métricas primárias e secundárias, unidades, custos, robustez, eficiência e trade-offs.
5. Estabelecer repetições, sementes, intervalos de confiança/testes quando justificáveis; evitar testes sem pressupostos.
6. Prever controles, ablações, sensibilidade, casos negativos e ameaça à validade externa/interna/de constructo.
7. Registrar ambiente, versões, parâmetros e protocolo de reprodutibilidade.
8. Entregar plano de análise e tabelas vazias. Só preencher resultados com dados reais.

## Saída esperada
- Matriz hipótese→baseline→dados→métrica→análise; protocolo executável; checklist de ameaças; tabelas-modelo.

## Critérios de conclusão
- Comparações suportam a afirmação científica.
- Não confundir significância estatística com relevância prática.
- Nenhum resultado simulado é apresentado como real.

## Regras
- Não inventar dados, fontes, argumentos empíricos nem resultados.
- Indicar claramente hipóteses, decisões propostas e lacunas de informação.
- Preservar distinção entre proposta técnica e contribuição científica.
- Encaminhar a `scientific-integrity` se houver alegações sem lastro; a `scientific-reviewer` se for solicitada avaliação completa.
