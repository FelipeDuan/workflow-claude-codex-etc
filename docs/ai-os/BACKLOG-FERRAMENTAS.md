# Backlog de ferramentas — pesquisa do Codex

Consulta em **22/10/2026**. Objetivo: avaliar as ferramentas do item 1 da última seção “PRÓXIMOS PASSOS” do STATUS, sem instalar, configurar ou executar testes de produto. As recomendações e os critérios abaixo são propostas desta pesquisa, não resultados experimentais. Base de escopo: [STATUS no commit de referência][status], lido em 22/10/2026.

## Proveniência e limites

Os documentos de AI OS não estavam na branch deste worktree. Foram lidos integralmente com `git show feat/ai-os-v2:<arquivo>`: STATUS, PESQUISA-ROTEAMENTO e as três decisões, usando como referência `cd0252a834d1d6b93d0cd15caeb802cffb4f406a`. As URLs do GitHub abaixo identificam esses artefatos; sua publicação e acessibilidade pública são **não confirmado**. A evidência é o Git local, não uma página pública validada. Os arquivos contêm registros de 23/10/2026, posteriores à data do ambiente, 22/10/2026; essa divergência temporal é **não confirmado** e os registros são tratados como histórico declarado, sem mudar a data desta consulta. Fontes locais: [STATUS][status], [ADR-0001][adr1], [ADR-0002][adr2], [ADR-0003][adr3], [pesquisa anterior][roteamento], leitura em 22/10/2026.

Somente documentação dos autores, repositórios dos mantenedores e documentação dos serviços sustentam as afirmações externas. “Oficial” identifica a origem da ferramenta; não implica endosso da Anthropic ou OpenAI para projetos comunitários. Páginas em `main`/`master` são mutáveis. Versão instalada, compatibilidade efetiva e consumo no MacBook Air M4 de 16 GB são **não confirmado**, salvo quando explicitamente atribuídos a um artefato local. Nenhum valor de RAM, disco ou economia de tokens foi medido nesta pesquisa. Base metodológica e de escopo: [STATUS][status] e [ADR-0002][adr2], leitura em 22/10/2026.

## Base que as ferramentas precisam complementar

| Componente atual | Papel e limite usado nesta comparação |
|---|---|
| ai-memory | O STATUS registra captura, conhecimento durável e handoff entre Claude, Codex e OpenCode. A ADR-0003 mantém memória e handoff sob sua responsabilidade. Não se presume que ele ofereça navegação semântica, documentação de bibliotecas ou proxy de inferência. Fontes locais: [STATUS][status], [ADR-0003][adr3], leitura em 22/10/2026. |
| Skills | O README descreve instruções próprias e de terceiros, com seleção e SHAs fixados pelo lock. São a base para comparar procedimentos, diagnóstico e revisão, em vez de instalar outro conjunto global por padrão. Fontes locais: [README][readme], [lock][lock], leitura em 22/10/2026. |
| Graphify | O lock de referência declara `graphifyy 0.9.70`; o lock desta branch declara `0.9.67`. O README o apresenta como CLI opcional com skill e sem instalação de hooks. Portanto, versão realmente ativa no Mac é **não confirmado** nesta pesquisa; não foi deduzida do lock. Fontes locais: [lock de referência][lock], [README desta branch][readme-atual], [lock desta branch][lock-atual], leitura em 22/10/2026. |
| Plugins skill-creator e Context7 | Já instalados, conforme o pedido do usuário. Não houve auditoria da configuração ativa, autenticação ou versão. Há homônimo `skill-creator` da OpenAI; a seção correspondente avalia a implementação da Anthropic para A/B e marca a identidade instalada como **não confirmado**. Fontes de comparação: [Anthropic Skill Creator][creator], [OpenAI Skill Creator][openai-creator], [Context7][context7], consulta em 22/10/2026; declaração de instalação: pedido desta tarefa, 22/10/2026. |
| Roteamento e execução | A ADR-0002 é consultiva e adia gateway até existir necessidade de várias APIs e orçamento. A ADR-0003 atribui execução, worktrees e aprovações ao Paseo e proíbe Continuity. Essas decisões orientam as recomendações; não foram revalidadas operacionalmente. Fontes locais: [ADR-0002][adr2], [ADR-0003][adr3], leitura em 22/10/2026. |

