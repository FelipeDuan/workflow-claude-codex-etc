# Retrospectiva do AI OS, 09/11/2026

Base: `telemetria.jsonl`, `paseo ls -a` (80 agentes), `~/.local/state/ai-os/{agentes,quota}`, INCIDENTES e STATUS. Contagens por modelo vêm de nomes de agentes, não de tokens. Não abri o conteúdo dos worktrees; "descartável" é suposição por nome e idade. Não consultei o ai-memory.

## Limite da amostra
- `telemetria.jsonl` tem 18 linhas, todas de 22 a 26/10 (5 de laboratório, 13 de orquestração real). O Paseo registra 80 agentes, quase todos criados depois de 26/10. Taxas abaixo são indicativas.
- Sem commits entre 27/10 e 09/11; o STATUS estava parado em 26/10.

## Achados
- Funcionou: 11 das 13 linhas de orquestração real são `success`. Revisão cruzada de outra família deu valor (Astra revisando proposta do Sol, 4 achados incorporados, linhas 15 e 17). OpenCode free serviu em tarefa pequena e documental (linhas 3 a 5 e 8). `paseo schedule` e o vigia foram validados.
- Limite do Codex derrubando agentes: 3 agentes Astra em `error` por usage limit hoje (`agentes.json`), apesar do sensor de franquia. Já era I-11 e I-23.
- OpenCode free: 2 de 2 falhas por limite de conta (I-29); 5 agentes em `parado_sem_entrega` (I-25); pedido de `curl` pendente há ~5 dias.
- `human_corrections` é 0 em 17 de 18 linhas, mas 5 notas dizem que o orquestrador completou ou relançou a tarefa. O campo não mede retrabalho.
- Incidentes da quinzena não estavam registrados. Hipótese: acontecem e ninguém anota.
- Higiene: 9 agentes `idle` e 8 `error` sem tarefa; `~/.paseo/worktrees` com ~11 GB (70 diretórios) num Mac de 256 GB.
- Antigravity estreou em 09/11 sem telemetria prévia; custo real por modelo é desconhecido (ver `MODELOS_2026.md`).

## Melhorias

Operacional, aplicada nesta rodada
- Registrar a quinzena em INCIDENTES: ocorrências somadas em I-11 e I-25 (sem duplicar linhas).
- STATUS: Antigravity registrado para uso direto de Felipe; provider do Paseo desabilitado conforme ADR-0006.
- Guia histórico de modelos do Antigravity em `MODELOS_2026.md`; a skill de orquestração não oferece esse executor.
- Três linhas de telemetria de hoje, só com valores observados.

Operacional, pendente
- Backfill de telemetria dos agentes desde 26/10 a partir de `paseo ls -a` e `agentes.json`, marcado `"fonte":"backfill"`. Não feito para não inventar duração, tokens ou resultado.
- Comando que lista `idle`, `error` e `parado` com mais de 3 dias e worktrees sem diff pendente. Listar é seguro; apagar exige confirmação do Felipe.
- Medição automática do Antigravity: cancelada pela ADR-0006. A ferramenta de franquia permanece manual para Felipe.
- Resolver ou fechar o agente `fotos-fora-do-codigo` (pedido de rede pendente).

Normativa, aguarda Felipe
- Guarda de franquia: exigir `quota/codex.json` abaixo de ~70% em 5h antes de lançar 2 ou mais agentes Codex pesados (muda regra de roteamento).
- Tratar OpenCode free como "só para o que pode falhar": sem prazo, sem revisor único, fallback Luna já no prompt (muda o perfil `economico-pessoal`).
- Telemetria automática pelo vigia (M1) e novos campos `orquestrador_completou` e `motivo_falha` (mudam o esquema da ADR-0002).
- ADR-0005 foi substituída pela ADR-0006 (2026-11-09), que remove o Antigravity da automação.
