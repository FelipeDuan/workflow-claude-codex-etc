# Felipe AI OS: uso diário

## Começar

1. Abra o **Paseo** (app). Ele sobe o daemon sozinho em `127.0.0.1:6767`. Fechar o app derruba esse daemon (I-28). Para orquestrar sem o app, rode `paseo start`: o daemon sobe solto do terminal (filho do `launchd`) e continua vivo se o terminal fechar. Ele não sobe sozinho no login; depois de reiniciar o Mac, abra o app ou rode `paseo start` de novo. Confira com `paseo daemon status` (`localDaemon: running`).
2. Escolha o projeto e crie a tarefa com o provedor certo (ver "Quem faz o quê").
3. Para trabalho em paralelo, peça um **worktree novo** por agente que vai escrever.
4. Aprove permissões pelo app, ou pela CLI: `paseo permit ls` e `paseo permit allow <agente> <id>`.

Sem o app, tudo continua funcionando pelo terminal: `claude`, `ai-memory run codex`, `opencode`.

## Quem faz o quê (ADR-0002, consultivo)

| Tarefa | Primeira escolha | Revisor |
|---|---|---|
| Risco alto (segurança, auth, dados, arquitetura) | Claude Opus; Codex Astra só com cautela (ver abaixo) | outra família |
| Risco médio | Codex gpt-6.1-sol / gpt-6-luna ou Claude Sonnet | quando o diff for grande: revisor de outro harness elegível, depois gpt-6.1-sol (`--thinking low/medium`), gpt-6-luna se mecânica |
| Risco baixo e com teste | OpenCode gratuito (GLM-5.3-Flash / DeepSeek V4.1 Flash) | conferir testes e diff |
| Dados de SEPLAN/clientes | somente `allowed_models` em `config/ai-os-memory.toml`; conferir treino das contas | — |

Antes de escolher, olhe a franquia:

- Claude: barra de status (`Claude 5h X% · sem Y%`) ou `~/.local/state/ai-os/quota/claude.json`.
- Codex: `~/.local/state/ai-os/quota/codex.json`. O vigia executa `python3 scripts/quota_codex.py --write` a cada 5 min, fora do sandbox, pelo launchd.
- Antigravity: consulta manual pelo Felipe no app ou CLI oficial. O AI OS não atualiza nem consulta essa franquia.
- No Paseo: `paseo usage`.

**GPT-6 Astra (Codex), usar com muito cuidado.** Uma revisão somente leitura com `gpt-6-astra` (thinking padrão) consumiu 27% da janela de 5h do Codex em 09/11; antes, 3 agentes Astra pararam por limite (I-11). Só para risco alto quando nenhum executor mais barato atinge o piso de qualidade, sempre com `--thinking low` ou `medium` explícito, uma tarefa por vez (a regra de uma por vez vale para agentes Codex pesados, I-23) e com franquia Codex 5h < 50% (franquia `unknown` bloqueia o Astra). Modelos Codex (`paseo provider models codex`): gpt-6.1-sol (workhorse), gpt-6-astra (frontier), gpt-6.1-terra (custo não medido), gpt-6-sol, gpt-6-luna (rápido e barato), gpt-5.6-sol/terra/luna (gerações antigas).

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
paseo run --provider codex/gpt-6.1-sol --thinking medium --new-workspace worktree --worktree-slug <nome> --base <branch> "<tarefa>"   # agente novo em worktree próprio (--thinking explícito no Codex)
paseo run --provider opencode/opencode/deepseek-v4.1-flash-free --new-workspace worktree "<tarefa>"
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

Referência de medição: `docs/research/PROTOCOLO-GQM.md`, contrato de dados e perguntas Q2/Q4/Q5. Esse protocolo ainda não está presente neste checkout.

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

## Memória

O `./install.sh --only codex` mantém o MCP do ai-memory via `mcp-bridge`, com backup (Python >= 3.11; `--no-mcp` pula essa configuração).

- O `./install.sh` registra SessionStart no Claude e no Codex (Python >= 3.11). No Codex, depois da instalação, abra `/hooks` → trust. O ai-memory deve estar instalado e continuar em modo allowlist: sem marcador válido, não captura.
- Em repositórios dentro das raízes de `config/ai-os-memory.toml`, o hook cria `.ai-memory.toml` local, ignora-o no Git e exclui o checkout do Claude-Mem. Preserva marcadores existentes. Worktrees herdam a classificação do checkout principal; SEPLAN/SGG usam workspace `restrito`, os demais `pessoal`. O projeto é derivado pelo ai-memory, sem nome fixado no marcador.
- Sem Git, a raiz do projeto é o segundo nível abaixo da raiz configurada (ex.: `~/Workspace/projetos/sgg-controle` ou `~/Workspace/seplan/ats`), mesmo abrindo uma subpasta. A raiz e as categorias (`projetos`, `seplan`) são ignoradas. No Paseo, só Git é aceito. Um subrepositório herda o marcador ancestral do projeto, sem duplicá-lo.
- O aviso de projeto restrito orienta a delegação; não bloqueia tecnicamente modelos. Claude/Codex significam assinaturas: Felipe deve conferir e desativar treino nas contas Claude/ChatGPT. Do OpenCode Zen/Console, só os dois IDs gratuitos listados na política estão permitidos.
- Os hooks do Claude rodam em paralelo: o primeiro briefing pode exigir abrir outra sessão após criar o marcador. O instalador preserva os hooks do ai-memory; marcadores existentes também mantêm sua configuração de briefing.
- Ao terminar uma sessão, o agente deixa uma nota de estado; o próximo recebe o handoff sozinho.
- Algo antigo que o ai-memory não sabe: a skill `memory-backfill` busca no Claude-Mem, confere e grava.

## Sessões e contexto (ADR-0004)

Uma sessão por objetivo. O chat é descartável; o estado fica no STATUS, nos ADRs e no ai-memory. Protocolo completo e contingências: `GESTAO-CONTEXTO.md`. A skill `sessao` executa cada etapa: peça "abrir sessão", "encerrar sessão", "recuperar sessão que caiu" ou "destilar este chat".

- **Abrir:** o handoff chega sozinho. Leia o STATUS do checkout canônico e confira a branch (`git worktree list`).
- **Durante:** registre cada decisão na hora, como linha no STATUS ou rascunho de ADR. Mande exploração pesada para subagente.
- **Encerrar** quando: o objetivo acabar, o assunto mudar, houver mais de duas correções falhas no mesmo problema, vier uma pausa longa ou o contexto passar de ~200k tokens (alerta experimental). Antes de sair, atualize só a sua frente no STATUS e escreva a nota de estado.
- **Sessão caiu sem handoff:** `memory_briefing` → `memory_read_session_observations` da sessão → `git status`/`diff`/`log` → STATUS.

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