## 1. Claude Code Setup

**Identidade e função.** O candidato é `anthropics/claude-plugins-official/plugins/claude-code-setup`, não pacotes homônimos de configuração. Seu README declara análise do repositório e indicação de uma ou duas automações por categoria, incluindo MCPs, skills, hooks, subagentes e comandos. Declara expressamente operação somente leitura. Fonte: [README oficial][setup], consulta em 22/10/2026.

**Sobreposição.** Como avaliação desta pesquisa, duplica parte do inventário e diagnóstico já cobertos pelo README, skills e decisões locais; pode revelar uma lacuna específica. Não substitui ai-memory, Graphify, Skill Creator ou Context7: recomenda automações, enquanto os demais guardam contexto, analisam relações, criam skills ou consultam documentação. Bases: [Setup][setup], [base local][readme], [STATUS][status], consulta/leitura em 22/10/2026.

**Riscos e custo no M4.** Somente leitura não significa ausência de acesso ao conteúdo: o propósito é examinar o código. Escopo lido, tokens consumidos, RAM e disco no M4 são **não confirmado**. A análise e suas recomendações acrescentam contexto; a magnitude e a redução de trabalho posterior são **não confirmado**. Não há evidência aqui de isolamento técnico próprio ou garantia de que as sugestões respeitem todas as decisões locais. Fonte e inferência: [Setup][setup], consulta em 22/10/2026.

**Recomendação: testar**, exclusivamente como diagnóstico somente leitura. Critério de aceite proposto: em um projeto público pequeno, apresentar no máximo três sugestões úteis com evidência de arquivo, confrontá-las com o inventário atual e justificar ao menos uma lacuna real; não alterar arquivos nem configuração, e registrar tokens/tempo. Se apenas recomendar o que já existe, encerrar o teste. Proposta baseada em [Setup][setup] e [ADR-0001][adr1], em 22/10/2026.

## 2. Skill Creator

**Identidade e função.** A implementação avaliada é `anthropics/skills/skills/skill-creator`. Ela orienta criar ou melhorar skills, executar avaliações, comparar desempenho com análise de variância e melhorar gatilhos. O procedimento inclui prompts de teste, avaliação humana e métricas. A correspondência com o plugin já instalado é **não confirmado**; não confundir com a skill homônima da OpenAI. Fontes: [skill Anthropic][creator], [skill OpenAI][openai-creator], consulta em 22/10/2026.

**Sobreposição.** Avaliação: complementa as skills existentes ao permitir testá-las; não cria razão para duplicar sua instalação. Sobrepõe-se ao Task Observer na melhoria de skills, mas o foco aqui é avaliação deliberada. Não substitui memória de projeto, relações do Graphify ou documentação do Context7. Bases: [Creator][creator], [Task Observer][observer], [README local][readme], [STATUS][status], consulta/leitura em 22/10/2026.

**Riscos e custo no M4.** Repetições de avaliação consomem chamadas do modelo e podem produzir arquivos e executar scripts; o próprio procedimento usa execuções com e sem skill. O consumo de contexto, RAM, disco, tempo e franquia no M4 é **não confirmado**. Riscos metodológicos propostos: otimizar só para os exemplos usados e confundir variação do modelo com melhoria. Fonte e análise: [Creator][creator], consulta em 22/10/2026.

**Recomendação: adotar agora** o uso avaliativo da instalação existente, após conferir sua identidade, sem novo plugin. Critério de aceite proposto: escolher uma skill, congelar versão/modelo, usar três casos representativos e um caso fora do gatilho, comparar A/B em três repetições por caso, registrar correção, acionamento, tokens e tempo e revisar os resultados sem saber qual variante os gerou. Aprovar alteração só sem regressão de segurança/correção e com ganho reproduzível; não extrapolar essa amostra para todo o catálogo. Proposta de 22/10/2026 baseada em [Creator][creator] e [ADR-0002][adr2].

