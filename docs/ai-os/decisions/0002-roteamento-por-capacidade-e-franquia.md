# ADR-0002: Roteamento por capacidade e franquia (Quota-Aware Capability Routing), v0

**Status:** aceita como v0 experimental em 22/10/2026. Só sugere: não executa nada sozinha.

## Contexto

O Felipe quer evitar que um provedor (em geral o Claude) gaste a franquia em tarefas que outro modelo faria igual, e quer guardar os modelos frontier para onde eles fazem diferença. Os percentuais de provedores diferentes não são comparáveis entre si, e uma janela perto do reset vale menos do que uma janela semanal no fim.

## Decisão

Regra central: **escolher o executor de menor custo efetivo que atenda o piso de qualidade e risco da tarefa, considerando a chance de terminar com a franquia disponível.**

Duas camadas:

1. **Determinística (agora).** Franquia, reset, preço, privacidade, permissões e resultado dos testes vêm de fontes estruturadas, nunca de modelo:
   - Claude: mod `quota-guard` (`session.measure`) → `~/.local/state/ai-os/quota/claude.json`.
   - Codex: `scripts/quota_codex.py` (App Server, `account/rateLimits/read`) → `~/.local/state/ai-os/quota/codex.json`.
   - OpenCode gratuito: sem medidor oficial → `status: "unknown"`.
   - Sem sinal confiável, o estado é `unknown`. Ninguém inventa percentual.
2. **Interpretação da tarefa (agora por regra, depois talvez por classificador).** Categoria, risco, complexidade, ambiguidade e divisibilidade. Começa com regras e com o julgamento do orquestrador. JEV, Clef, Laya e similares só entram numa POC comparativa depois que existirem dados reais (ver abaixo).

Política inicial (em `roteamento.json`, que segue consultivo):
- Risco alto (segurança, auth, dados, arquitetura): piso frontier (Claude Opus ou GPT-6 Astra), com revisor de outra família. A franquia baixa não rebaixa o piso: espera o reset ou pergunta ao Felipe.
- Risco médio: Codex (Luna/Sol) ou Claude Sonnet. O revisor entra quando o diff é grande.
- Risco baixo e verificável por teste: OpenCode com modelo gratuito/econômico, e o orquestrador só confere o resultado.
- Janela de 5h ≥ 85% em um provedor: tarefas novas de risco baixo e médio vão para outro. Faltando menos de 20 min para o reset, pode gastar o resto numa tarefa curta.
- Dado institucional (SEPLAN, clientes): nenhum provedor sem acordo. O roteador bloqueia.
- Dividir uma tarefa só quando as partes forem independentes e cada uma tiver critério de aceite verificável. Cada handoff tem custo.
- O orquestrador delega a tarefa especificada e verifica o resultado; não acompanha comando por comando.

## Contrato de franquia (um arquivo por provedor)

```json
{"provider":"codex","source":"app-server","fetched_at":"2026-10-22T20:00:00Z","status":"ok","windows":[{"kind":"five_hour","used_percent":41.0,"resets_at":"2026-10-22T23:10:00Z","window_minutes":300}],"note":""}
```

## Telemetria de tarefas (base para calibrar e, um dia, treinar)

Uma linha JSON por tarefa em `docs/ai-os/telemetria.jsonl`:

```json
{"date":"2026-10-22","task":"lab etapa 4","category":"backend","risk":"low","complexity":"low","divisible":false,"harness":"opencode","model":"opencode/glm-5.3-flash-free","duration_s":0,"tests_passed":true,"human_corrections":0,"handoff":false,"outcome":"success","notes":""}
```

## Alternativas adiadas

- **Classificador (JEV, Clef, Decision-1, Laya):** benchmarks do Akita (decisão v2, 10/10/2026) indicam JEV/Decision-1 ≈ 97,6% e Laya base 42,9%, mas em cenários sintéticos que não medem escolha de LLM para código. Só faz sentido com 100–200 tarefas reais na telemetria. A comparação seria: regras × classificador clássico × JEV/Clef. Fine-tuning do Laya só com vantagem demonstrada. O classificador nunca substitui permissões, verificações determinísticas ou aprovação humana, e precisa ter opção de abstenção.
- **Gateway (OmniRoute/OpenRouter/LiteLLM):** só se houver múltiplas APIs pagas com orçamento a controlar. Ver `PESQUISA-ROTEAMENTO.md`.
- **Roteador automático:** só depois que a v0 consultiva mostrar que as regras acertam.

## Referências de capacidade (evidência inicial, não ranking universal)

Akita LLM benchmark v4 (23/09/2026, Rails com 14 sabotagens de segurança): Opus 5.5 e GPT-6 Astra 100; GPT-6 Luna 95,5; GLM 5.3 94; DeepSeek V4.1 Flash 92,5; Sonnet 5 e GPT-6 Sol 91; GLM 5.3 Flash 84,25. Mede vigilância de segurança em Rails, não frontend nem arquitetura. Os custos são da execução dele, não da franquia do Felipe.

## Consequências

Os sensores e a telemetria começam a gerar dados reais. O roteamento continua uma sugestão revisável. Qualquer automação (failover, classificador) precisa provar ganho medido antes de entrar no caminho principal.


## Emenda 2026-11-09

Aprovada por Felipe em 09/11/2026, junto com a aceitação do ADR-0005. O trecho de roteamento do Antigravity desta emenda é histórico; a ADR-0006 o substitui.

**GPT-6 Astra (Codex), uso com muito cuidado.** Evidência: uma única revisão somente leitura com `gpt-6-astra` (thinking padrão) consumiu 27% da janela de 5h do Codex em 09/11; antes, 3 agentes Astra pararam por limite (I-11). Regra: Astra só para risco alto, quando nenhum executor mais barato atinge o piso de qualidade; sempre com `--thinking low` ou `medium` explícito, uma tarefa por vez (a regra de uma por vez vale para agentes Codex pesados, I-23) e com franquia Codex 5h < 50% (franquia `unknown` bloqueia o Astra). Todo `paseo run` de Codex leva `--thinking` explícito.

**Revisores de risco médio**, nesta ordem: gpt-6.1-sol com thinking low/medium, gpt-6-luna para revisões mecânicas. Antigravity saiu do roteamento por decisão da ADR-0006; a referência abaixo ao uso via Antigravity registra apenas fatos históricos da rodada de 09/11.

**Modelos Codex disponíveis** (`paseo provider models codex`): gpt-6.1-sol (workhorse), gpt-6-astra (frontier), gpt-6.1-terra (custo relativo não medido), gpt-6-sol, gpt-6-luna (rápido e barato), gpt-5.6-sol/terra/luna (gerações antigas).

**Decomposição para economia.** O orquestrador (Claude) quebra a tarefa e envia cada parte ao modelo mais barato que atinge o piso de qualidade:

- Haiku: checagens, inventários e verificações mecânicas.
- Sonnet nativo (subagente do Claude Code) para docs e rotina.
- Gemini Flash via Paseo: código pequeno verificável por testes (medição histórica de 09/11: 3% da janela 5h para script + 14 testes; integração encerrada pela ADR-0006).
- Opus: só orquestração e decisão de risco alto.

Exemplo real de 09/11 (registro histórico, antes da ADR-0006): instalação → orquestrador; pesquisa e retrospectiva → Sonnet; script de franquia → Gemini Flash via Paseo; revisão → Astra (27% da janela 5h); correções → Sonnet; checagem final → Haiku; documentação → Claude Sonnet nativo.
