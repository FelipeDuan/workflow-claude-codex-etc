# Visão do Felipe AI OS

Documento para Felipe e agentes que evoluem seu ambiente de engenharia. Base documental: 23/10/2026. Define direção e critérios de evolução; o estado operacional permanece em [STATUS.md](STATUS.md).

## Como interpretar as afirmações

- Fato verificado documentalmente: registro encontrado nos arquivos locais, sem repetir os testes ou auditar a máquina nesta tarefa.
- Decisão aceita: escolha explicitamente aceita em ADR ou instrução do Felipe, com o escopo indicado.
- Hipótese/visão: capacidade desejada, proposta de arquitetura ou experimento ainda sem demonstração suficiente.

Foram lidos integralmente os quatro `contexto-conversa*.md` em `/Users/felipe/Workspace/tools/`, STATUS, INCIDENTES, as três decisões, ORQUESTRADORES, BACKLOG-FERRAMENTAS e USO-DIARIO. Os contextos registram desejos e recomendações de outras IAs; suas alegações externas exigem confirmação na fonte. Quando documentos divergem, os registros posteriores de STATUS e a ADR-0003 orientam esta fotografia: a tabela inicial de STATUS e a comparação anterior à POC não descrevem o último estado registrado.

## Objetivo de longo prazo (visão)

Felipe escolhe um projeto e conversa com o Felipe AI OS sem precisar selecionar um modelo. O sistema recupera as decisões pertinentes, ajuda a explorar a ideia, propõe um plano verificável e distribui o trabalho autorizado. A escolha do coordenador e dos executores considera capacidade, risco, franquia e custo total, podendo mudar entre fases com justificativa explícita.

Claude Opus é o coordenador preferencial de Felipe, especialmente no planejamento aberto, mas não obrigatório. Codex ou outro agente pode coordenar tarefas adequadas ou assumir um plano persistido quando o Claude estiver indisponível. A conversa, as decisões e o estado da tarefa devem sobreviver à sessão de qualquer provedor. Essa entrada independente de modelo ainda é uma visão, não uma função demonstrada do Paseo.

O resultado esperado cobre descoberta, pesquisa, prototipação, implementação, entrega e manutenção. Felipe define objetivos, aprova decisões relevantes e acompanha evidências; tarefas rotineiras já autorizadas avançam sem confirmação repetitiva.

## Princípios

1. Toda nova camada precisa resolver lacuna identificada ou demonstrar melhoria medida. Sem isso, permanece candidata.
2. Reutilizar a infraestrutura existente. Responsabilidades conceituais não exigem serviços separados, outra IDE ou outro supervisor.
3. Qualidade mínima, privacidade e permissões restringem a escolha antes da otimização de custo. Franquia baixa não autoriza reduzir o piso de segurança.
4. Preferir regras explícitas e verificações determinísticas. Classificação probabilística deve poder abster-se e escalar.
5. Conhecimento compartilhado precisa ser descoberto e recuperado sob demanda. Acesso autorizado não exige carregar todo o acervo em cada contexto.
6. Código, testes, contratos e decisões aceitas prevalecem sobre memória histórica. Registrar proveniência e incerteza.
7. Cada tarefa tem um responsável lógico; cada checkout tem um escritor por vez. Paralelismo depende de independência real e critérios de aceite.
8. Supervisão por marcos, bloqueios e resultados. Medir o custo de coordenação e permitir escolher um único agente quando for suficiente.
9. Autonomia depende de limites técnicos e testes. Instruções, boa experiência anterior e confiança do modelo não substituem sandbox.
10. Preservar portabilidade, saída pela CLI e reversibilidade. Considerar RAM, disco e concorrência no MacBook Air M4 de 16 GB/256 GB.

## Decisões aceitas e fatos que sustentam a base

