# Protocolo de medição do AI OS (GQM v1)

**Versão:** `metric_definition_version = 1` · **Data:** 09/11/2026 · **Estado:** aceito para a fase de baseline

Este documento define o que o AI OS mede, por que mede e como cada número deve ser lido. Ele vem antes da coleta: nenhum coletor novo entra no repo sem apontar para uma pergunta daqui.

Referências do debate que originou o protocolo: RFC consolidada v2 e contraproposta do GPT (fora do repo), parecer do Claude de 09/11/2026 e `docs/ai-os/BASELINE-2026-11-09.md`.

## 1. Enquadramento

O AI OS é um artefato em construção, e a pergunta de fundo é se ele melhora o trabalho. Usamos três referências, cada uma com um papel:

- **Design Science Research** (Hevner et al., 2004; Peffers et al., 2007) para o ciclo do artefato: problema, objetivos, construção, demonstração, avaliação. Estamos na fase de instrumentação. Nada aqui declara o artefato validado.
- **GQM** (Basili, 1992) para a medição: objetivo, pergunta, métrica. Métrica sem pergunta não é coletada.
- **Experimentação em engenharia de software** para hipóteses causais, mais tarde. A observação do uso real não prova causa.

## 2. Fases

| Fase | Duração | O que permite afirmar |
|---|---|---|
| Baseline observacional | 2 a 4 semanas após o P1 e o P2 | Tendências, taxas de falha, problemas de instrumentação. Não permite atribuir causa |
| Experimentos pequenos | Depois da baseline | Efeito de uma mudança específica, com pré-registro (seção 7) |
| Estudo comparativo A/B/C | Só se os anteriores indicarem valor | Comparação entre arquiteturas em tarefas equivalentes |

## 3. Contrato mínimo de dados

Todo registro novo (JSONL, uma linha por registro) tem estes campos:

| Campo | Regra |
|---|---|
| `schema_version` | inteiro; começa em 1 |
| `type` | ex.: `quota.sample`, `agent.transition`, `task.opened`, `task.closed` |
| `occurred_at` | UTC ISO 8601, quando o fato aconteceu (ou `null` se desconhecido) |
| `observed_at` | UTC ISO 8601, quando o coletor viu |
| `source` / `source_version` | quem gerou (ex.: `watchdog`, `ai-os-task`) e versão |
| `confidence` | `observed`, `estimated` ou `unknown` |
| `task_id` | ID da tarefa ou `null`; agentes sem tarefa ficam `unlinked` |
| `agent_id`, `provider`, `model` | quando houver; modelo é o observado, nunca inferido |
| `reason` | obrigatório quando algum valor é `unknown` |

Regras que valem para todos os registros:

- Valor desconhecido é `null` com `reason`, nunca 0.
- Sem prompts, respostas, trechos de código, e-mails ou caminhos completos. Projeto em caminho restrito aparece como `restrito`.
- Registros são só de acréscimo. Correção vira um registro novo, não edição.
- Dados brutos ficam fora do Git, em `~/.local/state/ai-os/`. No repo entram scripts, definições e agregados revisados.

## 4. Perguntas e métricas

### Q1. As tarefas delegadas saem aceitas sem retrabalho?

| Métrica | Fórmula | Fonte |
|---|---|---|
| Aceite na primeira entrega | tarefas `aceito` sem relançamento ou retrabalho ÷ tarefas com veredito | `task.closed` (P2) |
| Cobertura de avaliação | tarefas com veredito ÷ tarefas abertas no período | `task.opened` / `task.closed` |
| Taxa de retrabalho | tarefas `retrabalho` ÷ tarefas com veredito | `task.closed` |

**Leitura:**
- Sempre publicar a cobertura ao lado da taxa. Se poucas tarefas recebem veredito, a taxa não diz nada.
- `closed` ou `idle` de agente nunca conta como aceite.
- Mudança de escopo pedida pelo Felipe não é retrabalho do agente.

### Q2. A franquia bloqueia menos e dura mais?

| Métrica | Fórmula | Fonte |
|---|---|---|
| Trajetória do pool | série de `used_percent` por provedor, pool e janela | `quota.sample` (P1) |
| Saturações | tentativas encerradas por limite de uso ÷ 100 tentativas | `agent.transition` com motivo de limite (P1) |
| Tempo indisponível | minutos com pool ≥ 95% enquanto havia agente esperando | `quota.sample` + `agent.transition` |

