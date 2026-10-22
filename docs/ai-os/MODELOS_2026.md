# Modelos e harnesses — fatos e hipóteses verificadas em 22/10/2026

- **Gemini 4 Argon:** disponível no app Gemini para Google AI Pro/Ultra desde 13/10/2026. Acesso via Antigravity depende de plano/configuração e deve ser checado no app/CLI (suporte Google confirmou Pro em discussão pública de 16/10). API `gemini-4-argon` paga e não incluída por inferência na assinatura. Gemini CLI login consumidor antigo descontinuado em 18/06/2026. Referências: https://gemini.google/br/release-notes/ ; https://developers.google.com/gemini-code-assist/docs/deprecations/code-assist-individuals ; https://ai.google.dev/gemini-api/docs/models/gemini-4-argon
- **OpenCode 2.x:** atualização major explícita (`opencode upgrade --major` a partir de 1.19.x). Houve reconstrução de API/plugin. Atualizar apenas após verificar compatibilidade com Paseo e plugins instalados. Referência: https://dev.opencode.ai/changelog/
- **DeepSeek Harness:** runtime local-first/open-source em prévia com Cordis, plugins, sessões e modos de execução. Não é a API DeepSeek nem equivalente a OpenCode; é alternativa experimental. Referências: https://www.deepseek.com/harness/en/ e https://github.com/deepseek-ai/deepseek-harness
- **Ponytail 5.x:** a comunidade e o autor anunciam reescrita voltada à menor mudança *completa*, review de bugs/segurança/performance e auditoria. Não tomar métricas divulgadas pelo autor como prova independente. Revisar a release/tag DIRETAMENTE antes de pin SHA. Referência: https://github.com/DietrichGebert/ponytail
- **Claude/Codex:** permanecer nos CLIs oficiais para poder aproveitar as respectivas assinaturas. Detectar modelos/níveis de esforço reais localmente, não presumir que alias do benchmark é ID válido na CLI.
- **NVIDIA/DeepSeek/GLM/Kimi/Qwen:** possíveis trabalhadores de tarefas de baixo risco (somente material pessoal publicável se termos permitirem). Cotas grátis/termos/privacidade são variáveis e exigem verificação por provedor, não garantia de disponibilidade.

## Regra de ranking

Role é independente de modelo; classificar tarefa por risco/escopo/ambiguidade e medir retrabalho. Frontier para decisões arriscadas; modelo econômico para tarefas com testes rápidos e baixo blast radius. Revisão cega por família diferente. Não tornar custo de API do Argon ou Claude API equivalente a consumo da assinatura.