## 3. Task Observer

**Identidade e função.** O STATUS fornece só o nome; a identidade pretendida é **não confirmado**. Candidato avaliado, como hipótese: `rebelytics/one-skill-to-rule-them-all`, do autor Eoghan Henn. O README descreve observações sobre correções e padrões de trabalho para propor novas skills ou melhorias, com decisão humana sobre instalação. Não se atribuem a esse projeto características de homônimos. Fontes: [STATUS][status], [README do autor][observer], leitura/consulta em 22/10/2026.

**Sobreposição.** Avaliação: compete com a coleta de observações e manutenção de aprendizados do ai-memory e se aproxima do Skill Creator; sua diferença potencial é organizar sinais para mudanças nas skills. O guia relaciona explicitamente Observer e Creator. Não fornece o serviço de documentação do Context7 nem a navegação estrutural do Graphify. Bases: [guia][observer-guide], [Creator][creator], [STATUS][status], [README local][readme], consulta/leitura em 22/10/2026.

**Riscos e custo no M4.** O guia descreve referências carregadas sob demanda, cinco scripts auxiliares, diretórios próprios de observações e versões preparadas em `skill-updates/`, sem instalar alterações automaticamente. Ainda há risco de registrar informação confidencial e manter fontes concorrentes de orientação; os controles são descritos pelo autor, não auditados aqui. Ativação recorrente aumenta trabalho/contexto; tokens, RAM, disco e compatibilidade real com os três harnesses são **não confirmado**. Fonte e inferência: [guia oficial][observer-guide], consulta em 22/10/2026.

**Recomendação: testar**, somente após resolver a identidade, sem ativação global. Critério proposto: observar três sessões pessoais em cópias descartáveis de skills, gerar propostas com origem verificável, impedir inclusão de segredos sintéticos, não editar skills ativas e comparar utilidade com observações já recuperáveis do ai-memory. Aceitar apenas se houver melhoria útil não duplicada e custo registrado. Proposta de 22/10/2026 baseada em [Observer][observer], [guia][observer-guide] e [STATUS][status].

## 4. Serena

**Identidade e função.** `oraios/serena` oferece recuperação semântica, edição, refatoração e depuração no nível de símbolos, acessíveis por MCP. O README anuncia interface REPL na v2; isso não confirma qual versão estaria instalada ou compatível com este ambiente. Fonte: [README oficial][serena], consulta em 22/10/2026.

**Sobreposição.** Avaliação: aproxima-se do Graphify na exploração das relações do código; a distinção relevante para testar é operação semântica sobre símbolos e refatoração, em vez de acrescentar outra memória. Não substitui histórico/handoff do ai-memory, instruções das skills, avaliação do Creator ou consulta de bibliotecas do Context7. Bases: [Serena][serena], [Graphify oficial][graphify], [README local][readme], [STATUS][status], consulta/leitura em 22/10/2026.

**Riscos e custo no M4.** É uma ferramenta com capacidade de escrita, portanto uma chamada equivocada pode alterar código. A configuração precisa restringir o projeto. Servidores de linguagem e indexação acrescentam processos e dados locais; RAM, disco, tempo de início e economia líquida de tokens no M4 são **não confirmado**. Ganhos anunciados não constituem benchmark do projeto do Felipe. Fonte e análise: [Serena][serena], consulta em 22/10/2026.

**Recomendação: testar**, quando houver navegação/refatoração complexa que as ferramentas atuais não resolvam bem. Critério proposto: no mesmo repositório e modelo, comparar cinco buscas de referências com `rg`/Graphify e uma refatoração em worktree descartável; validar referências por testes e diff, registrar contexto/latência, pico de RAM e disco após indexação. Aceitar apenas com ganho útil e sem omissões semânticas; começar somente leitura. Proposta de 22/10/2026 baseada em [Serena][serena], [Graphify][graphify] e [ADR-0001][adr1].

## 5. Headroom

