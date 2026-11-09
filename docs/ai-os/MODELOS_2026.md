# Modelos e harnesses — fatos e hipóteses verificadas em 22/10/2026

- **Gemini 4 Argon:** disponível no app Gemini para Google AI Pro/Ultra desde 13/10/2026. Acesso via Antigravity depende de plano/configuração e deve ser checado no app/CLI (suporte Google confirmou Pro em discussão pública de 16/10). API `gemini-4-argon` paga e não incluída por inferência na assinatura. Gemini CLI login consumidor antigo descontinuado em 18/06/2026. Referências: https://gemini.google/br/release-notes/ ; https://developers.google.com/gemini-code-assist/docs/deprecations/code-assist-individuals ; https://ai.google.dev/gemini-api/docs/models/gemini-4-argon
- **OpenCode 2.x:** atualização major explícita (`opencode upgrade --major` a partir de 1.19.x). Houve reconstrução de API/plugin. Atualizar apenas após verificar compatibilidade com Paseo e plugins instalados. Referência: https://dev.opencode.ai/changelog/
- **DeepSeek Harness:** runtime local-first/open-source em prévia com Cordis, plugins, sessões e modos de execução. Não é a API DeepSeek nem equivalente a OpenCode; é alternativa experimental. Referências: https://www.deepseek.com/harness/en/ e https://github.com/deepseek-ai/deepseek-harness
- **Ponytail 5.x:** a comunidade e o autor anunciam reescrita voltada à menor mudança *completa*, review de bugs/segurança/performance e auditoria. Não tomar métricas divulgadas pelo autor como prova independente. Revisar a release/tag DIRETAMENTE antes de pin SHA. Referência: https://github.com/DietrichGebert/ponytail
- **Claude/Codex:** permanecer nos CLIs oficiais para poder aproveitar as respectivas assinaturas. Detectar modelos/níveis de esforço reais localmente, não presumir que alias do benchmark é ID válido na CLI.
- **NVIDIA/DeepSeek/GLM/Kimi/Qwen:** possíveis trabalhadores de tarefas de baixo risco (somente material pessoal publicável se termos permitirem). Cotas grátis/termos/privacidade são variáveis e exigem verificação por provedor, não garantia de disponibilidade.

## Antigravity (agy 1.5.3), verificado em 09/11/2026

Modelos em `agy models`: `gemini-4-argon`, `gemini-3.8-flash`, `claude-opus-5-5`, `claude-sonnet-5-5` (cada um com sufixos `-low/-medium/-high`, nível de raciocínio) e `gpt-oss-120b-medium`. Plano e preços: Pro ou Ultra provável, não confirmado (`/usage` não mostra o plano).

| Modelo | Custo relativo | Forças |
|---|---|---|
| gemini-3.8-flash | menor (hipótese) | trivial, volume, leitura longa, contexto 1M, imagem |
| claude-sonnet-5-5 | médio (hipótese) | implementação rotineira, testes, docs |
| gemini-4-argon | alto; barra semanal própria (verificado) | segunda opinião de outra família, contexto 1M, imagem/vídeo |
| claude-opus-5-5 | maior (hipótese) | tarefa difícil; não é revisão de outra família para código escrito por Claude |
| gpt-oss-120b-medium | desconhecido | fallback; a página de modelos indica remoção em 18/11/2026 |

- Pools de franquia (verificado com `agy -p "/usage"`, que não gasta cota): "Gemini Models" e "Claude and GPT models", cada um com janelas de 5h e semanal; "Gemini 4 Argon" tem barra semanal própria. Claude via `agy` gasta cota Google, não a da Anthropic (inferência, sem fonte direta).
- O Google não publica peso por modelo. A ordem de custo acima vem de preço de API e comportamento esperado; medir `/usage` antes e depois de uma tarefa padrão. `scripts/quota_antigravity.py` (em implantação) vai gravar `~/.local/state/ai-os/quota/antigravity.json`.
- Não verificado: qual plano a conta tem; se `AI Credit Overages` está em `Always` (pode gerar cobrança; conferir); desempenho por tipo de tarefa (frontend, docs, testes). Preço promocional do Argon vale até 30/11 segundo fontes secundárias.
- Segurança: ver ADR-0005 (proposto) e I-32. Só `low`/`medium`, worktree isolado, nunca em projeto restrito.
- Fontes: https://antigravity.google/docs/models ; https://antigravity.google/docs/plans

## Regra de ranking

Role é independente de modelo; classificar tarefa por risco/escopo/ambiguidade e medir retrabalho. Frontier para decisões arriscadas; modelo econômico para tarefas com testes rápidos e baixo blast radius. Revisão cega por família diferente. Não tornar custo de API do Argon ou Claude API equivalente a consumo da assinatura.
