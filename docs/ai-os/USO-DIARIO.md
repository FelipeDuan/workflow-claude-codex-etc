# Felipe AI OS: uso diário

## Começar

1. Abra o **Paseo** (app). Ele sobe o daemon sozinho em `127.0.0.1:6767`. Fechar o app derruba esse daemon (I-28). Para orquestrar sem o app, rode `paseo start`: o daemon sobe solto do terminal (filho do `launchd`) e continua vivo se o terminal fechar. Ele não sobe sozinho no login; depois de reiniciar o Mac, abra o app ou rode `paseo start` de novo. Confira com `paseo daemon status` (`localDaemon: running`).
2. Escolha o projeto e crie a tarefa com o provedor certo (ver "Quem faz o quê").
3. Para trabalho em paralelo, peça um **worktree novo** por agente que vai escrever.
4. Aprove permissões pelo app, ou pela CLI: `paseo permit ls` e `paseo permit allow <agente> <id>`.

Sem o app, tudo continua funcionando pelo terminal: `claude`, `ai-memory run codex`, `opencode`.

## Quem faz o quê

A política vigente está em [`roteamento.json`](roteamento.json). Ela define modelos por risco, modos, parâmetros obrigatórios, franquia, concorrência e a regra do Astra. Os projetos restritos usam `allowed_models` de `config/ai-os-memory.toml`, inclusive revisores e alternativas. A [ADR-0002](decisions/0002-roteamento-por-capacidade-e-franquia.md) registra a justificativa histórica; a [ADR-0007](decisions/0007-politica-canonica-e-preflight.md) registra a fonte canônica.

| Risco | Executor | Verificação |
|---|---|---|
| Alto: segurança, auth, dados, arquitetura | Claude Opus; Codex Astra sob as condições do JSON | Revisor de outra família de modelo |
| Médio | Codex gpt-6.1-sol / gpt-6-luna ou Claude Sonnet | Diff grande: outro harness elegível, depois gpt-6.1-sol com thinking low/medium, gpt-6-luna se mecânica |
| Baixo e verificável por teste | OpenCode gratuito ou Codex gpt-6-luna | Orquestrador confere testes e diff |

Antes de cada lançamento, rode no checkout do workflow-ai (Python 3.11 ou superior):

```sh
python3 scripts/preflight.py --provider codex/gpt-6.1-sol --mode auto-review --thinking medium --base <branch> --cwd <projeto> --new-workspace worktree --risk medium
```

O preflight só consulta dados e imprime JSON. `allow` autoriza seguir com os mesmos argumentos; `ask_human` pede decisão de Felipe; `deny` exige corrigir a solicitação e repetir a consulta. Códigos de saída: `0`, `2` e `1`, respectivamente. O preflight nunca executa `paseo run` e não reserva vaga de concorrência: confira novamente antes de lançar.

`--cwd` é obrigatório. `--base` só é obrigatório com `--new-workspace worktree`; quando fornecido, sempre precisa resolver para um commit no Git do `--cwd`. `--new-workspace local` e execução no workspace atual podem omiti-lo. `--provider` inclui o modelo, `--mode` é explícito e os parâmetros exigidos por provider vêm do JSON. Para Astra, `--no-cheaper-eligible` registra a avaliação humana de que nenhum executor mais barato atende o piso. Essa flag não substitui as demais verificações.

A função pura `decide(task, policy, quotas, running_agents, restricted)` recebe o instante ISO em `task.now` e a confirmação Git em `task.base_exists`. `restricted` contém `enabled` e `allowed_models`; a CLI faz a classificação por caminho, marcador e checkout principal do worktree. Nenhuma quota reduz o piso de risco alto.

Uma tarefa pesada do Codex por vez, conforme `concurrency` no JSON. Lance em sequência: preflight, run, preflight, run. `--planned-heavy N` soma os pesados adicionais já planejados que ainda não aparecem no snapshot; o padrão é zero. A coleta global inclui agentes de outros diretórios e workspaces em background. Qualquer estado diferente de `idle`, `closed` e `error` conta como ativo.

