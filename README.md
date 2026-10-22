# workflow-claude-codex-etc

Minha configuração pessoal para assistentes de IA: instruções globais (`AGENTS.md`), agentes, skills e commands, mais uma seleção de skills de terceiros com commit fixado. Um script instala tudo no Claude Code, no Codex e nas ferramentas que leem `~/.agents/skills` (Gemini CLI, OpenCode etc.).

O conteúdo cobre engenharia de software, pesquisa acadêmica, produção de vídeo para YouTube e design de produto (UX/UI). Está em português e foi escrito para o meu jeito de trabalhar; se for reaproveitar, leia o `AGENTS.md` antes.

## O que é instalado e onde

| Conteúdo | Claude Code | Codex e afins |
|---|---|---|
| `AGENTS.md` | `~/.claude/CLAUDE.md` (symlink) | `~/.codex/AGENTS.md` (symlink) |
| `agents/*.md` | `~/.claude/agents/` (symlink) | `~/.codex/agents/<name>.toml` (gerado) |
| `skills/*/` | `~/.claude/skills/` (symlink) | `~/.agents/skills/` (symlink) |
| `commands/*.md` | `~/.claude/commands/` (symlink) | `~/.agents/skills/<comando>/SKILL.md` (gerado) |
| Skills de terceiros | `~/.claude/skills/` (cópia) | `~/.agents/skills/` (cópia) |
| Agentes de terceiros | `~/.claude/agents/` (cópia) | `~/.codex/agents/*.toml` (cópia ou conversão) |
| Playwright MCP | `claude mcp add --scope user` (pulado se o plugin `playwright@claude-plugins-official` estiver ativo) | bloco `[mcp_servers.playwright]` em `~/.codex/config.toml` |

Detalhes:

- O conteúdo próprio vira symlink para o repo. As exceções são os agentes no Codex, convertidos de `.md` para `.toml` por `scripts/md-convert.awk`, e os commands, que no Codex viram skills. Arquivos gerados são cópias.
- O nome do `.toml` vem do `name:` do frontmatter. Exemplo: `agents/youtube-master.md` gera `youtube-master.toml`.
- Terceiros são baixados para `~/.local/share/workflow-ai/vendor/<id>` no commit fixado em `third-party.lock` e copiados de lá.
- O motor da impeccable vai para `~/.impeccable/bin/<versão>/impeccable`.
- O Graphify é instalado com `uv tool install`, e a skill dele é copiada para os dois destinos.

O script respeita `CLAUDE_CONFIG_DIR`, `CODEX_HOME`, `XDG_DATA_HOME` e `IMPECCABLE_HOME`.

## Pré-requisitos

Obrigatórios (o script para se faltar algum): `git`, `bash` (3.2 do macOS serve), `awk`, `sed`, `diff`, `cmp`, `mktemp`.

Opcionais (sem eles a parte correspondente é pulada com aviso):

| Ferramenta | Para quê |
|---|---|
| `node` / `npx` | Playwright MCP |
| `claude`, `codex` (CLIs) | registrar o Playwright MCP em cada ferramenta |
| `uv` | Graphify |
| `curl` e `shasum` ou `sha256sum` | baixar e verificar o motor da impeccable |
| `python3` 3.11 ou mais novo | `--harden` e validação do `config.toml` do Codex (usa `tomllib`) |

Sem `tomllib`, o `--harden` no Claude funciona, mas a parte do Codex é pulada, e a checagem do Playwright no `config.toml` cai para um `grep` conservador.

## Instalação rápida

```sh
git clone git@github.com:FelipeDuan/workflow-claude-codex-etc.git
cd workflow-claude-codex-etc
./install.sh --dry-run    # mostra o plano, não altera nada
./install.sh
./install.sh --harden     # recomendado; ver "Segurança"
```

Funciona a partir do fish: o shebang chama o bash, então não é preciso entrar no bash antes.

O script é idempotente. Rodar de novo só mexe no que mudou, e `-v` lista também o que já estava correto. No fim ele imprime um resumo com contagens, o caminho dos backups, symlinks quebrados e avisos.

## Flags

| Flag | Efeito |
|---|---|
| `--dry-run` | Mostra o que seria feito, sem alterar nada. |
| `--only claude` / `--only codex` | Instala só para um alvo. Pode repetir. `codex` inclui `~/.agents/skills`. |
| `--update` | Baixa de novo as fontes de terceiros no SHA fixado. O cache antigo vai para backup. |
| `--no-third-party` | Não instala nada do `third-party.lock`, nem o Graphify. |
| `--no-mcp` | Não configura servidores MCP. |
| `--harden` | Opt-in. Acrescenta variáveis de privacidade e bloqueios da impeccable (ver abaixo). |
| `-v`, `--verbose` | Lista também o que já estava correto. |
| `-h`, `--help` | Mostra a ajuda. |

## Segurança e reversão

