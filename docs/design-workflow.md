# Workflow de design

## O que é

Um conjunto de skills e agents que organiza trabalho de produto, UX e UI com profundidade proporcional ao risco. A skill `design-director` faz a triagem, monta um plano de fases, cobra evidência em cada gate e passa cada etapa para o especialista certo. Ela não tem gosto próprio e não escreve código de interface. Roda na conversa principal, porque precisa parar para ouvir você nos checkpoints e disparar subagents (um subagent do Claude Code não consegue fazer nenhuma das duas coisas). Quem implementa continua sendo o agent `frontend-ux-ui`. As regras completas estão em `skills/design-director/SKILL.md`; este documento explica como as peças se encaixam e o que fazer quando algo dá errado.

## Arquitetura

```
usuário
  └─> design-director  (conversa principal; triagem, plano, gates, checkpoints)
        ├─ reference-research   referências -> REFERENCES.md
        ├─ skill de direção     impeccable (produto) OU design-taste-frontend (marketing), uma só
        ├─ impeccable           shape, document, critique, audit, polish...
        ├─ skills do Figma      figma-use primeiro, depois as outras
        ├─> frontend-ux-ui      build (subagent) com PRODUCT.md, DESIGN.md, fluxos e findings aceitos
        ├─> design-critic       subagent, contexto limpo: recebe brief, tarefas, DESIGN.md e capturas
        └─> QA                  Playwright 390/1440 px, estados, teclado, impeccable audit, design-critic

refinamento de design já definido: usuário -> frontend-ux-ui direto
conhecimento canônico = PRODUCT.md, DESIGN.md, DDRs, código, testes
```

Figma, screenshots e conversas são material de trabalho. O que precisa sobreviver vai para os arquivos da última linha.

## Quando é ativado

Ativa para: produto novo, tela ou página nova, redesign, portfólio, landing page, ou qualquer tarefa que peça discovery, direção visual, decisão de design system ou protótipo no Figma.

Não ativa para: bug de frontend, ajuste pequeno num design já definido, troca de cor ou texto. Refinamento vai direto para o `frontend-ux-ui` (ou para a `impeccable`) e mantém a identidade existente.

## Fases e profundidade

A triagem classifica o trabalho (marketing/portfólio, tela de produto, design system, redesign, refinamento) e estima o risco pelo público, por dinheiro ou dados pessoais em jogo, pela novidade e pelo custo de errar. O resultado é uma tabela com cada fase marcada como `required`, `light` ou `skip`. "Light" é algumas linhas no chat ou num doc existente, sem arquivo novo. Se alguma fase passar de light, o director para e pede confirmação (gate G0).

Exemplo 1, portfólio pessoal:

| Fase | Profundidade | Por quê |
|---|---|---|
| Frame | light | uma pessoa, objetivo claro |
| UX | light | poucas páginas, navegação simples |
| Referências | required | identidade é o produto |
| Divergir | required | 5-7 territórios, porque o trabalho é de identidade |
| Direção e sistema | light | DESIGN.md curto, sem biblioteca de componentes |
| Protótipo | skip | vai direto para o código |
| Validar | light | sem protótipo, roda no primeiro build durante o QA (G5 checado lá) |
| QA | required | responsivo, contraste, teclado |

Exemplo 2, ferramenta interna de operações financeiras:

| Fase | Profundidade | Por quê |
|---|---|---|
| Frame | required | regras de negócio e ações irreversíveis |
| UX | required | fluxos com erro, permissão e dado parcial |
| Referências | light | padrões conhecidos de tabela e aprovação |
| Divergir | light | 2 territórios ou uma direção argumentada |
| Direção e sistema | required | densidade, semântica de status, componentes de domínio |
| Protótipo | required | validar fluxos críticos no Figma antes do código |
| Validar | required | heurísticas e, se houver, teste com usuários reais |
| QA | required | estados forçados, teclado, axe, severidade 3-4 zerada |

## Peças

Próprias deste repo:

- `design-director` (skill): triagem, plano, gates e roteamento. Não desenha.
- `reference-research` (skill): coleta referências heterogêneas e devolve padrões, divergências, hipóteses e anti-referências em REFERENCES.md.
- `design-critic` (agent): crítica read-only em contexto novo, com heurísticas de Nielsen, severidade 0-4, acessibilidade separada em automática e manual, sem nota geral.
- `frontend-ux-ui` (agent): implementação, rodando como subagent. Se receber trabalho novo ou direcional, para e devolve ao chamador recomendando o director.
- `frontend-screen-design` (skill): objetivo, ação principal e estados de cada tela.

