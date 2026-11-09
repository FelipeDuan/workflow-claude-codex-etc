# ADR-0007: Política canônica e preflight consultivo

Status: Aceita 2026-11-09

## Contexto

A política de roteamento se repetia na ADR-0002, no JSON, na skill e nos guias, com divergências. Parâmetros omitidos também causavam lançamentos na branch, no modelo ou no modo incorreto.

## Decisão

`docs/ai-os/roteamento.json`, schema 3 e `policy_version 2026-11-09.1`, é a fonte canônica executável. A ADR-0002 preserva a justificativa e o histórico. A lista de projetos restritos e `allowed_models` permanece em `config/ai-os-memory.toml`.

Antes de lançar um agente, o orquestrador executa `scripts/preflight.py`. A função pura `decide` avalia dados e segurança, parâmetros explícitos, franquia e concorrência, nessa ordem. A CLI coleta as evidências e devolve `allow`, `ask_human` ou `deny`; nunca inicia agentes. Risco alto mantém seu piso de qualidade mesmo com franquia limitada.

## Consequências

Mudanças de regra exigem alterar o JSON, sua versão e os testes. Os guias apontam para essa fonte. Testes verificam incidentes, fronteiras de franquia e consistência documental. Leituras ausentes ou vencidas exigem decisão humana; Astra exige dados válidos. A exceção já prevista para tarefa curta perto do reset permanece vigente em `quota.reset_exception`, mediante `--short-task` e `resets_at` válido. Ela só se aplica à janela de cinco horas; o limite semanal e a concorrência continuam valendo.

O resultado é consultivo: não intercepta chamadas diretas ao Paseo e não reserva concorrência entre duas consultas simultâneas. O orquestrador deve respeitar o resultado e conferir novamente antes de lançar. IDs de modelos ainda precisam ser confirmados no host. As opções de simulação (`--policy`, `--restricted-config`, `--quota-dir`, `--agents-file`, `--now`) são entradas controladas pelo operador: este comando consultivo não constitui uma fronteira de segurança. Classes de dados, revisão por outra família, ordem de revisores e limite de fallback seguem como deveres do orquestrador documentados no JSON, sem fiscalização pelo preflight.

## Rollback

Reverta em conjunto o preflight, o JSON e os apontamentos documentais para a revisão anterior. Até a revisão da política, suspenda lançamentos que dependam dessa validação; não trate uma falha de leitura como permissão.