| Tipo | Conteúdo e limite | Evidência local |
|---|---|---|
| Decisão aceita | Workflow existente como fundação; Paseo como execução provisória, com memória e políticas fora do cockpit. | [ADR-0001](decisions/0001-arquitetura-inicial.md), [ADR-0003](decisions/0003-paseo-como-camada-de-execucao.md) |
| Decisão aceita | Roteamento v0 consultivo: menor custo efetivo entre executores com capacidade e risco adequados; sinal ausente fica `unknown`. | [ADR-0002](decisions/0002-roteamento-por-capacidade-e-franquia.md) |
| Decisão aceita | Não instalar Continuity; eventual failover será integração pequena, sujeita aos requisitos de segurança. | ADR-0003 |
| Fato documental | STATUS registra Claude, Codex e OpenCode funcionais; T2 Claude → Codex → OpenCode → Claude e T3 com modelos gratuitos concluídos no laboratório. | [STATUS](STATUS.md), seções T2 e rodada de 22–23/10 |
| Fato documental | POC do Paseo validou três harnesses, dois worktrees paralelos, aprovações, handoff Claude → Codex e encerramento sem órfãos. | ADR-0003; STATUS, “Paseo adotado” |
| Fato documental | ai-memory com escopo por projeto e backfill verificado; Claude-Mem preservado como arquivo e excluído dos projetos migrados/worktrees Paseo. | STATUS; [INCIDENTES](INCIDENTES.md), I-07, I-09, I-13 e I-14 |
| Fato documental | quota-guard foi validado em sessão real; há leitor Codex via App Server e cinco tarefas iniciais de telemetria registradas no STATUS. | STATUS; ADR-0002 |

Essas evidências são históricas e limitadas aos testes descritos. Não comprovam failover automático, disponibilidade atual de modelos gratuitos ou execução autônoma de todo um produto.

## Arquitetura conceitual em camadas

O fluxo desejado passa por entrada, contexto, decisão e execução; qualidade e aprendizado realimentam as políticas. As camadas abaixo podem começar como arquivos, perfis e integrações pequenas no workflow.

| Camada | O que já existe, segundo as fontes locais | O que falta (visão ou lacuna) |
|---|---|---|
| Entrada conversacional | CLI dos harnesses e cockpit Paseo; guia de uso diário. | Projeto + conversa sem escolha inicial obrigatória de modelo; histórico canônico independente do provedor e transferência de coordenação. |
| Contexto e conhecimento | AGENTS.md, skills, agentes especializados, ADRs, Git e ai-memory; backfill do histórico legado. | Contrato de contexto reconstruível, catálogo de capacidades/permissões e biblioteca técnica com fontes; medir omissões e conflitos na recuperação. |
| Decisão e roteamento | ADR-0002, política consultiva, sensores Claude/Codex e telemetria inicial. | Aplicação demonstrada nos perfis Paseo, validade dos sinais, estimativas calibradas e seleção explicável de coordenador/executores. |
| Execução | Paseo adotado após POC; harnesses oficiais, aprovações e worktrees isolados. | Validar invocação de subagentes nativos no Paseo, notificações, dependências e perfis de autonomia; evitar repetir recursos nativos. |
| Continuidade | Handoff ai-memory testado; nota de estado automática e contornos de incidentes. | Recuperação após falha abrupta, distinção de erros, reconciliação de efeitos, espera por reset e failover/retorno seguro. |
| Qualidade e aprendizado | Testes do laboratório, revisão de diffs, incidentes e backlog de avaliações. | Avaliações comparáveis, métricas de esforço total e regressão; mudanças em skills/políticas promovidas por evidência. |
| Ciclo de produto | Skills de engenharia/design e SGG definido como primeiro projeto real. | Demonstrar descoberta até manutenção em um produto; integração proporcional com CI/CD e operação autorizada. |

### Agentes, skills e ferramentas

