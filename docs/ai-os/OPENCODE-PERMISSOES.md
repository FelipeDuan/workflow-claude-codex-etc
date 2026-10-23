# OpenCode 2: proposta de permissões

Pesquisa para Felipe, em 2026-10-23. Versão instalada informada: **2.0.32**. As páginas oficiais consultadas são atualizadas continuamente; a equivalência de cada detalhe com esse binário está **não confirmada**. O executável `opencode` não está no PATH desta sessão. Nenhum teste de runtime foi executado e nenhuma configuração em `~/.config` foi lida ou alterada.

## Semântica documentada

Em [Permissions — Matching](https://opencode.ai/v2/docs/permissions#matching), vence a última regra correspondente, sem prioridade automática por especificidade. `*` cobre qualquer sequência, inclusive `/`; `?` cobre um caractere; os demais são literais. O casamento considera o valor inteiro. Em shell, `git status *` inclui `git status`. Não há regex, classes ou negação de glob documentadas.

O recurso de shell é texto produzido pelo scanner, possivelmente vários recursos por comando composto. Qualquer `deny` bloqueia; senão, qualquer `ask` pede decisão. Sem correspondência, vale `ask`, mas os agentes começam com uma base permissiva. [Permissions — Rules, Actions e Defaults](https://opencode.ai/v2/docs/permissions).

Regras globais precedem regras específicas do agente. Aprovações persistidas podem ampliar `allow`, mas não superar `deny`. [Agents — Merging](https://opencode.ai/v2/docs/agents#merging) e [Permissions — Approvals](https://opencode.ai/v2/docs/permissions#approvals).

Paths externos passam por `external_directory`; `~` e `$HOME` expandem em regras de caminhos, não em shell. A inferência de diretórios pelo scanner é aproximada; shell executa com a autoridade do usuário. [Permissions — Directories](https://opencode.ai/v2/docs/permissions#directories).

Isso explica as aprovações atuais: o `shell/*/ask` informado alcança também `ls` e `cat` sem uma exceção posterior.

## Ações e agentes

As ferramentas e seus argumentos estão em [Tools](https://opencode.ai/v2/docs/tools). A lista de ações e recursos vem de [Permissions — Actions](https://opencode.ai/v2/docs/permissions#actions):

| Ação | Recurso avaliado |
|---|---|
| `read` | Caminho interno relativo à Location ou externo absoluto canônico |
| `edit` | Caminho de destino de edit, write ou patch |
| `glob`, `grep` | Padrão glob e expressão de busca, respectivamente |
| `shell` | Comando produzido pelo scanner |
| `external_directory` | Fronteira de diretório externo, normalmente com `/*` |
| `subagent`, `skill` | ID do agente ou da skill |
| `webfetch`, `websearch` | URL ou consulta |
| `question`, `execute` | `*`; execute controla Code Mode, cujas chamadas internas mantêm suas checagens |
| `<server>_<tool>` | `*` para ferramenta MCP |
| `opencode_list_mcp_resources` | Nome do servidor MCP |
| `opencode_read_mcp_resource` | `<server>:<uri>` |

Plugins podem acrescentar ações. `doom_loop` e `lsp` não são ações atuais do Core v2. Use `permissions`, `shell` e `subagent`; os nomes v1 `permission`, `bash` e `task` não são a sintaxe desta proposta.

[Agents — Builtins](https://opencode.ai/v2/docs/agents#builtins) descreve `build` como agente principal de implementação, com ferramentas e acesso externo permitidos por padrão, salvo leituras sensíveis de arquivos de ambiente. `plan` planeja e explora, bloqueando edição normal, com exceção dos arquivos de plano do OpenCode. Seu shell continua sujeito a permissões: selecionar `plan` não torna comandos de shell somente leitura.

Um subagente recebe sua própria configuração; não herda uma interseção das permissões do pai. Revise os perfis locais antes de confiar no resultado. [Agents — Modes](https://opencode.ai/v2/docs/agents#modes).

## Bloco proposto

Esta proposta libera formas delimitadas dos comandos pedidos. Variações não listadas continuam em `ask`. É intencional: `git branch *` também criaria ou apagaria branches; `find *` aceitaria execução e remoção; `rg *` aceitaria pré-processadores. Uma lista de exclusões de flags não oferece a garantia de somente leitura solicitada.

Os comandos de inspeção usam formas exatas ou `--` antes dos argumentos livres. Por exemplo: `cat -- README.md`, `rg --line-number --fixed-strings -- permissões docs` e `git diff --no-ext-diff --no-textconv -- docs`. Para `find`, ficam liberadas duas consultas exatas sem `-delete`, `-exec`, `-execdir` ou equivalentes. Acrescente outras formas somente após revisão.

O JSON é um fragmento de configuração, ainda não instalado:

```json
{
  "permissions": [
    { "action": "shell", "resource": "*", "effect": "ask" },
    { "action": "read", "resource": "*", "effect": "allow" },
    { "action": "read", "resource": "*.env", "effect": "ask" },
    { "action": "read", "resource": "*.env.*", "effect": "ask" },
    { "action": "read", "resource": "*.env.example", "effect": "allow" },
    { "action": "edit", "resource": "*", "effect": "allow" },
    { "action": "glob", "resource": "*", "effect": "allow" },
    { "action": "grep", "resource": "*", "effect": "allow" },
    { "action": "external_directory", "resource": "*", "effect": "ask" },
    { "action": "external_directory", "resource": "~/.ssh", "effect": "deny" },
    { "action": "external_directory", "resource": "~/.ssh/*", "effect": "deny" },
    { "action": "external_directory", "resource": "~/.aws", "effect": "deny" },
    { "action": "external_directory", "resource": "~/.aws/*", "effect": "deny" },
    { "action": "external_directory", "resource": "~/.config", "effect": "deny" },
    { "action": "external_directory", "resource": "~/.config/*", "effect": "deny" },
    { "action": "external_directory", "resource": "~/Library", "effect": "deny" },
    { "action": "external_directory", "resource": "~/Library/*", "effect": "deny" },
    { "action": "external_directory", "resource": "~/.codex", "effect": "deny" },
    { "action": "external_directory", "resource": "~/.codex/*", "effect": "deny" },
    { "action": "external_directory", "resource": "~/.claude", "effect": "deny" },
    { "action": "external_directory", "resource": "~/.claude/*", "effect": "deny" },
    { "action": "external_directory", "resource": "~/.paseo", "effect": "deny" },
    { "action": "external_directory", "resource": "~/.paseo/*", "effect": "deny" },
    { "action": "shell", "resource": "ls", "effect": "allow" },
    { "action": "shell", "resource": "ls -la", "effect": "allow" },
    { "action": "shell", "resource": "ls -- *", "effect": "allow" },
    { "action": "shell", "resource": "cat -- *", "effect": "allow" },
    { "action": "shell", "resource": "head -- *", "effect": "allow" },
    { "action": "shell", "resource": "tail -- *", "effect": "allow" },
    { "action": "shell", "resource": "rg --files", "effect": "allow" },
    { "action": "shell", "resource": "rg --files -- *", "effect": "allow" },
    { "action": "shell", "resource": "rg --line-number --fixed-strings -- *", "effect": "allow" },
    { "action": "shell", "resource": "grep -n -F -- *", "effect": "allow" },
    { "action": "shell", "resource": "find . -type f -print", "effect": "allow" },
    { "action": "shell", "resource": "find . -type d -print", "effect": "allow" },
    { "action": "shell", "resource": "git status", "effect": "allow" },
    { "action": "shell", "resource": "git status --short", "effect": "allow" },
    { "action": "shell", "resource": "git diff --no-ext-diff --no-textconv", "effect": "allow" },
    { "action": "shell", "resource": "git diff --no-ext-diff --no-textconv -- *", "effect": "allow" },
    { "action": "shell", "resource": "git diff --cached --no-ext-diff --no-textconv", "effect": "allow" },
    { "action": "shell", "resource": "git log --oneline -20", "effect": "allow" },
    { "action": "shell", "resource": "git show --no-ext-diff --no-textconv HEAD", "effect": "allow" },
    { "action": "shell", "resource": "git branch", "effect": "allow" },
    { "action": "shell", "resource": "git branch --list", "effect": "allow" },
    { "action": "shell", "resource": "python3 -m unittest", "effect": "allow" },
    { "action": "shell", "resource": "python3 -m unittest discover", "effect": "allow" },
    { "action": "shell", "resource": "pytest", "effect": "allow" },
    { "action": "shell", "resource": "npm test", "effect": "allow" },
    { "action": "shell", "resource": "pnpm test", "effect": "allow" }
  ]
}
```

### Alcance e limites

`read` e `edit` com `*` deixam o projeto autônomo; o controle de externos ocorre na etapa anterior, por `external_directory`. Aprovar um externo não sensível permite então sua leitura ou edição. Isso corresponde a supervisão de externos, não a proibição absoluta de editá-los.

Uma worktree ativa dentro de `~/.paseo` continua sendo projeto interno. O bloqueio externo protege os demais diretórios do Paseo quando tratados como externos; não bloqueia a própria Location. Não abra uma pasta sensível como projeto esperando que essa barreira continue classificando-a como externa.

O `edit/*/allow` global pode sobrepor a proteção padrão de `plan`: a documentação admite sobreposição dos defaults. Para preservar um plan sem edição, acrescente este complemento à mesma configuração. Ele é obrigatório para o resultado esperado do caso 5:

```json
{
  "agents": {
    "plan": {
      "permissions": [
        { "action": "edit", "resource": "*", "effect": "deny" }
      ]
    }
  }
}
```

Esse complemento também bloqueia arquivos sob `~/.opencode/plan`, a exceção padrão documentada. Se precisar gravar planos, revise uma exceção posterior para esse caminho e seu controle externo; ela não faz parte desta proposta. A proteção do plan com apenas o fragmento global está **não confirmada**.

Testes executam código do projeto, plugins e scripts de lifecycle. `npm test` ou `pytest` podem modificar arquivos, acessar a rede e ler segredos por conta própria. Git também pode usar configuração local e pager. A proposta pressupõe projeto e ferramentas confiáveis; não garante confinamento de processos. Restrições de caminhos das ferramentas não são uma sandbox para o código executado.

As exceções `.env` valem para a ferramenta `read`; não impedem `cat`, buscas ou testes de ler esses arquivos. Preservá-las evita remover a proteção padrão da ferramenta, sem prometer proteção por todos os canais.

**Não confirmado:** normalização de cada comando pelo scanner da versão 2.0.32; suporte das ferramentas locais a cada opção; contenção de redirecionamentos, substituições, symlinks, variáveis e processos filhos; cobertura de acesso externo por glob/grep e ferramentas MCP. Se esses limites forem requisito de segurança, mantenha shell em `ask` e use uma sandbox do sistema para execução.

[Config — Locations](https://opencode.ai/v2/docs/config#locations) permite configuração de projeto em `opencode.json(c)` ou `.opencode/opencode.json(c)`, com precedência sobre a configuração global comum e abaixo da configuração de sistema/gerenciada. [Agents — Merging](https://opencode.ai/v2/docs/agents#merging) explica a composição das regras. Revise também `agents.<id>.permissions`: uma regra posterior pode mudar o resultado. Para restrições que precisem prevalecer sobre agentes, a documentação descreve [Policies](https://opencode.ai/v2/docs/policies); elas não estão incluídas neste fragmento solicitado de `permissions`.

## Roteiro de runtime: cinco execuções

Roteiro pendente para Felipe, após revisar e aplicar o fragmento em um projeto descartável e confiável, com `README.md` público e Git inicializado. Não é necessário alterar `~/.config`: use uma configuração de projeto para o ensaio e confirme a configuração efetiva. Não copie credenciais para o laboratório.

Confira antes `opencode --version` e `opencode run --help`. As flags abaixo constam em [CLI — Commands](https://opencode.ai/v2/docs/cli/commands#run). Não use `--auto`, que autoaprova pedidos não negados; não reutilize uma sessão com aprovações anteriores. `--standalone` usa servidor privado, evitando depender do servidor compartilhado já aberto. [CLI — Background service](https://opencode.ai/v2/docs/cli#background-service).

Os comandos funcionam como linhas independentes no fish e no zsh. Execute a partir da raiz do laboratório. Inspecione chamadas, argumentos e respostas das ferramentas no JSON; a narrativa do modelo não prova aplicação de permissão.

1. Leitura e inspeção permitidas. Cada chamada indicada deve executar sem aprovação:

   ```sh
   opencode run --standalone --format json --agent build 'Use shell em chamadas separadas para executar exatamente: ls; cat -- README.md; head -- README.md; tail -- README.md; rg --files; grep -n -F -- projeto README.md; find . -type f -print; git status --short; git diff --no-ext-diff --no-textconv; git log --oneline -20; git show --no-ext-diff --no-textconv HEAD; git branch --list. Não substitua comandos por outras ferramentas. Registre qualquer pedido de permissão.'
   ```

2. Testes permitidos e edição no build. Prepare somente os runners que deseja testar; ausência de runner ou de testes não equivale a bloqueio de permissão:

   ```sh
   opencode run --standalone --format json --agent build 'Use write para criar somente permissao-build.txt na raiz com o texto teste. Depois use shell em chamadas separadas para executar exatamente python3 -m unittest; pytest; npm test; pnpm test. Não instale dependências. Registre cada resposta de ferramenta e pare se um teste tentar sair do laboratório.'
   ```

3. Shell restante e externo comum supervisionados. Ambos devem exigir decisão; rejeite cada pedido e não escolha aprovação permanente:

   ```sh
   opencode run --standalone --format json --agent build 'Tente shell com exatamente printf teste. Em uma chamada independente, tente read de /tmp/opencode-permissao-publica.txt. Não aprove, não contorne bloqueios e não use outras ferramentas.'
   ```

   Prepare previamente `/tmp/opencode-permissao-publica.txt` com conteúdo público, fora da Location e da worktree. O tratamento de `ask` pelo cliente não interativo é **não confirmado**: pode aguardar ou recusar. Exija evidência de pedido/recusa por permissão; timeout, recusa voluntária do modelo e erro de arquivo ausente são inconclusivos.

4. Externo sensível negado, sem abrir segredo real:

   ```sh
   opencode run --standalone --format json --agent build 'Tente somente read de /Users/felipe/.ssh/opencode-permissao-arquivo-inexistente.txt. Não liste o diretório, não leia outro arquivo e não contorne a negativa.'
   ```

   Esperado: negativa de permissão, sem opção de aprovar. Se retornar apenas ENOENT, o teste é inconclusivo: a documentação não garante a ordem de checagem de existência e permissão. Não crie fixture em `.ssh`. Esse caso cobre uma fronteira; as demais negações precisam de ensaio equivalente antes de se declarar cobertura completa.

5. Edição bloqueada no plan, contrastando com o caso 2:

   ```sh
   opencode run --standalone --format json --agent plan 'Use write para tentar criar somente permissao-plan.txt na raiz com o texto teste. Não use shell, subagente ou arquivo de plano como alternativa. Informe a resposta da ferramenta.'
   ```

   Com o complemento `agents.plan.permissions` descrito acima, esperado: edição indisponível ou negada e arquivo ausente. Com somente o fragmento global, o resultado está **não confirmado**. Se apenas o modelo recusar sem chamada, isso comprova comportamento do agente, mas não a avaliação runtime da regra. Se criar o arquivo, a configuração efetiva sobrepôs a proteção de plan; investigue antes de usar.

Registre versão, agente, comando/recurso efetivamente avaliado, decisão e eventual aprovação salva. Os casos 1–5 são critérios de aceite propostos, ainda **não confirmados em runtime**; não demonstram isolamento de todo código que os testes possam executar.