**Leitura:**
- Percentuais de provedores diferentes não se somam nem se comparam como se fossem a mesma moeda.
- Delta de quota só é atribuído a uma tarefa quando ela rodou sozinha naquele pool entre duas leituras e não houve reset no meio. Com agentes simultâneos, o delta é do pool e fica `unallocated`.
- Tokens não são franquia. Servem para explicar o mix, não para medir economia.

### Q3. Quanto custa a coordenação?

| Métrica | Fórmula | Fonte |
|---|---|---|
| Agentes por tarefa | agentes com `label task=<id>` ÷ tarefas | Paseo + `task.*` |
| Relançamentos por tarefa | agentes além do primeiro com o mesmo papel | idem |
| Proxy de interação | soma dos intervalos entre mensagens do Felipe na sessão, com corte de 10 min de silêncio | transcripts do Claude Code (`confidence: estimated`) |

**Leitura:**
- O proxy de interação (`interaction_time_proxy`) não mede esforço humano. Ele não sabe se o intervalo foi revisão, estudo ou café. Não pode sustentar sozinho uma afirmação de produtividade. Pode ser calibrado mais tarde, com amostras cronometradas voluntárias.
- Subagentes nativos do Claude não recebem `task_id` na v1. Ficam como `unlinked`, e a cobertura do vínculo é publicada.

### Q4. O AI OS é confiável?

| Métrica | Fórmula | Fonte |
|---|---|---|
| Falha técnica por tentativa | agentes que terminaram em `error` ÷ agentes com estado final conhecido | `agent.transition` |
| Esperas longas | entradas em `waiting_permission` por mais de 10 min | `agent.transition` |
| Incidentes recorrentes | ocorrências por causa (`I-xx`) no período | `INCIDENTES.md` |

**Leitura:** o número de IDs de incidente não é taxa de falha. Conta-se a recorrência por causa.

### Q5. O AI OS pesa no Mac?

| Métrica | Fórmula | Fonte |
|---|---|---|
| Disco por classe | bytes em worktrees, logs, estado e caches do AI OS | inventário (P0b, depois P4) |
| Custo do coletor | tempo por ciclo do vigia e bytes gravados por dia | auto-medição do vigia (P1) |

**Leitura:** RAM usada pelo macOS não é sinal sozinha. Pressão de memória e swap sustentado são.

### Q6. A retomada preserva as decisões? (entra no P5)

| Métrica | Fórmula | Fonte |
|---|---|---|
| Fidelidade de retomada | fatos e decisões recuperados corretamente ÷ fatos verificados, em testes controlados | teste de retomada |

## 5. O que não é métrica principal

Commits por dia, tokens totais, número de agentes ou de skills, quantidade de notificações e participação de cada modelo no consumo. Esses números descrevem atividade. Podem aparecer como contexto, nunca como prova de melhora.

## 6. Ameaças à validade conhecidas

- **Mix de tarefas muda de semana para semana.** Comparar períodos não isola o efeito do workflow.
- **O próprio orquestrador escolhe o que vira tarefa.** Isso cria viés de seleção na cobertura.
- **Modelos e quotas mudam sem aviso.** Toda série registra a versão observada e a data.
- **Mac em repouso cria lacunas.** Lacuna é marcada, nunca interpolada.
- **Baseline anterior a 09/11 é retroativa** (scripts sobre transcripts). Tem as limitações descritas em `docs/ai-os/BASELINE-2026-11-09.md`.

## 7. Pré-registro de experimentos

Antes de qualquer experimento, criar `docs/research/experimentos/<id>.md` com:
- pergunta e hipótese;
- métrica primária;
- tarefas incluídas e critério de inclusão;
- baseline e versões (commit, modelos, política);
- regra de parada;
- plano de análise;
- ameaças à validade.

Resultado negativo ou inconclusivo é registrado do mesmo jeito.

## 8. Mudanças neste protocolo

Mudar uma fórmula incrementa `metric_definition_version`. Períodos medidos com versões diferentes só se comparam depois de documentar a equivalência. A revisão do protocolo acontece no fim da baseline observacional.