Subagentes nativos continuam sob o ciclo de vida do harness. Agentes criados via Paseo são sessões independentes, possivelmente de outros provedores e worktrees. Skills descrevem procedimentos; modelos executam inferência; agentes combinam instruções, ferramentas e responsabilidade. Compartilhar instruções exige adaptadores por harness e não garante comportamento equivalente.

Visão: o coordenador usa especialistas nativos para investigações delimitadas e Paseo para delegações entre provedores quando houver ganho. Cada atribuição informa objetivo, entradas, limites de escrita, dependências, verificações e forma de retorno. Ele verifica artefatos e integra entregas, sem acompanhar cada comando.

O contexto 4 descreve notificações do Paseo para agentes-pais gerenciados e consulta explícita para clientes externos no terminal. Essa diferença, inclusive notificações em turnos posteriores e após reinício, está a verificar em teste local. Reconhecer AGENTS.md e localizar uma skill na POC não comprova que um subagente especializado foi invocado e retornou corretamente.

MCPs e plugins devem constar de um catálogo de capacidades com disponibilidade e permissões por agente. Um plugin nativo de um harness não se torna portátil por compartilhar um nome; credenciais não devem ser distribuídas a todos.

### Conhecimento compartilhado sem carregar tudo

Separar regras normativas, memória episódica e estado operacional. Manter identidade/princípios curtos; recuperar ADRs, contratos e trechos de fontes pelo escopo da tarefa. O pacote de continuidade deve identificar objetivo, decisões vigentes, branch/worktree, diff, testes, efeitos já executados, pendências e próximo passo.

A biblioteca de engenharia pretendida reúne requisitos, arquitetura, UX, segurança, testes, dados, algoritmos, operações e manutenção. Cada entrada precisa de autor/fonte, versão ou data, escopo, limitações e vínculo com procedimentos e verificações. Livros e normas entram como referências e sínteses permitidas, respeitando licenças; uma citação não transforma uma preferência em regra universal.

## Roteamento como decisão sob incerteza (visão sobre a v0 aceita)

A v0 da ADR-0002 já separa observações determinísticas da interpretação da tarefa. O próximo passo é avaliar decisões com resultados reais, sem afirmar que um algoritmo sempre encontrará o melhor modelo.

1. Caracterizar domínio, complexidade, risco, ambiguidade, reversibilidade e dependências. Estimar se decompor reduz trabalho total.
2. Eliminar candidatos incompatíveis com permissões, dados, ferramentas ou piso de qualidade. Ler franquia, origem, timestamp, janela e reset; sinal desconhecido ou obsoleto não vira saldo disponível.
3. Comparar alternativas permitidas pelo custo esperado de execução + coordenação + retrabalho + espera. Considerar também qualidade, prazo e capacidade futura, com limites explícitos quando não couber reduzir tudo a um preço.
4. Recomendar coordenador, executores e revisão, justificando a escolha e a incerteza. Persistir a decisão e conferir o resultado.

Percentuais de provedores diferentes não são diretamente comparáveis; assinatura e API por token têm contabilidade distinta. Uma janela perto do reset pode justificar tarefa curta; falta de capacidade adequada pode exigir espera ou decisão do Felipe. Trocar o coordenador só em checkpoint seguro e quando o benefício esperado superar reconstrução de contexto e coordenação.

Grafos de dependência e ordenação topológica podem organizar tarefas. Escalonamento, pesquisa operacional ou classificadores como JEV, Clef e Laya permanecem hipóteses de melhoria. Comparar primeiro regras, depois um classificador tradicional e candidatos especializados. Treinamento exige dados representativos, teste separado, calibração e abstenção; os 100–200 exemplos sugeridos na ADR-0002 não garantem suficiência.

## Autonomia supervisionada (perfis propostos)

