# EXP-001: retomada de contexto com o ai-memory

Formato do pré-registro: `docs/research/PROTOCOLO-GQM.md`, seção 7. Pergunta de origem: Q6 (fidelidade da retomada). Tarefa T-20261109-05 (AI OS v0.2.1, frente D).

**Desvio do protocolo:** a seção 7 pede o pré-registro antes de rodar. Aqui o conjunto de fatos e a régua de pontuação foram fixados antes das consultas, mas tudo foi escrito no mesmo documento depois da execução. Quem lê o resultado deve tratá-lo como exploratório.

## 1. Pergunta e hipóteses

**Pergunta:** o teste n=1 de 09/11 (`MEMORIA-E-CONTEXTO-2026-11.md`, seção 3) deu ai-memory 0/6, `MEMORY.md` 1/6, STATUS+git 6/6. Por que o ai-memory recuperou tão pouco, e o que custa menos para corrigir?

| Id | Hipótese |
|---|---|
| H1 | O briefing só traz contagens e títulos truncados. |
| H2 | Os handoffs guardam prompt e última resposta, não decisões. |
| H3 | Faltam páginas duráveis (só 1 decisão fixada). |
| H4 | A busca (`memory_query`) não acha porque o vocabulário da pergunta difere do registrado. |
| H5 | O teste foi mal desenhado: fatos de menos de 1 h, ainda não capturados ou indexados. |

## 2. Métrica primária

Fidelidade por canal = soma dos pontos ÷ 12 fatos (e por faixa de idade, ÷ 4).

Pontuação, fixada antes das consultas:

- **1**: o fato aparece com seu identificador exato (ADR, incidente, hash, caminho) e a afirmação.
- **0,5**: aparece a ideia sem o identificador, ou o identificador sem a afirmação do fato.
- **0**: ausente. Citar um identificador só como instrução de leitura ("leia a ADR-0003") não conta.
- **ERRADO**: contradiz a fonte. **DESATUALIZADO**: era verdade e foi superado. Marcados à parte, não descontam ponto.

## 3. Método

- Congelamento: repositório em `0c6bd0d` (base v0.2.1, tag `6fee611`), ai-memory 3.2.0, projeto `pessoal/workflow-ai` (46 páginas, 52 versões, 46 sessões, 6.193 observações no início; 6.364 no fim, porque as próprias sessões ativas continuam sendo capturadas). Execução na noite de 09/11/2026 (horário local).
- Somente leitura: `memory_briefing`, `memory_handoff_list`, `memory_query`, `memory_recent`, `memory_read_page`, `memory_read_session_observations`, `memory_status`. Nada foi gravado, aceito, cancelado ou consolidado.
- Quatro canais, cada um com a consulta exata registrada (apêndice A):
  - **(a) briefing**: `memory_briefing` (e uma repetição com `settled_first: true`).
  - **(b) busca**: `memory_query`, `limit: 3`, duas formulações em linguagem natural por fato (N1 e N2). Como teste de H4, uma terceira formulação com os termos do documento (T).
  - **(c) handoffs**: `memory_handoff_list` (26 abertos), lidos por inteiro com `jq`.
  - **(d) STATUS+git**: d1 = `docs/ai-os/STATUS.md` + `git log --all`; d2 = d1 + `grep -rn` em `docs/ai-os/` (ADRs, `INCIDENTES.md`, `BASELINE`). Mantive as duas porque o I-23 vive no registro de incidentes e não no STATUS.
- Critério de inclusão dos fatos: verdadeiro e verificável no git ou no STATUS, com fonte canônica anotada antes de consultar.
- Regra de parada: um passe por canal e formulação, sem reformular depois de ver o resultado.
- Plano de análise: tabelas por canal e por idade; hipótese confirmada se a evidência direta aponta para ela, refutada se contradiz, parcial se só parte do mecanismo se sustenta.

## 4. Conjunto de fatos

Idade = data do evento. Fontes: arquivos e commits deste repositório (nada de projeto restrito).