**Identidade e função.** `headroomlabs-ai/headroom` comprime conteúdo antes do modelo e documenta biblioteca, proxy, wrapper de agentes e MCP. O README declara compressão local, sem enviar conteúdo para um serviço de compressão; o envio posterior ao provedor de inferência continua existindo. Preservação de toda informação relevante no fluxo do Felipe é **não confirmado**. Fonte: [README oficial][headroom], consulta em 22/10/2026.

**Sobreposição.** A compressão pode atuar sobre saídas de ai-memory, Graphify e Context7. Porém Headroom também documenta memória persistente, extração de fatos e reinjeção de contexto, o que se sobrepõe ao ai-memory; o wrapper registra Serena para navegação de código. Avaliação: limitar a POC à compressão, mantendo memória/aprendizado e registro de MCP fora do teste, evita misturar responsabilidades. Bases: [memória Headroom][headroom-memory], [proxy][headroom-proxy], [STATUS][status], [README local][readme], consulta/leitura em 22/10/2026.

**Riscos e custo no M4.** Um proxy entra no caminho de prompts, respostas e autenticação; é preciso avaliar logs, encaminhamento e falhas. Compressão pode omitir evidência necessária, e economia bruta pode ser anulada por latência, recuperação de conteúdo ou perda de cache. Essas são hipóteses de risco, não falhas observadas. O manifesto declara Python >=3.10 e dependências de tokenização/compressão; componentes opcionais mudam o custo. RAM, disco, downloads de modelos e compatibilidade arm64 efetiva são **não confirmado**. Bases: [README][headroom], [manifesto][headroom-manifesto], consulta em 22/10/2026.

A documentação do proxy informa beacon anônimo ligado por padrão, separado das estatísticas locais, e opção de registrar conteúdo completo. Também documenta o destino OpenAI padrão para a rota compatível e substituição explícita do upstream. A POC deve desativar beacon/log de conteúdo e conferir o destino antes de fornecer qualquer chave; “compressão local” não implica ausência de conexões externas. Fonte e proposta: [proxy oficial][headroom-proxy], consulta em 22/10/2026.

**Recomendação: testar**, apenas em proxy isolado, sem wrapper ou alteração global. Critério proposto: usar fixtures públicas com erros raros, identificadores e restrições obrigatórias; preservar 100% desses fatos e o resultado dos testes, observar falha segura do proxy e ausência de credenciais em logs; comparar tokens faturados/cache, latência, RAM e disco com a rota direta. Rejeitar se perder fato necessário ou mudar permissões/handoff. Proposta de 22/10/2026 baseada em [Headroom][headroom], [manifesto][headroom-manifesto] e [ADR-0001][adr1].

## 6. Context7

**Identidade e função.** `upstash/context7` recupera documentação e exemplos específicos de versões para o contexto do agente. O README documenta MCP e CLI com skills; a CLI requer Node >=22.13. O plugin já instalado foi informado pelo usuário, mas seu modo de execução, chave e limites ativos são **não confirmado**. Fonte: [README oficial][context7], consulta em 22/10/2026; estado de instalação: pedido desta tarefa, 22/10/2026.

**Sobreposição.** Avaliação: complementa skills e Skill Creator com referências de APIs; não substitui memória de decisões ou relações do código local. Evita nova instalação para uma capacidade já disponível. Ainda cabe conferir a versão do projeto e a fonte original, em vez de tomar qualquer trecho recuperado como verdade universal. Bases: [Context7][context7], [README local][readme], [STATUS][status], consulta/leitura em 22/10/2026.

**Riscos e custo no M4.** A recuperação introduz texto no contexto e consultas ao serviço; não enviar código institucional ou segredos como consulta é uma restrição proposta. Retenção específica da consulta, SLA, tokens por tarefa, limites da conta, RAM e disco do plugin no M4 são **não confirmado** nas fontes consultadas. MCP remoto e execução local têm custos diferentes; o modo instalado precisa ser identificado antes de medir. Fonte e análise: [Context7][context7], consulta em 22/10/2026.

