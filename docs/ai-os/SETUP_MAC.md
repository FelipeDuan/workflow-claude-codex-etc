# Instalação rápida no Mac M4 (fish)

Este documento serve de referência para o Claude executar o setup; não rode tudo indiscriminadamente.

## 1) CLIs nativas

Cheque antes: `command -v claude`, `command -v codex`, `command -v opencode`, `command -v paseo`, `command -v ai-memory`.

Se não estiverem instaladas, as fontes oficiais indicam:

```fish
# Claude Code — método nativo, leia antes o script de instalação:
# https://code.claude.com/docs/en/setup
# curl -fsSL https://claude.ai/install.sh | bash

# Codex CLI — escolha APENAS uma forma:
# npm install -g @openai/codex@latest

# OpenCode — escolha APENAS uma forma; verifique se o nome mudou na versão vigente:
# brew install anomalyco/tap/opencode-v2
# ou npm install -g @opencode/cli

# Paseo: recomendamos app Desktop em https://paseo.sh/download
# alternativa CLI para servidores: npm install -g @getpaseo/cli
```

Depois, faça login pelas CLIs `claude`, `codex` e `opencode`; não cole credenciais em textos de handoff. Em OpenCode use `/connect` para NVIDIA **somente se usuário aprovar e projeto for pessoal compatível com termos de tratamento de dados**; `/models` lista modelos reais. Evite integrações não autorizadas que reutilizem credenciais Claude Pro fora das ferramentas oficialmente suportadas.

## 2) Paseo Desktop

Baixe o instalador oficial em https://paseo.sh/download e abra o app. **Não precisa de daemon CLI separado**, pois o Desktop o inclui. Confira detecção das três CLIs em https://paseo.sh/docs/providers. Use worktrees distintos para tarefas independentes. Comece com uma única tarefa, depois duas.

Handoff: a documentação recomenda instalar `/paseo-handoff` pelo painel de Orchestration skills e usar essa skill para transferir tarefas. Não presumir que handoff manual equivale a failover automático.

## 3) AI-Memory v3.x

O projeto publicou **v3.1.0 em 16/10/2026**. A instalação deve seguir o guia oficial atual, não instruções antigas da v2.0. O projeto oferece instalador nativo com checksum. Caminho de revisão:

```fish
# apenas download — inspecione a origem ANTES de executar
curl -fsSLO https://github.com/akitaonrails/ai-memory/releases/latest/download/install.sh
curl -fsSLO https://github.com/akitaonrails/ai-memory/releases/latest/download/install.sh.sha256
shasum -a 256 -c install.sh.sha256
less install.sh
# Após aprovação explícita:
# sh install.sh
# fish_add_path ~/.local/bin
# ai-memory setup --plan
# ai-memory setup --web
```

O setup pode instalar hooks globais para vários agentes; confirme a política de **capture allowlist** antes de permitir coleta. A versão mais recente possui marketplace plugins e `ai-memory doctor`. Consulte https://github.com/akitaonrails/ai-memory/blob/main/docs/install.md e https://github.com/akitaonrails/ai-memory/blob/main/docs/macos.md para flags suportadas pela release instalada. O serviço local deve ficar em loopback com autenticação habilitada.

## 4) Continuity (NÃO instalar antes de auditar)

Em https://paseo.sh/plugins/keefeere/continuity há um plugin comunitário que detecta erro de quota/rate limit e inicia nova sessão no próximo provedor. Ele recebe histórico resumido; **não transfere raciocínio interno** nem prova restauração exata. A documentação do Paseo informa que plugins possuem acesso unsandboxed ao usuário do daemon. Auditoria e aprovação obrigatórias. Em caso de aprovação, o comando listado é:

```fish
# Somente depois de revisar o código-fonte e aprovar:
# paseo plugin add keefeere/continuity
```

Não ativar retorno ao provider principal durante uma tarefa em andamento. Não gerar tarefas duplicadas quando a falha foi ambígua.
