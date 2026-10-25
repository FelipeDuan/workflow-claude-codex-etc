# Felipe AI OS: uso diário

## Começar

1. Abra o **Paseo** (app). Ele sobe o daemon sozinho em `127.0.0.1:6767`.
2. Escolha o projeto e crie a tarefa com o provedor certo (ver "Quem faz o quê").
3. Para trabalho em paralelo, peça um **worktree novo** por agente que vai escrever.
4. Aprove permissões pelo app, ou pela CLI: `paseo permit ls` e `paseo permit allow <agente> <id>`.

Sem o app, tudo continua funcionando pelo terminal: `claude`, `ai-memory run codex`, `opencode`.

## Quem faz o quê (ADR-0002, consultivo)

| Tarefa | Primeira escolha | Revisor |
|---|---|---|
| Risco alto (segurança, auth, dados, arquitetura) | Claude Opus ou Codex (GPT-6 Astra) | outra família |
| Risco médio | Codex (Luna/Sol) ou Claude Sonnet | quando o diff for grande |
| Risco baixo e com teste | OpenCode gratuito (GLM-5.3-Flash / DeepSeek V4.1 Flash) | conferir testes e diff |
| Dados de SEPLAN/clientes | somente `allowed_models` em `config/ai-os-memory.toml`; conferir treino das contas | — |

Antes de escolher, olhe a franquia:
- Claude: barra de status (`Claude 5h X% · sem Y%`) ou `~/.local/state/ai-os/quota/claude.json`.
- Codex: `python3 ~/Workspace/tools/workflow-ai/scripts/quota_codex.py`.
- No Paseo: `paseo usage`.

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
paseo run --provider codex --new-workspace worktree --worktree-slug <nome> "<tarefa>"   # agente novo em worktree próprio
paseo run --provider opencode/opencode/deepseek-v4.1-flash-free --new-workspace worktree "<tarefa>"
paseo ls                     # agentes (atenção: "running" pode ser espera de aprovação)
paseo wait <id>              # mostra se está esperando aprovação ou terminou
paseo logs <id>              # o que o agente fez
paseo delete <id>            # encerra e apaga o agente
ai-memory run codex          # continuar de onde o último agente parou (terminal)
ai-memory run --fresh codex  # tarefa nova no Codex (terminal)
```

## Vigia dos agentes do Paseo

O `paseo_watchdog` roda a cada 30 s pelo LaunchAgent e responde a pergunta "algum agente precisa de mim agora?". Ele lê `paseo ls -a --json`, `inspect`, `permit ls` e os agendamentos, e calcula o estado real de cada agente:

| Estado | Critério |
|---|---|
| `aguardando_aprovacao` | pedido em `permit ls` pendente há mais de 2 min |
| `parado` | `running` com `UpdatedAt` do inspect há mais de 10 min (sem atividade) |
| `erro` | status `error` (mostra a mensagem, inclusive limite de uso com horário) ou `closed` no meio de uma execução |
| `concluido` | `idle`/`closed` normal |
| `trabalhando` | `running` com atividade recente |

Quando algum agente entra em `aguardando_aprovacao`, `parado` ou `erro`, chega uma notificação do macOS. A mesma notificação não repete por 10 min.

A autoaprovação segue `config/paseo-watchdog-policy.toml`, versionada no repo. As regras são ordenadas e valem por nome da ferramenta e regex da descrição. `allow` só aprova leitura/inspeção dentro de `~/.paseo/worktrees` ou de um repo listado em `allowed_roots`; `.env`, segredos, backups, planilhas, `rm -rf`, instalação de pacotes, migração, docker e download com escrita caem em `deny` (nunca aprovam sozinhos). Perguntas e todo o resto viram `notify`. Projeto restrito em `config/ai-os-memory.toml` nunca é autoaprovado.

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

## Configuração local do Paseo (já aplicada)

```sh
paseo daemon config set agents.providers '{"opencode":{"command":["/Users/felipe/.opencode/bin/opencode"]}}'
paseo daemon config set features.dictation.enabled false
paseo daemon config set features.voiceMode.enabled false
paseo daemon restart
```

Não instalar o plugin Continuity (ver `AUDITORIA-CONTINUITY.md`). Não ligar o relay nem expor a porta sem decidir antes (Tailscale é o caminho preferido para o celular).

## Quando algo der errado

Veja `INCIDENTES.md`: cada problema conhecido tem um contorno. Se for novo, registre lá.
