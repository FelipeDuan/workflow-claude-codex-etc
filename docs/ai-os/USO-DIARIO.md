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
| Dados de SEPLAN/clientes | nenhum provedor sem acordo | — |

Antes de escolher, olhe a franquia:
- Claude: barra de status (`Claude 5h X% · sem Y%`) ou `~/.local/state/ai-os/quota/claude.json`.
- Codex: `python3 ~/Workspace/tools/workflow-ai/scripts/quota_codex.py`.
- No Paseo: `paseo usage`.

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

## Memória

- Projeto com memória compartilhada: `.ai-memory.toml` na raiz (`workspace` + `project`) e o caminho na exclusão do Claude-Mem (`CLAUDE_MEM_EXCLUDED_PROJECTS`). Os worktrees do Paseo já estão excluídos.
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
