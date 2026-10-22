# Testes de aceite — prova de conceito real

Os testes descritos aqui exigem execução no Mac do usuário; os testes locais incluídos apenas verificam o scaffolding, NÃO comprovam integração com provedores.

## T1 — primeira tarefa (essencial)

Num `laboratorio/` descartável, criar um utilitário local pequeno, executar testes, abrir diff no Paseo e confirmar resultado. Usar um único modelo e nenhum acesso a dados privados.

**Pronto:** código produzido, testes executados e diff revisável.

## T2 — handoff manual (essencial)

Claude (ou Codex) começa uma tarefa de duas etapas; encerra após a primeira, registra um handoff com próximo passo, outro agente retoma no mesmo checkout. Exigir que o segundo cite o que já foi feito, não reimplemente etapas e preserve o diff. Validar se o AI-Memory melhora recuperação, sem exigir este sistema se ainda não instalado.

**Pronto:** tarefa concluída no segundo agente, sem colagem manual de longa transcrição nem perda das decisões.

## T3 — paralelismo (essencial)

Dois worktrees em branches separadas executam tarefas sem sobreposição de arquivos, com 2 agentes no máximo no Mac de 16 GB. Inspecionar consumo de RAM, testes e diferenças antes do merge.

**Pronto:** nenhuma tarefa sobrescreveu a outra e ambas possuem diffs explicáveis.

## T4 — política de rotas (essencial)

Usar `python3 scripts/rotear_preview.py --classe low --dados pessoal-publico` e repetir `--classe high`; confirmar que `institucional` é bloqueado por padrão. Essa CLI somente sugere **papéis**, não verifica conta nem executa fallback.

**Pronto:** rotas legíveis e restrição a dados sensíveis.

## T5 — quota/failover (experimental)

Após auditoria e aprovação do Continuity, testar detecção controlada de rate limit em ambiente descartável, sempre com dois provedores autenticados e uma operação reversível. Se não houver modo de simulação válido, testar somente handoff manual e registrar limite **NÃO TESTADO**. Não esgotar intencionalmente assinaturas.

**Pronto (parcial):** transição controlada, estado preservado, nenhuma ação duplicada. **Pronto (completo):** erro de quota real detectado e fallback seguro comprovado, com evidência de eventos.

## Métricas mínimas

Tempo para retomar; quantidade de perguntas repetidas; ações reexecutadas; intervenção humana; sucesso nos testes; RAM observada; consumo de franquia quando o provedor expuser informação confiável.

## Condição de parada

Se uma integração exigir novo SaaS pago, alteração sensível do macOS, bypass de permissão, credenciais enviadas para terceiro ou construção de orquestrador próprio: parar, anotar e pedir escolha informada do usuário.