| Id | Faixa | Fato (resumo) | Fonte canônica |
|---|---|---|---|
| A1 | 23-26/10 | Paseo adotado como camada de execução (ADR-0003), em 23/10 | `decisions/0003-paseo-como-camada-de-execucao.md`, STATUS "23/10/2026: Paseo adotado", commit `cd0252a` |
| A2 | 23-26/10 | Regra I-23: uma tarefa pesada do Codex por vez (duas em paralelo esgotaram a janela de 5 h) | `INCIDENTES.md` linha do I-23 |
| A3 | 23-26/10 | ADR-0004: gestão de contexto com sessões curtas, skill `sessao` | `decisions/0004-gestao-de-contexto.md`, commits `44cc96c`, `7c27c91` |
| A4 | 23-26/10 | Vigia `paseo_watchdog` instalado como LaunchAgent, estado em `agentes.json` | STATUS "ESTADO ATUAL", commits `3127380`, `b60055e` |
| B1 | 02-08/11 | 21 servidores `astro dev` ficaram órfãos, iniciados em 04 e 05/11 por agentes do portfólio | `incidentes/I-35-astro-orfaos.md`, STATUS "v0.2.1", commit `b9da4bc` |
| B2 | 02-08/11 | Períodos de medição: baseline 08-21/10, S1 22/10-01/11, S2 a partir de 02/11 | `BASELINE-2026-11-09.md` linha 17 |
| B3 | 02-08/11 | Em 08/11 o trabalho não commitado foi salvo antes da migração do Mac, num commit `wip` fora da `main` | commit `d36e20d` (só aparece com `git log --all`) |
| B4 | 02-08/11* | Worker do claude-mem no ar desde 27/10 | STATUS "Saúde do Mac" |
| C1 | 09/11 | Antigravity fora da automação (ADR-0006, substitui a ADR-0005) | `decisions/0006-...`, STATUS "Frente: Antigravity", commit `8bf9992` |
| C2 | 09/11 | v0.2.1 e incidente I-35; correção `ASTRO_DEV_BACKGROUND=0` | tag `v0.2.1` (`6fee611`), INCIDENTES I-35, commit `b9da4bc` |
| C3 | 09/11 | Protocolo GQM em `docs/research/PROTOCOLO-GQM.md` | commit `45fee32`, STATUS "Publicado" |
| C4 | 09/11 | Plugin claude-mem desabilitado | `~/.claude/settings.json` (`enabledPlugins`: `false`), INCIDENTES I-35 ("desativação do claude-mem") |

\* **Limitação da faixa B:** entre 27/10 e 08/11 o git não tem nenhum commit de trabalho (só o `wip` de 08/11) e o ai-memory deste projeto não registra sessão real de trabalho (as sessões com data de atualização em 05/11 começaram em 26/10 e foram só fechadas depois). Os fatos de B vêm de outros projetos ou foram documentados em 09/11. B4 está na borda (27/10) e entrou por falta de um quarto fato datável. Quem escolheu os 12 fatos já conhecia o STATUS.

## 5. Resultados

### 5.1 Placar por canal e faixa de idade (pontos)

| Canal | A 23-26/10 (÷4) | B 02-08/11 (÷4) | C 09/11 (÷4) | Total (÷12) |
|---|---|---|---|---|
| (a) briefing | 0 | 0,5 | 0,5 | **1,0** |
| (b) busca N1, pergunta natural | 0 | 0 | 0 | **0** |
| (b) busca N2, outra formulação | 1,0 | 1,0 | 0 | **2,0** |
| (b) busca T, termos do documento | 4,0 | 2,0 | 0,5 | **6,5** |
| (c) handoffs abertos | 2,5 | 1,0 | 2,0 | **5,5** |
| (d1) STATUS + `git log --all` | 3,0 | 3,5 | 3,5 | **10,0** |
| (d2) d1 + `grep` em `docs/ai-os/` | 4,0 | 4,0 | 4,0 | **12,0** |

União dos canais do ai-memory sem a formulação T (melhor de a, b-N1, b-N2, c por fato): **5,5/12**. Com T: **8,0/12**.

### 5.2 Pontos por fato

| Fato | a | b N1 | b N2 | b T | c | d1 | d2 |
|---|---|---|---|---|---|---|---|
| A1 ADR-0003 | 0 | 0 | 0 | 1 | 0 | 1 | 1 |
| A2 I-23 | 0 | 0 | 0 | 1 | 1 | 0 | 1 |
| A3 ADR-0004 | 0 | 0 | 0,5 | 1 | 0,5 | 1 | 1 |
| A4 vigia | 0 | 0 | 0,5 | 1 | 1 | 1 | 1 |
| B1 I-35 (21 astro) | 0,5 | 0 | 1 | 1 | 1 | 1 | 1 |
| B2 períodos S1/S2 | 0 | 0 | 0 | 1 | 0 | 0,5 | 1 |
| B3 migração do Mac | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| B4 worker claude-mem | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| C1 ADR-0006 | 0 | 0 | 0 | 0 | 0,5 | 1 | 1 |
| C2 v0.2.1 + I-35 | 0,5 | 0 | 0 | 0 | 1 | 1 | 1 |
| C3 GQM | 0 | 0 | 0 | 0,5 | 0,5 | 1 | 1 |
| C4 claude-mem desabilitado | 0 | 0 | 0 | 0 | 0 | 0,5 | 1 |