**Recomendação: adotar agora** o plugin existente, sob demanda. Critério proposto: consultar três APIs da versão fixada no projeto e conferir assinatura/exemplo nas respectivas documentações oficiais; testar um caso de biblioteca ambígua ou versão ausente e exigir declaração da lacuna; registrar tokens e tempo. Aceite exige referências corretas, nenhuma API inventada e nenhuma segunda instalação. Proposta de 22/10/2026 baseada em [Context7][context7] e [ADR-0002][adr2].

## 7. OmniRoute

**Identidade e função.** `cheaper-inference/OmniRoute` é um gateway de inferência com endpoint unificado, provedores e fallback. O guia separa circuit breaker do provedor, cooldown da conexão e bloqueio de modelo. Isso não comprova transferência de estado interno, aprovações ou ações já realizadas numa sessão de agente. Fontes: [repositório oficial][omni], [guia de resiliência][omni-resilience], consulta em 22/10/2026.

**Sobreposição.** Avaliação: disputa a responsabilidade de roteamento da ADR-0002 e adiciona execução de alternativas de inferência. Não substitui o handoff do ai-memory nem a execução/aprovações do Paseo; skills, Graphify e os plugins atuais resolvem outras camadas. OpenCode já documenta integração própria com OpenRouter, sem exigir OmniRoute. Bases: [ADR-0002][adr2], [ADR-0003][adr3], [OpenCode][opencode], [resiliência][omni-resilience], consulta/leitura em 22/10/2026.

**Riscos e custo no M4.** Centraliza acesso a credenciais e conteúdo, exige validar cada provedor/rota e acrescenta serviço local e estado operacional. Gratuidade ou presença no catálogo não autoriza uso automatizado. A pesquisa anterior registra riscos de termos; não foi possível reconfirmar a issue #15059 nesta consulta, portanto sua situação atual é **não confirmado**. RAM, disco, tokens adicionais e compatibilidade efetiva no M4 são **não confirmado**; não há medição local. Bases: [OmniRoute][omni], [resiliência][omni-resilience], [pesquisa anterior][roteamento], consulta/leitura em 22/10/2026.

**Recomendação: evitar** no fluxo atual, por falta de lacuna demonstrada que justifique outra camada. Critério proposto para futura reabertura: duas APIs autorizadas, problema de disponibilidade/gasto medido, rotas permitidas explícitas, fallback simulado sem repetição de efeitos e sem vazamento de chaves, orçamento e rollback verificáveis. Só depois comparar com a integração direta, medindo RAM, disco e latência. Proposta de 22/10/2026 baseada em [ADR-0001][adr1], [ADR-0002][adr2], [OpenCode][opencode] e [resiliência][omni-resilience].

## 8. OpenRouter

**Identidade e função.** Serviço remoto de acesso e seleção de provedores/modelos. A API documenta ordenação, restrição de provedores, fallback e filtros de política de dados. OpenCode v2 documenta runtime próprio de OpenRouter. Não é um novo harness nem um mecanismo de memória. Fontes: [seleção de provedores][router-selection], [OpenCode][opencode], consulta em 22/10/2026.

**Sobreposição.** Avaliação: é uma alternativa de fornecimento de inferência na política consultiva existente; não duplica ai-memory, Graphify, skills, Creator ou Context7. Sobrepõe-se ao catálogo/fallback do OmniRoute, mas pode ser usado diretamente pelo OpenCode. Não trata as franquias das assinaturas Claude/Codex como créditos OpenRouter. Bases: [OpenCode][opencode], [limites OpenRouter][router-limits], [ADR-0002][adr2], consulta/leitura em 22/10/2026.

**Riscos e custo no M4.** Acrescenta intermediário remoto e políticas por endpoint. OpenRouter declara retenção de prompts opt-in, mas os provedores têm regras próprias; filtros `data_collection`/`zdr` precisam ser verificados na rota. Preço depende de modelo/provedor e limites dependem da conta; saldo, oferta gratuita efetiva e gasto da tarefa são **não confirmado**. Não exige executar o modelo localmente pela integração documentada, mas RAM/disco do cliente, latência e tokens faturados no M4 são **não confirmado**. Fontes: [coleta de dados][router-data], [seleção][router-selection], [limites][router-limits], [OpenCode][opencode], consulta em 22/10/2026.

