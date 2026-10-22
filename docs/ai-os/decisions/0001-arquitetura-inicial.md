# ADR-0001 — Ambiente multiagente inicial

**Status:** proposta aprovada como experimento, ainda não comprovada na máquina do usuário.

## Contexto

O usuário quer continuidade de tarefas Claude→Codex→OpenCode, baixo custo, controle de contexto e múltiplos projetos em paralelo, sem criar uma segunda plataforma de engenharia desnecessária.

## Decisão

Começar com Paseo Desktop como cockpit, CLIs oficiais existentes, AI-Memory v3.x em modo opt-in e conhecimento durável no repositório. Usar skill de handoff e teste de worktrees. Avaliar Continuity somente após auditoria e aprovação. Nada de gateway/proxy/DB extra nesta prova de conceito.

## Alternativas

- Orca: candidato válido caso Paseo não cumpra critérios de estabilidade e integração.
- Orquestrador próprio: adiado, fazer somente a lacuna mensurada.
- LiteLLM: adiado até existirem múltiplos custos por API e necessidade de budget tracking.

## Consequências

A continuidade manual fica demonstrável primeiro. Failover de quota real permanece hipótese de integração até evidência prática. Privacidade e segurança exigem escopo pessoal e consentimento.