### 5.3 ERRADO e DESATUALIZADO

- **ERRADO: 0** em todos os canais (nenhuma afirmação contradiz a fonte).
- **DESATUALIZADO, handoffs:** 2 dos 26 handoffs abertos (09/11, mesma frente) tratam a ADR-0005 como norma vigente (um deles a descreve como "ACEITO"); ela foi substituída pela ADR-0006 no mesmo dia. Outros handoffs de 09/11 descrevem o `agy` ligado ao Paseo, ao vigia e ao Claude, que depois saiu da automação.
- **DESATUALIZADO, busca:** na formulação T, o fato C1 devolve o trecho "Decisão proposta 1. Antigravity..." (proposta anterior à ADR-0006), e o fato C4 devolve duas páginas de sessão com a tabela de 22/10 em que o claude-mem aparece como "CONFIRMADO FUNCIONAL".
- **DESATUALIZADO, STATUS:** a seção "ESTADO ATUAL E PENDÊNCIAS" está datada de 26/10, e o STATUS trata o claude-mem como pendência de aposentar, sem dizer que o plugin já está `false` nas configurações (por isso C4 vale 0,5 em d1).
- **Ruído (não é erro):** a busca por "v0.2.1" casou com a versão de outro plugin ("keefeere/continuity v0.2.1") em vez da tag do AI OS.

## 6. Hipóteses

| Hip. | Veredito | Evidência principal |
|---|---|---|
| H1 | **Confirmada** | O briefing tem contagens, `rules: []`, `slots: []`, 1 decisão fixada, 5 sessões recentes e 10 páginas recentes, cada uma com o prompt truncado em cerca de 80 caracteres. Ficou em 1,0/12 e só acertou por título ("v0.2.1 A1, processos órfãos"). `settled_first: true` apenas repete a mesma decisão única. |
| H2 | **Confirmada em parte** | Em 26 handoffs, `next_steps` e `files_touched` vêm vazios (26/26). O texto são o prompt inicial (`open_questions`, "Continue from: ...") e, quando existe, a última resposta (`summary`). Totalizam cerca de 66,7 mil caracteres, no máximo 5 mil por handoff. Não há campo de decisão. Mesmo assim os handoffs foram o melhor canal do ai-memory (5,5/12), porque o orquestrador escreve a decisão dentro do prompt dos agentes ("I-23 (um Codex pesado por vez)", "I-35: 21 servidores astro dev"). A decisão só chega quando alguém a digitou no prompt. Não há handoff entre 27/10 e 08/11. |
| H3 | **Confirmada** | 46 páginas atuais: 44 de sessão (resumo heurístico, sem LLM: título de 80 caracteres, contagem de chamadas de ferramenta, linha do tempo), 1 `decision` e 1 `lint-report`. Zero `rules`, `gotchas`, `procedures`. Nenhum dos 12 fatos tem página própria. A página de sessão que li por inteiro (P0a) não tem conteúdo de decisão; a consolidação por LLM está desligada. |
| H4 | **Confirmada, com ressalva** | Perguntas naturais: 0/12 (N1) e 2/12 (N2). Os mesmos fatos com termos do documento: 6,5/12. Mecanismo observado: os termos vazios ("o", "de", "que", "os") não são descartados (aparecem destacados nos trechos) e a única página de decisão fica em 1º lugar em 23 das 24 consultas naturais, sem relação com o assunto. Ressalva: B3, B4, C1 e C2 continuam em 0 mesmo com os termos exatos, então vocabulário não explica tudo; o fato simplesmente não está no índice (nenhuma ocorrência de "ADR-0006" nos 26 handoffs nem nos trechos). |
| H5 | **Refutada como causa principal** | Se o problema fosse captura tardia, os fatos de 09/11 estariam pior só por serem recentes e os antigos bem. O que aparece é outra coisa: A (antigos) vai a 4/4 na formulação T e C (recentes) a 0,5/4, mas porque as sessões antigas do Claude guardam trechos de saída de ferramenta que leram o STATUS, e as decisões de 09/11 foram tomadas na conversa do orquestrador, que não gerou página. As sessões de trabalho de 09/11 estão capturadas (570 observações em uma delas, com prompt e resposta final de cada turno). Parte do desenho continua frágil: n=1 original, fatos escolhidos por quem conhecia o STATUS. |