**Recomendação: testar**, somente se faltar uma opção útil entre os provedores atuais, direto no OpenCode. Critério proposto: uma tarefa pessoal pública verificável, modelo/endpoint fixados, restrição de coleta e orçamento conferidos antes do envio, resultado aprovado pelos mesmos testes da rota atual e gasto registrado; indisponibilidade não pode abrir fallback fora da lista autorizada. Não comprar créditos para cumprir este backlog. Proposta de 22/10/2026 baseada em [seleção][router-selection], [limites][router-limits], [OpenCode][opencode] e [ADR-0002][adr2].

## 9. Ponytail 5.x versus o SHA fixado

**Versões e escopo.** Tanto o lock desta branch quanto o da referência fixam `e3ba2aa6f1e6f0bc4d69eb09c9f0d0a93af56156` e selecionam somente `ponytail-review`, `ponytail-audit` e `ponytail-debt`, sem plugin/hooks. O manifesto desse SHA informa 4.10.0; o `package.json` de `main` informa 5.3.2. Isso identifica artefatos, não confirma versão instalada no Mac nem último pacote publicado. Fontes: [lock atual][lock-atual], [lock de referência][lock], [manifesto antigo][pony-old-manifest], [manifesto atual][pony-manifest], leitura/consulta em 22/10/2026.

| Aspecto | SHA fixado × linha 5.x |
|---|---|
| Revisão | No SHA antigo, `ponytail-review` trata exclusivamente excesso de engenharia e exclui bugs/segurança/desempenho. Em `main`, passa a revisar correção, segurança, carga, testes, velocidade e simplicidade, lendo código conectado. Fonte: [skill antiga][pony-old-review], [skill atual][pony-review], consulta em 22/10/2026. |
| Auditoria | `ponytail-audit` antigo ordena cortes de complexidade no repo inteiro e exclui correção, segurança e desempenho. O atual amplia para qualidade, exige rastrear fluxos, prioriza gravidade e informa áreas não verificadas; permanece relatório sem aplicar correções. Fontes: [audit antigo][pony-old-audit], [audit atual][pony-audit], consulta em 22/10/2026. |
| Dívida | `ponytail-debt` antigo busca `ponytail:` com `grep`; o atual reconhece também `shortcut:`, aceita marcador escolhido pelo usuário, respeita exclusões do Git e manda descartar ocorrências que não sejam adiamentos. Ambos produzem relatório e só persistem arquivo quando solicitado. Fontes: [debt antigo][pony-old-debt], [debt atual][pony-debt], consulta em 22/10/2026. |
| Integração | O fluxo local copia três skills. O README atual promove plugin ativo por sessão com hooks; atualizar só as skills e adotar plugin completo são mudanças distintas. Fontes: [lock][lock], [README atual][pony], consulta/leitura em 22/10/2026. |
| Marcadores | A documentação atual usa `shortcut:`; a skill atual também reconhece o antigo `ponytail:`. Não migrar comentários existentes sem necessidade. Fonte e recomendação: [skill atual][pony-review], consulta em 22/10/2026. |

**Sobreposição e riscos.** Avaliação: a revisão ampliada se sobrepõe ao `code-review`, ao checklist e às revisões de segurança existentes; a variante antiga é mais especializada. Não substitui ai-memory/Graphify/Creator/Context7. Plugin e hooks ampliam a superfície e podem disputar instruções; compatibilidade com quota-guard e fluxo Paseo é **não confirmado**. Bases: [README local][readme], [skill antiga][pony-old-review], [skill atual][pony-review], [ADR-0003][adr3], consulta/leitura em 22/10/2026.

**Contexto e recursos.** Copiar skills sob demanda e executar hooks globais têm custos diferentes. Quantidade de tokens, RAM e disco no M4, e benefício líquido da troca são **não confirmado**. Os resultados publicados pelo autor usam tarefas/modelo próprios; não demonstram ganho neste workflow. Fonte e análise: [README Ponytail][pony], [benchmark do autor][pony-benchmark], consulta em 22/10/2026.

