# Modelos e harnesses — fatos e hipóteses verificadas em 22/10/2026

- **Gemini 4 Argon:** disponível no app Gemini para Google AI Pro/Ultra desde 13/10/2026. Acesso via Antigravity depende de plano/configuração e deve ser checado no app/CLI (suporte Google confirmou Pro em discussão pública de 16/10). API `gemini-4-argon` paga e não incluída por inferência na assinatura. Gemini CLI login consumidor antigo descontinuado em 18/06/2026. Referências: https://gemini.google/br/release-notes/ ; https://developers.google.com/gemini-code-assist/docs/deprecations/code-assist-individuals ; https://ai.google.dev/gemini-api/docs/models/gemini-4-argon
- **OpenCode 2.x:** atualização major explícita (`opencode upgrade --major` a partir de 1.19.x). Houve reconstrução de API/plugin. Atualizar apenas após verificar compatibilidade com Paseo e plugins instalados. Referência: https://dev.opencode.ai/changelog/
- **DeepSeek Harness:** runtime local-first/open-source em prévia com Cordis, plugins, sessões e modos de execução. Não é a API DeepSeek nem equivalente a OpenCode; é alternativa experimental. Referências: https://www.deepseek.com/harness/en/ e https://github.com/deepseek-ai/deepseek-harness
- **Ponytail 5.x:** a comunidade e o autor anunciam reescrita voltada à menor mudança *completa*, review de bugs/segurança/performance e auditoria. Não tomar métricas divulgadas pelo autor como prova independente. Revisar a release/tag DIRETAMENTE antes de pin SHA. Referência: https://github.com/DietrichGebert/ponytail
- **Claude/Codex:** permanecer nos CLIs oficiais para poder aproveitar as respectivas assinaturas. Detectar modelos/níveis de esforço reais localmente, não presumir que alias do benchmark é ID válido na CLI.
- **NVIDIA/DeepSeek/GLM/Kimi/Qwen:** possíveis trabalhadores de tarefas de baixo risco (somente material pessoal publicável se termos permitirem). Cotas grátis/termos/privacidade são variáveis e exigem verificação por provedor, não garantia de disponibilidade.

## Antigravity (referência para uso direto do Felipe; dados de 09/11/2026)

O Antigravity fica fora da automação do AI OS. O uso é direto pelo Felipe no app ou CLI oficial. Nenhum agente, Paseo, Claude ou script invoca `agy`; a FAQ do Google informa que envolver software de terceiros viola os Termos de Serviço e pode levar à suspensão ou encerramento da conta, e que agentes de terceiros não são suportados nos planos de consumidor. Ver [ADR-0006](decisions/0006-antigravity-fora-da-automacao.md) e [FAQ oficial](https://antigravity.google/docs/faq).

Registro de modelos vistos na versão 1.5.3 em 09/11. É uma referência histórica para o uso direto, não uma recomendação de despacho. Os sufixos `-low/-medium/-high` indicavam níveis de raciocínio.

| Modelo | Custo relativo observado/estimado | Forças descritas na época |
|---|---|---|
| `gemini-3.8-flash` | menor (hipótese) | tarefas simples, volume, leitura longa, contexto 1M, imagem |
| `claude-sonnet-5-5` | médio (hipótese) | implementação rotineira, testes, documentação |
| `gemini-4-argon` | alto; barra semanal própria observada | segunda opinião, contexto 1M, imagem/vídeo |
| `claude-opus-5-5` | maior (hipótese) | tarefas difíceis |
| `gpt-oss-120b-medium` | desconhecido | fallback; remoção anunciada para 18/11/2026 |

O Google não publica pesos por modelo. A tarefa T1 de 09/11 consumiu 3% da janela de 5h e 1% da semanal do pool "Gemini Models"; é uma única medição. Plano, preço, franquia atual, retenção, treino e jurisdição da conta não foram confirmados. Fonte de modelos: https://antigravity.google/docs/models.

## Regra de ranking

Role é independente de modelo; classificar tarefa por risco/escopo/ambiguidade e medir retrabalho. Frontier para decisões arriscadas; modelo econômico para tarefas com testes rápidos e baixo blast radius. Revisão cega por família diferente. Não tornar custo de API do Argon ou Claude API equivalente a consumo da assinatura.