De terceiros: o roteamento completo fica em [`skills/design-director/SKILL.md#routing`](../skills/design-director/SKILL.md#routing). Em resumo:

- Frame: grilling (invocável pelo modelo), ou sugerir que você rode /grill-me (/grill-with-docs se existir CONTEXT.md); agent product-strategist; `impeccable init`.
- Direção visual: impeccable para produto (frontend-design só se a impeccable não estiver disponível); design-taste-frontend só para marketing.
- Resto: impeccable para sistema, crítica e polish; emil-design-eng e animate para motion; humanizer para texto; skills do Figma para o Figma.

## Ferramentas

### Figma

No Claude Code, a recomendação é o plugin oficial:

```sh
claude plugin install figma@claude-plugins-official
```

Ele usa o mesmo servidor do conector do claude.ai (`https://mcp.figma.com/mcp`), mas traz as skills do Figma em disco e tem precedência sobre o conector (verificado em 2026-09-27: depois de instalar o plugin, `claude mcp list` mostra só `plugin:figma:figma`). Na primeira vez, autentique pelo `/mcp`. Se aparecerem dois, veja o Troubleshooting.

No Codex:

```sh
codex mcp add figma --url https://mcp.figma.com/mcp
codex mcp login figma
```

Limite por assento: em plano Starter ou com assento View ou Collab, o MCP libera cerca de 6 chamadas de ferramenta por mês. Trabalhe num time onde você tenha assento Full ou Dev e confira com a ferramenta `whoami` antes de gastar chamadas.

### Playwright

O `install.sh` registra o Playwright MCP no Claude Code, exceto quando o plugin `playwright@claude-plugins-official` já está ativo; nesse caso ele não registra de novo. Atenção à divergência de versão: o plugin roda `@playwright/mcp@latest`, enquanto o instalador fixa `0.0.82` (sempre no Codex, e no Claude quando não há plugin). Se algo se comportar diferente entre as duas ferramentas, comece por aí.

### Referências

O padrão não pede instalação: busca na web, screenshots seus e Playwright capturando sites ao vivo. Pablooo (gratuito), Mobbin e Refero (pagos) são MCPs opcionais. Detalhes, cuidados de privacidade e comandos em `skills/reference-research/SKILL.md`.

### Só no Claude Code vs. Codex

- `frontend-design` é plugin do Claude Code e agora só serve de fallback, quando a impeccable não está disponível. A direção de produto é a impeccable nas duas ferramentas.
- Sem subagents (Codex ou outra ferramenta), a crítica roda numa sessão nova, só com brief, tarefas, DESIGN.md e screenshots.
- As skills do Figma vêm com o plugin do Claude. No Codex, elas seriam servidas pelo próprio MCP como recursos `skill://figma/...` (verificar: ainda não foi confirmado num Codex real).

## Artefatos

Avise antes de criar qualquer um. Arquivo só existe se tiver conhecimento real para guardar.

| Arquivo | Quando criar | Quando não criar |
|---|---|---|
| PRODUCT.md | Frame required; problema, usuários e critérios de sucesso vão ser consultados de novo | página pontual em que duas linhas no chat bastam |
| UX.md ou FLOWS.md | fluxos com erros, permissões ou várias etapas | site de poucas páginas com navegação óbvia |
| REFERENCES.md | a fase de referências rodou como required | só 1-2 referências citadas de passagem |
| DESIGN.md | existe direção que outra pessoa precisa aplicar | ajuste dentro de um design já documentado |
| VALIDATION.md | há findings com status para acompanhar | crítica rápida sem nada severidade 3-4 |
| docs/ddr/DDR-NNN-slug.md | decisão que alguém vai questionar depois (cards vs. tabela, modal vs. página) | radius, token de cor, copy |

## Gates

São oito (G0 a G7), cada um fechando uma fase (G0 depois da triagem, G1 depois do Frame, até G7 depois de Iterar) com uma pergunta respondida com evidência proporcional ao risco. Qualquer gate pode reprovar e mandar o trabalho de volta a uma fase anterior. Se o protótipo for pulado, a validação roda no primeiro build durante o QA e o G5 é checado lá. A tabela está em `skills/design-director/SKILL.md`.

## Anti-padrões

- Rodar duas skills de direção na mesma superfície (impeccable e design-taste-frontend juntas geram regras de fonte, cor e layout contraditórias).
- Fazer UI antes de Frame e UX quando o risco não é trivial.
- Reportar "UX score" ou qualquer métrica composta inventada.
- Dizer "WCAG compliant" com base num scanner. Scanner acha uma parte dos problemas; o resto é manual.
- Copiar uma referência só. Uma referência não prova padrão nenhum.
- Tratar os defaults do shadcn/ui como design system. É código copiado que você precisa adaptar.
- Deixar o modelo escolher o território vencedor. Quem converge é a pessoa.

## Troubleshooting

**Figma aparece duas vezes em `/mcp`.** Plugin e conector do claude.ai (ou um `claude mcp add` manual) estão ativos juntos. Fique com o plugin: remova o manual com `claude mcp remove figma -s user` ou desative o conector nas configurações do claude.ai.

**Figma para de responder ou devolve limite de uso.** Rode `whoami` e confira plano e assento. Com Starter, View ou Collab, as ~6 chamadas mensais acabam rápido. Mude para um time com assento Full ou Dev.

**Uma skill não dispara.** O roteamento depende do `description:` do frontmatter. Confira se ele descreve a situação em que você está e rode `scripts/check.sh` para validar frontmatter e nomes.

**Playwright duplicado.** Rode `claude mcp list`. Se aparecerem o do plugin e um registrado à mão, remova o manual com `claude mcp remove playwright -s user`.

**design-critic no Codex sem restrição de ferramenta.** A conversão para `.toml` leva só `name`, `description` e as instruções; `tools:` e `model:` ficam de fora. No Codex, o modo read-only depende apenas do que o prompt manda. Revise o `git status` depois de uma crítica.