**Recomendação: testar** somente as três skills da 5.x em cópias isoladas, preservando o lock atual até comparar. Critério proposto: usar quatro diffs conhecidos (bug, vulnerabilidade, complexidade e mudança correta), comparar achados verificáveis/falsos positivos e contexto com o SHA antigo e `code-review`; manter comentários `ponytail:` reconhecidos e confirmar que não cria hooks, muda mods ou instala plugin. Aceitar atualização só com benefício sobre a combinação existente; plugin completo permanece fora deste teste. Proposta de 22/10/2026 baseada em [lock][lock], [skill antiga][pony-old-review], [skill atual][pony-review] e [ADR-0001][adr1].

## Ordem proposta e registro dos futuros testes

1. Usar o que já está instalado: Context7 sob demanda e Skill Creator para avaliar uma skill. Confirmar primeiro a identidade do Creator. Proposta de 22/10/2026 baseada em [Creator][creator], [Context7][context7] e [STATUS][status].
2. Fazer o diagnóstico somente leitura do Setup; testar Ponytail isolado se houver achados a comparar. Proposta de 22/10/2026 baseada em [Setup][setup], [Ponytail][pony] e [lock][lock].
3. Testar Serena ou Task Observer apenas para uma lacuna concreta; Headroom exige laboratório próprio por interceptar tráfego. Proposta de 22/10/2026 baseada em [Serena][serena], [Observer][observer], [Headroom][headroom] e [ADR-0001][adr1].
4. OpenRouter direto, quando necessário; evitar OmniRoute enquanto a necessidade de gateway não for demonstrada. Proposta de 22/10/2026 baseada em [OpenCode][opencode], [OmniRoute][omni] e [ADR-0002][adr2].

Para cada teste futuro, registrar versão/SHA, tarefa e resultado esperado, modelo, permissões, tokens de entrada/saída/cache, tempo, pico de memória dos processos envolvidos, disco antes/depois e rollback. Comparar a mesma tarefa com a base atual e executar uma ferramenta por vez, sem dados institucionais. Não há teto numérico de RAM/latência proposto como fato: o orçamento aceitável ainda precisa ser acordado com Felipe e medido com os demais apps abertos. Proposta metodológica de 22/10/2026 baseada na exigência local de ganho mensurado e telemetria da [ADR-0002][adr2].

## Nota de estado

Pesquisa documental e revisão de linguagem concluídas em 22/10/2026. Foram lidos os artefatos locais indicados e consultadas fontes dos mantenedores. Nenhuma ferramenta foi instalada/configurada, nenhuma credencial foi usada e nenhum benchmark ou chamada de inferência foi executado. Permanecem **não confirmado** a identidade pretendida do Task Observer, a implementação instalada do Skill Creator, as versões/configurações ativas e todos os custos no M4. Próximo passo proposto: conferir a identidade dos plugins existentes e escolher um único A/B do Skill Creator; adoções/experimentos não estão executados por este documento. Base do escopo e das pendências: [STATUS][status], [Creator][creator], [Observer][observer], leitura/consulta em 22/10/2026.

