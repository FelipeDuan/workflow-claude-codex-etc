# I-35: servidores `astro dev` órfãos de agentes

Registro resumido em [INCIDENTES.md](../INCIDENTES.md). Evidência bruta (PIDs, caminhos, saídas) fica fora do repo, no estado privado do Felipe.

## Linha do tempo

- 04/11 a 05/11: agentes do Paseo trabalham no projeto de portfólio (um worktree por agente) e rodam `astro dev` para testar. Os agentes terminam; os servidores não.
- 09/11: ao investigar pressão de memória, 21 processos `astro dev` (Astro 7.3.8) aparecem com 4 a 5 dias de vida, ppid 1 e 0 conexões.
- 09/11: revalidação e SIGTERM nos 21. Mesmo dia: correção por env e regra no AGENTS.md.

## Evidência (agregada)

- 21 processos, todos com cwd num worktree do Paseo, 6 iniciados em 04/11 e 15 em 05/11; nenhum tinha conexão ativa.
- Footprint somado do `top`: ~11,7 GB. Esse número não é memória exclusiva (inclui páginas compartilhadas e comprimidas); serve como ordem de grandeza.
- Swap em uso: 11,36 GB (12 GB alocados), pressão de memória nível 2.

## Causa

Confirmada na documentação oficial do Astro (consultada em 09/11: guia "Build with AI" e referência da CLI). Desde o astro@7.0.0, `astro dev` (e `astro preview`, desde 7.2.0) inicia como processo destacado em background quando detecta um agente de IA no macOS/Linux. O servidor grava um lock `.astro/dev.json` (ou `preview.json`) e só termina com `astro dev stop`. Opt-out oficial: `ASTRO_DEV_BACKGROUND=0` e `ASTRO_PREVIEW_BACKGROUND=0`.

Ou seja: o agente achou que estava rodando um servidor em primeiro plano, que morreria com a sessão. Não morria.

## Por que o lock por projeto não impediu

O lock protege contra dois servidores no mesmo projeto. Cada worktree é um projeto distinto, com seu próprio `.astro/`, então 21 worktrees geraram 21 locks válidos e 21 servidores. O lock também não depende de o agente ainda existir.

## Intervenção

Procedimento seguro, sem `pkill` por nome (poderia atingir servidor legítimo de outro projeto):

1. Listar candidatos por comando e cwd.
2. Revalidar cada PID imediatamente antes de agir: horário de início igual ao registrado (descarta reuso de PID), cwd dentro de worktree do Paseo, comando `astro ... dev`, porta, e número de conexões.
3. SIGTERM só nos que passaram. Resultado: 21 encerrados, 0 com conexão ativa.

## Medição antes e depois

| | Antes | ~90 s depois |
|---|---:|---:|
| Swap em uso | 11,36 GB | 4,76 GB |
| Swap alocado | 12 GB | 6 GB |
| Pressão de memória | nível 2 | nível 1 |

Ressalvas: o footprint do `top` não é memória exclusiva, e o swap pode cair com atraso depois que os processos saem (a queda medida pode não estar completa). No mesmo intervalo o claude-mem foi desabilitado, então parte da melhora pode vir dele; a medição não separa os dois efeitos.

## Correções

- Raiz: `ASTRO_DEV_BACKGROUND=0` e `ASTRO_PREVIEW_BACKGROUND=0` no env gerenciado pelo `scripts/harden.py` (Claude `settings.json` e Codex `shell_environment_policy.set`), aplicado com `install.sh --harden`. Lacuna: o OpenCode não tem ponto de env gerenciado pelo repo.
- Regra no AGENTS.md: servidor de dev/preview iniciado pelo agente é dele; encerrar antes de terminar e informar porta/PID.
- Detecção (A1, em andamento): higiene/vigia apontar processo órfão (ppid 1, cwd em worktree sem agente ativo).

## Teste de regressão esperado

- `tests/test_harden_env.py`: as duas variáveis entram no env do Claude e do Codex, sem sobrescrever valor existente.
- Após aplicar o harden e abrir um agente novo: `astro dev` num worktree de teste deve rodar em primeiro plano e morrer com o agente. Ainda não verificado.

## Lições

- Ferramenta que muda de comportamento quando detecta agente precisa ser lida nas notas de versão antes de entrar no fluxo.
- Todo recurso temporário precisa de dono (padrão registrado em INCIDENTES.md).
- Ao encerrar processos em lote, revalidar cada um na hora de agir, não confiar na lista de minutos antes.
