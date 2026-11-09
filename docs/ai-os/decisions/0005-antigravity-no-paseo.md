# ADR-0005: Antigravity CLI (Gemini) como executor do Paseo

**Status:** Aceito em 2026-11-09 por Felipe, como recomendado. O uso continua sob as restrições abaixo.

## Contexto

O ADR-0003 adotou o Paseo contando com o portão de aprovação dos harnesses: shell e escrita pedem permissão, e o vigia só autoaprova pelo `config/paseo-watchdog-policy.toml`. O provider `antigravity` do Paseo 0.14.0 não tem esse portão. Ele expõe um único modo, `full-access`, e sempre inicia o `agy` com `--dangerously-skip-permissions`, porque o `agy` não consegue perguntar nada quando outro programa o controla. Fonte: `/Applications/Paseo.app/Contents/Resources/builtin-plugins/antigravity-provider/server/internal/{catalog,process}.ts`.

Mitigação disponível e testada em 09/11: o override `agents.providers.antigravity.command = ["/opt/homebrew/bin/agy", "--sandbox"]` em `~/.paseo/config.json`. O Paseo coloca esses argumentos antes dos dele, então todo agente roda com o sandbox de terminal do `agy`. No teste, `ls ~/.ssh` falhou com `Operation not permitted` e a escrita no worktree funcionou. Pelo changelog do `agy`, sob `--dangerously-skip-permissions` os comandos da denylist do sistema continuam bloqueados, e as regras de negação explícitas continuam valendo.

O worktree do Paseo não isola o host: o agente continua com o usuário e o HOME do Felipe. O `--sandbox` só cobre o terminal; ferramentas nativas de arquivo, rede e chamadas MCP não foram comprovadas como restritas (o `ls ~/.ssh` bloqueado não prova isolamento geral). O changelog diz que, com o flag, leituras e escritas fora do workspace "go through without a prompt".

## Decisão

1. Não despachar o Antigravity pelo Paseo como rotina. Uso via Paseo só para tarefa de risco baixo, em repo sem segredos, em worktree novo (`--new-workspace worktree --base <branch>`), com revisão do diff pelo orquestrador. Nunca no checkout principal.
2. Nunca em projeto restrito (`config/ai-os-memory.toml`); ele não entra em `allowed_models` sem decisão explícita do Felipe.
3. O override com `--sandbox` é obrigatório para esse uso (reduz o risco no terminal, não o elimina). Sem ele, não despachar.
4. Preferir modelos `gemini-*`. Os modelos Claude oferecidos pelo `agy` rodariam com bypass de permissões, o que contraria a regra de nunca usar bypass no Claude.
5. Para revisão e segunda opinião cross-family, usar o `agy` direto, somente leitura e sem bypass: `agy --mode plan --model gemini-4-argon-low -p "<pergunta>"` no diretório do repo. Teste de 09/11 em `MODELOS_2026.md`: respondeu sem pedir permissão e não escreveu no workspace.

## Consequências

- Ganha uma família de modelos a mais para segunda opinião e tarefas baratas, com captura no ai-memory.
- Perde o portão humano por ação. O controle passa a ser sandbox de terminal, worktree (organização, não isolamento) e revisão posterior.
- A franquia do Antigravity não aparece em `paseo usage`; para o roteamento, ler `~/.local/state/ai-os/quota/antigravity.json` (sensor escrito pelo vigia a cada 5 min). Ausente, velho ou com erro é `unknown`.

## Revisar se

- O Paseo ganhar um modo com aprovação para o Antigravity, ou o `agy` passar a responder permissões por ACP no provider.
- Algum agente Antigravity agir fora do worktree.

## Rollback

Desabilitar o provider antes de remover o override: `agents.providers.antigravity.enabled = false` (mantendo o `command` com `--sandbox`) + `paseo reload`, e conferir `paseo provider ls`. Remover só o `--sandbox` deixaria o provider ativo com bypass total.
