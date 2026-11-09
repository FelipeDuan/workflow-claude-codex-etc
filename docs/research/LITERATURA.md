# Registro de literatura — AI OS

Este registro reúne as fontes que embasam as decisões do AI OS: arquitetura de agentes, avaliação e produtividade, telemetria e dados, segurança, provedores e termos, contexto e memória, e metodologia de pesquisa. Nenhuma fonte foi verificada ainda: todas entram com status "a verificar" e devem ser lidas na íntegra antes de virar referência. Fonte de fornecedor descreve como a ferramenta funciona, mas não é evidência independente de ganho no nosso ambiente.

| ID | Fonte (título) | Autor/organização | Ano | Tipo | URL | O que informa no AI OS | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **Arquitetura de agentes** | | | | | | | |
| L01 | Building Effective Agents | Anthropic | 2024 | relato de engenharia (fornecedor) | https://www.anthropic.com/research/building-effective-agents | Preferir workflows simples; orquestração só quando a tarefa justifica. | a verificar |
| L02 | How we built our multi-agent research system | Anthropic | 2025 | relato de engenharia (fornecedor) | https://www.anthropic.com/engineering/multi-agent-research-system | Multiagente custa muitos tokens; programação tem menos paralelismo que pesquisa. | a verificar |
| L03 | Effective harnesses for long-running agents | Anthropic | 2025 | relato de engenharia (fornecedor) | https://www.anthropic.com/research/effective-harnesses-for-long-running-agents | Git e logs de progresso funcionam como handoff durável em agentes de longa duração. | a verificar |
| L04 | Agentless: Demystifying LLM-based Software Engineering Agents | Xia et al. | 2024 | preprint | https://arxiv.org/abs/2407.01489 | Sustenta o fluxo simples como baseline obrigatória. | a verificar |
| L05 | AFlow | Zhang et al. | 2025 | artigo revisado por pares | https://proceedings.iclr.cc/paper_files/paper/2025/hash/5492ecbce4439401798dcd2c90be94cd-Abstract-Conference.html | Otimizar workflow exige função objetivo e feedback. | a verificar |
| L06 | git-worktree | Git | — | documentação oficial | https://git-scm.com/docs/git-worktree | Referência para gerenciar worktrees (remove vs. prune; lock). | a verificar |
| L07 | Paseo orchestration docs | Paseo | — | documentação oficial | https://paseo.sh/docs/orchestration | Orienta quando vale orquestrar e usar worktrees. | a verificar |
| **Avaliação e produtividade** | | | | | | | |
| L08 | Demystifying evals for AI agents | Anthropic | 2026 | relato de engenharia (fornecedor) | https://www.anthropic.com/research/demystifying-evals-for-ai-agents | Ajuda a distinguir tarefa, tentativa, trajetória, resultado e avaliador. | a verificar |
| L09 | SWE-Bench Pro | Deng et al. | 2026 | artigo revisado por pares | https://proceedings.mlr.press/v306/deng26f.html | Benchmarks realistas também precisam de auditoria. | a verificar |
| L10 | We are changing our developer productivity experiment design | METR | 2026 | estudo/relatório | https://metr.org/blog/2026-02-24-uplift-update/ | Alerta para viés de seleção e para medir tempo humano. | a verificar |
| L11 | DORA Report 2025 | Google DORA | 2025 | estudo/relatório | https://dora.dev/research/2025/dora-report/ | IA amplifica forças e fraquezas do processo; atividade não é entrega. | a verificar |
| **Telemetria e dados** | | | | | | | |
| L12 | Claude Code hooks reference | Anthropic | — | documentação oficial | https://code.claude.com/docs/en/hooks | Mapeia eventos disponíveis para telemetria automática. | a verificar |
| L13 | Codex App Server | OpenAI | — | documentação oficial | https://learn.chatgpt.com/docs/app-server | Expõe eventos de execução e leitura de limites de uso. | a verificar |
| L14 | OpenTelemetry GenAI semantic conventions | OpenTelemetry | — | documentação oficial | https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/ | Padroniza nomes de atributos para eventos de IA. | a verificar |
| L15 | SQLite Write-Ahead Logging | SQLite | — | documentação oficial | https://www.sqlite.org/wal.html | Referência caso o armazenamento em JSONL deixe de bastar. | a verificar |
| **Segurança** | | | | | | | |
| L16 | OWASP Top 10 for Agentic Applications 2026 | OWASP | 2026 | norma/guia | https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/ | Cataloga riscos como abuso de ferramentas, privilégios e memória. | a verificar |
| L17 | Claude Code sandboxing | Anthropic | — | relato de engenharia (fornecedor) | https://www.anthropic.com/research/claude-code-sandboxing | Deixa claro que worktree não é isolamento do host. | a verificar |
| **Provedores e termos** | | | | | | | |
| L18 | Advisor tool | Anthropic | — | documentação oficial | https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool | Recurso beta da API; não presumir que está incluído na assinatura. | a verificar |
| L19 | Antigravity FAQ | Google | — | documentação oficial | https://antigravity.google/docs/faq | Proíbe encapsular agy em agentes de terceiros com login de consumidor. | a verificar |
| L20 | Antigravity Terms | Google | — | termos de serviço | https://antigravity.google/terms | Indica risco de suspensão de conta. | a verificar |
| L21 | Gemini Developer API pricing | Google | — | documentação oficial | https://ai.google.dev/gemini-api/docs/pricing | O nível gratuito pode usar conteúdo para melhorar produtos. | a verificar |
| L22 | python-apple-fm-sdk | Apple | — | documentação oficial | https://github.com/apple/python-apple-fm-sdk | SDK local; exige macOS 26+ e Xcode 26+. | a verificar |
| L23 | WWDC26 sessão 334 (Foundation Models, CLI fm) | Apple | 2026 | documentação oficial | https://developer.apple.com/videos/play/wwdc2026/334/ | A CLI fm só está disponível no macOS 27. | a verificar |
| **Contexto e memória** | | | | | | | |
| L24 | Context engineering: memory, compaction, and tool clearing | Anthropic | 2026 | documentação oficial | https://platform.claude.com/cookbook/tool-use-context-engineering-context-engineering-tools | Distingue limpeza de resultados, compactação e memória. | a verificar |
| **Metodologia de pesquisa** | | | | | | | |
| L25 | Design Science in Information Systems Research | Hevner et al. | 2004 | artigo revisado por pares | https://aisel.aisnet.org/misq/vol28/iss1/6/ | Fundamenta a pesquisa por construção e avaliação de artefatos. | a verificar |
| L26 | A Design Science Research Methodology for Information Systems Research | Peffers et al. | 2007 | artigo revisado por pares | https://www.jmis-web.org/articles/765 | Propõe as seis etapas da DSRM. | a verificar |
| L27 | Goal/Question/Metric Paradigm | Basili | 1992 | estudo/relatório | https://drum.lib.umd.edu/items/8119803a-362b-42ec-b6ce-2311713e7236 | Orienta medir a partir de objetivos e perguntas. | a verificar |
| L28 | Metodologia de Pesquisa para Ciência da Computação (3ª ed.) | Wazlawick, R. S. | 2021 | norma/guia | Livro (LTC), sem URL | Ajuda a distinguir construir ferramenta de produzir conhecimento e a rastrear objetivo → evidência. | a verificar |
| L29 | PRISMA for Scoping Reviews | PRISMA | — | norma/guia | https://www.prisma-statement.org/scoping | Referência apenas se um dia fizermos revisão de escopo formal. | a verificar |

## Como usar

1. Ler método e limitações, não só o resumo.
2. Registrar a data de acesso toda vez que consultar uma fonte.
3. Fonte de fornecedor não prova ganho no nosso ambiente.
4. Mudança de política exige experimento interno + decisão do Felipe.
