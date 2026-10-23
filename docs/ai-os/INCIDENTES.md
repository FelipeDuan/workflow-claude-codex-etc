# Incidentes e atritos do Felipe AI OS

Cada problema que travou ou atrasou o trabalho entra aqui, mesmo depois de resolvido. O objetivo é ver o que se repete, se a correção pegou e se uma ferramenta nova (Paseo, gateway etc.) resolveria ou traria o mesmo problema.

Como registrar: some 1 em **Ocorrências** quando acontecer de novo. Em **Ferramenta futura resolve?** fica a hipótese, marcada como hipótese até ser testada.

| ID | Primeira vez | Ocorrências | Sintoma | Causa | Correção / contorno | Ferramenta futura resolve? |
|---|---|---|---|---|---|---|
| I-01 | 22/10 | 1 | `codex exec` em segundo plano ficou "vivo" sem fazer nada por ~20 min, sem sessão e sem erro | Provável: stdin herdado aberto; o Codex esperou entrada (não confirmado) | Passar o prompt por arquivo: `codex exec ... - < prompt.txt`. Orquestrador confere se a sessão foi criada logo após disparar | Hipótese: Paseo mostra o status de cada agente e evitaria o "vivo mas parado" silencioso. Testar |
| I-02 | 22/10 | 1 | `ai-memory run codex exec --sandbox ...` falhou com "unexpected argument --sandbox" | Com sessão anterior no workstream, o `run` vira `codex exec resume`, que não aceita essas flags | Tarefa nova: `ai-memory run --fresh codex exec ...`. Continuar: `ai-memory run codex` | Não se aplica: é semântica do ai-memory. Documentado |
| I-03 | 22/10 | 1 | OpenCode 2 não iniciava: porta 49374 em uso | O serviço do OpenCode 2 e o ai-memory usam a mesma porta padrão (issue #1044 do ai-memory) | `opencode service set port 49375` | Paseo também sobe daemon: conferir a porta antes de instalar |
| I-04 | 22/10 | 1 | `opencode run` travou | Disparado junto com `opencode service restart` (corrida na subida do serviço) | Esperar o serviço subir (`opencode service status`) antes do `run` | Não |
| I-05 | 22/10 | 2 | Codex não consegue `git commit` | O sandbox `workspace-write` protege o `.git` | O orquestrador commita depois de verificar (padrão adotado: quem verifica commita) | Paseo usa worktrees próprios: verificar como trata commits |
| I-06 | 22/10 | 1 | Leitor de franquia do Codex deu `error` quando rodado pelo próprio Codex | O sandbox bloqueia o `codex app-server` (rede/`~/.codex`) | Sensores rodam fora do sandbox (orquestrador, launchd ou hook) | — |
| I-07 | 22/10 | 1 | Dois handoffs abertos para a mesma sessão | Pedido de handoff explícito + o automático do SessionEnd | Regra no AGENTS.md: não criar handoff explícito; terminar com nota de estado | — |
| I-08 | 22/10 | 2 | Hooks do ai-memory ignorados pelo Codex ("untrusted"/"modified") | O Codex exige aprovação manual dos hooks e de novo quando o comando muda | Felipe roda `/hooks` → Trust all depois de cada mudança nos hooks | Não: é segurança do Codex. Avisar sempre que mexer em hooks |
| I-09 | 22/10 | 1 | Volta Codex → Claude sem saber o que o Codex entregou | O ai-memory não capturava o texto do agente (`capture_assistant` desligado) | `capture_assistant = true` + hooks reinstalados com `--capture-assistant` | — |
| I-10 | 22/10 | 1 | Notificação de "failed" num teste que tinha passado | O `wait` do shell devolveu exit 1, não os modelos | Verificar o resultado real (testes/commits), nunca só o exit code do wrapper | — |
| I-11 | 22/10 | 1 | O Codex não tem gancho quando bate o limite de uso | Nenhum hook dispara em UsageLimitExceeded (openai/codex#21160) | Aviso de sessão cortada do ai-memory + leitor de franquia (`quota_codex.py`) para agir antes | Hipótese: Paseo/Continuity detecta o erro de quota pelo lado do orquestrador. Testar no laboratório |

## Padrões que já aparecem

- **Sandbox × tarefas de orquestração** (I-05, I-06): o Codex em sandbox é ótimo para editar código, mas commit, sensores e instalação ficam com o orquestrador.
- **Processo vivo ≠ progresso** (I-01, I-10): conferir sinais concretos (sessão criada, arquivo escrito, testes) em vez de status do processo.
- **Conflitos de daemon/porta** (I-03): cada ferramenta nova com serviço local precisa de checagem de porta antes.