`--short-task` declara uma tarefa curta para a exceção nos 20 min antes do reset, definida em `quota.reset_exception`. A exceção exige `resets_at` válido na janela de cinco horas; não vale para limite semanal nem dispensa a verificação de concorrência.

OpenCode gratuito não tem medidor oficial: sua quota é `unmetered`, sem inventar leitura `ok` e sem bloquear por quota ausente. Claude/Codex usam assinaturas, não APIs via gateway. As classes `acesso_dados`, a nota institucional, a família do revisor, a ordem de revisão de risco médio e `limite_fallback` continuam documentados no JSON; o preflight não os fiscaliza. O orquestrador aplica essas regras e verifica os termos e a configuração de treino das contas.

Para simular sem alterar o HOME, use `--quota-dir <pasta>`, `--agents-file <snapshot.json>` e `--now <ISO-com-fuso>`. O snapshot de agentes aceita uma lista JSON ou um objeto com `agents`; a quota segue o contrato da ADR-0002. Arquivo ausente, inválido ou coleta indisponível gera estado desconhecido, nunca uma lista vazia presumida. Esses overrides são entradas de simulação sob controle do operador, não uma fronteira de segurança. Alternativas só aparecem se passarem as mesmas verificações e mantiverem o piso de risco.

Antes de escolher, olhe a franquia:

- Claude: barra de status (`Claude 5h X% · sem Y%`) ou `~/.local/state/ai-os/quota/claude.json`.
- Codex: `~/.local/state/ai-os/quota/codex.json`. O vigia executa `python3 scripts/quota_codex.py --write` a cada 5 min, fora do sandbox, pelo launchd.
- Antigravity: consulta manual pelo Felipe no app ou CLI oficial. O AI OS não atualiza nem consulta essa franquia.
- No Paseo: `paseo usage`.

As condições do Astra, os limiares e a validade das leituras ficam somente em `roteamento.json`. Consulte os IDs disponíveis com `paseo provider models codex`.

**Decomposição para economia.** O orquestrador quebra a tarefa e manda cada parte ao modelo mais barato que atinge o piso de qualidade: Haiku para checagens, inventários e verificações mecânicas; Sonnet nativo (subagente do Claude Code) para docs e implementação de rotina; Opus só para orquestração e decisão de risco alto. Gemini via AI Studio permanece como experimento futuro separado.

Agentes em sandbox devem ler esses arquivos de estado (`claude.json` e `codex.json`), sem executar o leitor de franquia (I-06). Arquivo ausente, leitura vencida ou status diferente de `ok` significa franquia desconhecida.

## Perfis sugeridos no Paseo (criar na UI)

| Perfil | Provedor/modelo | Modo | Quando usar (campo "When to use") |
|---|---|---|---|
| Arquitetura | claude / Opus | Plan Mode | Requisitos ambíguos, decisões de arquitetura e segurança. Não altera código de produção |
| Desenvolvimento autônomo | codex / gpt-6.1-sol | Auto-review | Implementar um plano aprovado num worktree próprio, rodar testes e corrigir sem perguntar a cada passo |
| Frontend e design | claude / Sonnet 5.5 | Auto mode | Telas e UX usando as skills de design e o agente frontend-ux-ui |
| Revisão independente | codex (se o autor foi Claude) ou claude (se foi Codex) | Plan Mode | Revisar diff de risco médio/alto sem escrever no checkout do autor |
| Economia | opencode / deepseek-v4.1-flash-free ou glm-5.3-flash-free | Build | Tarefas de baixo risco, com teste, só em projeto pessoal/público |

Um Claude aberto **dentro do Paseo** recebe notificações dos filhos (acorda quando terminam). Um Claude aberto no terminal delega por `paseo run` e consulta com `paseo wait`.

