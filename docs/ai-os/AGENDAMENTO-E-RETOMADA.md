# Agendamento e retomada após limite de franquia (desenho)

Documento de desenho, escrito em 25/10/2026. Nada aqui foi implementado. O objetivo é responder a uma pergunta prática: como deixar trabalho rodando e ele continuar sozinho quando um provedor bate o limite, sem duplicar escritores e sem aprovar nada por engano. O ponto de partida é a diferença conhecida: um Claude CLI aberto no terminal espera o reset e segue; o Paseo não espera o reset nem retoma o turno interrompido (I-21, I-23).

Base: Paseo 0.12.0 instalado nesta máquina (app Homebrew, daemon em `127.0.0.1:6767`), documentação oficial consultada na mesma data, help local e inspeção somente leitura do código empacotado no app. O comportamento de restart vem do código e do incidente I-21; o comportamento durante o sono do Mac ainda não foi testado.

## Fontes e método

| Fonte | O que foi usado |
|---|---|
| https://paseo.sh/docs/schedules (25/10/2026) | schedule cria agente novo; heartbeat reenvia ao mesmo agente; cron é a cadência canônica; `archiveOnFinish` |
| https://paseo.sh/docs/schedules-cli (25/10/2026) | flags, `--every` compilado para cron, `--run-now`, `run-once`, UTC padrão, `--timezone`, heartbeats exigem `PASEO_AGENT_ID` |
| https://paseo.sh/docs/schedules-chat (25/10/2026) | heartbeat como "acorde-me depois"; superfície pequena de create/delete |
| https://paseo.sh/docs/mcp (25/10/2026) | ferramentas `create_schedule`, `create_heartbeat`, `run_schedule_once`, `schedule_logs` |
| https://paseo.sh/docs/cli (25/10/2026) | `paseo send`, `wait`, `inspect`, `usage ls --json` |
| https://paseo.sh/docs/troubleshooting (25/10/2026) | `daemon restart` e a afirmação de que agentes em execução continuam |
| `paseo schedule --help`, `paseo schedule create --help`, `paseo heartbeat --help` (25/10/2026) | opções reais da versão instalada |
| `~/Library/.../Paseo.app/Contents/Resources/app.asar` (0.12.0 local) | `ScheduleService`, `ScheduleStore`, `executeSchedule`, `recoverInterruptedRuns`, `ensureAgentLoaded` |
| `paseo usage ls --json` (25/10/2026) | janelas `five_hour` e `weekly`, `usedPct`, `resetsAt` de Claude e Codex |
| `docs/ai-os/INCIDENTES.md` I-11, I-21, I-23 e `decisions/0002`, `0003` | histórico do problema e regra de roteamento |

Durante a pesquisa foi criado um schedule de teste (`--every 1h`, `--cwd /tmp`, OpenCode free) só para ler o JSON persistido. Ele foi apagado na sequência com `paseo schedule delete`. Nenhum agente foi lançado.

Não existe página `/docs/heartbeats`. O heartbeat é documentado dentro de `/docs/schedules`, `/docs/schedules-cli`, `/docs/schedules-chat` e na referência de ferramentas em `/docs/mcp`. O help local confirma as mesmas opções da versão instalada.

## 1. O que schedule e heartbeat fazem

### Schedule

Cada execução começa um agente novo, com o prompt configurado e as configurações de provedor, modelo, modo e diretório daquele schedule. O agente nasce marcado como `unattended: true`, com `promptFailure: "return-error"` e `notifyOnFinish: false`. Na prática: ninguém recebe notificação do fim, e um pedido de permissão faz a execução falhar em vez de esperar por um humano.

A cadência é cron de cinco campos. `--every 5m` ou `--every 1h` não criam intervalo rolante: são compilados para uma expressão cron. O teste com `--every 1h` gravou `"expression": "0 * * * *"`, o que confirma o comportamento descrito na documentação. O fuso padrão é UTC; `--timezone` interpreta a expressão no horário local, com `nextRunAt` persistido em UTC.

Não existe agendamento único para um horário futuro. Há `--run-now` na criação e `schedule run-once <id>` para disparar agora sem mexer na cadência. Um disparo único num horário específico precisa ser aproximado com cron exato mais `--max-runs 1`, lembrando que uma execução que falha também conta como concluída e encerra o schedule.

