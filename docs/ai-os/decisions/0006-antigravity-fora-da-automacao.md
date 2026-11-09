# ADR-0006: Antigravity fora da automação

**Status:** Aceita em 2026-11-09 por Felipe  
**Substitui:** ADR-0005

## Contexto

A FAQ oficial do Antigravity, consultada em 09/11/2026, afirma: “Using third-party software, tools, or services to access Antigravity is a violation of our Terms of Service” e diz que isso pode resultar em suspensão ou encerramento da conta. Também registra que envolver `agy` em agentes ou aplicativos de terceiros não é suportado nos planos de consumidor. O modo headless é destinado a scripts diretos e CI; para usar agentes de terceiros com Gemini, o Google recomenda uma chave Gemini Enterprise ou Google AI Studio.

A integração do AI OS usava o CLI em três pontos: Paseo despachava o provider, Claude podia chamar o CLI para revisão e o vigia consultava a franquia. Essa automação contrariava os termos do plano de consumidor. O incidente I-33 também registrou que um agente controlado externamente saiu do sandbox após falha no commit.

Fonte: [FAQ oficial do Antigravity](https://antigravity.google/docs/faq), consultada em 09/11/2026.

## Decisão

Remover `agy` de toda automação do AI OS. Nenhum agente, Paseo, Claude ou script do AI OS invoca o CLI. O provider do Paseo fica desabilitado. Felipe pode continuar usando Gemini diretamente pelo app ou CLI oficial; resultados entram no repositório por Git e passam por revisão.

Uma integração futura com Gemini API via Google AI Studio será um experimento separado e não faz parte desta decisão. Se usar o tier gratuito, o experimento deve conter somente dados públicos, nunca conteúdo de projeto restrito, pois esse tier pode usar o conteúdo para treinamento.

## Consequências

- O pool do Antigravity deixa de ser um executor automático disponível ao orquestrador.
- A operação deixa de envolver `agy` em software de terceiros nos planos de consumidor, alinhando o AI OS à FAQ do Google.
- O sensor de franquia permanece como ferramenta manual de Felipe e não é chamado pelo vigia.
- A integração do `install.sh --only antigravity` continua preparando a configuração para o uso direto de Felipe; não despacha tarefas.

## Alternativas consideradas

- **Gemini API pelo Google AI Studio:** experimento futuro separado. Não implementar agora. No tier gratuito, limitar a dados públicos por causa do possível uso do conteúdo para treinamento.
- **Manter o provider com limites e sandbox:** rejeitada; ainda envolveria o CLI em um agente de terceiro e não resolveria o problema contratual.

## Rollback

Somente após nova decisão de Felipe: reabilitar `agents.providers.antigravity.enabled` no Paseo e reverter o commit desta mudança. A reversão não deve ser feita automaticamente nem com base apenas em mudança de configuração local.
