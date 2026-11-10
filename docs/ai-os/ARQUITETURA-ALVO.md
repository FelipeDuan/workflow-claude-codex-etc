# AI OS: arquitetura-alvo e plano de reestruturação

**Data:** 09/11/2026 · **Base:** v0.2.2 · **Estado:** proposta para debate (não é ADR aceita)

Este documento responde à pergunta "como deixar o AI OS sólido, profissional e correto, mesmo que seja preciso refazer". Ele parte do que a v0.1–v0.2.2 mostrou na prática, não de preferência estética.

## 1. Diagnóstico honesto da v0.2.2

**O que já está certo e deve ser preservado**
- Cultura de evidência: protocolo GQM, contrato de dados com `unknown`, baseline reprodutível, incidentes com análise de causa.
- Revisão cruzada por outra família: achou defeitos reais em todas as entregas de código do dia.
- Política de roteamento canônica com preflight testado por incidente (ADR-0007).
- Ledger de tarefas com veredito honesto (`retrabalho` conta).
- ~305 testes, fixtures reais para saídas de sistema.

**O que não aguenta crescer**

| # | Problema | Evidência |
|---|---|---|
| 1 | Produção roda de um checkout git mutável | O launchd executa `workflow-ai/scripts/paseo_watchdog.py`; qualquer edição ou checkout nessa árvore muda o vigia em produção na hora |
| 2 | Scripts monolíticos com importação cruzada | `paseo_watchdog.py` (>1.000 linhas) faz polling, permissões, quota, histórico, transições, agendamento de higiene e resíduos; `hygiene.py` e `ai_os_task.py` importam funções internas dele |
| 3 | Estado espalhado em formatos diferentes | `watchdog-state.json`, `agentes.json`, `quota/*.json`, `history/*.jsonl`, ledger, `telemetria.jsonl` legado, `arquivo-agentes/`, STATUS.md, ai-memory |
| 4 | Integração por parsing de CLI e polling | `paseo ls/inspect`, `ps`, `lsof`, `top`: formatos mudam (locale, flags), sandbox bloqueia (EPERM), fixtures inventadas passaram nos testes |
| 5 | Dois Pythons | 3.9 do sistema pula ~90 testes; 3.14 do Homebrew roda tudo; o launchd depende do caminho certo |
| 6 | Sem CI, sem checagem de tipos, sem lint | Bugs que um type checker pega chegaram à revisão cruzada, que é cara |
| 7 | O maior custo é retrabalho dos agentes | 5 de 6 entregas do dia precisaram de 1–3 rodadas de correção; as instruções dos agentes vivem em prompts longos escritos na hora |
| 8 | Privacidade aplicada em vários lugares | Mascaramento de projeto restrito reimplementado em métricas, higiene, ledger e vigia |
| 9 | Documentação cresce por acúmulo | STATUS.md tem centenas de linhas de histórico; mais de 20 docs em `docs/ai-os/`; a retomada depende de ler tudo |
| 10 | Dependências externas sem fronteira | Paseo, ai-memory, Codex e Claude chamados diretamente de vários pontos |

## 2. Princípios da arquitetura-alvo

1. **Núcleo pequeno, fronteiras explícitas.** Um pacote com módulos de responsabilidade única; adaptadores isolam cada ferramenta externa.
2. **Dados primeiro.** Um modelo de domínio (Task → Attempt → Agent → Resource) e um log de eventos append-only como fonte; todo estado "atual" é derivado e reconstruível.
3. **Produção imutável.** O que roda é uma release instalada, não a árvore em que se edita.
4. **Determinismo no controle, LLM só para julgamento.** Políticas, verificações e limpeza são código testado; modelos executam e revisam.
5. **Toda verificação contra o mundo real.** Fixtures capturadas do sistema, testes de contrato por adaptador, verificação pelo orquestrador fora do sandbox.
6. **Migrar por estrangulamento, nunca reescrever de uma vez.** Cada passo preserva comportamento, provado pelos mesmos testes e por replay de eventos reais.
7. **Linguagem: Python.** O custo está em comandos externos, disco e franquia, não em CPU. Rust só se surgir um daemon com orçamento medido estourado.

## 3. Arquitetura-alvo

```text
┌──────────────── superfícies ────────────────┐
│ CLI `ai-os`  · skills (sessao, orquestração)│
│ status line  · hooks Claude/Codex           │
└──────────────────────┬──────────────────────┘
                       │ chamam só a CLI/biblioteca
┌──────────────── núcleo `aios` ──────────────┐
│ domain   Task/Attempt/Agent/Resource, estados│
│ events   writer único + schema + leitura incremental│
│ store    paths, escrita atômica, locks, retenção│
│ policy   roteamento + preflight (funções puras)│
│ privacy  classificação restrita + redação (único ponto)│
│ health   sessão, recursos, órfãos (regras puras)│
└──────────────────────┬──────────────────────┘
┌──────────────── adaptadores ────────────────┐
│ paseo · codex · claude · opencode · ai-memory│
│ procs(ps/lsof/top, LC_ALL=C) · git · macos(pmset, sysctl)│
│ cada um: interface tipada + fixtures reais + teste de contrato│
└──────────────────────┬──────────────────────┘
┌──────────────── supervisor ─────────────────┐
│ um processo launchd; coletores independentes │
│ com intervalo e orçamento próprios:          │
│ agentes 30 s · quota 5 min · higiene 6 h ·   │
│ transcripts (ingestão incremental) 15 min    │
│ coletores → eventos → snapshot derivado →    │
│ regras de alerta (só em transição)           │
└──────────────────────────────────────────────┘
```

