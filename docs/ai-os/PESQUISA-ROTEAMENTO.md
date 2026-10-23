# Pesquisa de roteamento de IA

Público: Felipe, para decidir como usar agentes em projetos pessoais com orçamento limitado. Consulta: 22/10/2026. Este documento distingue declaração do fornecedor, catálogo observado e recomendação. Não houve instalação, cadastro, autenticação, uso de chave ou chamada de inferência.

## 1. OpenCode 2 e OpenCode Zen

A URL de Zen redireciona para Console. Os gratuitos são temporários. Fontes: [Console](https://opencode.ai/v2/docs/console/models/), consulta em 22/10/2026.

Políticas abaixo: declaração do OpenCode para essa rota; “melhoria” permite uso dos dados. Fonte: [privacidade](https://opencode.ai/v2/docs/console/models/#privacy), consulta em 22/10/2026.

| ID | API pública nesta consulta | Retenção / uso dos dados |
|---|---|---|
| `glm-5.3-flash-free` | Presente | Zero/sem treino |
| `deepseek-v4.1-flash-free` | Presente | Zero/sem treino |
| `mimo-v2.6-flash-free` | Presente | Prazo não confirmado; melhoria |
| `big-pickle` | Presente | Prazo não confirmado; melhoria |
| `beam-free` | Presente | 30 dias; sem treino |
| `flint-40b-free` | Presente | 30 dias; melhoria |
| `nemotron-3.5-lightning-free` | Presente | Registro para segurança/melhoria; prazo não confirmado |
| `nemotron-3.5-super-vl-free` | Presente | Registro para segurança/melhoria; prazo não confirmado |
| `jev-1.13-free` | Presente | Regra geral zero/sem treino; confirmação específica não encontrada |
| `nemotron-3-ultra-free` | Ausente; consta nas docs | Registro para segurança/melhoria; prazo não confirmado |
| `mimo-v2.5-free` | Ausente; consta nas docs | Prazo não confirmado; melhoria |
| `exo-free` | Ausente; consta nas docs | Prazo não confirmado; melhoria |
| `longcat-2.5-preview-free` | Ausente; consta nas docs | Zero/sem treino |

Fontes de cada linha: [IDs e políticas documentados](https://opencode.ai/v2/docs/console/models/), [presença na API](https://opencode.ai/inference/v1/models), consulta em 22/10/2026. Não interpretar os ausentes como encerrados: o motivo da ausência é não confirmado.

Conclusão sobre a alegação: confirmada para essas variantes GLM/DeepSeek; MiMo admite melhoria. Fonte: [política](https://opencode.ai/v2/docs/console/models/#privacy), consulta em 22/10/2026.

Os endpoints NVIDIA são experimentais, com restrição a dados pessoais/confidenciais. Seus termos restringem a avaliação, sem uso em produção. Fonte: [NVIDIA API Trial Terms, §§1.2, 1.4 e 2.6](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf), consulta em 22/10/2026.

RPM, requisições/dia, tokens/dia, fim da promoção e SLA: não confirmado. Fontes verificadas: [Console](https://opencode.ai/v2/docs/console/models/), [API](https://opencode.ai/inference/v1/models), consulta em 22/10/2026.

O catálogo público respondeu sem chave, mas não foi feita inferência. As ausências não comprovam encerramento. Fonte: [API observada](https://opencode.ai/inference/v1/models), consulta em 22/10/2026. No OpenCode, confira `/models` antes de selecionar. Fonte: [modelos v2](https://opencode.ai/v2/docs/models/), consulta em 22/10/2026. Jev produz decisões estruturadas, não código. Fonte: [TypeSafe](https://docs.typesafe.ai/concepts/system-one), consulta em 22/10/2026.

## 2. OpenRouter

### Gratuitos e limites

A coleção oficial mostra os 16 gratuitos mais usados, não um inventário completo. Em 22/10/2026 ela lista os nomes abaixo; são nomes de exibição, não IDs para copiar na configuração. Lista exaustiva e disponibilidade para uma conta específica: não confirmado. Fontes: [coleção oficial](https://openrouter.ai/collections/free-models/), [API de modelos](https://openrouter.ai/api/v1/models), consulta em 22/10/2026.

| Família | Modelos exibidos na coleção |
|---|---|
| NVIDIA | Nemotron 3 Ultra, 3.5 Super VL, 3.5 Lightning, 3 Super, 3 Nano Omni |
| Poolside | Laguna S 2.1, Laguna XS 2.1 |
| Thinking Machines | Inkling, Inkling Small |
| Outros | Dots3-Note Preview, North Mini Code, Mercury Decide, Xing4.0 29B A4B, Flint, LFM2.5-2.6B, Span-01 Lite |

Fonte de todas as linhas: [coleção de gratuitos](https://openrouter.ai/collections/free-models/), consulta em 22/10/2026. A coleção também informa que Laguna S/XS podem usar entradas e saídas para treino; Liquid pode reter e treinar. Não presumir privacidade uniforme entre gratuitos. Fonte: [mesma coleção, avisos dos modelos](https://openrouter.ai/collections/free-models/), consulta em 22/10/2026.

A afirmação de terceiros está confirmada: 20 requisições/minuto e 50/dia; depois de comprar ao menos US$ 10 de créditos, 1.000/dia. É compra acumulada, não uma assinatura mensal nem exigência documentada de manter US$ 10 de saldo. Tentativas com erro contam; saldo negativo bloqueia gratuitos. Fontes: [preços e FAQ atuais](https://openrouter.ai/pricing), [limites, campo de compras acumuladas](https://openrouter.ai/docs/api_reference/limits), consulta em 22/10/2026.

As cotas são da conta; multiplicar chaves ou contas não aumenta os limites. O contador autenticado `GET /api/v1/key` informa uso e teto diário. Não foi consultado porque esta pesquisa não usa chaves. Fonte: [limites](https://openrouter.ai/docs/api_reference/limits), consulta em 22/10/2026.

### Treino e retenção

OpenRouter declara que não armazena prompts/respostas por padrão; os registros de conteúdo são opcionais. Isso não define o tratamento no provedor que executa o modelo. Fonte: [coleta de dados do OpenRouter](https://openrouter.ai/docs/guides/privacy/data-collection), consulta em 22/10/2026.

Cada endpoint tem política própria. Há opções separadas para permitir provedores que treinam em modelos pagos e gratuitos. Recusar treino remove esses provedores das rotas elegíveis. Fonte: [políticas dos provedores](https://openrouter.ai/docs/guides/privacy/provider-logging), consulta em 22/10/2026.

É possível exigir retenção zero na conta ou por requisição, com `provider.zdr: true`. Esse filtro pode reduzir a oferta elegível. OpenRouter considera cache implícito em memória compatível com ZDR; portanto, “zero retenção” segue essa definição. Fonte: [ZDR](https://openrouter.ai/docs/guides/features/zdr), consulta em 22/10/2026.

Na API, `provider.data_collection: "deny"` exclui provedores que coletam dados; `provider.zdr: true` exige endpoints classificados como ZDR. `only` restringe os provedores permitidos, `order` prioriza a sequência e `allow_fallbacks` controla alternativas. A classificação representa o conhecimento do OpenRouter sobre as políticas, sem substituir os termos do provedor. Fonte: [seleção de provedores](https://openrouter.ai/docs/guides/routing/provider-selection), consulta em 22/10/2026.

Há uma divergência a conferir antes de depender desses controles sem pagar: a FAQ anuncia ZDR em todos os planos, mas a tabela de preços marca “Data Policy-Based Routing” como ausente no Free. O alcance exato de cada controle numa conta gratuita é não confirmado nesta pesquisa. Fontes: [preços](https://openrouter.ai/pricing), [controles documentados](https://openrouter.ai/docs/guides/privacy/provider-logging), consulta em 22/10/2026.

### Integração com OpenCode 2

Sim, é nativa: OpenCode v2 possui runtime e catálogo do OpenRouter e recomenda preservar `@opencode/ai/providers/openrouter`. O modelo usa o prefixo `openrouter/` seguido do ID completo. Nenhum OmniRoute é necessário para essa integração. Fonte: [provedores v2, Gateways](https://opencode.ai/v2/docs/providers/#gateways), consulta em 22/10/2026.

## 3. OmniRoute

### O que faz e sinais de manutenção

O endereço solicitado redireciona para `cheaper-inference/OmniRoute`. É um gateway local com API compatível com OpenAI, catálogo de provedores, painel e fallback. Gratuitos dependem das contas e condições dos serviços conectados; o gateway não concede a soma das franquias anunciadas. Fontes: [repositório oficial](https://github.com/diegosouzapw/OmniRoute), [esclarecimento do mantenedor](https://github.com/cheaper-inference/OmniRoute/issues/15059), consulta em 22/10/2026.

A release marcada Latest é v3.8.52, publicada em 19/10/2026; há releases anteriores próximas e notas de correções. O `package.json` também informa 3.8.52 e exige Node `>=22.22.2 <23 || >=24.0.0 <27`. São sinais de manutenção ativa, não prova de estabilidade para o fluxo do Felipe. Fontes: [releases](https://github.com/cheaper-inference/OmniRoute/releases), [manifesto](https://raw.githubusercontent.com/cheaper-inference/OmniRoute/main/package.json), consulta em 22/10/2026.

A licença é MIT, com uso, alteração e redistribuição permitidos sob suas condições e sem garantia. Ela cobre o software; não autoriza acesso a serviços externos. Fonte: [LICENSE](https://raw.githubusercontent.com/cheaper-inference/OmniRoute/main/LICENSE), consulta em 22/10/2026.

### Como faz fallback

O projeto separa falha do provedor, indisponibilidade de uma conexão e seleção de alternativas. Um circuit breaker suspende provedores com falhas repetidas; conexões com quota/erro entram em cooldown, com espera crescente e consideração de `Retry-After`. Combos podem tentar outros alvos. Isso trata requisições de inferência; restauração exata de uma sessão Claude Code/Codex, permissões e ações já executadas é não confirmado. Fonte: [guia de resiliência](https://raw.githubusercontent.com/cheaper-inference/OmniRoute/main/docs/architecture/RESILIENCE_GUIDE.md), consulta em 22/10/2026.

### Rotas gratuitas e `tos: avoid`

`tos: avoid` é uma classificação do próprio OmniRoute sobre termos dos serviços, não uma autorização desses serviços. Há divergência oficial: `FREE_TIERS.md` diz que o rótulo é apenas informativo; na issue #15059, o mantenedor relata alteração para excluir esses provedores do Auto por padrão na linha 3.8.52. Confirmar a política efetiva de cada versão/configuração continua necessário; exclusão universal em toda rota ou combo é não confirmado. Fontes: [tabela e aviso](https://raw.githubusercontent.com/cheaper-inference/OmniRoute/main/docs/reference/FREE_TIERS.md), [correção e histórico](https://github.com/cheaper-inference/OmniRoute/issues/15059), consulta em 22/10/2026.

Um exemplo verificável direto nos termos: Duck.ai proíbe consultas automatizadas e contorno de limites/restrições, e pode suspender acesso. Usá-lo como uma rota programática gratuita conflita com essa cláusula. A classificação dos demais serviços não foi auditada individualmente; sua permissão é não confirmado. Fonte: [termos do Duck.ai, atualizados em 01/10/2026](https://duckduckgo.com/duckai/privacy-terms), consulta em 22/10/2026.

O mantenedor também registrou erro 403 do OpenCode Free fora do OpenCode em teste da versão 3.8.51. Isso impede assumir que os gratuitos do Console funcionarão pelo gateway. A situação de cada modelo na versão atual é não confirmado por execução. Fonte: [issue #15059, relato versionado](https://github.com/cheaper-inference/OmniRoute/issues/15059), consulta em 22/10/2026.

### Comparação com este repositório

O projeto local tem política consultiva em `roteamento.json`, com execução automática desativada e bloqueio de dados institucionais. A ADR-0002 adia gateway e automação. OmniRoute acrescentaria execução centralizada de fallback, mas também outro serviço para configurar e manter. Esta é uma comparação de artefatos, não uma confirmação do que está instalado no Mac. Fontes primárias locais: [política](roteamento.json), [ADR-0002](decisions/0002-roteamento-por-capacidade-e-franquia.md), leitura em 22/10/2026. Exceção ao uso de URLs públicas: publicação desses arquivos no GitHub não confirmada; os links apontam para os arquivos efetivamente lidos. Fonte externa: [resiliência do OmniRoute](https://raw.githubusercontent.com/cheaper-inference/OmniRoute/main/docs/architecture/RESILIENCE_GUIDE.md), consulta em 22/10/2026.

Avaliação: não apareceu uma necessidade atual que justifique adicioná-lo apenas para usar OpenCode com OpenRouter, cuja integração já é nativa. Faria sentido reavaliar quando houver várias APIs autorizadas e um problema medido de disponibilidade ou gestão de gasto. Base da recomendação: [integração nativa](https://opencode.ai/v2/docs/providers/#gateways), [ADR local](decisions/0002-roteamento-por-capacidade-e-franquia.md), consulta/leitura em 22/10/2026.

## 4. Paseo e Continuity

### O que o Paseo entrega

Paseo executa agentes na máquina do usuário, reúne edição/revisão e permite acesso por desktop, web e celular. O app desktop inclui e inicia o daemon. Fonte: [início oficial](https://paseo.sh/docs), consulta em 22/10/2026.

Claude Code, Codex e OpenCode constam como provedores nativos, exigindo a CLI instalada e autenticada. As docs não indicam ali uma versão específica de OpenCode 2 validada: compatibilidade com cada release v2 é não confirmado nesta pesquisa. Fonte: [provedores suportados](https://paseo.sh/docs/supported-providers), consulta em 22/10/2026.

A orquestração lança agentes com provedores/modelos disponíveis no host, envia mensagens entre eles e acompanha tarefas. A injeção de ferramentas MCP fica desligada por padrão. Fonte: [orquestração](https://paseo.sh/docs/orchestration), consulta em 22/10/2026.

Worktrees dão diretórios separados para mudanças paralelas. Dependências e arquivos ignorados não aparecem automaticamente no novo diretório; scripts de preparação precisam ser avaliados pelo que executam. No Mac do Felipe, manter poucos worktrees ativos é uma recomendação para limitar duplicação de dependências. Fonte do comportamento: [worktrees](https://paseo.sh/docs/worktrees), consulta em 22/10/2026.

`/paseo-handoff` transfere briefing com arquivos, progresso, decisões e critérios de aceite. Não há evidência nessa função de transferência de estado interno do modelo ou de renovação da franquia. Handoff automático seguro para qualquer falha é não confirmado. Fonte: [skills de orquestração](https://paseo.sh/docs/skills), consulta em 22/10/2026.

### Instalação no macOS, somente referência

A página de download anuncia v0.12.0, binário Apple Silicon e macOS 13+. Para o M4, a opção correspondente é Apple Silicon. Fonte: [download](https://paseo.sh/download), consulta em 22/10/2026.

```sh
# Alternativa documentada: instala o aplicativo desktop pelo Homebrew.
brew install --cask paseo

# Alternativa para uso sem desktop: instala a CLI e inicia o daemon.
npm install -g @getpaseo/cli
paseo
```

Comandos documentados, não executados. O desktop já inclui daemon; a CLI separada é opção para outro modo de uso. Fontes: [download](https://paseo.sh/download), [getting started](https://paseo.sh/docs), consulta em 22/10/2026.

### Continuity: origem, acesso e manutenção

É um plugin comunitário de `keefeere/paseo-continuity`. O manifesto exige Paseo `>=0.10.1`; o pacote consultado declara versão 0.2.1, autor Chechulin Serhii e licença MIT. A versão efetivamente publicada no npm é não confirmado. Fontes: [manifesto](https://raw.githubusercontent.com/keefeere/paseo-continuity/main/paseo-plugin.json), [package.json](https://raw.githubusercontent.com/keefeere/paseo-continuity/main/package.json), consulta em 22/10/2026.

Ao reconhecer quota esgotada ou rate limit, cria outro agente no próximo provedor pronto, no mesmo workspace, com contexto limitado. Não troca o provedor da sessão existente. O README descreve redação de segredos comuns, prevenção de sucessores duplicados e teto de transições; esses mecanismos não foram testados aqui. Fonte: [README do autor](https://github.com/keefeere/paseo-continuity), consulta em 22/10/2026.

Há opção manual de compactar e mover e resumo por outro modelo. Esse resumo acrescenta outro destinatário potencial do contexto. Não há garantia documentada de preservação integral nem de detecção de todo segredo; revisar o material transferido continua necessário. Fonte: [README do autor](https://github.com/keefeere/paseo-continuity), consulta em 22/10/2026.

Plugins executam sem sandbox com o acesso do usuário do daemon; código cliente roda no app. Confiar no Continuity inclui suas dependências e atualizações, além do acesso a históricos e criação de agentes. Fonte: [segurança dos plugins Paseo](https://paseo.sh/docs/plugins), consulta em 22/10/2026.

O repositório mostra cinco commits e scripts de typecheck/testes. É evidência de código e verificações disponíveis, insuficiente para concluir manutenção duradoura ou maturidade operacional; SLA, auditoria independente e estabilidade em OpenCode 2 são não confirmado. Fontes: [histórico visível](https://github.com/keefeere/paseo-continuity), [scripts](https://raw.githubusercontent.com/keefeere/paseo-continuity/main/package.json), consulta em 22/10/2026.

## 5. Escolha mais simples para Felipe

As opções abaixo são recomendações desta pesquisa, não resultados de benchmark nem mudanças já aplicadas.

| Momento | Recomendação e motivo | Base consultada em 22/10/2026 |
|---|---|---|
| Adotar agora no fluxo | Usar as CLIs já disponíveis e handoff explícito. Para tarefas pessoais pequenas e verificáveis, priorizar GLM/DeepSeek gratuitos dentro do OpenCode enquanto disponíveis; conferir o diff e os testes. | [Políticas do Console](https://opencode.ai/v2/docs/console/models/), [handoff Paseo](https://paseo.sh/docs/skills) |
| Testar depois | OpenRouter direto no OpenCode, se faltar uma opção útil. Começar no gratuito; comprar US$ 10 somente se o teto de 50/dia estiver atrapalhando e couber no orçamento. | [Integração](https://opencode.ai/v2/docs/providers/#gateways), [limites](https://openrouter.ai/pricing) |
| Testar depois | Paseo Desktop se revisar várias sessões/worktrees resolver um problema real. Continuity só após revisar código e transferência de contexto, num projeto descartável. | [Paseo](https://paseo.sh/docs), [plugins](https://paseo.sh/docs/plugins), [Continuity](https://github.com/keefeere/paseo-continuity) |
| Evitar agora | OmniRoute como camada adicional; rotas `tos: avoid`; tratar gratuidade como disponibilidade garantida. Reservar MiMo/Nemotron e outros acessos com melhoria de dados a material público apropriado. | [Termos Duck.ai](https://duckduckgo.com/duckai/privacy-terms), [divergência OmniRoute](https://github.com/cheaper-inference/OmniRoute/issues/15059), [Console](https://opencode.ai/v2/docs/console/models/) |

Nota de estado: pesquisa e revisão de linguagem concluídas em 22/10/2026. Foram consultadas fontes públicas oficiais e arquivos locais; não houve instalação, cadastro, uso de chave ou commit. Pendências: testar compatibilidade Paseo/OpenCode 2, disponibilidade real e quotas do Console, controles de privacidade numa conta gratuita OpenRouter e comportamento do Continuity. Próximo passo exato: escolher uma tarefa pessoal curta com teste verificável e validar um único modelo já disponível, antes de acrescentar gateway ou fallback automático.