| Perfil de permissão | Autonomia pretendida | Quando interromper |
|---|---|---|
| Planejamento/revisão | Ler o escopo autorizado, investigar e produzir análise; sem modificar código de produção. | Requisito ambíguo ou decisão de produto/arquitetura relevante. |
| Desenvolvimento aprovado | Editar workspace delimitado, executar testes locais e corrigir a tarefa autorizada. | Necessidade de ampliar escopo, permissões ou orçamento. |
| Operações críticas | Preparar mudança revisável, validação e rollback. | Deploy, dados de produção, credenciais, instalação global e ações destrutivas exigem autorização específica. |

São perfis desejados, ainda sem validação conjunta nos três harnesses. Precisam ser aplicados pelas ferramentas de permissão/sandbox, com testes de ações permitidas e negadas. Dados institucionais/clientes ficam bloqueados sem acordo; rotas gratuitas e assinaturas de consumidor não concedem autorização implícita.

Continuidade deve distinguir quota, autenticação, rede, timeout, permissão e erro de código. Antes de transferir, parar ou reconciliar o executor anterior, preservar checkpoint e confirmar dono único. Esperar reset, transferir e voltar ao preferido são capacidades diferentes. Suspensão do Mac e retomada ao despertar exigem ensaio; não prometer trabalho contínuo com a tampa fechada.

O I-17 exige selecionar explicitamente a branch base ao criar worktree. O guia diário não elimina esse cuidado: `--base <branch-aprovada>` evita partir da versão errada. Status `running` não prova progresso, conforme I-01 e I-16.

## Avaliação e métricas (proposta)

Comparar mudanças com a base atual em tarefas equivalentes e critérios de aceite fixados. Registrar modelo/harness/versão, perfil, tarefa e risco, resultados, intervenções e condições do teste. Usar amostras reais pequenas sem esgotar franquias; ampliar quando a incerteza justificar.

| Dimensão | Evidência a acompanhar |
|---|---|
| Qualidade | Critérios aceitos, testes relevantes, defeitos/regressões, vulnerabilidades e aderência a contratos/ADRs. |
| Eficiência | Tempo até entrega aceita, esforço humano, tentativas, retrabalho, custo de coordenação, tokens/cache e consumo de franquia quando mensurável. |
| Roteamento | Custo por tarefa aceita, escalonamentos, falhas por perfil, erros de classificação e comportamento de abstenção. |
| Continuidade | Handoffs corretos, contexto omitido, checkpoints recuperáveis, efeitos duplicados e tempo de recuperação. |
| Operação e experiência | Interrupções necessárias/redundantes, RAM/disco/swap, incidentes e, em produto operante, lead time e falhas de implantação. |

Contagem de linhas, mensagem de sucesso e autoconfiança do agente não bastam. Revisão de outra família precisa fundamentar achados; concordância entre modelos não substitui verificação. Observações podem propor melhorias de skills, mas promoção requer avaliação, revisão e versionamento.

O [BACKLOG-FERRAMENTAS](BACKLOG-FERRAMENTAS.md) fornece propostas de A/B para Skill Creator, Context7, Setup, Task Observer, Serena, Headroom e Ponytail. Instalação declarada não significa configuração/ganho confirmado. Headroom requer ensaio isolado; gateways e classificadores não são dependências da fundação.

## Marcos M0 a M5

Os critérios abaixo orientam evolução e ainda precisam de resultados para serem declarados satisfeitos. Não condicionam o uso diário à automação completa.