Observações adicionais: sessões com `ended: false` (inclusive a atual) aparecem no briefing, mas ainda não têm página, só observações brutas (`memory_read_session_observations` as lê, e traz prompt e resposta final por turno). O passo "retomar sem ler STATUS/git" do protocolo de `MEMORIA-E-CONTEXTO` ainda não foi medido com esse caminho.

## 7. Ameaças à validade

- **n pequeno:** 12 fatos, uma rodada, um repositório. Diferenças de 0,5 ponto não significam nada. O placar serve para ordenar causas, não para medir.
- **Avaliador = mesmo agente que consultou:** a pontuação (1/0,5/0) tem julgamento, e o limite entre 0 e 0,5 em títulos de sessão pode mudar o total em 1 a 2 pontos. Uma segunda pessoa ou outro modelo deveria pontuar as mesmas saídas.
- **Fatos escolhidos por quem conhece o STATUS:** favorece o canal d. d2 = 12/12 é quase tautológico, porque os fatos foram buscados lá.
- **Termos T vêm do documento:** na vida real, quem retoma não sabe que existe "I-23". A coluna T mede o teto do índice, não o uso realista.
- **Faixa B sem cobertura:** só 3 fatos datam de 02-08/11 de verdade; B4 foi puxado de 27/10. A comparação por idade entre B e as outras faixas é fraca.
- **Mudança do estado durante o teste:** o número de observações subiu de 6.193 para 6.364 enquanto eu consultava; o conjunto de páginas e handoffs não mudou.
- **Régua diferente da rodada de 09/11:** a rodada original usava 6 fatos e marcava parcial quando faltava o identificador. Aqui o identificador sem a afirmação também vale 0,5. Os totais (0/6 antes, 5,5 a 8,0/12 agora) não são comparáveis diretamente. A diferença vem principalmente da escolha dos fatos (aqui entram I-23 e I-35, que estão em prompts de agentes).
- **Fonte de C4 fora do git:** `~/.claude/settings.json` não é versionado.

## 8. Recomendação (barata, só recomendação; nada foi gravado)

**Diagnóstico em uma frase:** o ai-memory guarda o que os agentes de trabalho receberam e responderam; as decisões do orquestrador (ADR, incidente, regra) não entram, e a busca por pergunta natural é derrubada por termos vazios. Páginas duráveis resolvem as duas coisas.

**1. Gravar 5 páginas duráveis curtas** (tipo `decision` ou `gotcha`, uma por fato, até 15 linhas), usando a skill `ai-memory-durable-pages`, depois de Felipe aprovar o texto. Cada página: decisão, motivo, data, fonte canônica (arquivo e commit), "substitui/substituída por", e uma linha com sinônimos em linguagem natural (para o índice lexical).

| # | Caminho | Título (com termos) | Termos a incluir |
|---|---|---|---|
| 1 | `decisions/adr-0003-paseo-camada-de-execucao.md` | ADR-0003: Paseo é a camada de execução dos agentes | Paseo, orquestrar, paralelo, worktree, Codex, OpenCode, 23/10 |
| 2 | `decisions/adr-0004-gestao-de-contexto-sessoes-curtas.md` | ADR-0004: gestão de contexto com sessões curtas | sessões curtas, skill sessao, encerrar sessão, STATUS, handoff, compactar |
| 3 | `decisions/adr-0006-antigravity-fora-da-automacao.md` | ADR-0006: Antigravity fora da automação (substitui a ADR-0005) | Antigravity, agy, Gemini, termos de uso, provider do Paseo desabilitado, uso direto |
| 4 | `gotchas/i-23-um-codex-pesado-por-vez.md` | I-23: um Codex pesado por vez | Codex, janela de 5 h, franquia, paralelo, esgotou |
| 5 | `gotchas/i-35-astro-dev-orfaos.md` | I-35: `astro dev` órfão de agentes | Astro, servidor em background, ASTRO_DEV_BACKGROUND=0, órfão, swap, v0.2.1 |

Por que esses cinco: são as decisões vigentes que os agentes erram se não souberem, estão em faixas de idade diferentes e aparecem em 0 ou 0,5 nos canais do ai-memory. Ficam de fora o GQM, o claude-mem e a migração do Mac: o primeiro já está em arquivo versionado fácil de achar, e os outros dois mudam rápido.

**2. Hook de handoff:** não alterar agora. Registrar decisões no hook exigiria um classificador do que é decisão, que é justamente o trabalho que a consolidação por LLM faria (desligada por decisão da ADR-0004). Alternativa de custo zero: tornar o passo "uma página durável por decisão nova" parte do encerramento da skill `sessao`, e tirar a decisão do prompt dos agentes para o próprio texto da página. Reavaliar o hook depois de 2 rodadas deste experimento com as páginas gravadas.