O estado fica em `$PASEO_HOME/schedules/<id>.json` (padrão `~/.paseo/schedules`). Cada arquivo guarda `status`, `nextRunAt`, `maxRuns`, `expiresAt` e um array `runs`, com id, `scheduledFor`, início, fim, status, `agentId`, `workspaceId`, saída e erro. O JSON do teste tinha esses campos, e o diretório estava vazio antes.

Cada execução cria também um workspace. O isolamento padrão é `local`, apontando para o `cwd` configurado; worktree só entra quando pedido pela interface ou pelo MCP. Ao terminar, o workspace é arquivado por padrão (`archiveOnFinish: true`). Com isolamento local, o diretório permanece; com worktree, o worktree é removido quando o último workspace ativo dele é arquivado.

Sobre restart do daemon, a documentação de troubleshooting diz que "running agents keep going". O código do schedule mostra outra parte: no boot, `recoverInterruptedRuns` marca a execução que estava rodando como `failed`, com a mensagem `Daemon restarted before the scheduled run completed`, e avança `nextRunAt` para a próxima ocorrência futura. O schedule continua ativo, mas não continua a execução interrompida nem repõe slots perdidos. O I-21 confirma o lado do agente: o restart encerrou o agente no meio da tarefa, sem retomada. A frase da documentação e o comportamento observado divergem; até um teste controlado, vale o que foi medido aqui.

O tick do serviço roda a cada segundo enquanto o daemon está vivo. Se o Mac dorme, os timers congelam junto com o processo. A expectativa é que, ao acordar, o tick atrasado rode uma vez e execute o slot vencido. A documentação não promete esse comportamento, então ele entra no plano de teste como hipótese.

O custo tem duas partes. O Paseo roda no daemon local e não cobra por execução; a documentação não descreve cobrança para schedules. A execução em si é um turno real do modelo no provedor, então consome franquia, tokens ou créditos conforme a conta. Em disco, o estado é pequeno (o registro de agente observado tem cerca de 1,5 KB e `~/.paseo/creations` inteiro tem 472 KB), mas cada execução carrega consigo a sessão do provedor, que é onde o volume real mora.

### Heartbeat

Heartbeat usa o mesmo motor de cron e o mesmo arquivo de estado. A diferença está no alvo: `target.type` é `"agent"`, com o id do agente que criou o heartbeat. Em vez de criar um agente, ele reenvia o prompt para a mesma conversa. É o "me acorde em 20 minutos e continue" da documentação.

A criação é limitada ao próprio agente. A CLI exige `PASEO_AGENT_ID`, que só existe dentro de uma sessão do Paseo; o MCP exige sessão com agente. Um orquestrador externo não cria heartbeat para outro agente. Para cutucar outro agente, o caminho é `paseo send`.

A interface é pequena de propósito: criar e apagar pelo MCP; pela CLI, atualizar apenas o cron. Mudar prompt ou alvo exige apagar e recriar.

No restart, o estado do heartbeat sobrevive. Se o agente alvo foi arquivado ou apagado, o schedule é encerrado no boot (`sweepOrphanedSchedules`); ele não recria o agente. Se o registro existe, o disparo chama `ensureAgentLoaded`, que tenta retomar a sessão do provedor pelo id salvo. Esse é o caminho mais próximo de continuar a mesma conversa depois de uma queda, mas depende de o provedor aceitar o resume.

O custo é o de um turno normal no mesmo contexto. Cada batida relê uma conversa que só cresce, então o custo por batida tende a subir com o tempo. Um heartbeat a cada 5 minutos num agente longo é uma conta que não fecha.

### Comparação curta

| | Schedule | Heartbeat |
|---|---|---|
| Alvo | agente novo a cada execução | agente que criou o heartbeat |
| Criação | app, CLI, MCP, chat | só de dentro do agente |
| Cadência | cron ou preset `--every` | cron de cinco campos |
| Estado | `~/.paseo/schedules/<id>.json` | mesmo arquivo, `target.type = "agent"` |
| Sobrevive a restart | sim, mas o run em curso vira `failed` e slots perdidos são pulados | sim, se o agente alvo não foi arquivado |
| Custo | um turno do provedor por execução, em contexto novo | um turno do provedor no contexto existente, que cresce |
| Notificação | nenhuma por padrão | nenhuma por padrão |

## 2. Lacunas para o nosso caso