| Marco | Critério de conclusão | Estado atual e próximo passo |
|---|---|---|
| M0: fundação utilizável | Acessar três harnesses, instruções/skills e memória; executar dois trabalhos isolados; fazer handoff e recuperação manual; respeitar permissões; consultar franquias; ter guia diário e recursos aceitáveis. | Praticamente concluído. STATUS registra T2/T3, quota-guard, leitor Codex e POC Paseo; ADR-0003 e USO-DIARIO sustentam uso. Fechar POC D/stdin e retomada após interrupção; comparar `paseo usage` aos sensores. A POC mediu ~1,1 GB de RAM do app/daemon, sem estabelecer orçamento geral de concorrência. |
| M1: roteamento consultivo | Recomendar coordenador/executores com capacidade, risco e franquia explicitados; testar `unknown`, reset e piso de qualidade; registrar resultado e revisão. | Parcial: ADR-0002 aceita, sensores e telemetria inicial existentes. Aplicação nos perfis Paseo continua nos próximos passos de STATUS; validar recomendações em tarefas representativas. |
| M2: entrada unificada | Abrir projeto e conversar sem selecionar modelo; reconstruir contexto e trocar coordenação em checkpoint, preservando decisões e artefatos verificáveis. | Pendente. Há cockpit/CLI por agente; conversa canônica independente de provedor e seleção inicial automática não estão demonstradas. Experimentar a menor integração após M1. |
| M3: orquestração autônoma | Executar plano aprovado com dependências e permissões delimitadas; receber resultados; recuperar falha/quota sem duplicar efeitos; pedir apenas decisões necessárias. | Parcial/experimental: paralelismo, aprovações e handoff demonstrados. Perfis autônomos, subagentes nativos no Paseo, notificações, recuperação abrupta e failover seguro ainda exigem POC. |
| M4: melhoria contínua | Comparar política/skill nova com a base, medir ganho reproduzível sem regressão e versionar promoção/rollback. | Inicial: incidentes, cinco tarefas de telemetria e backlog de avaliações. Não há melhoria adaptativa/classificador comprovados; começar por um A/B delimitado. |
| M5: ciclo completo de produto | Um projeto real atravessa descoberta, design, implementação, validação, entrega autorizada e manutenção, com evidências de qualidade e esforço total. | Pendente. SGG é o primeiro projeto real previsto; começar quando o núcleo estiver utilizável, sem esperar M4 completo. Esta documentação não inicia sua implementação. |

## Ciclo da ideia à manutenção (visão)

1. Explorar problema, usuários e alternativas; registrar objetivo e dúvidas.
2. Pesquisar fontes e requisitos; definir restrições e critérios de sucesso.
3. Prototipar e decidir design/arquitetura; validar experiência e registrar decisões relevantes.
4. Planejar tarefas e dependências; atribuir responsáveis, orçamento, permissões e checkpoints.
5. Implementar com isolamento; verificar contratos e integrar entregas revisadas.
6. Validar testes, segurança, acessibilidade e operação conforme o risco.
7. Preparar entrega, staging e rollback; obter autorização para produção e observar resultados.
8. Manter o produto; usar incidentes, feedback e métricas para revisar decisões e procedimentos.

Uma correção pequena usa apenas as etapas necessárias. Cada tarefa persiste estado, pré-requisitos, responsável, critério de aceite e evidências; percentual declarado pelo agente não substitui esse registro.

## Questões de pesquisa

- Roteamento por capacidade/franquia/risco melhora custo por tarefa aceita e esforço humano frente ao fluxo atual? Em quais tipos de tarefa?
- Quando subagentes nativos, agente único ou agentes de famílias diferentes oferecem melhor resultado após incluir coordenação e revisão?
- Quais sinais predizem necessidade de divisão ou escalonamento? Como calibrar classificadores e medir erros graves/abstenção?
- Quanto contexto é necessário para trocar coordenador? Quais omissões e decisões conflitantes aparecem na recuperação sob demanda?
- Como usar janelas de franquia e resets com consumo incerto, sem comparar percentuais incompatíveis nem violar contratos?
- Como recuperar falhas, perda de notificação e repouso do host sem duplicar efeitos ou ampliar permissões?
- Biblioteca com fontes e skills avaliadas melhora aderência e manutenção? Como separar efeito da skill, do modelo e da tarefa?
- A entrada neutra reduz trabalho manual suficiente para justificar sua implementação e manutenção no Paseo?

## Referências dos contextos e verificações pendentes

