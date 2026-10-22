# Política de segurança inicial

- **Somente laboratório pessoal e código sintético nesta primeira etapa.** SEPLAN, clientes, credenciais, documentos internos, dados pessoais de terceiros e repositórios não autorizados estão excluídos.
- Contas pagas de consumo não significam autorização corporativa. Modelos NVIDIA gratuitos são tratados como externos e experimentais; avaliar termos antes de qualquer dado não público.
- Não transmitir histórico de outro provedor sem entender exatamente o que o plugin/handoff envia. Padrões de redação de segredo não eliminam todos os riscos.
- Nada de `--dangerously-skip-permissions`, YOLO, shell irrestrito ou instalação de plugin comunitário sem revisão/consentimento.
- AI-Memory com captura por allowlist/opt-in antes de ativar. Guardar dados locais, loopback, autenticação. Nunca permitir captura ampla por padrão em máquina com projetos institucionais.
- Worktrees são isolamento de checkout, não sandbox do SO. Plugins do Paseo executam com privilégios da conta do usuário. Evite permissões globais de diretórios sensíveis.
- Toda alteração em configurações globais deve ter backup reversível; não sobrescrever skills existentes ou `~/.claude`/`~/.codex` silenciosamente.
- Para testar failover, use tarefas idempotentes e arquivos descartáveis. Quando houver erro ambíguo, parar em vez de executar a mesma ação em outro agente.
- Tratar custo de assinatura como franquia limitada, e API como custo monetário; nenhum componente torna uso ilimitado.