1. Limite de franquia. O Paseo registra o erro (I-23) e para. Nem schedule nem heartbeat leem quota, reset ou custo. Um heartbeat durante o limite só repete o erro, e cada repetição gasta uma tentativa sem progresso.
2. Restart do daemon. O schedule sobrevive, mas a execução em curso é marcada como falha e não é retomada. Os slots vencidos enquanto o daemon estava fora são pulados. O heartbeat sobrevive, mas a retomada do turno interrompido depende do provedor e não foi demonstrada.
3. Mac dormindo. Com a tampa fechada nada roda. Ao acordar, o timer atrasado deve disparar uma vez; se o daemon reiniciar nesse intervalo, o slot é perdido. Não existe promessa de continuidade com o Mac suspenso.
4. Granularidade. Cron trabalha em minutos e não tem "uma vez às 03:05". Para esperar um reset é suficiente, desde que o horário seja calculado e a margem seja explícita.
5. Sem checkpoint nem idempotência. O schedule guarda a saída da execução, não o estado do trabalho. `run-once` pode ser chamado duas vezes. Criar schedule pela CLI duas vezes com o mesmo nome duplica; só o caminho MCP tem `createOrReplace` por nome e alvo.
6. Aprovação e operações sensíveis. Execuções de schedule são unattended e falham ao pedir permissão. Isso protege contra aprovação automática, mas exige um desenho de escalonamento para o Felipe.
7. Sem fallback. O Paseo não troca de provedor. O ADR-0002 é consultivo e não executa nada.
8. Detecção incompleta. `paseo inspect --json` mostra `Status`, `LastUsage`, permissões pendentes e worktree, mas não a mensagem do erro. O texto do limite aparece no timeline (`paseo logs`) e o reset aparece em `paseo usage ls --json` e nos sensores locais. Nenhum campo diz "limite atingido".

## 3. Desenho: retomada após reset de franquia

### Princípios

O mecanismo é determinístico: esperar, trocar de provedor ou pedir ajuda é uma decisão de regra sobre arquivos e saídas de comando. O agente que retoma executa trabalho; ele não decide sozinho que pode ampliar escopo, aprovar permissão ou trocar dados de projeto.

Um trabalho tem um escritor por vez. Um checkpoint é gravado antes de qualquer parada. Toda ação é idempotente pela chave do trabalho e do reset. O pior caso tem limite de tentativas e termina com o Felipe sendo avisado.

### Fluxo e estados

`detectado → agendado → executando → concluido`

Ramificações: `bloqueado` (tentativas esgotadas, sinal desconhecido ou aprovação negada), `fallback` (trocou de provedor), `cancelado` (o Felipe encerrou ou o trabalho já foi concluído por outro caminho).

1. Um agente termina com status `error` e o detector confirma que a causa é limite de franquia.
2. O detector grava o checkpoint e o estado `detectado`.
3. A regra calcula o instante de retomada e decide entre esperar e trocar de provedor.
4. Se espera: cria um schedule com nome derivado da chave, para disparar depois do reset, ou deixa o disparo para `paseo send` quando o agente original ainda pode ser retomado. O estado vira `agendado`.
5. No disparo, o agente de retomada adquire o lock, relê o checkpoint, confere a quota antes de trabalhar e retoma no mesmo worktree. O estado vira `executando`.
6. Se concluir, grava a nota de estado e marca `concluido`. Se falhar, incrementa tentativas e reagenda com backoff até o limite.

### Detecção

Quem detecta é o orquestrador pai dentro do Paseo, que recebe notificação de erro do filho. Como reforço, um watchdog em schedule a cada 10 minutos varre os trabalhos com estado `detectado` e os agentes com status `error`. O watchdog não substitui o pai; ele cobre o caso em que o pai também morreu. Um agente pago a cada 10 minutos só para ler arquivos é desperdício, então o watchdog deve rodar em provedor gratuito ou virar um job determinístico de `launchd`.

Sinais, em ordem de confiança:

1. `paseo inspect <id> --json` com `Status: "error"` e o instante da última atividade.
2. `paseo logs <id> --tail 20` com um dos padrões de limite por provedor (`usage limit`, `rate limit`, `quota`, `try again at`, `5-hour limit`). O texto varia e precisa de uma lista versionada.
3. `paseo usage ls --json`: a janela com `usedPct` em 100 ou `tone: "danger"` e `resetsAt` preenchido. Na leitura de 25/10, os relatórios de Claude e Codex traziam janelas com `usedPct`, `tone` e `resetsAt` no mesmo payload, o que dá o horário de volta sem depender do texto do erro.
4. Sensor local `~/.local/state/ai-os/quota/claude.json` ou `codex.json`, com `fetched_at` de no máximo 15 minutos.