As referências externas abaixo foram citadas nos contextos e não foram confirmadas na fonte nesta tarefa: todas estão **a verificar** quanto a identidade, versão, método e alcance. Não se adotam aqui seus números de ganho, preços ou rankings como fatos. Quando o contexto só fornece nome/domínio, falta localizar a publicação exata.

| Referência citada | Uso pretendido e situação |
|---|---|
| Anthropic, sistema de pesquisa multiagente (`anthropic.com`) | Orquestrador/trabalhadores e custo de coordenação; artigo e resultados a verificar. |
| *Building Effective Agents*, Anthropic | Padrões de composição e critérios de simplicidade; a verificar. |
| *Towards a Science of Scaling Agent Systems* (`arxiv.org`) | Efeito da paralelização e configuração de equipes; autores, versão e experimentos a verificar. |
| SWE-Bench Pro (`proceedings.mlr.press`) | Engenharia em repositórios reais; publicação/atualização mencionadas no contexto 4 a verificar. |
| METR, experimento de produtividade de 2025 e atualização de fevereiro/2026 (`metr.org`) | Tempo total e limites metodológicos; publicações e resultados a verificar. |
| SWEBOK Guide v4, IEEE Computer Society (`computer.org`) | Organização da biblioteca de engenharia; edição e escopo a verificar. |
| ISO/IEC 25010:2023 | Atributos de qualidade; texto aplicável e acesso/licença a verificar. |
| NIST Secure Software Development Framework (`csrc.nist.gov`) | Práticas de desenvolvimento seguro; versão aplicável a verificar. |
| DORA, *State of AI-Assisted Software Development 2025* e métricas de entrega | Avaliação de produtividade/estabilidade; fontes exatas e definições a verificar. |
| Agent Skills e Agent2Agent/A2A (`a2a-protocol.org`) | Carregamento progressivo e interoperabilidade; especificações/versões a verificar. Não são dependências novas propostas. |
| OpenTelemetry, convenções GenAI; Promptfoo | Observabilidade e avaliações; maturidade e adequação a verificar. |
| [Akita, benchmark programação v4](https://akitaonrails.com/2026/09/23/llm-benchmark-v4-opus-5-5-gpt-6-sol-luna-mimo-2-6-grok-4-7/) | Metodologia e resultados a verificar; não estabelecem ranking universal nem custo da assinatura do Felipe. |
| [Akita, modelos abertos em B300](https://akitaonrails.com/en/2026/10/19/llm-benchmark-v4-the-top-open-source-llms-on-a-b300/) | Comparação de execução própria/API citada no contexto 2; a verificar. |
| [Akita, modelos de decisão](https://akitaonrails.com/2026/10/10/qual-modelo-de-decisao-classificador-de-ia-tipo-jev-e-melhor/) | JEV, Clef, Laya, Decision-1 e demais candidatos; resultados e disponibilidade a verificar. Classificação sintética não comprova seleção de executor. |
| [Paseo](https://paseo.sh/docs), Apple Developer, Claude Code Mods e Codex App Server | Alegações dos contextos sobre notificações, suspensão, permissões e franquia a verificar na fonte aplicável e no runtime. As evidências locais limitam-se aos ensaios documentados. |
| Ferramentas adicionais dos contextos 1 a 3 | ORQUESTRADORES e BACKLOG-FERRAMENTAS preservam fontes de Paseo/Orca/Superset e alternativas, Headroom, Setup, Observer, Serena, Creator, Context7, Ponytail e gateways. Nesta visão, capacidades externas e alegações de ganho continuam a verificar; recomendações de pesquisa não equivalem a adoção. |

## Nota de estado

Visão documentada e revisada com a skill humanizer em 23/10/2026. M0 permanece praticamente concluído pelas evidências históricas de STATUS; roteamento automático, entrada neutra e autonomia completa permanecem evolução. Nenhuma instalação ou revalidação do runtime foi feita nesta tarefa. Próximo passo: fechar as lacunas de M0 e validar a política consultiva nos perfis Paseo antes de implementar outra camada.
