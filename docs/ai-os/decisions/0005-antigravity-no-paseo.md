# ADR-0005: Antigravity CLI (Gemini) como executor do Paseo

**Status:** Proposto, aguarda Felipe (rascunho de 09/11/2026). Até a aceitação, o uso segue as restrições abaixo e vale como experimento.

## Contexto

O ADR-0003 adotou o Paseo contando com o portão de aprovação dos harnesses: shell e escrita pedem permissão, e o vigia só autoaprova pelo `config/paseo-watchdog-policy.toml`. O provider `antigravity` do Paseo 0.14.0 não tem esse portão. Ele expõe um único modo, `full-access`, e sempre inicia o `agy` com `--dangerously-skip-permissions`, porque o `agy` não consegue perguntar nada quando outro programa o controla. Fonte: `/Applications/Paseo.app/Contents/Resources/builtin-plugins/antigravity-provider/server/internal/{catalog,process}.ts`.

Mitigação disponível e testada em 09/11: o override `agents.providers.antigravity.command = ["/opt/homebrew/bin/agy", "--sandbox"]` em `~/.paseo/config.json`. O Paseo coloca esses argumentos antes dos dele, então todo agente roda com o sandbox de terminal do `agy`. No teste, `ls ~/.ssh` falhou com `Operation not permitted` e a escrita no worktree funcionou. Pelo changelog do `agy`, sob `--dangerously-skip-permissions` os comandos da denylist do sistema continuam bloqueados, e as regras de negação explícitas continuam valendo.

O que o sandbox não cobre (não verificado em detalhe): leitura e escrita de arquivos pelas ferramentas do próprio agente fora do terminal, rede e chamadas MCP. O changelog diz que, com o flag, leituras e escritas fora do workspace "go through without a prompt".

## Decisão proposta

1. Antigravity entra como executor só para tarefas de risco baixo ou médio, em worktree isolado do Paseo (`--new-workspace worktree --base <branch>`), nunca no checkout principal.
2. Nunca em projeto restrito (`config/ai-os-memory.toml`); ele não entra em `allowed_models` sem decisão explícita do Felipe.
3. O override com `--sandbox` é obrigatório. Sem ele, não despachar.
4. Preferir modelos `gemini-*`. Os modelos Claude oferecidos pelo `agy` rodariam com bypass de permissões, o que contraria a regra de nunca usar bypass no Claude.
5. Revisão do diff pelo orquestrador antes de integrar, como em qualquer agente.

## Consequências

- Ganha uma família de modelos a mais para segunda opinião e tarefas baratas, com captura no ai-memory.
- Perde o portão humano por ação. O controle passa a ser isolamento (worktree + sandbox) e revisão posterior.
- A franquia do Antigravity não aparece em `paseo usage`; para o roteamento, ela fica `unknown`.

## Revisar se

- O Paseo ganhar um modo com aprovação para o Antigravity, ou o `agy` passar a responder permissões por ACP no provider.
- Algum agente Antigravity agir fora do worktree.