Se os sinais discordarem, o estado é `unknown` e o mecanismo não age sozinho: registra e pergunta ao Felipe. Um 429 com segundos de espera é limite momentâneo, não franquia esgotada, e fica fora dessa máquina de estados; nesse caso o agente tenta de novo após o tempo indicado.

O horário de reset vem do primeiro sinal que trouxer `resetsAt` confiável. A retomada é marcada para reset mais 2 a 5 minutos, com jitter de até 60 segundos. A margem cobre relógio, cache de 5 minutos do `paseo usage` (a doc oficial descreve esse cache) e a diferença entre o instante do erro e o instante do reset.

### Agendamento

Com reset conhecido, um schedule de uma linha de cron no minuto calculado:

```sh
paseo schedule create \
  --cron "43 23 * * *" \
  --timezone UTC \
  --name "retomada-sgg-fase2-p3-<reset_epoch>" \
  --provider codex/gpt-6.1-sol \
  --mode auto-review \
  --cwd /Users/felipe/.paseo/worktrees/<id>/<slug> \
  --max-runs 1 \
  --expires-in 2h \
  "<prompt de retomada>"
```

O `--cwd` aponta para o worktree existente, então o run cria um workspace local em cima dele, arquiva o workspace no fim e deixa o diretório intacto. Isso evita worktree novo e mantém o escritor no mesmo lugar.

Com `--max-runs 1`, uma execução que falha encerra o schedule. Por isso a falha precisa virar estado `bloqueado` com aviso ao Felipe, em vez de terminar em silêncio.

Sem reset conhecido, o schedule roda a cada 10 minutos com `--max-runs 6` e `--expires-in 2h`. O prompt manda conferir a quota e sair sem trabalhar quando ela ainda não voltou. Um run que sai sem trabalhar conta como execução concluída, então o limite de execuções é o teto real de tentativas.

A escolha entre `paseo send` e schedule novo depende do estado do agente. Se o agente ainda existe, está idle ou em erro e o provedor aceita retomar a sessão, `send` preserva o contexto e é mais barato. Se o agente foi fechado, arquivado ou o resume falhou, o schedule cria um agente novo no mesmo worktree e a retomada vem do checkpoint. A primeira versão deve preferir o caminho que já foi provado no laboratório; o outro fica como alternativa.

### Checkpoint

O checkpoint é gravado no momento da detecção. Se o agente ainda estiver vivo quando o limite chega, o hook `StopFailure` já chama `ai-memory finalize-session`, que gera o handoff com a última mensagem. Se ele já morreu, o detector monta o checkpoint com o que existe: branch, worktree, `git status`, diff, testes já executados, último passo registrado e próximo passo.

O agente de retomada começa lendo o checkpoint e conferindo o diff antes de escrever. A regra é explícita: continuar do estado observado, não reimplementar o que já está no worktree, e terminar com nota de estado e atualização do JSON.

### Um único escritor e idempotência

O Paseo não oferece lock por worktree. O mecanismo usa um lock de arquivo em `~/.local/state/ai-os/retomadas/.lock-<trabalho>`, com `flock` e um heartbeat de posse a cada 60 segundos. Lock parado por mais de 30 minutos é considerado órfão e pode ser tomado, com registro no log.

A chave de idempotência é `trabalho + reset_at + tentativa`. Dela saem o nome do schedule e o nome do arquivo de estado. Antes de criar, o mecanismo lista `paseo schedule ls --json` e procura o mesmo nome com status ativo; se existir, não cria outro. Pelo MCP, `create_schedule` com o mesmo nome e alvo já é idempotente (`createOrReplace`), mas a CLI não é, então a checagem prévia é obrigatória.

Escritas de estado são atômicas: arquivo temporário no mesmo diretório e `rename`. Nunca `run-once` para retomada automática, porque ele ignora a cadência e pode duplicar disparo. Nenhuma ação é repetida sem antes reler o estado.

### Cooldown e limite de tentativas

Não há tentativa antes de reset mais 2 minutos, nem duas tentativas separadas por menos de 15 minutos. Falhas repetidas usam backoff de 5, 15 e 30 minutos. O teto é 3 tentativas de trabalho por tarefa, com no máximo uma por janela de reset. Uma checagem que confirma que a quota ainda não voltou e sai sem trabalhar não conta como tentativa; ela só consome uma execução do schedule. Ao esgotar, o estado vira `bloqueado`, o schedule é pausado e o Felipe recebe um resumo com o que foi tentado.

### Fallback para outro provedor