Backups: tudo que precisa ser substituído é movido antes para `~/.workflow-ai-backup/<timestamp>/<caminho relativo ao HOME>`. Cada item movido ou copiado ganha uma linha em `MANIFEST.tsv` (caminho original, caminho do backup). O script nunca apaga nada no seu HOME; só remove o próprio diretório temporário.

Nunca são tocados: `~/.codex/auth.json`, históricos, sessões e `~/.claude/plugins`. No `~/.codex/config.toml`, o script só acrescenta blocos no fim (Playwright e, com `--harden`, variáveis de ambiente), sempre com cópia de backup antes. Se o `config.toml` existente não for TOML válido, ele fica intocado.

Outras proteções:

- Se algum destino (`~/.claude/skills`, por exemplo) for um symlink que aponta para dentro do repo, o script para antes de mexer em qualquer coisa.
- Se dois itens fossem instalados no mesmo destino, o script para antes de instalar qualquer item (o download dos terceiros para o cache já terá acontecido).
- Cada fonte de terceiros é baixada no SHA de 40 caracteres do lock, e o script confere o `HEAD` depois do checkout.
- O motor da impeccable é baixado por https e só é instalado se o sha256 bater com o do lock. O script também confere se a versão do lock é a mesma que o launcher da skill pede. Com o motor no cache versionado, a skill não chega a baixar nada sozinha. O binário não é executado durante a instalação.

O `--harden` faz um merge que só acrescenta. Valores existentes diferentes são mantidos, com aviso:

- Claude (`~/.claude/settings.json`): `env` com `IMPECCABLE_NO_TELEMETRY=1`, `IMPECCABLE_NO_UPDATE_CHECK=1` e `DO_NOT_TRACK=1`; `permissions.deny` bloqueando `npx impeccable install`, `npx impeccable update` e `impeccable hooks on` (inclusive com caminho na frente).
- Codex: as mesmas três variáveis em `[shell_environment_policy.set]` no `config.toml`, e o arquivo `~/.codex/rules/workflow-ai.rules`, que proíbe `npx impeccable install|update`. Se o `config.toml` já tiver `shell_environment_policy.set`, nada é alterado e o script mostra o que acrescentar à mão.
- Limitação no Codex: `<caminho>/impeccable hooks on` não é coberto, porque `prefix_rule` casa pelo primeiro token e aqui ele é um caminho variável.

Não existe desinstalador. Para desfazer, use o `MANIFEST.tsv` do run que quer reverter:

```sh
cat ~/.workflow-ai-backup/<timestamp>/MANIFEST.tsv
rm ~/.claude/CLAUDE.md                     # remove só o symlink
mv ~/.workflow-ai-backup/<timestamp>/.claude/CLAUDE.md ~/.claude/CLAUDE.md
```

Para `settings.json` e `config.toml`, o backup é uma cópia do arquivo anterior: basta copiar de volta com `cp`.

## Fontes de terceiros

