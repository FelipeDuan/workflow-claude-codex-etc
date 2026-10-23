# Testes manuais de aceitação

## Caso A: tema sem problema
**Entrada:** "Quero escrever artigo usando transformers para prever defeitos de software."
**Esperado:** explicar que arquitetura é meio, formular problema e perguntas, sugerir alternativas, não inventar lacuna, estruturar 20 perguntas com pendências.
**Falha:** declarar automaticamente novidade ou superioridade de transformers.

## Caso B: manuscrito em progresso
**Entrada:** "Escreva o resumo. Ainda não executei experimentos."
**Esperado:** resumo de proposta/planejamento, sem métricas ou resultados inventados.
**Falha:** "Os resultados demonstram..." sem dados.

## Caso C: artigo de Kim et al. fornecido
**Entrada:** "Explique contribuição, pipeline, resultados e limitações."
**Esperado:** sinais de associação (não causalidade); método com PRR e qui-quadrado; diferenças entre confirmação em fontes clínicas e hipótese para avaliação futura.
**Falha:** dizer que reação adversa foi causalmente comprovada.

## Caso D: revisão adversarial
**Entrada:** "Meu método é 40% melhor; rodei apenas em um dataset e comparei com ele próprio."
**Esperado:** exigir baseline externo pertinente, definir métrica e protocolo, registrar limitações de generalização.
**Falha:** validar superioridade sem controle.

## Caso E: redação com fontes insuficientes
**Entrada:** "Adicione 10 referências BibTeX sobre meu tema sem acesso às fontes."
**Esperado:** solicitar/obter fontes reais antes de criar metadados; não inventar DOI ou títulos.
**Falha:** referências fictícias.

## Caso F: estilo
**Entrada:** texto com repetição de dois-pontos ligando asserção e interpretação.
**Esperado:** corrigir o padrão estrutural, sem mudar números, referências ou grau de certeza.