A decisão segue o ADR-0002, com um limite de espera explícito. O valor inicial de 45 minutos é escolha de projeto, sem medição que o sustente.

| Situação | Ação |
|---|---|
| Reset em até 15 minutos, risco baixo ou médio | Esperar. O ADR-0002 permite gastar o resto da janela numa tarefa curta |
| Reset entre 15 e 45 minutos, risco baixo ou médio | Esperar, salvo se houver uma tarefa independente que o outro provedor possa adiantar |
| Reset em até 45 minutos, risco alto | Esperar. O piso de qualidade não cai por causa da franquia |
| Reset acima de 45 minutos, risco baixo ou médio, outro provedor com franquia e piso adequado | Trocar de provedor no mesmo worktree, com o mesmo checkpoint, e registrar a troca |
| Reset acima de 45 minutos, risco alto, prazo crítico | Perguntar ao Felipe. Não trocar sozinho o revisor nem o executor frontier |
| Projeto restrito (SEPLAN, SGG) | Só `allowed_models` do `config/ai-os-memory.toml`, incluindo o fallback |
| Sinal `unknown` | Não agir. Registrar e perguntar |

OpenCode gratuito não tem medidor oficial e fica como `unknown`. Ele pode ser executor de tarefa de baixo risco, mas não serve como prova de que existe franquia disponível para justificar uma troca.

### Aprovação humana e dados restritos

O agente de retomada herda o mesmo escopo autorizado do trabalho original. Deploy, dados de produção, credenciais, instalação global e ação destrutiva param e escalam. O modo nunca é `bypassPermissions`, e a ferramenta `respond_to_permission` fica fora do alcance do retomador. Em projeto restrito, o provedor de retomada precisa estar em `allowed_models`; a ausência do modelo na lista bloqueia o fallback.

### Estado persistido

```json
{
  "schema": 1,
  "trabalho": "sgg-fase2-p3",
  "agente_id": "cf5783de-9ffe-407d-ab9c-ecd56782f3e2",
  "provider": "codex",
  "model": "gpt-6.1-sol",
  "worktree": "/Users/felipe/.paseo/worktrees/3fqbtnxd/sgg-fase2-p3",
  "branch": "sgg-fase2-p3",
  "detectado_em": "2026-10-25T20:41:00Z",
  "motivo": "quota",
  "janela": "five_hour",
  "reset_at": "2026-10-25T23:38:21Z",
  "retomar_em": "2026-10-25T23:43:00Z",
  "checkpoint": {
    "feito": ["analise dos arquivos X e Y", "testes de unidade passando"],
    "verificado": ["python3 -m unittest discover -s tests"],
    "pendente": ["integrar o diff no branch principal"],
    "proximo_passo": "rodar os testes de integracao e commitar"
  },
  "tentativas": 0,
  "max_tentativas": 3,
  "estado": "agendado",
  "schedule_id": "9f2c1a04",
  "lock": null
}
```

## 4. Plano de teste em laboratório

Laboratório: `~/Workspace/tools/laboratorio`, repositório descartável, sem dados reais. Nenhum teste usa a franquia principal de propósito.

| # | Objetivo | Como | Critério de aprovação |
|---|---|---|---|
| T1 | Cron, fuso e persistência | schedule para daqui a 2 minutos, `--timezone America/Fortaleza`, prompt que escreve um arquivo | dispara no minuto certo; `~/.paseo/schedules/<id>.json` tem o run com `agentId` e `output`; workspace arquivado e diretório intacto |
| T2 | Restart com run em curso | agente dormindo 10 minutos, `paseo daemon restart` no meio | run vira `failed` com a mensagem de restart; `nextRunAt` avança; nenhum run duplicado; schedule segue ativo |
| T3 | Restart com slot perdido | daemon parado no horário marcado, subir 10 minutos depois | slot perdido não roda; próxima ocorrência roda; nenhum catch-up |
| T4 | Mac dormindo | schedule para daqui a 5 minutos, dormir por 10, acordar | registrar se dispara ao acordar e quanto tempo depois. Precisa do Felipe, porque suspende a máquina |
| T5 | Detector sem queimar franquia | provedor falso que imita o erro de limite, com textos reais de Claude e Codex gravados | detector classifica como `quota`, extrai reset quando existe e devolve `unknown` quando os sinais discordam |
| T6 | Idempotência | rodar o detector duas vezes e, em paralelo, dois processos com o mesmo trabalho | um schedule, um estado, um lock; o segundo processo sai sem escrever |
| T7 | Cooldown e tentativas | forçar falha do retomador três vezes | backoff de 5, 15 e 30 minutos; para em `bloqueado`; Felipe é avisado |
| T8 | Fallback | reset fictício de 3 horas, Codex disponível, risco médio | troca de provedor no mesmo worktree, sem segundo escritor, com registro da troca |
| T9 | Aprovação | prompt de retomada que tenta `rm` ou instalação global | run pede permissão, não recebe aprovação automática, estado vira `bloqueado` |
| T10 | Heartbeat após restart | agente de teste com heartbeat de 2 minutos, restart do daemon | heartbeat dispara e retoma a mesma sessão do provedor. Se falhar, o desenho fica só com schedule |

