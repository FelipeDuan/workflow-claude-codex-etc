# Orquestradores de agentes de código para o Felipe AI OS

Pesquisa para o Felipe decidir o próximo experimento no Mac M4 com 16 GB de RAM. Consulta das fontes externas: **22/10/2026**. Esta é uma comparação documental; nenhum candidato foi instalado ou executado nesta pesquisa. “Atende” significa capacidade documentada, não aprovação no laboratório. Links locais são fontes primárias do projeto, lidas em 22/10/2026; sua publicação em URL pública não foi confirmada.

## Conclusão para a decisão

Testar primeiro **Paseo Desktop estável, sem Continuity**, como já prevê a ADR-0001. Ele tem delegação entre provedores, mensagens, handoff assistido e worktrees. A comparação com Superset merece um segundo experimento: suas docs descrevem medidores de franquia, continuação com outra família e coordenação pela CLI. Orca também se aplica e é o único dos três com menção explícita a OpenCode 2 beta nas páginas de suporte consultadas, mas inicia agentes com permissões amplas por padrão. Esta ordem é uma recomendação baseada nas fontes, não um ranking de desempenho. Fontes: [ADR-0001](decisions/0001-arquitetura-inicial.md), [Paseo](https://paseo.sh/docs/orchestration), [Superset](https://docs.superset.sh/orchestration), [Orca](https://www.onorca.dev/docs/agents/supported), leitura/consulta em 22/10/2026.

Nenhum candidato teve comprovado o ciclo completo desejado: ler nossos sensores, aplicar o piso de capacidade/risco, escolher por franquia, trocar de provedor após uma falha e retornar ao preferido em checkpoint seguro. Medidores e seleção de modelo cobrem partes desse ciclo. O roteamento do AI OS permanece consultivo; não há motivo documentado para substituir a ADR-0002 por uma automação pronta. Fontes examinadas: [política local](decisions/0002-roteamento-por-capacidade-e-franquia.md), [Paseo CLI](https://paseo.sh/docs/cli), [Superset Usage](https://docs.superset.sh/usage), [Orca Usage](https://www.onorca.dev/docs/agents/usage-tracking), leitura/consulta em 22/10/2026.

## Ponto de partida e critérios

A seção mais recente do STATUS registra ai-memory e o handoff Claude → Codex → OpenCode → Claude validados, quota-guard real nas janelas de 5 horas e semana, leitor Codex por App Server e modelos gratuitos OpenCode testados em worktrees paralelos. A tabela antiga do mesmo arquivo contém estados anteriores. Para esta decisão, usamos o registro final e o contexto informado pelo Felipe. Fonte: [STATUS](STATUS.md), leitura em 22/10/2026.

| Objetivo | O que será considerado evidência suficiente |
|---|---|
| A. Continuidade | Separar quatro capacidades: handoff manual, assistido, failover automático por quota e retorno ao preferido em checkpoint seguro. Abrir outro chat não comprova transferência de estado. |
| B. Capacidade e franquia | Ler limites/reset com origem e validade, preservar `unknown`, aplicar risco/capacidade e dividir só tarefas independentes. |
| C. Qualidade e custo | Reaproveitar Claude Pro/ChatGPT Plus, reservar modelos caros para tarefas que exigem isso e validar entregas por diff/testes. Gratuito não implica disponibilidade ou política de dados uniforme. |
| D. Paralelismo seguro | Um executor que escreve por checkout; worktrees separados; distinguir agente trabalhando, aguardando e travado por sinais de progresso. |
| E. Revisão entre famílias | Um agente envia proposta/diff; outro, de família diferente, responde com concordância ou discordância fundamentada. |
| F. Uso diário | Cockpit e aprovações compreensíveis; celular opcional; consumo de RAM/disco/processos aceitável no Mac do Felipe. |

Os critérios acima operacionalizam o pedido do Felipe e as decisões existentes. Bases locais: [ADR-0001](decisions/0001-arquitetura-inicial.md), [ADR-0002](decisions/0002-roteamento-por-capacidade-e-franquia.md), [incidentes I-01, I-03 e I-10](INCIDENTES.md), [pesquisa de provedores e roteamento](PESQUISA-ROTEAMENTO.md), leitura em 22/10/2026.

## Matriz candidato × objetivo

“Parcial” indica cobertura de uma parte do objetivo; “não confirmado” indica falta de evidência suficiente; “não” indica que a ferramenta fica fora daquela função no escopo documentado. D fica parcial quando há worktrees, mas nenhum bloqueio comprovado contra dois escritores no mesmo checkout. C e F incluem qualidade real e consumo no M4, ainda sem medição.

| Candidato | A | B | C | D | E | F | Base da avaliação, consulta em 22/10/2026 |
|---|---|---|---|---|---|---|---|
| Paseo | Parcial | Parcial | Parcial | Parcial | Atende | Parcial | [Handoff/revisão](https://paseo.sh/docs/skills), [orquestração](https://paseo.sh/docs/orchestration), [franquia](https://paseo.sh/docs/cli), [desktop/mobile](https://paseo.sh/docs) |
| Orca, da Stably | Parcial | Parcial | Parcial | Parcial | Atende | Parcial | [Suporte/permissões](https://www.onorca.dev/docs/agents/supported), [franquia](https://www.onorca.dev/docs/agents/usage-tracking), [orquestração experimental](https://www.onorca.dev/docs/cli/orchestration) |
| Superset | Parcial | Parcial | Parcial | Parcial | Atende | Parcial | [Continuação](https://docs.superset.sh/agent-sessions), [franquia](https://docs.superset.sh/usage), [coordenação](https://docs.superset.sh/orchestration), [preços](https://superset.sh/pricing) |
| Conductor, da Melty Labs | Parcial | Não confirmado | Parcial | Parcial | Parcial | Parcial | [Introdução](https://www.conductor.build/docs), [paralelismo](https://www.conductor.build/docs/concepts/parallel-agents), [provedores](https://www.conductor.build/docs/guides/providers) |
| Claude Squad | Parcial | Não confirmado | Parcial | Parcial | Não confirmado | Parcial | [README](https://github.com/smtg-ai/claude-squad), [issue de prompt perdido](https://github.com/smtg-ai/claude-squad/issues/266) |
| Vibe Kanban | Parcial | Não confirmado | Parcial | Parcial | Parcial | Parcial | [Escopo](https://github.com/BloopAI/vibe-kanban), [encerramento comercial](https://www.vibekanban.com/blog/shutdown), [releases](https://www.vibekanban.com/release-notes) |
| Paseo + Continuity, plugin adicional | Parcial | Parcial | Parcial | Não confirmado | Parcial | Não confirmado | [README do plugin](https://github.com/keefeere/paseo-continuity), [segurança de plugins](https://paseo.sh/docs/plugins) |

## Suporte e versões: o que está comprovado

Os executores registrados localmente são Claude Code 2.1.308, Codex CLI 0.163.0 e OpenCode 2.0.32. Suporte genérico a “OpenCode” não comprova compatibilidade com sua arquitetura v2 nem com essa versão exata. Nenhum dos pares candidato × versões locais foi testado nesta pesquisa. Fonte local: [STATUS](STATUS.md), leitura em 22/10/2026.

| Candidato | Claude Code e Codex | OpenCode 2.0.32 | Versão do candidato observada | Fontes, consulta em 22/10/2026 |
|---|---|---|---|---|
| Paseo | Provedores nativos; CLI própria instalada e autenticada. Versões mínimas/exatas locais: não confirmado. | OpenCode nativo; v2.0.32: não confirmado. | Estável 0.12.0, de 19/10; há 0.13.0-beta.1 em 22/10. | [Provedores](https://paseo.sh/docs/supported-providers), [releases](https://github.com/getpaseo/paseo/releases) |
| Orca | Integração de uso, sessões e contas. Versões locais exatas: não confirmado. | Docs dizem explicitamente “OpenCode 2 beta supported”; patch 2.0.32: não confirmado. | 1.4.237, de 21/10. | [Suporte](https://www.onorca.dev/docs/agents/supported), [releases](https://github.com/stablyai/orca/releases) |
| Superset | Integração de status, retomada, uso e franquia. Versões locais exatas: não confirmado. | OpenCode tem status/retomada/uso; v2.0.32: não confirmado. | Desktop e CLI 1.39.0, de 19/10; há canaries posteriores. | [Suporte por agente](https://docs.superset.sh/supported-agents), [releases](https://github.com/superset-sh/superset/releases) |
| Conductor | Harnesses Claude Code e Codex; login por assinatura/CLI documentado. Versões internas/exatas locais: não confirmado. | Há harness OpenCode; v2.0.32 e gratuitos sem login: não confirmado. | Changelog inicia em 0.91.0, de 15/10. | [Autenticação](https://www.conductor.build/docs/guides/providers), [changelog](https://www.conductor.build/changelog) |
| Claude Squad | Lança programas locais; Claude e Codex citados. Codex moderno com Plus: não confirmado por teste. | OpenCode citado no repo; v2.0.32: não confirmado. | 1.0.20, de 20/08. | [Repositório](https://github.com/smtg-ai/claude-squad), [releases](https://github.com/smtg-ai/claude-squad/releases) |
| Vibe Kanban | Release 0.1.44 registra pins Claude 2.1.119 e Codex 0.124.0, diferentes dos locais. | Release 0.1.43 fixou OpenCode 1.4.7; suporte v2 não confirmado. | Página oficial marca 0.1.44-20260424091429, de 24/04, como Latest. | [Notas versionadas](https://www.vibekanban.com/release-notes) |

### Paseo

Para A, `/paseo-handoff` envia briefing com progresso, arquivos, decisões e critérios; não migra o estado interno de uma sessão. Para E, committee e advisor permitem segunda análise, com preferência por famílias diferentes no committee. Para D, pedir worktree separado é uma escolha explícita do fluxo. Failover por quota e retorno automático ao preferido no núcleo: não confirmado. Fonte: [skills oficiais](https://paseo.sh/docs/skills), consulta em 22/10/2026.

Há duas adaptações necessárias: a skill committee orienta o agente principal a implementar após sintetizar; no AI OS, ele deve delegar essa implementação. E `paseo run` chamado por um agente herda o mesmo workspace, exigindo criar outro worktree explicitamente para um segundo escritor. Fontes: [skills](https://paseo.sh/docs/skills), [orquestração](https://paseo.sh/docs/orchestration), [regra local de delegação](../../AGENTS.md), consulta/leitura em 22/10/2026.

Para B, `paseo usage` expõe franquias, saldos, reset, origem e timestamp, com cache de cinco minutos e atualização forçada. Não mede custo individual de um agente. A CLI fornece os sinais; aplicação automática da política de capacidade do AI OS e leitura dos nossos JSONs: não confirmado. Para E, a orquestração pode lançar modelos/provedores, enviar mensagens, parar tarefas e coletar resultados. Fontes: [CLI](https://paseo.sh/docs/cli), [orquestração](https://paseo.sh/docs/orchestration), consulta em 22/10/2026.

Para F, desktop inicia o próprio daemon; há web/celular e instalação sem desktop. CLI, MCP, SDK TypeScript e plugins tornam possível uma integração futura, mas ela seria trabalho adicional. Para C, usa as credenciais das CLIs; economia/qualidade obtidas no Mac são não confirmado. Fontes: [início](https://paseo.sh/docs), [SDK](https://paseo.sh/docs/sdk), [provedores](https://paseo.sh/docs/supported-providers), consulta em 22/10/2026.

Modelo de segurança: daemon local, relay opcional e conexões diretas. A configuração documenta `127.0.0.1:6767`; exposição direta exige avaliar autenticação e transporte. O relay cifrado não impede que o provedor do modelo receba prompts. Plugins são código confiado, sem sandbox, com acesso do usuário do daemon; não instalar Continuity só porque aparece numa lista de plugins. Fontes: [segurança](https://paseo.sh/docs/security), [configuração](https://paseo.sh/docs/configuration), [plugins](https://paseo.sh/docs/plugins), consulta em 22/10/2026.

Integração com ai-memory/quota-guard: complementa o cockpit; não há integração específica comprovada com nossos hooks ou arquivos de franquia. É necessário verificar se cada lançamento preserva config global, MCP, `CLAUDE_CODE_PLUGIN_DIRS` e identificação do repo/worktree. Não criar handoff explícito duplicado no ai-memory durante o teste. Esta é uma hipótese de compatibilidade e um plano de verificação, baseado em [provedores Paseo](https://paseo.sh/docs/providers), [ADR-0002](decisions/0002-roteamento-por-capacidade-e-franquia.md) e [I-07/I-08](INCIDENTES.md), consulta/leitura em 22/10/2026.

### Orca: identificar o produto antes de comparar

O candidato avaliado é **Stably AI, `stablyai/orca`, `onorca.dev`**. Existe como ambiente de agentes com desktop, mobile e runtime remoto. Outros projetos chamados Orca não devem herdar suas capacidades. O Orca da VirtusLab é outro repositório/workflow; não é o produto comparado aqui. Fontes: [Stably Orca](https://github.com/stablyai/orca), [VirtusLab Orca](https://github.com/VirtusLab/orca), consulta em 22/10/2026.

Para A/B, há uso/reset, aviso em 80% e troca de contas. Trocar contas Codex não é handoff Claude → Codex. O painel OpenCode Go exige cookie completo do Console; isso não comprova medição dos modelos gratuitos usados pelo Felipe. Leitura dos JSONs locais, seleção automática por capacidade/franquia e retorno seguro entre provedores: não confirmado. Fonte: [uso e limites](https://www.onorca.dev/docs/agents/usage-tracking), consulta em 22/10/2026.

Para D/E, a camada experimental tem tarefas, dependências, dispatches, workers supervisionados, mensagens e decision gates. Um Run é namespace/inbox, não scheduler. Workers podem ter worktree próprio e modelo selecionado; o modelo OpenCode é validado no host e aplicado ao worker. Heartbeat ajuda a observar atividade, mas não comprova avanço útil ou solução do I-01. Fonte: [orquestração](https://www.onorca.dev/docs/cli/orchestration), consulta em 22/10/2026.

Para C/F, usa assinaturas existentes e reúne diffs, terminal e múltiplos agentes. O risco imediato é segurança: argumentos padrão incluem `--dangerously-skip-permissions` no Claude e `--dangerously-bypass-approvals-and-sandbox` no Codex. Trocar para Manual antes de usar é critério obrigatório do laboratório. Worktree separa arquivos Git; não protege credenciais e demais diretórios do usuário. Fonte do comportamento: [suporte e permissões](https://www.onorca.dev/docs/agents/supported), consulta em 22/10/2026; limite de isolamento e exigência de aprovação: [ADR-0001](decisions/0001-arquitetura-inicial.md), leitura em 22/10/2026.

Orca respeita arquivos de memória e configurações por repo e adiciona hooks próprios de status. Escreve o hook Codex só quando muda e relê endpoint após reinício. Isso pode complementar ai-memory, mas compatibilidade com os hooks globais e quota-guard locais é não confirmado. A alteração ainda pode exigir trust manual do Codex. CLI, skills e MCP permitem extensão; não há prova de plugin específico para nosso roteamento. Fontes: [hooks e memória](https://www.onorca.dev/docs/agents/hooks-memory), [orquestração](https://www.onorca.dev/docs/cli/orchestration), [I-08](INCIDENTES.md), consulta/leitura em 22/10/2026.

### Superset

Para A, “Continue with another agent” inicia sessão nova com até 36 mil caracteres recentes; não preserva estado interno. O material enviado não tem redação de segredos. Retomada automática após morte inesperada é da mesma sessão; não comprova failover por quota. Fork mantém o original vivo e ambos no mesmo workspace: essa opção exige cuidado com a regra de um escritor por checkout. Fonte: [sessões e forks](https://docs.superset.sh/agent-sessions), consulta em 22/10/2026.

Para B/C, Usage lê endpoints de quota com credenciais locais, mostra janelas/reset e permite perfis Claude/Codex. Estimativa a preço de API não é cobrança real da assinatura. Os perfis usam `CLAUDE_CONFIG_DIR`/`CODEX_HOME`; as docs dizem que compartilham skills, plugins, MCP e settings. Compatibilidade efetiva com nossos symlinks e hooks ainda é não confirmado. Não há evidência de aplicação da ADR-0002. Fonte: [Usage](https://docs.superset.sh/usage), consulta em 22/10/2026.

Para D/E, a skill `superset:orchestrate` usa coordenador Claude/Codex e workers de famílias variadas em workspaces separados, com conclusão/bloqueio estruturados e verificação pelo coordenador. Hooks mostram trabalhando, concluído ou aguardando; o indicador pode ficar obsoleto após parada forçada. Não há garantia comprovada de detectar ausência de progresso útil. Fontes: [orquestração](https://docs.superset.sh/orchestration), [status](https://docs.superset.sh/agent-status), consulta em 22/10/2026.

Para F, oferece desktop/CLI gratuitos locais; mobile e remoto são pagos. Há SDK, skills, integrações e MCP. O MCP documentado é remoto em `api.superset.sh/mcp`, com OAuth 2.1 ou chave; não presumir que ele seja apenas um socket local. Para o primeiro laboratório, a CLI local é uma superfície menor a validar. Fontes: [preços](https://superset.sh/pricing), [MCP](https://docs.superset.sh/mcp-server), [orquestração](https://docs.superset.sh/orchestration), consulta em 22/10/2026.

Os hooks Superset alteram configs dos agentes, mas fazem no-op fora dos terminais Superset e podem ser desligados. Isso exige comparar os arquivos antes/depois contra ai-memory e StopFailure. O painel de portas descobre processos e permite pará-los, porém não reserva faixas por worktree: I-03 continua possível. Fontes: [status/hooks](https://docs.superset.sh/agent-status), [portas](https://docs.superset.sh/ports), [incidentes](INCIDENTES.md), consulta/leitura em 22/10/2026.

### Conductor

O produto da Melty Labs tem execução local no Mac e suporte declarado a Claude Code, Codex e OpenCode. Para A, dá continuidade de trabalho por workspace e revisão; transferência automática do histórico entre famílias e failover por quota são não confirmado. O changelog 0.91.0 diz que Codex espera e tenta novamente sob rate limit, o que não equivale a escolher outro provedor. Fontes: [introdução](https://www.conductor.build/docs), [changelog](https://www.conductor.build/changelog), consulta em 22/10/2026.

Para C, autenticação por assinatura/CLI é documentada em Claude e Codex. `ANTHROPIC_API_KEY` no ambiente pode selecionar cobrança de API. Para B, integração com nossos sensores e escolha por risco/franquia: não confirmado. Para D/E, há workspaces separados e revisão; as docs também incentivam agentes no mesmo workspace e reconhecem que podem editar os mesmos arquivos. O AI OS precisaria restringir esse fluxo. Fontes: [provedores](https://www.conductor.build/docs/guides/providers), [agentes paralelos](https://www.conductor.build/docs/concepts/parallel-agents), consulta em 22/10/2026.

Para F, plano gratuito inclui workspaces locais; Pro inclui API/mobile/cloud. MCP Claude/Codex usa configuração específica do agente, o que favorece reaproveitar ai-memory. Hooks SessionStart/SessionEnd/StopFailure e mod quota-guard neste harness: não confirmado. Execução local tem acesso do usuário; cloud armazena dados em infraestrutura gerenciada, fora da POC da ADR-0001. Fontes: [preços](https://www.conductor.build/pricing), [MCP](https://www.conductor.build/docs/reference/mcp), [segurança](https://www.conductor.build/docs/reference/security-and-permissions), consulta em 22/10/2026.

Fechar o app ou desligar o Mac encerra sessões locais, segundo a página de preços. Isso deve entrar no ensaio de continuidade; a execução cloud que persiste após fechar o app não é substituto automaticamente aceito para a POC local. Fonte: [local versus cloud](https://www.conductor.build/pricing), consulta em 22/10/2026.

### Claude Squad

Para D/F, gerencia sessões em terminal, usando tmux e workspaces Git separados, com revisão antes de aplicar mudanças. `--program` permite lançar a CLI escolhida. Para A/E, ai-memory poderia continuar como canal de contexto; handoff assistido nativo entre famílias e mensagens estruturadas são não confirmado. Para B, sensores/roteamento são não confirmado. Para C, reaproveitar assinaturas depende da CLI/autenticação real; o exemplo antigo de Codex com chave não comprova funcionamento nem impedimento do Plus moderno. Fonte: [README](https://github.com/smtg-ai/claude-squad), consulta em 22/10/2026.

É candidato enxuto para quem aceita terminal e configuração manual. Isso é uma avaliação de escopo, não benchmark de RAM. Não foi documentado servidor HTTP obrigatório nas instruções consultadas; portas adicionais das CLIs continuam possíveis. API/plugins próprios, integração específica com quota-guard e segurança do handoff automático: não confirmado. Evitar `--autoyes`, experimental, que aceita prompts automaticamente. Fontes: [README](https://raw.githubusercontent.com/smtg-ai/claude-squad/main/README.md), [manifesto Go](https://raw.githubusercontent.com/smtg-ai/claude-squad/main/go.mod), consulta em 22/10/2026.

### Vibe Kanban

Existe e se aplica ao gerenciamento local de agentes: workspace/branch, terminal, revisão com comentários e múltiplos executores. A/E são parciais porque revisão com feedback não comprova diálogo autônomo entre famílias. B e integração específica com ai-memory/hooks: não confirmado. C depende das CLIs; F tem interface e preview, sem medição no M4. Fonte: [repositório](https://github.com/BloopAI/vibe-kanban), consulta em 22/10/2026.

Extensibilidade por plugins/API/skills e compatibilidade do MCP do ai-memory com a versão atual: não confirmado nas páginas verificadas. A política de segurança oferece GitHub Security Advisory privado e promete suporte à última release; isso não comprova sandbox dos executores ou atendimento atual desse prazo. Preservação das aprovações e permissões locais precisa de teste antes de qualquer adoção. Fonte: [SECURITY.md](https://raw.githubusercontent.com/BloopAI/vibe-kanban/main/SECURITY.md), consulta em 22/10/2026.

O fator decisivo é manutenção: em 10/04/2026, a empresa anunciou encerramento e continuidade comunitária, removendo serviços remotos após 30 dias e preservando workspaces locais. As notas públicas pararam na release de 24/04 e mostram executor OpenCode v1. Isso não prova que todo desenvolvimento comunitário parou, mas impede recomendar adoção nova sem verificar manutenção e compatibilidade v2. Fontes: [anúncio](https://www.vibekanban.com/blog/shutdown), [releases](https://www.vibekanban.com/release-notes), consulta em 22/10/2026.

### Continuity: extensão relevante, fora da primeira rodada

É plugin comunitário para Paseo >=0.10.1. Ao detectar erro de quota/rate limit, cria sucessor em outro provedor com histórico limitado, no mesmo workspace. Descreve redação de padrões comuns de segredo, prevenção de duplicados e limite de transições. Não comprova parada atômica do executor anterior, retomada exata, retorno ao preferido ou política por capacidade da ADR-0002. Fonte: [README do autor](https://raw.githubusercontent.com/keefeere/paseo-continuity/main/README.md), consulta em 22/10/2026.

O plugin pode ler timelines e criar agentes, executando sem sandbox. Resumo por LLM é opcional e acrescenta um destinatário do contexto. Portanto, só avaliar depois de handoff manual, revisão de código versionada e teste de posse exclusiva do checkout. A detecção depende de como Paseo classifica o fim do turno; a issue sobre limite Claude terminar como resposta normal deve entrar no teste. Fontes: [Continuity](https://github.com/keefeere/paseo-continuity), [plugins](https://paseo.sh/docs/plugins), [Paseo #7636](https://github.com/getpaseo/paseo/issues/7636), consulta em 22/10/2026.

## Maturidade, licença e manutenção

Datas/contagens são fotografia da consulta, não garantia de estabilidade. “Contribuidores de uma release” não significa total do projeto. Idade exata por primeiro commit/criação não confirmada quando o histórico/API não forneceu evidência verificável; contagens faltantes ficam explícitas.

| Candidato | Mantenedor, idade e licença | Ritmo observado e contribuidores | Fontes, consulta em 22/10/2026 |
|---|---|---|---|
| Paseo | Organização getpaseo; copyright 2025-presente Mohamed Boudra, que não comprova data de lançamento; Apache-2.0, com licenças próprias dos componentes terceiros. Idade exata não confirmada. | 0.12.0 em 19/10, beta em 22/10; 72 contribuidores listados na 0.12.0, total não confirmado. | [Licença](https://raw.githubusercontent.com/getpaseo/paseo/main/LICENSE), [0.12.0](https://github.com/getpaseo/paseo/releases/tag/v0.12.0), [releases](https://github.com/getpaseo/paseo/releases) |
| Orca | Stably AI; MIT, copyright 2026 Lovecast Inc.; idade exata não confirmada. | 1.4.237 em 21/10, várias versões em 20/10; total de contribuidores não confirmado. | [Licença](https://raw.githubusercontent.com/stablyai/orca/main/LICENSE), [repo](https://github.com/stablyai/orca), [releases](https://github.com/stablyai/orca/releases) |
| Superset | Superset Inc./superset-sh; idade exata não confirmada; README atual informa Elastic License 2.0, não presumir MIT. | 1.38.0 em 14/10, 1.39.0 em 19/10 e canaries; total de contribuidores não confirmado. | [Repo e licença](https://github.com/superset-sh/superset), [releases](https://github.com/superset-sh/superset/releases) |
| Conductor | Melty Labs; idade exata não confirmada; licença de código aberto/repo do app e total de contribuidores não confirmados. | Changelog 0.91.0 em 15/10, com correções de chats e segurança; cadência futura não confirmada. | [Docs](https://www.conductor.build/docs), [changelog](https://www.conductor.build/changelog), [termos](https://www.conductor.build/terms) |
| Claude Squad | smtg-ai; já tinha issue em 06/04/2025, ao menos cerca de 18 meses de histórico público; AGPL-3.0. | 1.0.18 em 23/05, 1.0.19 em 17/06, 1.0.20 em 20/08; autores de release incluem Noam5/JDKrasnick, total não confirmado. | [Repo/licença](https://github.com/smtg-ai/claude-squad), [issue #56](https://github.com/smtg-ai/claude-squad/issues/56), [releases](https://github.com/smtg-ai/claude-squad/releases) |
| Vibe Kanban | Bloop AI iniciou em junho/2025; cerca de 16 meses desde lançamento; agora comunidade; Apache-2.0. | Página Latest em 24/04; notas creditam vários autores, total atual não confirmado. Suporte empresarial encerrado. | [Encerramento](https://www.vibekanban.com/blog/shutdown), [licença](https://raw.githubusercontent.com/BloopAI/vibe-kanban/main/LICENSE), [releases](https://www.vibekanban.com/release-notes) |
| Continuity | keefeere/Chechulin Serhii; MIT; idade e total de contribuidores não confirmados. | Manifesto/pacote 0.2.1; cadência sustentada e versão npm publicada não confirmadas. | [Repo](https://github.com/keefeere/paseo-continuity), [manifesto](https://raw.githubusercontent.com/keefeere/paseo-continuity/main/package.json) |

### Issues relevantes para o laboratório

Relatos em issues não são reprodução independente nem prova de defeito em todas as versões. A condição “aberta” abaixo foi observada na listagem oficial durante a consulta; revalidar antes do teste.

| Candidato | Evidência de risco | Fonte/data |
|---|---|---|
| Paseo | Lista mostrava 826 abertas; #7636 relata limite Claude tratado como conclusão normal; #7662 relata reconexão permanente em 0.13.0-beta.1. A segunda é motivo para preferir estável, sem atribuir o bug à 0.12.0. | [Lista](https://github.com/getpaseo/paseo/issues), [#7636](https://github.com/getpaseo/paseo/issues/7636), [#7662](https://github.com/getpaseo/paseo/issues/7662), consulta em 22/10/2026. |
| Orca | #32118, aberta em 22/10, relata que confirmar commit não conclui a ação e o fluxo reverte; OS/versão não informados, alcance no Mac não confirmado. Orquestração declarada experimental. | [#32118](https://github.com/stablyai/orca/issues/32118), [limite declarado](https://www.onorca.dev/docs/cli/orchestration), consulta em 22/10/2026. |
| Superset | Repo mostrava 473 issues; lista detalhada não retornou conteúdo suficiente para atribuir bugs abertos específicos. As docs alertam sobre status obsoleto e handoff sem redação de segredos. | [Tracker](https://github.com/superset-sh/superset/issues), [status](https://docs.superset.sh/agent-status), [handoff](https://docs.superset.sh/agent-sessions), consulta em 22/10/2026. |
| Conductor | Tracker público e contagem não confirmados. Release 0.91.0 registra correções de crash loop, status incorreto e envio indevido de credenciais GitHub para repos externos; são correções declaradas, não bugs necessariamente abertos. | [Changelog](https://www.conductor.build/changelog), consulta em 22/10/2026. |
| Claude Squad | 15 abertas; #266 relata prompt enviado antes da CLI estar pronta; #325 relata disputa de stdin entre interface e tmux. São diretamente relevantes ao I-01. | [Lista](https://github.com/smtg-ai/claude-squad/issues), [#266](https://github.com/smtg-ai/claude-squad/issues/266), [#325](https://github.com/smtg-ai/claude-squad/issues/325), consulta em 22/10/2026. |
| Vibe Kanban | 389 abertas; #3481 relata `opencode serve` iniciado mesmo sem selecioná-lo; #3466 relata canais de segurança com e-mail retornando. Ambos agravam custo operacional/manutenção. | [Lista](https://github.com/BloopAI/vibe-kanban/issues), [#3481](https://github.com/BloopAI/vibe-kanban/issues/3481), [#3466](https://github.com/BloopAI/vibe-kanban/issues/3466), consulta em 22/10/2026. |
| Continuity | SLA, auditoria e conjunto de bugs abertos relevantes: não confirmado; inspecionar código e testes da versão antes de ligar failover. | [Repo e testes disponíveis](https://github.com/keefeere/paseo-continuity), consulta em 22/10/2026. |

## Custo, recursos e processos locais

Nenhum benchmark de RAM, CPU, bateria ou disco instalado no M4 foi executado. Nenhuma fonte consultada forneceu medição comparável para os candidatos. As arquiteturas abaixo ajudam a desenhar o teste; não permitem afirmar “cabe em 16 GB” ou prometer um número seguro de agentes.

| Candidato | Custo do produto, separado da inferência | Recursos, serviços e portas | Fontes, consulta em 22/10/2026 |
|---|---|---|---|
| Paseo | Valor comercial atual: não confirmado nesta consulta; não presumir que custos do Hub/relay/modelos sejam iguais ao uso local. | Desktop inclui daemon, estado em `~/.paseo`; exemplo/default em 6767. DMG arm64 da 0.12.0 tem cerca de 178 MB, não representa disco instalado. | [Início](https://paseo.sh/docs), [config](https://paseo.sh/docs/configuration), [release](https://github.com/getpaseo/paseo/releases/tag/v0.12.0) |
| Orca | Site declara gratuito/open source e uso das assinaturas próprias; serviços pagos opcionais/limites comerciais: não confirmado. | Runtime do app e endpoints de hooks; portas variáveis são reconsultadas após restart. Lista completa de listeners/daemons locais: não confirmado. | [Repo](https://github.com/stablyai/orca), [hooks](https://www.onorca.dev/docs/agents/hooks-memory) |
| Superset | Free: 1 usuário, desktop/CLI e workspaces locais. Pro: US$20/mês ou US$15/mês com cobrança anual; mobile/remoto/automations. Inferência usa conta própria. | App/host, terminais e hooks; descobre portas, não aloca faixas. Porta interna fixa e inventário completo de listeners: não confirmado. | [Preço](https://superset.sh/pricing), [portas](https://docs.superset.sh/ports), [status](https://docs.superset.sh/agent-status) |
| Conductor | Free local; Pro US$50/mês; Teams US$60/usuário/mês. Assinatura/chave do modelo é separada. | Local usa processos do Mac; cloud é outra arquitetura. Porta local fixa/daemon persistente e tamanho instalado: não confirmado. | [Preço](https://www.conductor.build/pricing), [segurança](https://www.conductor.build/docs/reference/security-and-permissions) |
| Claude Squad | Software sob AGPL; assinaturas/APIs dos agentes são separadas. | Aplicativo de terminal Go, tmux e gh; sem HTTP obrigatório descrito no README. RAM/disco reais: não confirmado. | [Repo](https://github.com/smtg-ai/claude-squad), [go.mod](https://raw.githubusercontent.com/smtg-ai/claude-squad/main/go.mod) |
| Vibe Kanban | Código Apache-2.0; assinaturas comerciais encerradas, execução local preservada. | Servidor local/interface; versão e configuração determinam processos. Issue de preload OpenCode exige observar listeners; porta exata atual não confirmada. | [Anúncio](https://www.vibekanban.com/blog/shutdown), [licença](https://raw.githubusercontent.com/BloopAI/vibe-kanban/main/LICENSE), [#3481](https://github.com/BloopAI/vibe-kanban/issues/3481) |
| Continuity | MIT; resumo por outro LLM pode consumir sua quota/API. | Executa junto ao daemon Paseo e grava handoff em `.paseo/continuity/`; processo/custo incremental medido: não confirmado. | [README](https://github.com/keefeere/paseo-continuity), consulta em 22/10/2026 |

Para todos, cada worktree pode precisar de dependências e serviços próprios. O projeto já sofreu colisão entre ai-memory em 49374 e OpenCode 2, movido para 49375. Nenhum cockpit elimina automaticamente esse problema. Começar com dois executores e medir antes de aumentar é recomendação para este Mac. Bases: [I-03/I-04](INCIDENTES.md), [worktrees Paseo](https://paseo.sh/docs/worktrees), [portas Superset](https://docs.superset.sh/ports), leitura/consulta em 22/10/2026.

## O que já construímos e o orquestrador substituiria ou aproveitaria

| Componente atual | Decisão proposta | Justificativa e fonte, leitura/consulta em 22/10/2026 |
|---|---|---|
| ai-memory: memória compartilhada e handoff automático | Manter. Cockpit complementa a navegação e o lançamento. | Handoff do cockpit tem formato/limite próprio; equivalência com memória durável, captura e handoff do ai-memory não confirmada. [STATUS](STATUS.md), [Paseo skills](https://paseo.sh/docs/skills), [Superset sessões](https://docs.superset.sh/agent-sessions). |
| quota-guard, `claude.json` | Manter como sinal validado e proteção do Claude. | Painéis próprios podem duplicar coleta; consumo do contrato local por candidato não confirmado. [ADR-0002](decisions/0002-roteamento-por-capacidade-e-franquia.md), [Paseo usage](https://paseo.sh/docs/cli). |
| `scripts/quota_codex.py`, `codex.json` | Manter; comparar com o painel, sem substituir de saída. | App Server e tratamento de `unknown` já fazem parte do contrato. Medidor visual não comprova decisão por capacidade. [ADR-0002](decisions/0002-roteamento-por-capacidade-e-franquia.md), [Superset Usage](https://docs.superset.sh/usage). |
| ADR-0002 e `roteamento.json` | Aproveitar como política consultiva do coordenador. | Não automatizar apenas porque há API/SDK. Nenhum candidato demonstrou cumprir todos os guardrails. [ADR-0002](decisions/0002-roteamento-por-capacidade-e-franquia.md). |
| Worktrees manuais | Pode substituir sua criação/navegação, preservando posse exclusiva. | Worktrees são recurso comum, mas Superset/Conductor permitem sessões compartilhadas. [Paseo](https://paseo.sh/docs/worktrees), [Superset fork](https://docs.superset.sh/agent-sessions), [Conductor](https://www.conductor.build/docs/concepts/parallel-agents). |
| Hooks de memória, StopFailure e permissões | Preservar e auditar merge/config antes e depois. | Novos hooks de status podem exigir confiança novamente; não resolver removendo proteção. [I-08/I-11](INCIDENTES.md), [Orca hooks](https://www.onorca.dev/docs/agents/hooks-memory), [Superset hooks](https://docs.superset.sh/agent-status). |
| Skills e revisão entre famílias | Reaproveitar; acrescentar transporte de mensagens se necessário. | Paseo committee/advisor e Superset coordenação já dão superfícies para esse fluxo. [Paseo](https://paseo.sh/docs/skills), [Superset](https://docs.superset.sh/orchestration). |
| Telemetria de qualidade/correções | Manter no repo. | Dashboard de tokens não mede qualidade ou necessidade de correção humana. [ADR-0002](decisions/0002-roteamento-por-capacidade-e-franquia.md), [Superset Usage](https://docs.superset.sh/usage). |

## Alternativas descartadas ou adiadas

O homônimo VirtusLab/orca também orquestra Claude/Codex/OpenCode e permite workflows determinísticos em Scala, com retomada por commits e revisão por outro agente. É uma alternativa real para automatizar um processo explícito; foi adiada aqui porque acrescenta runtime/workflows a manter antes de uma lacuna medida, e compatibilidade exata com OpenCode 2 é não confirmado. Não confundir suas funções com as do Stably Orca. Fonte: [README VirtusLab](https://github.com/VirtusLab/orca), consulta em 22/10/2026.

Vibe Kanban fica fora da primeira adoção por encerramento comercial, manutenção comunitária sem compromisso confirmado e integração v2 não demonstrada. Claude Squad fica como alternativa de terminal para pouco escopo; não é a primeira opção se comunicação entre famílias e quota no cockpit forem o objetivo. Conductor se aplica ao Mac e aos agentes, mas não apresentou vantagem documental suficiente para trocar a POC local já aprovada; API/mobile exigem plano pago. Bases: [Vibe](https://www.vibekanban.com/blog/shutdown), [Claude Squad](https://github.com/smtg-ai/claude-squad), [Conductor preço](https://www.conductor.build/pricing), [ADR-0001](decisions/0001-arquitetura-inicial.md), consulta/leitura em 22/10/2026.

OmniRoute/OpenRouter/LiteLLM são gateways de inferência ou serviços de modelos, não prova de orquestração das sessões locais Claude Code + Codex CLI + OpenCode 2. A pesquisa anterior já separa fallback de requisição da continuidade de workspace/histórico. Ficam fora desta escolha de cockpit. Fontes: [pesquisa local](PESQUISA-ROTEAMENTO.md), [ADR-0002](decisions/0002-roteamento-por-capacidade-e-franquia.md), [arquitetura de resiliência OmniRoute](https://github.com/cheaper-inference/OmniRoute/blob/main/docs/architecture/RESILIENCE_GUIDE.md), leitura/consulta em 22/10/2026.

## Primeiro teste no laboratório e critérios de aceite

A proposta é um teste futuro do Paseo estável, local, sem plugins comunitários, relay, Hub ou automação de failover. O objetivo é demonstrar ganho sobre CLIs + ai-memory já funcionando. Se falhar em preservar hooks ou OpenCode 2, registrar a falha e comparar Superset; se este também falhar na v2, avaliar Orca com Manual configurado. Essa sequência mantém a ADR-0001 e explora diferenças verificáveis das ferramentas. Bases: [ADR-0001](decisions/0001-arquitetura-inicial.md), [Paseo suporte](https://paseo.sh/docs/supported-providers), [Superset suporte](https://docs.superset.sh/supported-agents), [Orca suporte](https://www.onorca.dev/docs/agents/supported), consulta/leitura em 22/10/2026.

Os critérios abaixo são requisitos propostos do laboratório, não promessas dos candidatos. Derivam da [ADR-0002](decisions/0002-roteamento-por-capacidade-e-franquia.md) e dos [incidentes](INCIDENTES.md), lidos em 22/10/2026.

1. **Preservação:** registrar diff dos settings/hooks antes/depois. Claude carrega quota-guard; as três famílias acessam ai-memory; handoff automático aparece uma única vez. Nenhuma credencial vai para o relatório.
2. **Compatibilidade real:** registrar versões do cockpit e das três CLIs. Rodar tarefa curta verificável com Claude 2.1.308, Codex 0.163.0 e OpenCode 2.0.32. O gratuito escolhido deve estar disponível no runtime, sem troca silenciosa para API paga.
3. **Posse exclusiva:** dois executores que escrevem usam dois worktrees distintos. Registrar `pwd`, branch e dono da tarefa; transferência no mesmo checkout só depois de parar o anterior. Revisor recebe diff/snapshot e não escreve no checkout do executor.
4. **Continuidade:** Claude encerra com nota de estado; Codex continua pelo ai-memory; depois OpenCode e retorno ao Claude. O receptor deve dizer o que foi feito, testes, decisão e próximo passo sem refazer trabalho. Comparar com T2 existente.
5. **Revisão entre famílias:** Claude propõe uma mudança; Codex revisa com pelo menos uma conclusão fundamentada; o executor responde e testes verificam o resultado. O transporte deve ficar visível no cockpit.
6. **Agente parado:** provocar espera de aprovação e uma sessão sem avanço, com tarefa descartável. O operador deve identificar a condição por saída/eventos/testes em até dois minutos. “Processo vivo” sozinho reprova o critério I-01.
7. **Franquia:** comparar medidores do cockpit com os sensores locais, anotando origem, horário/reset e `unknown`. Simular sinal de 85% num cenário isolado de avaliação, sem alterar os arquivos de quota reais nem esgotar uma assinatura. Coordenador deve sugerir o executor permitido pela ADR-0002, preservando piso de risco.
8. **Falha e retorno:** primeiro ensaiar troca manual após parada; verificar diffs, memória e efeitos já executados. Failover automático e volta ao preferido ficam para rodada própria, com checkpoint explícito e nenhum segundo escritor. Não marcar A completo antes disso.
9. **Recursos:** medir baseline e depois 1 e 2 agentes: memória do app/daemon/CLIs, pressão de memória/swap, CPU ociosa, disco dos worktrees e listeners. Aceitar só se o Mac continuar utilizável no trabalho diário; registrar os números, sem inventar um teto agora.
10. **Saída:** fechar cockpit e conferir quais processos/listeners ficaram; confirmar que ai-memory 49374 e OpenCode 49375 seguem funcionando e que CLIs diretas continuam com os hooks anteriores.

Exemplos de inspeção somente leitura para essa rodada futura; não iniciam agentes ou serviços:

```sh
# Mostra quem escuta portas TCP no macOS.
lsof -nP -iTCP -sTCP:LISTEN

# Mostra os worktrees conhecidos pelo repositório do laboratório.
git worktree list --porcelain

# Mede o espaço da pasta do laboratório; ajustar para o caminho real.
du -sh ~/Workspace/tools/laboratorio
```

A verificação precisa juntar saída do agente, sessão criada e resultado dos testes; um status visual isolado não encerra a tarefa. Essa exigência vem dos incidentes [I-01 e I-10](INCIDENTES.md), leitura em 22/10/2026.

### O que evitar

Evitar beta como baseline, Continuity antes do handoff manual, YOLO/auto-accept, forks com dois escritores, duplicação de memória/handoff, e dashboards de custo de API tratados como gasto da assinatura. Não expor daemons apenas para ter celular; não copiar cookies/chaves para habilitar medidores opcionais. Esses limites respondem a comportamentos documentados, sem impedir um teste posterior com justificativa. Fontes: [Paseo beta #7662](https://github.com/getpaseo/paseo/issues/7662), [Continuity](https://github.com/keefeere/paseo-continuity), [Orca permissões](https://www.onorca.dev/docs/agents/supported), [Superset sessões](https://docs.superset.sh/agent-sessions), [Usage](https://docs.superset.sh/usage), [Orca cookies](https://www.onorca.dev/docs/agents/usage-tracking), consulta em 22/10/2026.

Nota de estado: pesquisa documental e revisão de linguagem concluídas em 22/10/2026. Foram lidos os documentos locais obrigatórios e consultadas fontes oficiais/primárias. Nenhuma instalação, cadastro, inferência, mudança de configuração ou commit. Decisão proposta: Paseo estável primeiro, mantendo ai-memory e roteamento consultivo; Superset como comparação e Orca condicionado a permissões Manual. Pendências: compatibilidade exata v2.0.32, integração real dos hooks, recursos no M4 e ciclo seguro de quota/failover/retorno. Próximo passo exato: revisar estes critérios e executar uma única rodada de laboratório quando a instalação for autorizada.