**3. Regra de uso da busca** (uma linha no `AGENTS.md`, a decidir): consultar o ai-memory por palavras-chave e identificadores ("ADR-0003 Paseo"), não por pergunta; para retomar, ler primeiro `STATUS.md` e `git log --all`, e usar o ai-memory como complemento. Para sessão cortada, usar `memory_read_session_observations` (ordem `desc`) antes dos handoffs.

**4. Limpar o que induz erro** (decisão do Felipe): cancelar os handoffs que citam a ADR-0005 como vigente (2 dos 26) depois de revisar cada um; hoje eles servem de fonte DESATUALIZADA.

**5. Reaplicar:** repetir este mesmo conjunto de 12 fatos depois do passo 1, com uma segunda pessoa pontuando, e acrescentar fatos da faixa 02-08/11 quando existirem. Meta de sucesso a registrar antes: formulação N2 ≥ 8/12 e nenhum DESATUALIZADO sem marca de "substituída".

**O que não fazer:**

- Não ligar a consolidação por LLM nem o `auto_improve` só para resolver isso antes de testar as páginas manuais; custa franquia e a ADR-0004 desligou de propósito.
- Não copiar o STATUS inteiro para o ai-memory: duplica, envelhece e já rende 12/12 pelo canal d2.
- Não tratar o briefing como fonte de retomada: ele não foi feito para isso (H1).
- Não escrever "estado atual" como página durável; estado muda por hora, vale o STATUS.
- Não confiar em pergunta natural nem na primeira página devolvida (H4).
- Não aposentar o ai-memory nem o claude-mem com base neste n=1.

## Apêndice A: consultas exatas

Projeto: `workspace=pessoal`, `project=workflow-ai`. Ferramentas MCP do ai-memory, `limit: 3` nas buscas.

- (a) `memory_briefing()`; `memory_briefing(settled_first=true)`.
- (c) `memory_handoff_list()` (26 itens; saída analisada com `jq` por identificador).
- (d1) `grep -n` no `docs/ai-os/STATUS.md` e `git log --all --date=short --format='%h %ad %s'`. (d2) `grep -rn` em `docs/ai-os/`.

| Fato | N1 | N2 | T |
|---|---|---|---|
| A1 | Por que adotamos o Paseo para rodar os agentes? | qual ferramenta orquestra Codex e OpenCode em paralelo com worktrees | ADR-0003 Paseo camada execução |
| A2 | posso rodar duas análises pesadas do Codex ao mesmo tempo? | o que aconteceu quando dois Codex gastaram a janela de 5 horas | I-23 Codex paralelo janela 5h |
| A3 | como funciona a gestão de contexto com sessões curtas? | qual a decisão sobre encerrar sessão e abrir uma nova | ADR-0004 gestão contexto sessões curtas skill sessao |
| A4 | o que avisa quando um agente do Paseo trava ou fica parado? | monitor que notifica no macOS sobre agentes fantasmas | paseo_watchdog vigia LaunchAgent agentes.json |
| B1 | por que o Mac ficou com swap alto por causa de servidores de desenvolvimento esquecidos? | servidores astro dev que ficaram vivos depois que os agentes terminaram | I-35 astro dev órfãos |
| B2 | quais períodos foram usados como baseline e comparação nas métricas? | a partir de que dia começa o segundo período de medição | baseline S1 S2 02/11 BASELINE-2026-11-09 |
| B3 | o que foi salvo antes da migração do Mac? | trabalho não commitado antes de trocar de computador | migração Mac wip/migracao-2026-11 |
| B4 | o claude-mem ainda está capturando sessões? | desde quando o worker do claude-mem está no ar | claude-mem worker 27/10 observações Workspace |
| C1 | podemos usar o Antigravity dentro da automação dos agentes? | por que o agy foi tirado dos agentes e do Paseo | ADR-0006 Antigravity fora automação |
| C2 | qual a versão atual do AI OS e o que mudou no último incidente? | como evitar que o Astro deixe servidor em background quando um agente roda | v0.2.1 ASTRO_DEV_BACKGROUND |
| C3 | como medimos se o AI OS está melhorando? | qual método de métricas foi adotado para avaliar o workflow | PROTOCOLO-GQM GQM |
| C4 | o plugin claude-mem está ligado ou desligado? | claude-mem foi desabilitado | claude-mem plugin disable desabilitar thedotmack |

Leituras estruturais (H1 a H3): `memory_recent(limit=100)`; `memory_read_page(path=sessions/<P0a>.md)`; `memory_read_session_observations(session_id=<v021-orfaos>, kinds=[user-prompt, stop], limit=6, body_max_chars=300)`.