O teste com limite real (Claude 5h ou Codex) fica para quando acontecer naturalmente. Ele é o único que valida o texto de erro e o `resetsAt` de ponta a ponta, e não deve ser provocado só para testar.

## 5. O que precisa ser construído

### Opção A: só procedimento

Uma skill `ai-os-retomada` descrevendo detecção, checkpoint, agendamento e escalonamento, executada pelo orquestrador. Cobre o caso comum em que um agente pai está vivo para reagir. Não cobre daemon parado, sono do Mac nem garantia de um escritor, porque depende de um modelo lembrar de seguir o procedimento.

Tamanho: um arquivo, cerca de 100 linhas. Serve como documentação operacional, não como mecanismo.

### Opção B: script determinístico mais skill (recomendada)

Um script `scripts/retomada.py` com quatro subcomandos:

- `detectar <agente>`: lê status, logs e sensores; grava o checkpoint e o estado.
- `armar <trabalho>`: decide esperar ou trocar, calcula o cron e cria o schedule.
- `executar <trabalho>`: toma o lock, relê o checkpoint, confere a quota e retoma.
- `status <trabalho>`: mostra estado, tentativas e próximo disparo.

O script usa só a biblioteca padrão e chama a CLI do Paseo por `subprocess` com lista de argumentos, sem shell. A skill `ai-os-retomada` explica quando chamar cada subcomando e como escalar. Um watchdog em schedule, apontando para `detectar`, cobre o pai morto. Se o teste T4 mostrar que o timer do daemon não é confiável ao acordar, entra um `launchd` como relógio alternativo.

Tamanho estimado:

| Peça | Linhas |
|---|---|
| `scripts/retomada.py` | 300 a 350 |
| `tests/test_retomada.py` | 150 a 200 |
| `skills/ai-os-retomada/SKILL.md` | 80 a 100 |
| `launchd` plist e integração no `install.sh`, só se o T4 exigir | 60 a 80 |
| Atualização desta página e do STATUS | 20 a 30 |

Total: 4 a 6 arquivos, 550 a 700 linhas, com 1 a 2 dias incluindo os testes de laboratório. O caminho crítico é o T2 e o T5: sem eles não dá para afirmar que a retomada não duplica trabalho.

### Opção C: plugin do Paseo

Um plugin poderia ouvir o evento de erro e agendar sozinho, sem depender de um pai vivo. O custo é confiança: plugin roda sem sandbox, com o acesso do usuário, e a auditoria do Continuity já mostrou o tipo de risco que essa posição cria. Fica fora desta fase. A ADR-0003 também descarta o Continuity.

### O que não construir agora

Aprovação automática de permissões, envio de transcript entre provedores e troca automática de provedor em risco alto. Os três resolvem atrito, mas mudam o contrato de segurança sem evidência de que o ganho compensa.

## 6. O que ainda não sabemos

- Se o timer do daemon dispara o slot vencido depois do sono do Mac (T4).
- Se `paseo send` realmente retoma um agente que terminou em erro de quota, ou se o provedor recusa a sessão.
- Se o `resetsAt` do `paseo usage` coincide com o instante em que o provedor volta a aceitar chamadas. A margem de 2 a 5 minutos é uma aposta conservadora.
- Quanto custa, em franquia, uma retomada real com o contexto já grande. Só a telemetria responde.
- Se o schedule sobrevive a uma atualização do Paseo que mude o formato de `~/.paseo/schedules`. O estado é versionado só pelo schema implícito.

## Nota de estado

Desenho concluído em 25/10/2026, sem implementação. A opção B é a recomendada. Dependem do Felipe o limite de espera de 45 minutos, o teto de 3 tentativas e a aprovação do plano de teste. T1, T2 e T5 formam o caminho crítico. O schedule usado para ler o JSON foi apagado; nenhum agente foi lançado.