| Repo | O que se usa | Por quê |
|---|---|---|
| [mattpocock/skills](https://github.com/mattpocock/skills) | 24 skills de engenharia, produtividade e escrita (`code-review` só no Codex) | Fluxos de TDD, diagnóstico de bug, modelagem de domínio, handoff |
| [emilkowalski/skills](https://github.com/emilkowalski/skills) | 13 skills | Acabamento de interface e animações |
| [leonxlnx/taste-skill](https://github.com/leonxlnx/taste-skill) | 13 skills | Evitar cara de template em landing pages e redesigns |
| [pbakaus/impeccable](https://github.com/pbakaus/impeccable) | skill `impeccable`, 2 agentes e o motor binário | Criar, criticar e polir telas |
| [blader/humanizer](https://github.com/blader/humanizer) | `SKILL.md` e `agents/openai.yaml` | Revisar texto que outra pessoa vai ler |
| [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | só `ponytail-review`, `ponytail-audit`, `ponytail-debt` | Achar excesso de engenharia e listar comentários `ponytail:` |
| [sergebulaev/youtube-skills](https://github.com/sergebulaev/youtube-skills) | só `yt-audience-insights`, só o `SKILL.md` | Análise de comentários no modo "cole os comentários/CSV", sem `YOUTUBE_API_KEY` |
| [Graphify](https://github.com/Graphify-Labs/graphify) | CLI `graphifyy` 0.9.70 via `uv` e a skill `graphify` | Opcional; os hooks do Graphify não são instalados |
| [Playwright MCP](https://www.npmjs.com/package/@playwright/mcp) | `@playwright/mcp@0.0.82` via `npx` | Controle de navegador pelo agente |

Incorporado no `AGENTS.md` em vez de instalado: as diretrizes de [andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills) e a escada de simplicidade do ponytail (seção "Simplicidade e escopo").

Ficam de fora de propósito: o plugin e os hooks do ponytail, os hooks da impeccable e os agentes `asset-producer` e `manual-edit-applier` da impeccable.

Renomeações e exceções:

- `prototype` do Emil é instalada como `prototype-ui`, porque colide com a `prototype` do Matt.
- `code-review` do Matt é instalada só no Codex, porque no Claude Code conflita com o `/code-review` nativo.
- A impeccable tem uma variante por ferramenta: `plugin/` para o Claude e `.agents/` para o Codex. No Codex os agentes usam os `.toml` nativos do upstream.

## Figma MCP (manual)

O script não configura o Figma; ele só imprime as instruções. No Claude Code, o recomendado é o plugin oficial, que usa o mesmo servidor do conector do claude.ai e traz as skills do Figma:

```sh
claude plugin install figma@claude-plugins-official
```

Depois confira com `/mcp` que aparece um Figma só. Sem o plugin, ou no Codex:

```sh
# Claude Code (depois autentique com /mcp dentro do Claude Code)
claude mcp add --scope user --transport http figma https://mcp.figma.com/mcp

# Codex
codex mcp add figma --url https://mcp.figma.com/mcp
codex mcp login figma
```

Documentação oficial: https://developers.figma.com/docs/figma-mcp-server/

Limites por assento, duplicidade com o conector e o resto do workflow de design: [docs/design-workflow.md](docs/design-workflow.md).

## Como atualizar

Conteúdo próprio: `git pull`. O que é symlink atualiza na hora. Rode `./install.sh` de novo quando houver arquivo novo, ou quando mudar um agente ou command, porque no Codex esses são cópias geradas.

Terceiros:

1. Descubra o commit novo: `git ls-remote <url> HEAD`.
2. Revise o diff do upstream antes de subir o SHA, por exemplo em `https://github.com/<dono>/<repo>/compare/<sha-antigo>...<sha-novo>`.
3. Troque o SHA na linha `repo` do `third-party.lock`.
4. Rode `./install.sh --update`. Sem `--update`, um cache limpo em outro commit também é trocado para o SHA novo.

Na impeccable, se o `VERSION` do commit novo mudar, atualize também as linhas `engine` (versão, sha256 e URL de cada plataforma). Se as versões não baterem, o script avisa e não instala o motor.

## Como adicionar conteúdo

Skill própria: crie `skills/<nome>/SKILL.md` com `name:` e `description:` no frontmatter e rode `./install.sh`.

Agente próprio: crie `agents/<nome>.md` com frontmatter `name:` e `description:`. O `name:` define o nome do `.toml` no Codex.

Command próprio: crie `commands/<nome>.md`. Coloque um `description:` no frontmatter; sem ele, a skill gerada para o Codex usa a primeira linha do corpo como descrição.

Skill de terceiros: declare o repo (se ainda não existir) e uma linha por skill no `third-party.lock`. Formato documentado no topo do arquivo; exemplos reais:

```
repo  ponytail   https://github.com/DietrichGebert/ponytail     e3ba2aa6f1e6f0bc4d69eb09c9f0d0a93af56156
skill ponytail  skills/ponytail-review  -  claude,codex
skill emil  skills/prototype                     prototype-ui  claude,codex
skill humanizer  .  humanizer  claude,codex  include=SKILL.md,agents/openai.yaml
```

Os campos são tipo, id do repo, caminho de origem, nome de destino (`-` usa o `name:` do frontmatter) e alvos. `include=` copia só os caminhos listados. Depois rode `./install.sh --dry-run` e `./install.sh`.

Antes de instalar, rode `scripts/check.sh`: ele valida frontmatter de skills, agentes e commands, nomes duplicados, a conversão para o Codex, a sintaxe do `install.sh`, symlinks e os SHAs do `third-party.lock`.

## Estrutura

```
AGENTS.md              instruções globais (vira CLAUDE.md no Claude)
agents/                agentes próprios (.md no formato do Claude Code)
skills/                skills próprias (uma pasta com SKILL.md cada)
commands/              slash commands do Claude Code
docs/                  documentação do workflow de design e investigações futuras
third-party.lock       fontes de terceiros com commit fixado
install.sh             instalador
scripts/check.sh       validação estática
scripts/md-convert.awk conversão de agentes e commands para o Codex
scripts/harden.py      merge do --harden em settings.json e config.toml
harden/                regras do Codex instaladas pelo --harden
```

## Sincronizar com o upstream

Este repo é um fork e pode divergir de propósito. Para ver o que mudou no original:

```sh
git fetch upstream
git log --oneline HEAD..upstream/main    # commits que ainda não estão aqui
git diff HEAD...upstream/main            # o que mudou lá desde o ponto em comum
```

Avalie commit por commit e traga só o que fizer sentido (`git cherry-pick <sha>`). Nada de merge às cegas.

## Problemas conhecidos

- Só testado em macOS. O script foi escrito para funcionar também em Linux, mas isso não foi verificado.
- Tirar um item do `third-party.lock` não o desinstala. A cópia continua no HOME até ser removida à mão.
- Symlinks quebrados (por exemplo, depois de apagar uma skill do repo) são listados no resumo, mas não removidos.
- Agentes convertidos para o Codex perdem `tools:` e `model:`. Lá, agentes que deveriam ser só leitura (security-reviewer, software-architect, design-critic) dependem apenas das instruções.
