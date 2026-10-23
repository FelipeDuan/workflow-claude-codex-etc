# Auditoria do plugin Paseo Continuity (keefeere/paseo-continuity v0.2.1, commit 063b7e2)

Auditoria somente leitura em 22/10/2026, feita pelo agente security-reviewer. O código foi clonado como dado não confiável e nada dele foi executado. O orquestrador conferiu por amostragem os padrões em `shared/settings.ts`, a redação em `server/serialize.ts` e o histórico git.

**Veredito:** nenhum código malicioso, rede própria, telemetria ou execução de comandos. Os padrões, porém, são agressivos. **Não instalar como está.** Só com as condições abaixo, e depois de um teste no laboratório.

## Achados

| Sev. | Achado | Evidência |
|---|---|---|
| Alto | Num 429 ou erro de quota, manda até 60k caracteres do transcript (prompts, saída de shell, caminhos, URLs) para OUTRO fornecedor, sem confirmação | `index.server.ts:47`, `failover.ts:162-179`, `serialize.ts:30-64` |
| Alto | O sucessor nasce autônomo; o Codex vem em modo `auto` por padrão | `settings.ts:28-31` |
| Alto | A redação de segredos tem só 7 padrões. Não pega `.env` (`PASSWORD=`), `postgres://u:p@`, chaves privadas, JWT, `sk_live_`. Log, título e card não passam pela redação | `serialize.ts:194-202` |
| Médio | Agente de resumo (opcional) roda completo no cwd, sem restringir ferramentas, e pode disparar failover de si mesmo | `summarize.ts:41-46`, `index.server.ts:29-37` |
| Médio | Falso positivo: `\b429\b` ligado por padrão; texto curto do assistente (prompt injection) pode disparar | `classify.ts:26,57-60` |
| Médio | Handoff em `<cwd>/.paseo/continuity/` persiste, sem limpeza e com 0644 | `handoff-file.ts` |
| Médio | Maturidade: autor único, 5 commits entre 30/09 e 02/10/2026, sem testes do fluxo crítico. Roda sem sandbox com todo o acesso do usuário | git log, `tests/` |
| Baixo | O anti-duplicata e os limites ficam só em memória; sem retorno ao provedor preferido; `failover-now` ignora o cooldown | `state.ts`, `chain.ts`, `failover.ts:216-229` |

## Condições para um eventual uso
1. Versão fixa (commit `063b7e2`), revisando o diff a cada update.
2. `enabled=false`, usando só o `/continuity` manual. Se ligar o automático: `rateLimit=false`, `overloaded=false`, `summary.enabled=false`, `maxSwitchesPerChain=1`, `maxConsecutiveFailovers=1`, sucessor sem auto-approve e orçamento de 4k–15k caracteres.
3. Nunca em pastas com dados institucionais. O ideal é outro usuário do macOS ou outra instância do daemon.
4. `.paseo/` no gitignore global e limpeza periódica.

## Testes de runtime pendentes (laboratório, segredos falsos)
Se o `paseo plugin install` roda `npm install`/devDeps; conexões do daemon (LuLu); disparo com erro real × falso positivo ("linha 429"); o que chega ao sucessor com segredos falsos; idempotência com reinício do daemon; modo efetivo do sucessor.

## Relação com o que já temos
O ai-memory + hook StopFailure + `ai-memory run codex` já fazem o handoff com o estado explícito e sem mandar o transcript bruto para outro fornecedor. O Continuity só acrescentaria o disparo automático do sucessor, que é justamente a parte de maior risco.