**Modelo de dados.** Um evento por fato, com contrato GQM. `tasks`, `agents`, `resources` e `quota` atuais são projeções reconstruíveis do log. O JSONL mensal continua sendo a fonte; um índice SQLite opcional e descartável entra só se as consultas ficarem lentas (medir antes).

**Supervisor no lugar do vigia monolítico.** Cada coletor é uma função `collect(ctx) -> list[Event]` com timeout e orçamento. As regras de alerta e de aprovação de permissão consomem eventos e são testadas por replay de logs reais. Processos que o supervisor cria têm dono, prazo e limpeza garantida (lição do I-35).

**Ingestão incremental.** Transcripts do Claude e sessões do Codex são lidos uma vez, com cursor por arquivo (offset e mtime). O relatório lê eventos, não 2,2 GB de transcripts.

**Produção imutável.** `ai-os` é instalado como pacote versionado (`uv tool install` de uma tag) em `~/.local/share/ai-os/releases/<versão>`, com o launchd apontando para `current`. Upgrade instala a tag nova e troca o link; rollback volta o link. O checkout de desenvolvimento nunca é o que roda.

## 4. Engenharia de qualidade

| Item | Padrão |
|---|---|
| Runtime | Python ≥3.12 fixado com `uv` (um interpretador para launchd, testes e CLI) |
| Testes | pytest; unidade nas regras puras; contrato por adaptador com fixtures capturadas por `ai-os dev capture-fixtures`; replay de logs reais para supervisor e alertas; integração em HOME temporário |
| Estático | ruff + mypy strict no núcleo |
| CI | GitHub Actions em runner macOS: lint, tipos, testes, consistência da política, varredura de segredos e de dados restritos |
| Releases | SemVer, CHANGELOG.md, checklist de release, `ai-os doctor` como smoke test pós-instalação |
| Instalação | `install.sh`/`harden.py` viram `ai-os setup --check/--apply`, com diff do que muda em cada arquivo do usuário e backup automático |

## 5. Processo de trabalho com agentes (o maior retorno)

O retrabalho dos agentes custa mais que qualquer ineficiência de código. A estrutura proposta:

1. **Templates de tarefa versionados** (`templates/tasks/`): objetivo, arquivos sob posse, proibições, critérios de aceite como comandos executáveis, passo obrigatório de verificação com dado real e formato do relatório final.
2. **Definition of Done por risco**: baixo (testes + diff), médio (+ revisão cruzada), alto (+ revisão independente + verificação manual).
3. **Verificação do orquestrador codificada**: rodar a suíte, rodar contra o ambiente real fora do sandbox, conferir números relatados. Hoje isso depende de disciplina; vira checklist da skill e evento no ledger.
4. **Métrica de retrabalho por executor e por tipo de tarefa** no relatório, para o roteamento aprender com dados (ex.: Codex errou mais em código de sistema, acertou em docs).

## 6. Documentação

- `STATUS.md` volta a ser uma página: estado atual, decisões em vigor, próximo passo. O histórico vai para `CHANGELOG.md` e `docs/history/`.
- Índice de ADRs e um mapa de documentos; lint de links e de consistência no CI.
- Uma página durável no ai-memory por decisão nova, no encerramento da sessão.

## 7. O que remover ou congelar

- `telemetria.jsonl` manual: congelar como legado (o ledger substitui).
- claude-mem: desinstalar após o período de observação (backup existe).
- Restos do Antigravity: manter só o sensor manual.
- Auditar as ~40 skills e 11 agentes: uso real, sobreposição, custo de contexto (a lista de skills é o maior bloco fixo de cada sessão).
- OpenCode free: manter só para tarefas descartáveis; decidir com os dados de retrabalho.

## 8. Plano em fases (estrangulamento)

| Fase | Entrega | Critério de aceite |
|---|---|---|
| 0 | 1–2 semanas de baseline sem funcionalidade nova | relatórios semanais gerados; incidentes registrados |
| 1 Fundação | `uv` + Python fixado, pacote `aios` vazio, CLI `ai-os` delegando aos scripts atuais, CI, ruff/mypy, ferramenta de captura de fixtures, modelo de release com `current` | tudo verde; comportamento idêntico; launchd rodando de release instalada |
| 2 Núcleo | `store`, `events`, `privacy`, `procs`, `git` extraídos; scripts passam a usá-los | mesmos testes + replay de eventos reais idênticos |
| 3 Supervisor | vigia vira supervisor com coletores; alertas por regra | replay: mesmas transições, mesmas notificações, mesmas aprovações de permissão |
| 4 Experiência | Session Health (skill `sessao` + status line), `ai-os setup`, STATUS enxuto | falso "pode fechar" = 0 nos cenários de teste |
| 5 Processo | templates de tarefa, DoD, retrabalho por executor no relatório | retrabalho medido por 2 semanas |
| 6 Experimentos | EXP-002, wake lease, Gemini API, Apple FM | cada um com pré-registro |

Cada fase é uma ou mais branches pequenas, com revisão cruzada e release própria. O risco principal é a fase 3 (o vigia aprova permissões): só migra com replay de logs reais provando equivalência.

## 9. O que eu não faria

- Reescrever em Rust ou em outra linguagem.
- Construir um daemon novo, um banco remoto, um dashboard web ou um barramento de mensagens.
- Trocar o Paseo antes de isolá-lo atrás de um adaptador e medir.
- Big bang: congelar tudo por semanas para entregar uma v1 nova.