[status]: https://github.com/FelipeDuan/workflow-claude-codex-etc/blob/cd0252a834d1d6b93d0cd15caeb802cffb4f406a/docs/ai-os/STATUS.md
[adr1]: https://github.com/FelipeDuan/workflow-claude-codex-etc/blob/cd0252a834d1d6b93d0cd15caeb802cffb4f406a/docs/ai-os/decisions/0001-arquitetura-inicial.md
[adr2]: https://github.com/FelipeDuan/workflow-claude-codex-etc/blob/cd0252a834d1d6b93d0cd15caeb802cffb4f406a/docs/ai-os/decisions/0002-roteamento-por-capacidade-e-franquia.md
[adr3]: https://github.com/FelipeDuan/workflow-claude-codex-etc/blob/cd0252a834d1d6b93d0cd15caeb802cffb4f406a/docs/ai-os/decisions/0003-paseo-como-camada-de-execucao.md
[roteamento]: https://github.com/FelipeDuan/workflow-claude-codex-etc/blob/cd0252a834d1d6b93d0cd15caeb802cffb4f406a/docs/ai-os/PESQUISA-ROTEAMENTO.md
[readme]: https://github.com/FelipeDuan/workflow-claude-codex-etc/blob/cd0252a834d1d6b93d0cd15caeb802cffb4f406a/README.md
[lock]: https://github.com/FelipeDuan/workflow-claude-codex-etc/blob/cd0252a834d1d6b93d0cd15caeb802cffb4f406a/third-party.lock
[readme-atual]: https://github.com/FelipeDuan/workflow-claude-codex-etc/blob/3e2518b62a38243df8da691341b563ab46348fd8/README.md
[lock-atual]: https://github.com/FelipeDuan/workflow-claude-codex-etc/blob/3e2518b62a38243df8da691341b563ab46348fd8/third-party.lock
[setup]: https://raw.githubusercontent.com/anthropics/claude-plugins-official/main/plugins/claude-code-setup/README.md
[creator]: https://raw.githubusercontent.com/anthropics/skills/main/skills/skill-creator/SKILL.md
[openai-creator]: https://github.com/openai/skills/tree/main/skills/.system/skill-creator
[observer]: https://raw.githubusercontent.com/rebelytics/one-skill-to-rule-them-all/main/README.md
[observer-guide]: https://raw.githubusercontent.com/rebelytics/one-skill-to-rule-them-all/main/USER-GUIDE.md
[serena]: https://raw.githubusercontent.com/oraios/serena/main/README.md
[graphify]: https://github.com/Graphify-Labs/graphify
[headroom]: https://raw.githubusercontent.com/headroomlabs-ai/headroom/main/README.md
[headroom-manifesto]: https://raw.githubusercontent.com/headroomlabs-ai/headroom/main/pyproject.toml
[headroom-memory]: https://docs.headroomlabs.ai/docs/memory
[headroom-proxy]: https://docs.headroomlabs.ai/docs/proxy
[context7]: https://raw.githubusercontent.com/upstash/context7/master/README.md
[omni]: https://github.com/cheaper-inference/OmniRoute
[omni-resilience]: https://raw.githubusercontent.com/cheaper-inference/OmniRoute/main/docs/architecture/RESILIENCE_GUIDE.md
[opencode]: https://opencode.ai/v2/docs/providers/#gateways
[router-data]: https://openrouter.ai/docs/guides/privacy/data-collection
[router-selection]: https://openrouter.ai/docs/guides/routing/provider-selection
[router-limits]: https://openrouter.ai/docs/api_reference/limits
[pony]: https://github.com/DietrichGebert/ponytail
[pony-old-manifest]: https://raw.githubusercontent.com/DietrichGebert/ponytail/e3ba2aa6f1e6f0bc4d69eb09c9f0d0a93af56156/.claude-plugin/plugin.json
[pony-manifest]: https://raw.githubusercontent.com/DietrichGebert/ponytail/main/package.json
[pony-old-review]: https://raw.githubusercontent.com/DietrichGebert/ponytail/e3ba2aa6f1e6f0bc4d69eb09c9f0d0a93af56156/skills/ponytail-review/SKILL.md
[pony-review]: https://raw.githubusercontent.com/DietrichGebert/ponytail/main/skills/ponytail-review/SKILL.md
[pony-old-audit]: https://raw.githubusercontent.com/DietrichGebert/ponytail/e3ba2aa6f1e6f0bc4d69eb09c9f0d0a93af56156/skills/ponytail-audit/SKILL.md
[pony-audit]: https://raw.githubusercontent.com/DietrichGebert/ponytail/main/skills/ponytail-audit/SKILL.md
[pony-old-debt]: https://raw.githubusercontent.com/DietrichGebert/ponytail/e3ba2aa6f1e6f0bc4d69eb09c9f0d0a93af56156/skills/ponytail-debt/SKILL.md
[pony-debt]: https://raw.githubusercontent.com/DietrichGebert/ponytail/main/skills/ponytail-debt/SKILL.md
[pony-benchmark]: https://github.com/DietrichGebert/ponytail/blob/main/benchmarks/results/2026-10-07-agentic.md