## Comandos úteis

```sh
paseo run --provider codex/gpt-6.1-sol --mode auto-review --thinking medium --new-workspace worktree --worktree-slug <nome> --base <branch> --cwd <projeto> "<tarefa>"   # após allow do preflight
paseo run --provider opencode/opencode/deepseek-v4.1-flash-free --mode build --new-workspace worktree --base <branch> --cwd <projeto> "<tarefa>"   # após allow do preflight
paseo ls                     # agentes (atenção: "running" pode ser espera de aprovação)
paseo wait <id>              # mostra se está esperando aprovação ou terminou
paseo logs <id>              # o que o agente fez
paseo delete <id>            # encerra e apaga o agente
ai-memory run codex          # continuar de onde o último agente parou (terminal)
ai-memory run --fresh codex  # tarefa nova no Codex (terminal)
```

## Antigravity (Gemini)

Uso direto pelo Felipe no app ou CLI oficial. Nenhum agente, Paseo, Claude ou script do AI OS invoca `agy`. A FAQ do Google diz que acessar o Antigravity por software de terceiros viola os Termos de Serviço e pode levar à suspensão ou encerramento da conta; envolver `agy` em agentes de terceiros não é suportado nos planos de consumidor. Para Gemini em agentes de terceiros, o Google recomenda uma chave Gemini Enterprise ou Google AI Studio. Ver [ADR-0006](decisions/0006-antigravity-fora-da-automacao.md) e [FAQ](https://antigravity.google/docs/faq).

O guia de modelos em `MODELOS_2026.md` é somente referência para o uso direto. Uma futura via da API do Google AI Studio será um experimento separado. No tier gratuito, usar apenas dados públicos, nunca projeto restrito.

## Vigia dos agentes do Paseo

O `paseo_watchdog` roda a cada 30 s pelo LaunchAgent e responde a pergunta "algum agente precisa de mim agora?". Ele lê `paseo ls -a --json`, `inspect`, `permit ls` e os agendamentos, e calcula o estado real de cada agente:

| Estado | Critério |
|---|---|
| `aguardando_aprovacao` | pedido em `permit ls` pendente há mais de 2 min |
| `parado` | `running` com `UpdatedAt` do inspect há mais de 10 min (sem atividade) |
| `erro` | status `error` (mostra a mensagem, inclusive limite de uso com horário) ou `closed` no meio de uma execução |
| `parado_sem_entrega` | `idle`/`closed`/`error` num worktree Git, sem commit desde a criação do agente nem arquivos novos/modificados |
| `pedido_fantasma` | aprovação falhou com `handler_error`, 404 ou `unconfirmed`; não tenta novamente |
| `concluido` | `idle`/`closed` com entrega ou sem evidência suficiente de ausência de entrega |
| `trabalhando` | `running` com atividade recente |

Quando algum agente entra em `aguardando_aprovacao`, `parado` ou `erro`, chega uma notificação do macOS. A mesma condição contínua não repete o aviso. Aprovação pendente só avisa após 2 min; pergunta avisa imediatamente. Para receber lembretes, configure `reminder_min = 10` no topo de `config/paseo-watchdog-policy.toml`; ausente ou `0` desliga os lembretes.

A autoaprovação segue `config/paseo-watchdog-policy.toml`, versionada no repo. As regras são ordenadas e valem por nome da ferramenta e regex da descrição. `allow` só aprova leitura/inspeção dentro de `~/.paseo/worktrees` ou de um repo listado em `allowed_roots`; `.env`, segredos, backups, planilhas, `rm -rf`, instalação de pacotes, migração, docker e download com escrita caem em `deny` (nunca aprovam sozinhos). Perguntas e todo o resto viram `notify`. Em projeto restrito, a restrição vale para o modelo: `allow` continua possível se o provider/model estiver em `allowed_models` de `config/ai-os-memory.toml`. Modelo não permitido gera alerta de prioridade alta e bloqueia as aprovações desse agente. A classificação inclui o checkout principal dos worktrees.

Pedido `question` gera aviso de prioridade alta imediato: só humano responde. Pedido fantasma gera um aviso único: provável reinício do OpenCode; retome com `paseo send <id>` ou apague o agente. Preserve o serviço do OpenCode enquanto houver agentes ativos (I-26). Comandos compostos, opções opacas, leitura fora do cwd e acesso a diretório externo exigem decisão humana. A inspeção Git do vigia desativa `core.fsmonitor` para evitar executar hooks do repo fora do sandbox. A aprovação de `git status` mantém a configuração Git do agente e depende do isolamento dele. O subconjunto automático de shell é conservador: `git status`, listagem e leitura simples; `git log/diff/show/add/commit`, `rg`, `grep`, `file` e `stat` ficam para decisão humana.

O histórico fica em `<state_dir>/history/`: `quota-AAAA-MM.jsonl` guarda uma amostra por janela a cada atualização da franquia; `agents-AAAA-MM.jsonl` guarda mudanças de estado, primeiro avistamento e desaparecimento; `collector-AAAA-MM.jsonl` guarda lacunas maiores que 5 min desde o fim do ciclo anterior e o resumo diário, emitido no primeiro ciclo do dia seguinte. O diretório padrão é `~/.local/state/ai-os`, sobrescrevível por `AI_OS_STATE_DIR`. A atualização usa o sensor Codex existente e lê `quota/claude.json`, escrito externamente pelo hook do Claude. O cache Claude tem validade de 15 min; arquivo ausente, inválido ou antigo produz amostras desconhecidas. Leituras Claude com o mesmo `fetched_at` e estado do sensor não repetem janelas já anexadas, mesmo após reiniciar o vigia.

Cada linha é um objeto JSON independente com `schema_version = 1`, `type`, `occurred_at`, `observed_at`, `source = "watchdog"`, `source_version`, `confidence` e `task_id`. Instantes são UTC; valores desconhecidos ficam `null` com `reason`, inclusive consumo em falha ou leitura desatualizada. Transições têm `from`, `to` e `reason_code`; amostras têm `provider`, `pool`, `window_kind`, `used_percent`, `resets_at` e `sensor_status`. O estado acumula ciclos com e sem observação de agentes, duração total/máxima em ms e bytes anexados por dia local. A data do resumo e o mês dos arquivos seguem o fuso local; os instantes dos registros continuam em UTC. Lacunas não contam como inatividade do agente. Falha da CLI gera um `collector.gap` com `reason = "paseo_unavailable"` por sequência de falhas; os agentes anteriores são preservados e a recuperação retoma a contagem de atividade observada.

O histórico não inclui pedidos, mensagens ou cwd. Todos os agentes têm `title = null`; o projeto aparece apenas pelo nome da pasta, ou como `"restrito"` em projetos restritos. Na CLI verificada, `ls --json` e `inspect --json` não expõem labels: `task_id` fica `null` com justificativa. Se uma versão passar a expor `labels.task`, o vigia aproveita esse valor. Desligue só o histórico com `AI_OS_HISTORY=0` no ambiente do processo do vigia; notificações e decisões de permissão continuam funcionando. Leitores devem ignorar linhas inválidas: uma interrupção pode deixar a última linha incompleta. O vigia separa essa linha antes de anexar o próximo registro. Falhas de escrita são registradas em `watchdog.log` e o ciclo prossegue; `--dry-run` também não escreve histórico.

Referência de medição: `docs/research/PROTOCOLO-GQM.md`, contrato de dados e perguntas Q2/Q4/Q5.

Para ver o estado e desligar:

```sh
cat ~/.local/state/ai-os/agentes.json          # retrato atual (status, tempo, motivo)
tail -n 40 ~/.local/state/ai-os/watchdog.log   # eventos (aprovações, avisos, erros)
~/Workspace/tools/workflow-ai/scripts/paseo_watchdog.py --dry-run   # simula sem aprovar nem notificar
./install.sh --watchdog                        # instala/atualiza o LaunchAgent
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.felipe.ai-os.paseo-watchdog.plist   # desliga
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.felipe.ai-os.paseo-watchdog.plist  # religa
```

O vigia só aprova o que a política permitir. Aprovar ou negar o resto continua sendo decisão sua, pelo app ou por `paseo permit allow|deny`.

## Tarefas e relatório de métricas

Antes de delegar, abra uma tarefa no checkout do workflow-ai e use o ID impresso como prefixo do título do agente, por exemplo `[T-20261109-01] Corrigir validação`. Registre também o vínculo explícito; a CLI do Paseo não expõe labels. `--cwd` é obrigatório e identifica o projeto de destino: em caminhos restritos, o objetivo é gravado como `restrito`.

```sh
python3 scripts/ai_os_task.py open "Corrigir validação" --risk medium --cwd <projeto>
python3 scripts/ai_os_task.py link <task_id> <agent_id> --role exec
python3 scripts/ai_os_task.py close <task_id> aceito --nota "Testes e diff conferidos"
python3 scripts/ai_os_task.py list --open
python3 scripts/metrics/report.py
python3 scripts/metrics/report.py --since 2026-11-02 --until 2026-11-09
```

O veredito (`aceito`, `retrabalho` ou `rejeitado`) é decisão humana ou do orquestrador; o estado final do agente não o substitui. Antes de relançar ou vincular outro agente a uma tarefa fechada, use `reopen <task_id> --motivo "..."`. Os eventos ficam em `<state_dir>/history/tasks-AAAA-MM.jsonl`, com mês local e instantes UTC.

O relatório semanal padrão gera `RELATORIO.md` e `relatorio.json` em `<state_dir>/relatorios/<inicio>-<fim>/`; `--out DIR` troca o destino. Datas em `--since` e `--until` incluem os dois dias; com instantes ISO, o fim é exclusivo. `state_dir` é `~/.local/state/ai-os`, ou `AI_OS_STATE_DIR` quando definido. `telemetria.jsonl` permanece como histórico legado. Os relatórios publicam cobertura e motivos dos dados desconhecidos; o tempo de interação é um proxy estimado, não uma medida de esforço humano.

## Memória

O `./install.sh --only codex` mantém o MCP do ai-memory via `mcp-bridge`, com backup (Python >= 3.11; `--no-mcp` pula essa configuração).

- O `./install.sh` registra SessionStart no Claude e no Codex (Python >= 3.11). No Codex, depois da instalação, abra `/hooks` → trust. O ai-memory deve estar instalado e continuar em modo allowlist: sem marcador válido, não captura.
- Em repositórios dentro das raízes de `config/ai-os-memory.toml`, o hook cria `.ai-memory.toml` local, ignora-o no Git e exclui o checkout do Claude-Mem. Preserva marcadores existentes. Worktrees herdam a classificação do checkout principal; SEPLAN/SGG usam workspace `restrito`, os demais `pessoal`. O projeto é derivado pelo ai-memory, sem nome fixado no marcador.
- Sem Git, a raiz do projeto é o segundo nível abaixo da raiz configurada (ex.: `~/Workspace/projetos/sgg-controle` ou `~/Workspace/seplan/ats`), mesmo abrindo uma subpasta. A raiz e as categorias (`projetos`, `seplan`) são ignoradas. No Paseo, só Git é aceito. Um subrepositório herda o marcador ancestral do projeto, sem duplicá-lo.
- O aviso de projeto restrito orienta a delegação; o preflight nega modelos fora de `allowed_models`. Claude/Codex significam assinaturas: Felipe deve conferir e desativar treino nas contas Claude/ChatGPT. Do OpenCode Zen/Console, só os dois IDs gratuitos listados na política estão permitidos.
- Os hooks do Claude rodam em paralelo: o primeiro briefing pode exigir abrir outra sessão após criar o marcador. O instalador preserva os hooks do ai-memory; marcadores existentes também mantêm sua configuração de briefing.
- Ao terminar uma sessão, o agente deixa uma nota de estado; o próximo recebe o handoff sozinho.
- Algo antigo que o ai-memory não sabe: a skill `memory-backfill` busca no Claude-Mem, confere e grava.

## Sessões e contexto (ADR-0004)

Uma sessão por objetivo. O chat é descartável; o estado fica no STATUS, nos ADRs e no ai-memory. Protocolo completo e contingências: `GESTAO-CONTEXTO.md`. A skill `sessao` executa cada etapa: peça "abrir sessão", "encerrar sessão", "recuperar sessão que caiu" ou "destilar este chat".

- **Abrir:** o handoff chega sozinho. Leia o STATUS do checkout canônico e confira a branch (`git worktree list`).
- **Durante:** registre cada decisão na hora, como linha no STATUS ou rascunho de ADR. Mande exploração pesada para subagente.
- **Encerrar** quando: o objetivo acabar, o assunto mudar, houver mais de duas correções falhas no mesmo problema, vier uma pausa longa ou o contexto passar de ~200k tokens (alerta experimental). Antes de sair, atualize só a sua frente no STATUS e escreva a nota de estado.
- **Sessão caiu sem handoff:** `memory_briefing` → `memory_read_session_observations` da sessão → `git status`/`diff`/`log` → STATUS.

## Higiene em modo diagnóstico (scan e plano)

`scripts/hygiene.py` só lê e imprime. Ele só remove saídas antigas identificadas da própria ferramenta no diretório canônico de higiene; **nunca** move, poda, mata processo, descarrega launchd nem roda `git gc/prune/worktree remove` ou `paseo delete`. A v1 não tem `--apply`.

```sh
python3 scripts/hygiene.py scan                  # JSON em ~/.local/state/ai-os/higiene/scan-AAAAMMDD-HHMM.json (modo 600)
python3 scripts/hygiene.py plan --scan <arquivo> --out ~/.local/state/ai-os/higiene/plano-AAAAMMDD-HHMM.md
python3 scripts/hygiene.py plan --days 14        # sem --scan, faz um scan novo em memória
```

Requer Python >= 3.11 (reaproveita o `tomllib` do vigia). O `/usr/bin/python3` do macOS é 3.9: use `/opt/homebrew/bin/python3`, como o launchd do vigia; no 3.9 o CLI sai com mensagem clara. Tamanhos usam `du -sPk` (não segue symlinks). `plan --scan` valida a estrutura do arquivo: arquivo inválido dá erro, item adulterado vira DESCONHECIDO sem comando.

Como ler o plano (qualquer dúvida preserva; o que não dá para provar, como lock ilegível ou busca de patch truncada em mais de 40 refs, vira DESCONHECIDO):

- **PRESERVAR**: alteração local, untracked, commit sem equivalente em outra ref (`git cherry` cobre cherry-pick), lock, agente rodando/aguardando/recente, checkout principal, projeto restrito.
- **CANDIDATO**: worktree limpa e parada há mais de N dias (padrão 7), ou agente `idle`/`closed` sem pendência há mais de N dias. Cada candidato traz o comando exato como sugestão, nunca executado. Rode à mão, um por vez, depois de conferir. O espaço recuperável é ESTIMADO (soma de bytes em disco das worktrees candidatas).
- **DESCONHECIDO**: Paseo indisponível, agente em erro ou com status inédito, symlink, leitura do git falhou. Nada a fazer sem olhar.

Também aparecem disco livre, pressão de memória e swap (o sinal que importa, não "RAM usada") e o tamanho por classe; `~/Library/Caches` é só informativo. Caminhos de projeto restrito saem como `restrito/<n>` e títulos de agentes nunca são coletados. O plano e o scan têm caminhos reais: ficam fora do repo.

## Configuração local do Paseo (já aplicada)

```sh
paseo daemon config set agents.providers '{"opencode":{"command":["/Users/felipe/.opencode/bin/opencode"]},"antigravity":{"enabled":false}}'
paseo daemon config set features.dictation.enabled false
paseo daemon config set features.voiceMode.enabled false
paseo daemon restart   # se só agents.providers mudou, basta paseo reload (I-21)
```

O provider Antigravity está desabilitado. Sua reativação exige nova decisão de Felipe (ADR-0006).

Não instalar o plugin Continuity (ver `AUDITORIA-CONTINUITY.md`). Não ligar o relay nem expor a porta sem decidir antes (Tailscale é o caminho preferido para o celular).

## Quando algo der errado

Veja `INCIDENTES.md`: cada problema conhecido tem um contorno. Se for novo, registre lá.
## Processos deixados por agentes

`python3 scripts/hygiene.py scan` registra processos do usuário com diretório atual dentro das worktrees do Paseo e worktrees Git escaneadas. `python3 scripts/hygiene.py plan` marca `ORFAO_CANDIDATO` quando o processo tem `ppid=1`, o agente está fechado/inativo ou não existe, não há conexão TCP estabelecida e a idade passa de 6 horas. Use `python3 scripts/hygiene.py plan --orphan-hours N` para ajustar esse limite.

O plano só sugere comandos. Se o PID do lock Astro (`.astro/dev.json` ou `.astro/preview.json`) corresponder, sugere `astro dev stop` ou `astro preview stop`. Nos demais casos, o comando confere o horário de início antes de enviar `TERM`. Revise o worktree e o processo antes de executar qualquer sugestão. Nenhum processo é encerrado automaticamente.

## Memória, swap e custo do coletor (Q5)

`python3 scripts/metrics/report.py` publica na Q5 o scan mais recente dentro da janela: timestamp, swap alocado/usado, pressão, percentual livre, componentes com maior footprint, órfãos e resíduos de agentes, disco livre e custo do scan. Os tempos diários do vigia continuam ao lado. Use `--hygiene-scan <arquivo>` para escolher uma amostra dentro da janela. Sem amostra, o relatório mostra `unknown` e o motivo.

O footprint vem de uma única chamada ao `top` e inclui páginas compartilhadas e comprimidas: a soma por componente **não é memória exclusiva**. Sessões Claude Code na CLI incluem seus processos filhos; o app Claude aparece em outros apps. Se um PID do `ps` não aparecer no `top`, a soma dos demais continua disponível com `partial`, `missing_count` e status `estimated` no relatório. O próprio coletor e seus filhos ficam fora da soma. Para avaliar pressão no Mac, acompanhe swap e pressão ao longo do tempo; uma amostra isolada não mostra se o problema é sustentado.

O vigia existente inicia um scan em segundo plano a cada 6 horas e continua seu ciclo sem esperar o inventário. Os ciclos seguintes supervisionam o mesmo PID e registram `collector.hygiene_scan` com a duração real do filho, separada do custo diário do vigia. O coletor tem prazo próprio de 120 segundos; o vigia só pode interromper esse filho após conferir PID e horário de início. Sem identidade confirmada, preserva o vínculo e bloqueia outro scan.

Em `config/paseo-watchdog-policy.toml`, ajuste `hygiene_scan_hours`; `0` desliga novos scans, mantendo a supervisão de um scan em andamento. O scan manual continua disponível. A rotação mantém até 28 scans e 28 planos identificados como gerados pela ferramenta no diretório de higiene do estado configurado (`AI_OS_STATE_DIR`, quando definido). Outros arquivos e links são preservados; uma falha ao apagar saída antiga é avisada e não invalida o scan.
