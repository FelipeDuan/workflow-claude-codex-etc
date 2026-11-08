Eu enviei: "Seguinte, minha namorada fez aqui esse workflow em [https://github.com/whosbea/workflow-claude-codex-etc](https://github.com/whosbea/workflow-claude-codex-etc) , (é literalmente esse que acabei de fazer fork aqui) e quero instalar e usar, quero realmente saber se essas coisas aqui estão boas principalmente para design, e já vou testar pedindo para o claude code idealizar todo meu portfólio, e criar o projeto no figma, mas assim, eu quero saber a melhor forma de usar a IA para poder alcancar os melhores resultados nesse sentido, pois eu percebo que sempre que tento fazer essas coisas, eu tenho um resultado ruim, genérico, cheio de AI Slop, e mesmo tentando dizer a forma como quero, nunca sai do jeito que imagino, e principalmente quando quero que a IA faça um brainstorming para aquilo, aí é pior, fica mais genérico e tudo, então quero que pesquise a fundo na internet sobre o que os profissionais e pesquisadores estão falando sobre isso, sobre como gerar um design realmente de qualidade usando IA, e se as skills que minha namorada usa aqui são legais, eu quero tentar pegar esse workflow dela, e entender os pontos de melhoria e se necessário potencializar bastante"

o GPT respodeu: "Sim. A base que ela montou é boa e, principalmente, está muito acima de “instalar 40 skills e torcer para o Claude ficar com bom gosto”.

O problema que você está sentindo não é falta de prompt. É o **processo criativo inteiro**. E depois de olhar o workflow dela, a documentação atual do Figma/Claude e pesquisas sobre co-criação com IA, eu mudaria bastante a maneira como você usa esse conjunto.

## Minha leitura do workflow dela

O repositório tem algumas decisões muito boas:

- uma fonte única de instruções via `AGENTS.md`, distribuída para Claude e Codex;
- skills próprias separadas das skills de terceiros;
- versões de terceiros fixadas por commit;
- `--dry-run`, backup e opção `--harden`;
- Impeccable;
- Taste Skill;
- skills do Emil Kowalski;
- Playwright MCP;
- Humanizer;
- Figma MCP;
- possibilidade de usar a mesma base com Claude, Codex e outros agentes. :chatgpt-content-reference{index="0"}

A parte de segurança também está bem pensada: o instalador faz backup, evita mexer em autenticação/históricos, valida commits e checksum do Impeccable e oferece endurecimento de privacidade. :chatgpt-content-reference{index="1"}

Então eu **usaria esse projeto como base**.

Só que eu faria um fork seu, em vez de usar permanentemente o dela.

O próprio README avisa que o `AGENTS.md` foi escrito especificamente para o jeito dela trabalhar. :chatgpt-content-reference{index="2"}

---

# O maior problema que encontrei

Há uma lacuna relevante para o que **você especificamente quer fazer**.

O repositório configura o acesso ao Figma, mas trata a integração como algo essencialmente manual. :chatgpt-content-reference{index="3"}

Só que o Figma evoluiu bastante.

Hoje a recomendação oficial para Claude Code é instalar o **plugin oficial do Figma**, que já leva consigo o MCP e Agent Skills próprios para operar corretamente o canvas:

```bash
claude plugin install figma@claude-plugins-official
``` :chatgpt-content-reference{index="4"}


Isso é importante porque agora o MCP não serve somente para “ler um Figma”.

Ele pode **escrever Figma nativo**:

- frames;
- componentes;
- variants;
- variables;
- Auto Layout;
- estilos;
- estrutura real editável. :chatgpt-content-reference{index="5"}


E existem skills próprias como `figma-use` e `figma-generate-design`, que ensinam o agente a montar telas incrementalmente, descobrir tokens/componentes existentes e evitar ficar simplesmente desenhando retângulos com cores hardcoded. :chatgpt-content-reference{index="6"}

Para o seu caso isso é um **upgrade grande**.

---

# E as skills de design que ela escolheu?

### Impeccable — eu manteria com certeza

Talvez seja atualmente a peça mais valiosa desse workflow.

Não é mais simplesmente um “prompt de bom gosto”. O projeto possui:

- `PRODUCT.md`;
- `DESIGN.md`;
- fluxo de `craft`;
- `critique`;
- `audit`;
- `polish`;
- `distill`;
- `animate`;
- dezenas de detectores determinísticos de padrões ruins.

O detector atual cobre **61 regras determinísticas**, incluindo clichês de interface de IA e problemas reais de design/acessibilidade. :chatgpt-content-reference{index="7"}

Isso é muito melhor que:

> “Claude, seja um senior UX designer e faça algo incrível.”

Porque cria critérios verificáveis.

---

### Emil Kowalski — excelente, mas use no momento certo

As skills do Emil são provavelmente as melhores desse conjunto para **motion/design engineering**.

Ele próprio explica que os agentes normalmente erram pequenas decisões como:

- easing;
- duração;
- quando algo deve ou não animar;
- propriedades que devem ser animadas;
- transições;
- interrupções;
- feedback.

E essas pequenas decisões acumuladas separam uma interface excelente de uma que apenas parece “bonita”. :chatgpt-content-reference{index="8"}

Mas eu não usaria Emil para decidir a identidade visual do seu portfólio.

Usaria depois.

---

### Taste Skill — vale a pena, mas com uma ressalva

Ela é interessante especificamente porque tenta combater:

> “same AI-generated landing page syndrome”.

Trabalha:

- composição;
- tipografia;
- spacing;
- motion;
- layout;
- reference boards. :chatgpt-content-reference{index="9"}


Mas a versão atual principal é uma **v2 experimental**. :chatgpt-content-reference{index="10"}

Então eu trataria Taste como uma ferramenta de **direção/pressão criativa**, e não como autoridade absoluta.

---

### Playwright — fundamental

Não só para teste funcional.

Eu faria Claude usar Playwright para:

1. renderizar;
2. tirar screenshot;
3. olhar a screenshot;
4. comparar com a intenção;
5. corrigir;
6. testar mobile;
7. testar desktop.

Isso fecha o ciclo perceptual.

Uma IA produzindo CSS apenas a partir do texto que ela mesma escreveu sofre de algo parecido com revisar um livro sem jamais olhar a página diagramada.

---

### Humanizer

Boa decisão para:

- hero copy;
- About;
- projetos;
- CTAs;
- microcopy.

Não muda seu design diretamente, mas ajuda a evitar outro sinal clássico de portfólio de IA:

> “Crafting digital experiences at the intersection of technology and innovation.”

🤢

---

# Tem outra skill que eu acrescentaria

A oficial de **Frontend Design da Anthropic**.

A versão atual explicitamente orienta Claude a:

- partir do assunto real;
- escolher uma direção estética deliberada;
- evitar aparência de template;
- assumir risco estético justificável;
- criar identidade específica ao contexto. :chatgpt-content-reference{index="11"}


Esse princípio é muito importante:

**não decidir o estilo primeiro e colocar o conteúdo dentro.**

A identidade deve sair de:

> pessoa → contexto → conteúdo → narrativa → estética.

E não:

> “vamos fazer dark mode + serif + glow + glassmorphism porque parece premium.”

---

# Mas cuidado: mais skills ≠ design melhor

Esse é talvez o ponto que eu mais mudaria no workflow.

Imagine:

```text
Taste
+ Impeccable
+ Anthropic Frontend Design
+ Emil
+ outra UI skill
+ outra UX skill
+ CLAUDE.md gigante
```

Todas tentando dirigir Claude ao mesmo tempo.

Você cria uma espécie de:

**design by committee de agentes.**

Uma diz:

> ousado.

Outra:

> reduza ruído.

Outra:

> use assimetria.

Outra:

> maximize clareza.

Outra:

> surpreenda.

E Claude resolve o conflito fazendo uma média.

Resultado:

> bonito, correto e completamente esquecível.

---

# Por isso eu criaria UMA skill nova no seu fork

Algo como:

```text
design-director
```

Não seria outra skill ensinando cores e tipografia.

Seria uma **orquestradora**.

Algo assim:

```text
design-director
│
├── discover
│   ├── pesquisa
│   ├── identidade
│   ├── audiência
│   └── conteúdo
│
├── diverge
│   ├── gerar territórios
│   └── NÃO criar UI ainda
│
├── art-direct
│   ├── frontend-design
│   └── taste
│
├── prototype
│   └── Figma
│       ├── figma-use
│       └── figma-generate-design
│
├── build
│   └── frontend-design
│
├── review
│   ├── Playwright
│   ├── Impeccable critique
│   └── human review
│
└── polish
    ├── Impeccable
    └── Emil motion
```

Isso muda completamente o jogo.

---

# Por que seu brainstorming com IA costuma ficar ruim

Existe pesquisa interessante exatamente sobre isso.

Um experimento com ideação visual encontrou que participantes usando imagens geradas por IA tiveram:

- **menos ideias**;
- **menos variedade**;
- **menor originalidade**;
- mais fixação na primeira referência. :chatgpt-content-reference{index="12"}


Outro trabalho chama isso explicitamente de **Generative AI Design Fixation**: o próprio modelo tende a explorar uma região pequena do espaço de soluções e repetir estruturas familiares. :chatgpt-content-reference{index="13"}

E pesquisa mais recente sobre co-criação encontrou melhores resultados quando o fluxo é dividido explicitamente em:

**divergent thinking → convergent thinking**, em vez de uma conversa linear do tipo prompt → resultado → “melhore isso”. :chatgpt-content-reference{index="14"}

Isso encaixa perfeitamente com a sua experiência.

---

# O padrão ruim

Você manda:

> Quero um portfólio criativo, moderno, premium, elegante, diferente e muito bonito.

Claude pensa:

```text
developer portfolio
↓
dark
↓
serif heading
↓
sans body
↓
big hero
↓
cards
↓
gradient
↓
projects grid
↓
bento
```

Pronto.

A árvore criativa morreu em aproximadamente 800 ms.

😂

---

# O fluxo que eu usaria com IA

## Fase 1 — nenhuma tela

Primeiro Claude deve entender:

- quem é você;
- quais trabalhos devem aparecer;
- quem você quer impressionar;
- qual impressão deve permanecer;
- qual é sua personalidade;
- quais aspectos técnicos realmente o diferenciam;
- que narrativa seu portfólio conta.

E isso vai para:

```text
PRODUCT.md
```

ou

```text
design/BRIEF.md
```

---

# Fase 2 — referências reais

Aqui existe um erro enorme no uso de IA.

Você tenta **descrever sua imaginação em português**.

> “Quero moderno mas não muito moderno, clean mas diferente, premium e meio tecnológico…”

Há milhares de interpretações possíveis.

É muito melhor dar:

- 5 sites que você ama;
- 5 screenshots;
- 3 referências tipográficas;
- 2 movimentos que gosta;
- referências que odeia.

Não diga apenas:

> minimalista.

Diga:

```text
Gosto da escala tipográfica daqui.
Gosto da navegação daqui.
Gosto do ritmo vertical daqui.
Gosto do movimento daqui.
NÃO gosto do hero daqui.
NÃO quero esse padrão de cards.
```

Isso é absurdamente mais informativo.

---

# Fase 3 — territórios, não layouts

Aqui eu faria Claude criar **5 a 7 territórios visuais radicalmente diferentes**.

Não:

> opção 1 azul  
> opção 2 roxo  
> opção 3 preto

Mas algo como:

### Territory A — Engineering Notebook

Portfolio como caderno técnico vivo.

Referências:

- diagramas;
- ADRs;
- commits;
- terminal;
- notas;
- arquitetura.

---

### Territory B — Technical Editorial

Portfolio como revista de engenharia.

- tipografia editorial;
- grandes títulos;
- cases longform;
- whitespace;
- gráficos técnicos.

---

### Territory C — System Interface

Você como “sistema operacional”.

- command palette;
- system status;
- projetos como processos;
- carreira como timeline operacional.

---

### Territory D — Digital Laboratory

- experimentos;
- protótipos;
- diagrams;
- interactive simulations;
- project artifacts.

---

### Territory E — Quiet Engineering

Quase brutalmente minimalista.

- tipografia;
- grid;
- conteúdo;
- precisão;
- microinterações mínimas.

Percebe?

Agora estamos explorando **conceitos**, e não presets de Tailwind.

---

# E existe uma regra muito importante

Os conceitos precisam ser **ortogonais**.

Eu colocaria na sua skill:

```text
A direction is invalid if it could be obtained from another
direction merely by changing colors, typography, border radius,
or decorative treatment.
```

Isso sozinho melhora absurdamente brainstorming de IA.

---

# Fase 4 — você escolhe elementos

Não peça:

> qual é a melhor?

Peça para decompor:

```text
A:
narrativa excelente
layout médio
motion excelente

B:
tipografia excelente
narrativa fraca

C:
interação excelente
legibilidade ruim
```

E então você pode dizer:

> Quero a narrativa do A, tipografia do B e modelo de interação do C.

Isso preserva sua agência criativa.

---

# Fase 5 — DESIGN.md

Só depois eu criaria:

```text
DESIGN.md
```

Com:

```text
Visual thesis
Design principles
Typography
Color
Grid
Spacing
Shape language
Imagery
Motion
Interaction
Density
Responsive behavior
Accessibility
Signature elements
Anti-patterns
```

O Impeccable já está caminhando exatamente nessa direção e possui suporte a um `DESIGN.md` estruturado para manter agentes alinhados. :chatgpt-content-reference{index="15"}

---

# Fase 6 — Figma

Agora sim:

```text
Claude → Figma MCP
```

E eu não pediria:

> faça meu portfólio.

Pediria:

```text
Create:
00 Foundations
01 Components
02 Explorations
03 Desktop
04 Mobile
05 Motion Notes
```

Primeiro:

```text
Foundations
```

Depois:

```text
tokens
type scale
spacing
grid
colors
```

Depois:

```text
components
```

Depois:

```text
hero explorations
```

Depois:

```text
full page
```

A própria documentação do Figma recomenda mudanças grandes **incrementalmente**, inspecionando a estrutura antes e trabalhando em etapas menores. :chatgpt-content-reference{index="16"}

---

# E aqui está outra melhoria enorme

Não gere apenas **uma home** no Figma.

Eu faria:

```text
Hero A
Hero B
Hero C

Projects A
Projects B
Projects C
```

lado a lado.

O canvas do Figma é especialmente bom justamente por permitir comparação espacial, enquanto chat linear nos força a olhar uma única solução por vez.

---

# Fase 7 — construir

Somente quando a direção estiver aprovada:

```text
Figma
  ↓
Claude Code
  ↓
Next
```

O MCP consegue extrair:

- component structure;
- variables;
- layout;
- tokens;
- design context. :chatgpt-content-reference{index="17"}


E mais tarde você pode até usar Code Connect para aproximar:

```text
Figma Component
↕
React Component
``` :chatgpt-content-reference{index="18"}


---

# Fase 8 — crítica separada da criação

Outra mudança que eu considero fundamental.

Não faça:

```text
Claude cria
Claude pergunta se ficou bom
Claude diz que ficou bom
```

😂

Use papéis separados.

### Generator

Cria.

### Critic

Não recebe justificativa do Generator.

Analisa screenshot.

### Auditor

Analisa:

- acessibilidade;
- consistência;
- spacing;
- responsive;
- overflow;
- contrast;
- UX.

### Motion reviewer

Emil.

### Deterministic checker

Impeccable.

Isso reduz o viés de defender a própria criação.

---

# Minha arquitetura ideal

Eu transformaria seu fork em algo assim:

```text
workflow-ai/
│
├── AGENTS.md
│
├── agents/
│   ├── design-director.md
│   ├── design-critic.md
│   ├── ux-researcher.md
│   └── visual-qa.md
│
├── skills/
│   ├── design-director/
│   ├── design-discovery/
│   ├── design-diverge/
│   ├── design-converge/
│   └── visual-qa/
│
└── third-party
    ├── impeccable
    ├── taste
    ├── emil
    ├── anthropic frontend-design
    └── humanizer
```

E **não** colocaria todas essas regras dentro do `CLAUDE.md`.

O global deve ser pequeno.

Algo como:

```text
When doing design work:
route through design-director.

Do not start implementation before the visual direction
has been intentionally chosen.

Prefer references and artifacts over vague aesthetic adjectives.

During ideation, maximize divergence.
During execution, maximize consistency.
During review, maximize criticism.
```

Só.

---

# Portanto, para instalar agora

Eu faria primeiro exatamente isso:

```bash
git clone git@github.com:whosbea/workflow-claude-codex-etc.git
cd workflow-claude-codex-etc

./install.sh --dry-run
./install.sh --harden
```

O próprio projeto recomenda essa sequência e o instalador é idempotente. :chatgpt-content-reference{index="19"}

Depois:

```bash
claude plugin install figma@claude-plugins-official
```

Depois entre no Claude Code:

```bash
claude
```

e confira:

```text
/mcp
```

O Figma deve aparecer conectado ou solicitar autenticação. A instalação oficial recomendada atualmente é justamente pelo plugin do Figma. :chatgpt-content-reference{index="20"}

---

# E NÃO começaria seu teste com

> Idealize todo meu portfólio e crie no Figma.

Eu começaria com algo desta natureza:

Quero iniciar um processo completo de direção de arte e design para o meu portfólio pessoal.

Não crie telas, não escreva código e não altere o Figma ainda.

Nesta primeira etapa, aja como meu design director e conduza somente discovery e exploração divergente.

O objetivo não é chegar rapidamente a uma solução plausível. Quero evitar design fixation, convergência prematura, padrões recorrentes de portfolios de desenvolvedores e qualquer estética genérica de AI-generated UI.

Use as skills disponíveis como ferramentas especializadas, mas não misture indiscriminadamente todas as regras de design ao mesmo tempo. Nesta fase, priorize investigação, estratégia e direção criativa.

### 1. Discovery

Primeiro investigue profundamente:

- quem eu sou;
- minha trajetória;
- o tipo de profissional que quero transmitir que sou;
- público principal do portfólio;
- objetivos profissionais;
- trabalhos e projetos que realmente merecem destaque;
- conhecimentos técnicos que me diferenciam;
- características pessoais que deveriam aparecer na experiência;
- o que quero que alguém lembre 24 horas depois de visitar o site.

Identifique informações que já estejam disponíveis no projeto ou no contexto antes de perguntar algo.

Crie um documento de produto/brief durável com as conclusões.

### 2. References e anti-references

Quero trabalhar a partir de referências concretas e não apenas adjetivos abstratos.

Ajude-me a decompor referências em características como:

- composição;
- grid;
- hierarquia;
- typography;
- density;
- art direction;
- interaction;
- motion;
- imagery;
- navigation;
- storytelling.

Também mantenha explicitamente uma lista de anti-references e padrões que não queremos reproduzir.

### 3. Divergent exploration

Antes de desenhar qualquer interface, crie entre 5 e 7 territórios criativos substancialmente diferentes.

IMPORTANTE:

Duas direções não contam como diferentes se uma puder se transformar na outra apenas mudando:

- cores;
- fontes;
- radius;
- sombras;
- ornamentos;
- background.

Cada território precisa possuir uma ideia central própria.

Para cada território descreva:

- conceito;
- metáfora;
- narrativa;
- layout grammar;
- typography philosophy;
- color philosophy;
- imagery;
- interaction model;
- motion philosophy;
- signature element;
- como os projetos seriam apresentados;
- como a personalidade apareceria;
- riscos;
- coisas que deliberadamente NÃO faria.

Evite automaticamente:

- landing page SaaS;
- bento grid sem justificativa;
- hero centralizado convencional;
- gradient glow gratuito;
- glassmorphism gratuito;
- cards dentro de cards;
- badges decorativos;
- excesso de rounded rectangles;
- texto genérico de IA;
- ícones dentro de quadrados apenas como decoração;
- efeitos que poderiam pertencer a qualquer produto.

Não substitua esses clichês simplesmente por outro conjunto fixo de clichês.

### 4. Comparison

Depois de gerar TODOS os territórios, compare-os.

Não escolha um vencedor.

Mostre quais características interessantes existem em cada um e quais elementos poderiam ser combinados sem destruir sua coerência conceitual.

Pare nesse momento para que eu possa participar da decisão criativa.

### Regra fundamental

Durante ideação, maximize diversidade.

Durante convergência, maximize intenção.

Durante implementação, maximize consistência.

Durante revisão, maximize espírito crítico.

O Figma só deverá ser utilizado depois que escolhermos uma direção.

Esse prompt vai produzir resultados **muito melhores** que “faça algo incrível”.

---

# O que eu mudaria no repositório dela

Há cinco mudanças que eu faria antes de chamar o setup de “workflow de design definitivo”:

1. **Integrar o plugin oficial atual do Figma**, em vez de deixar apenas instruções de MCP manual. O plugin já traz as skills adequadas para `use_figma`. :chatgpt-content-reference{index="21"}

2. **Adicionar uma camada de orchestration para design**, para evitar ativar Taste + Impeccable + Emil + frontend-design simultaneamente.

3. **Separar geração de avaliação** com `design-director` e `design-critic`.

4. **Criar artefatos duráveis**, particularmente:
   ```text
   PRODUCT.md
   DESIGN.md
   REFERENCES.md
   DECISIONS.md
   ```

5. **Transformar Playwright em parte obrigatória do visual QA**, e não apenas ferramenta disponível.

---

Também corrigiria dois detalhes que o próprio repositório reconhece: os commands convertidos para Codex ainda têm descrições fracas, e remover algo do `third-party.lock` não o remove automaticamente do HOME. :chatgpt-content-reference{index="22"}

---

## A ideia central

A melhor maneira de usar IA para design não é tentar construir um:

> **“super designer autônomo”.**

É construir um:

> **processo criativo aumentado por IA.**

Onde você continua sendo **creative director**.

A IA faz muito bem:

```text
explorar
gerar
variar
executar
comparar
criticar
medir
refinar
```

Mas ela ainda é particularmente vulnerável a:

```text
default aesthetics
training-data priors
premature convergence
design fixation
self-reinforcing iterations
```

E é justamente por isso que você tem a sensação de que **“eu explico, explico, explico e ainda sai com cara de IA”**.

Não faltava adjetivo no prompt.

Faltava mudar a topologia do processo.

E, para o seu portfólio especificamente, eu iria além: faria o design derivar da sua identidade como engenheiro de software — projetos, arquitetura, experimentos, documentação, decisões técnicas, trajetória — em vez de tentar parecer apenas “um site bonito de desenvolvedor”. Isso abre espaço para uma identidade que dificilmente sairia de um template de portfolio."

---

Eu enviei: "Show demais, e acho que isso pode ser incrementado tendo todo um processo de análise da experiência de usuário e da construção da interface (UX/UI) e avaliando se o fluxo é realmente consistente, se é possível simplificá-lo, se não só cobre (soluciona) o que o problema pede, mas sim realmente resolve da melhor forma (se é bem idealizada, bem planejada), e tudo isso com métricas, e uma coisa que você falou e que é muito verdade é a dificuldade de explicar coisas abstratas e torná-las concretas, e tudo isso impacta diretamente não só o fluxo e interação com a aplicação (seja SaaS, landing page, etc...), mas também o design system e consistência de componentes (haja vista que hoje em dia muito se recorre a shadcn cru e ficam tudo com a mesma cara, aí o projeto perde a oportunidade de ter algo único - não tô dizendo que é errado usar shadcn, mas ela puramente como é faz com que o projeto já fique mais genérico, ainda mais por conta que tantas IAs e soluções simplesmente o adotam sem ajustar ou mudar nada, sem antes planejar de fato a identidade daquele solução, e sem antes verificar se não existem alternativas mais adequadas, se o uso de cores é correto, como vai funcionar, as vezes a IA deixa muito seca a página - bem vazia, quase sem componentes - as vezes deixa a página cheia de informações, quando é possível repaginar aquelas informações, exibindo de uma maneira muito mais inteligente e não só uma tabela, as vezes por cards, juntamente de hover, as vezes com carousels, e as vezes esse uso fica ruim também - tem situações em que os cards e carousels não ficam legais, e acontece mesmo, por isso a importância de planejar tudo isso e avaliar se realmente faz sentido). E quero realmente validar as coisas, com métricas, com as skills, manter as decisões documentadas, validar o protótipo no figma e tudo mais. E nesse workflow, eu percebo que ele é geral sobre as coisas, então eu queria avaliar até mesmo a possibilidade de usar o JEV (não sei bem o que são mas ouvi recentemente e penso que pode ser interessante, não sei como usar e nem se possível assim), e talvez até ver se tem graphify para criar um cérebro (queria ver se isso realmente faz sentido, se é bom, se economiza tokens, e tudo mais.), ou se as camadas dela já forem realmente maduras, deixar como está, e focar só nessa parte de design e avaliar se essas coisas que pensei impactam também na parte de design, talvez eu possa ir fazendo melhorias gerais aos poucos e no momento focar bem nessa parte de design então, o que acha disso tudo? Se necessário pesquise mais para avaliar essas coisas"

o GPT respodeu: "Sim. O que você descreveu muda bastante a proposta: em vez de uma skill para “deixar interfaces bonitas”, dá para construir uma **disciplina de Product Design assistida por IA**, cobrindo problema → UX → fluxo → direção visual → design system → protótipo → validação → implementação → QA.

E depois de pesquisar mais, eu seguiria exatamente a estratégia que você sugeriu: **não reestruturaria agora o workflow geral da Bea**. Ele já tem boas fundações de planejamento, delegação, simplicidade, revisão e Playwright; inclusive já separa `product-strategist` de `frontend-ux-ui` e diz explicitamente que uma interface bonita não compensa um fluxo confuso. :chatgpt-content-reference{index="1"} O que está subdesenvolvido é a profundidade do processo de design: a skill própria atual de tela é resumida essencialmente a objetivo, ação principal, estados, mobile/desktop e microcopy. :chatgpt-content-reference{index="2"}

Então eu faria um **Design Pack vertical**, e iria evoluindo o restante do workflow depois.

O conjunto de terceiros já instalado também é um ótimo ponto de partida: Emil, Taste, Impeccable, Humanizer, Graphify e Playwright estão de fato integrados ao instalador. :chatgpt-content-reference{index="3"}

## A principal mudança de mentalidade

Você apontou algo que considero fundamental:

> A pergunta não é “qual componente fica bonito aqui?”, mas “qual representação desta informação reduz melhor o esforço do usuário para atingir o objetivo?”.

Isso muda tudo.

Uma tabela pode ser excelente.

Uma tabela pode ser péssima.

Um card pode ser excelente.

Um card pode ser péssimo.

Carousel, tabs, progressive disclosure, master-detail, timeline, command palette, visualization, inline editing, drawer, wizard, dashboard, kanban etc. são **estruturas de interação**, não decorações.

A IA hoje frequentemente faz:

```text
informação
↓
"preciso mostrar isso"
↓
cards
```

ou:

```text
lista de objetos
↓
table
```

O workflow que estamos pensando precisa forçá-la a passar por:

```text
Qual é a tarefa do usuário?
↓
O que ele precisa perceber?
↓
O que ele precisa comparar?
↓
O que precisa decidir?
↓
Qual informação é primária?
↓
O que pode ser progressive disclosure?
↓
Qual modelo de interação reduz esforço?
↓
Só então:
qual componente representa melhor isso?
```

Isso é **UX antes de UI**.

---

# Inclusive, sobre shadcn: você identificou corretamente o problema

Curiosamente, a própria documentação do shadcn hoje diz:

> “This is not a component library. It is how you build your component library.”

A proposta é justamente entregar o código para que ele seja adaptado ao seu design system. :chatgpt-content-reference{index="4"}

Portanto, o problema não é:

> shadcn = genérico.

É:

> `npx shadcn add ...`  
> Claude usa defaults  
> acabou.

Isso é deixar de fazer a parte que o próprio shadcn espera que você faça.

E há uma mudança bem recente: desde julho de 2026, **novos projetos shadcn usam Base UI como base padrão**, embora Radix continue suportado. A própria equipe recomenda Base UI para novos projetos e explicitamente desencoraja trocar uma aplicação existente apenas por trocar. :chatgpt-content-reference{index="5"}

Então eu colocaria uma regra explícita no nosso processo:

> **Nunca selecionar biblioteca visual antes de definir a linguagem visual e os requisitos comportamentais do produto.**

Talvez seja shadcn.

Talvez Base UI diretamente.

Talvez Radix, que oferece primitives sem estilo justamente para construir um design system próprio. :chatgpt-content-reference{index="6"}

Talvez componentes nativos.

Talvez algo específico do domínio.

Talvez um componente realmente custom.

A stack vira **consequência do design**, não o design consequência da stack.

---

# Como eu estruturaria essa vertical

Eu não faria 15 agentes. Isso seria exatamente o tipo de overengineering que o próprio workflow tenta evitar.

Faria quatro responsabilidades principais e skills menores por baixo:

```text
DESIGN DIRECTOR
      │
      ├─────────────── PRODUCT / UX
      │                    │
      │              problema e evidência
      │              tarefas e jornadas
      │              IA e fluxos
      │              simplificação
      │              usability
      │
      ├─────────────── ART DIRECTION / UI
      │                    │
      │              referências
      │              territórios
      │              identidade
      │              composição
      │              visual language
      │
      ├─────────────── DESIGN SYSTEM
      │                    │
      │              tokens
      │              primitives
      │              componentes
      │              padrões
      │              estados
      │              acessibilidade
      │
      └─────────────── DESIGN CRITIC / QA
                           │
                     heuristics
                     métricas
                     Figma validation
                     screenshots
                     Playwright
                     regression
```

O `design-director` é o **orquestrador**.

Ele não tenta ser especialista em tudo simultaneamente.

---

# E o pipeline fica muito mais interessante

Eu usaria algo parecido com isto:

| Gate | Pergunta que precisa estar respondida | Artefato |
|---|---|---|
| G0 — Problem | Estamos resolvendo o problema certo? | `PRODUCT.md` |
| G1 — UX | O usuário consegue atingir o objetivo com o menor atrito razoável? | `UX.md` + `FLOWS.md` |
| G2 — Direction | Exploramos soluções realmente diferentes antes de convergir? | `EXPLORATIONS.md` |
| G3 — System | Existe uma linguagem consistente e reutilizável? | `DESIGN.md` + Figma Foundations |
| G4 — Prototype | O fluxo funciona como experiência, não só como screenshot? | Prototype Figma |
| G5 — Validation | Usuários conseguem realmente utilizá-lo? | `VALIDATION.md` |
| G6 — Build | A implementação preserva a intenção do design? | aplicação |
| G7 — QA | Funciona em estados, resoluções e entradas reais? | relatório visual/UX |
| G8 — Production | O comportamento real confirma nossas hipóteses? | métricas do produto |

E cada gate pode **reprovar**.

Isso é importante.

Claude não deveria fazer:

```text
PRODUCT.md ✅
UX ✅
FIGMA ✅
CODE ✅
```

apenas porque produziu arquivos.

Tem que existir:

```text
evidence → hypothesis → design → test → result
                               ↑          ↓
                               └── revise ┘
```

---

# E sim: dá para medir UX

Esse é outro ponto que eu acho excelente da sua ideia.

Não queremos transformar UX numa falsa matemática do tipo:

> “esse design tem 94/100 UX”.

Isso seria uma métrica inventada.

Mas existem medidas bastante úteis.

A literatura de medição de usabilidade costuma separar **eficácia, eficiência e percepção**. Completion rate, tempo de tarefa, erros e dificuldade percebida são exemplos clássicos. :chatgpt-content-reference{index="7"}

Eu faria o nosso processo registrar para tarefas críticas:

```text
Task Success Rate
Time on Task
Critical Error Rate
Recoverable Errors
Backtracking / unnecessary steps
Assistance required
SEQ
```

O **SEQ — Single Ease Question** é particularmente útil: depois de cada tarefa, o usuário avalia em escala de 1–7 o quão difícil/fácil foi completá-la. Há dados normativos extensos e estudos recentes continuam mostrando relação com outras medidas de tarefa. :chatgpt-content-reference{index="8"}

Exemplo:

```text
TASK
"Criar um novo colaborador e atribuí-lo ao projeto X."

Success criteria:
- colaborador criado
- projeto correto
- permissões corretas

Prototype A
Success: 7/8
Median successful time: 48s
Critical errors: 1
Average SEQ: 5.1

Prototype B
Success: 8/8
Median successful time: 31s
Critical errors: 0
Average SEQ: 6.2
```

Agora temos evidência.

Ainda cabe julgamento humano, mas deixamos de discutir exclusivamente:

> “acho B mais intuitivo”.

---

# E também teremos avaliações sem usuários

Antes de testes formais, o agente pode fazer **heuristic evaluation**.

As heurísticas de Nielsen continuam cobrindo coisas muito relevantes:

- visibilidade do estado;
- correspondência com o mundo real;
- controle e liberdade;
- consistência;
- prevenção de erros;
- reconhecimento em vez de memorização;
- eficiência;
- design estético/minimalista;
- recuperação de erros;
- ajuda. :chatgpt-content-reference{index="9"}

Aqui eu faria algo mais rigoroso que:

> “revise a UX”.

O critic produziria:

```text
Finding UX-017

Flow:
Create invoice

Heuristic:
H5 — Error prevention

Evidence:
Changing customer after adding items silently resets taxes.

Severity:
3 / 4

Affected task:
Create invoice

Expected consequence:
Potentially unexpected total and rework.

Suggested experiments:
A. confirmation dialog
B. preserve products and recompute
C. disable customer change after item addition

Status:
Needs product decision
```

Isso gera histórico.

---

# E acessibilidade também vira gate

Não apenas:

> “use aria-label”.

Por exemplo, WCAG 2.2 introduziu critérios específicos para foco não ficar oculto, alternativas a dragging e tamanho mínimo de alvos. O AA para pointer target estabelece 24×24 CSS px ou espaçamento equivalente; contraste textual normal continua em 4.5:1. :chatgpt-content-reference{index="10"}

Então o Design Pack pode ter verificações determinísticas sempre que possível:

```text
contrast
keyboard path
focus visibility
focus order
target size
text resize
reflow
reduced motion
semantic elements
screen-reader labels
```

Aqui ferramentas ganham da opinião do agente.

---

# Figma deixa de ser só desenho

Essa é uma parte que quero muito colocar no seu fluxo.

O protótipo deveria ser **interativo o suficiente para validar a hipótese**.

Figma suporta variables, modes, componentes e lógica condicional de protótipo. As variables podem inclusive controlar conteúdo, dimensões, visibilidade e estados, e combiná-las com condições `if/else`. :chatgpt-content-reference{index="11"}

Então para um SaaS eu não quero apenas:

```text
Dashboard.png
Users.png
Create-user.png
```

Quero:

```text
Dashboard
    ↓
Search
    ↓
empty state
    ↓
result
    ↓
select
    ↓
details
    ↓
edit
    ↓
validation error
    ↓
success
```

Testável.

---

# O design system também precisa nascer diferente

Eu separaria:

```text
Foundations
├── color semantics
├── typography
├── spacing
├── dimensions
├── radius
├── elevation
├── motion
└── breakpoints

Primitives
├── Button
├── Input
├── Select
├── Dialog
└── ...

Patterns
├── Search + Filter
├── Bulk actions
├── Creation flows
├── Empty states
├── Confirmation
└── Error recovery

Domain Components
├── EmployeeCard
├── PriceComparison
├── ContractStatus
└── ...
```

Essa última camada é frequentemente esquecida pelas IAs.

Elas fazem:

```text
Button
Card
Input
Select
Table
```

e dizem:

> Design system pronto.

Não.

O produto ganha identidade principalmente quando começa a existir **linguagem própria de domínio**.

---

# E o nosso `DESIGN.md` não deve dizer simplesmente

```text
Use shadcn.
Border radius 8.
Primary blue.
```

Isso perpetua o problema.

Deveria conter coisas como:

```text
Design Thesis

Information Hierarchy

Interaction Principles

Density Strategy

Navigation Model

Visual Grammar

Typography Principles

Color Semantics

Data Visualization Principles

Motion Principles

Component Anatomy

Domain Patterns

Responsive Strategy

Accessibility Contract

Anti-patterns

Reference rationale
```

Assim Claude sabe **por que** uma decisão existe.

---

# E documentação de decisão entra muito bem aqui

Eu criaria um pequeno ADR equivalente para design:

```text
DDR — Design Decision Record
```

Por exemplo:

```text
DDR-004
Dashboard employee representation

Decision:
Use compact rows with expandable detail.

Rejected:
Large employee cards.

Why:
Primary user task is comparing 20–60 employees.
Cards reduce information density and make comparison harder.

Evidence:
Prototype test P-03.

Metrics:
Rows:
8/8 success, median 27s

Cards:
7/8 success, median 43s

Revisit when:
Primary use case changes from comparison to individual browsing.
```

Isso é ouro para IA.

Na próxima sessão, ela não resolve de novo um problema já resolvido.

---

# Aí chegamos ao Graphify

Aqui minha opinião ficou mais definida depois da pesquisa.

**Graphify é interessante, mas eu não trataria como “o cérebro”.**

Ele cria um knowledge graph real de:

- código;
- documentos;
- SQL;
- configurações;
- PDFs;
- e outros artefatos.

Código é analisado localmente através de AST/tree-sitter; documentos e mídia podem passar por uma etapa semântica. As arestas são marcadas como `EXTRACTED` ou `INFERRED`, o que é uma boa característica para rastreabilidade. :chatgpt-content-reference{index="12"}

Então imagine:

```text
PRODUCT.md
   │
   ├─ requires → FLOW-03
   │                │
   │                └─ implemented-by → src/...
   │
DESIGN.md
   │
   └─ defines → component pattern
                    │
                    └─ used-by → pages/...
```

Para uma aplicação grande isso pode ficar muito interessante.

### Mas ele não substitui nossos documentos.

A verdade continua sendo:

```text
Canonical knowledge
=
PRODUCT.md
UX.md
DESIGN.md
DDR/*
source code
tests
```

Graphify seria:

```text
derived knowledge structure
```

Se apagar o Graphify amanhã, o projeto continua inteligível.

Essa é uma propriedade arquitetural muito saudável.

---

# Sobre economia de tokens do Graphify

O site deles mostra relatos de reduções enormes, como `79×` e `71.5×`, porque o agente consulta relações no grafo em vez de reler arquivos. :chatgpt-content-reference{index="13"}

Mas eu **não tomaria esses números como benchmark universal**.

São números apresentados pelo próprio fornecedor e depoimentos/casos selecionados.

Para nós, eu faria um experimento.

Mesmo tarefa:

```text
A — Claude normal
B — Claude + Graphify
```

Medir:

```text
input tokens
output tokens
tool calls
files opened
wall-clock time
correctness
missed dependencies
wrong assumptions
```

Em um monorepo grande, acredito que o ganho possa ser significativo.

No seu portfólio com:

```text
23 arquivos
```

provavelmente é desperdício.

Esse tipo de decisão deve ser automática pelo tamanho/complexidade do projeto, não ideológica.

---

# Há inclusive uma correção importante antes de você instalar

O workflow da Bea está fixando:

```text
graphifyy 0.9.67
``` :chatgpt-content-reference{index="14"}


A versão `0.9.68`, lançada em **25 de setembro de 2026**, corrige inclusive um problema de segurança envolvendo a passagem de um caminho substituído pelo agente sem quoting adequado em um fluxo `add ... --watch`, além de outras correções. :chatgpt-content-reference{index="15"}

Então eu faria o fork e atualizaria isso antes.

Não é motivo para descartar Graphify; pelo contrário, o fato de eles corrigirem rapidamente é positivo.

Mas não instalaria uma versão anterior quando já sabemos disso.

---

# Agora o Jev

Esse é mais interessante conceitualmente.

Foi lançado pela TypeSafe AI em 15 de setembro, então estamos falando de tecnologia com **menos de duas semanas de vida pública**.

Jev recebe:

```text
state
+
typed question
↓
choice / score / probability
```

em vez de gerar texto livre. :chatgpt-content-reference{index="16"}

Portanto poderia decidir:

```text
REQUEST:
"melhore essa dashboard"

route:
- ux-analysis
- visual-polish
- accessibility
- design-system
- full-design-process
```

ou:

```text
Should this tool result remain in context?

KEEP     .89
TRUNCATE .08
DROP     .03
```

Existe inclusive um projeto comunitário de **Jev context compaction para Claude Code**, justamente mantendo ou descartando resultados antigos de tools. :chatgpt-content-reference{index="17"}

Isso se conecta diretamente com sua pergunta sobre tokens.

---

# Mas eu NÃO adicionaria Jev agora

Por três motivos.

Primeiro: Claude e Codex já fazem roteamento de skills por descrição.

Segundo: o workflow da Bea já tem regras explícitas de roteamento. :chatgpt-content-reference{index="18"}

Terceiro: Jev é muito novo.

Adicionar:

```text
Claude
→ Jev
→ router
→ subagent
→ skills
→ Graphify
→ MCP
```

sem provar necessidade seria exatamente criar um sistema multiagente sofisticado para resolver algo que um `if` resolvia.

Curiosamente, a própria documentação do Jev recomenda começar com **um julgamento pequeno, limitado, conjunto de respostas conhecido e ação reversível**. :chatgpt-content-reference{index="19"}

Então eu deixaria uma integração futura preparada, mas desativada.

---

# Onde eu testaria Jev primeiro

Dois experimentos.

```text
EXPERIMENT J1
Skill routing

Claude-native routing
versus
Jev routing

Metrics:
accuracy
latency
tokens
cost
wrong routes
```

Depois:

```text
EXPERIMENT J2
Context compaction

Normal Claude session
versus
Jev keep/truncate/drop

Metrics:
context tokens
task success
lost relevant context
cost
latency
```

Se ganhar objetivamente:

integra.

Caso contrário:

não.

Isso combina perfeitamente com a filosofia de workflow que você quer construir.

---

# Jev NÃO deve avaliar design

Esse detalhe é importante.

Não faria:

```text
Jev:
"esse design é bom?"

score = 8.7
```

Isso não tem significado.

Jev é apropriado para escolhas limitadas e classificações. A própria documentação alerta que **um resultado válido estruturalmente ainda pode ser uma decisão errada**, e que geração/razão complexa continua pertencendo a outras ferramentas. :chatgpt-content-reference{index="20"}

Ele poderia eventualmente decidir:

```text
Finding UX-32 severity:
low
medium
high
critical
```

desde que tenhamos criado e validado muito bem esse classificador.

Mas eu continuaria preferindo regra determinística quando possível.

---

# E aqui surge a arquitetura que eu considero mais madura

Não é:

```text
Claude superprompt
```

Nem:

```text
20 agentes conversando
```

É:

```text
                    HUMAN
                      │
               Design Director
                      │
        ┌─────────────┼─────────────┐
        │             │             │
      UX           Visual      Design System
        │             │             │
        └─────────────┼─────────────┘
                      │
                    Figma
                      │
               Prototype Tests
                      │
               Design Critic
                      │
               human decision
                      │
                 implementation
                      │
               Playwright QA
                      │
                 production
                      │
              product metrics
```

E lateralmente:

```text
Knowledge
─────────
PRODUCT.md
UX.md
DESIGN.md
DDR/
VALIDATION.md
source
tests

        ↓ optional

     Graphify
```

E mais tarde:

```text
Routing / cheap judgments
────────────
rules
  ↓
Jev (if justified)
  ↓
LLM
```

---

# Algo que eu quero colocar como princípio fundamental

**Toda decisão deve usar o mecanismo mais barato que consegue fazê-la corretamente.**

```text
Deterministic rule
        ↓
existing project knowledge
        ↓
heuristic/check
        ↓
cheap classifier / Jev
        ↓
specialized agent
        ↓
frontier reasoning model
        ↓
human judgment
```

Não usar Claude Opus para verificar contraste.

Tem matemática para isso.

Não usar Jev para criar uma identidade visual.

Ele não é generativo.

Não usar Graphify para um projeto com 15 arquivos.

grep resolve.

Não fazer user testing para confirmar se:

```text
texto cinza #aaa em branco
```

tem contraste adequado.

WCAG resolve.

E não usar uma regra rígida para decidir se a home transmite a personalidade certa.

Aí precisamos de pessoas.

Essa separação vai economizar **tokens, dinheiro e erro**.

---

# Minha conclusão sobre o que você deve fazer agora

Eu faria **o fork do workflow dela**, corrigiria identidade/preferências globais para você e atualizaria somente pequenas questões técnicas, como o Graphify.

E então congelaria a parte geral.

Nada de sair agora adicionando:

```text
Jev
memory system
mais 15 agents
mais 30 skills
outro orchestration framework
```

Em vez disso, construiríamos profundamente:

> **Design Workflow v1**

com:

```text
discovery
→ problem framing
→ UX research
→ task modeling
→ information architecture
→ flow optimization
→ divergent ideation
→ art direction
→ design-system strategy
→ Figma foundations
→ Figma prototype
→ heuristic evaluation
→ accessibility evaluation
→ usability testing
→ measurable validation
→ implementation
→ Playwright visual QA
→ post-launch metrics
```

E cada execução produz conhecimento reutilizável:

```text
PRODUCT.md
UX.md
FLOWS.md
REFERENCES.md
DESIGN.md
DESIGN-SYSTEM.md
DDR/
VALIDATION.md
```

A parte mais poderosa é que isso resolve tanto:

**“Claude, faça meu portfólio”**

quanto:

**“Claude, precisamos projetar um SaaS de gestão de contratos para 300 usuários”**

sem tratar os dois como se fossem a mesma coisa.

O primeiro provavelmente terá foco brutal em narrativa, identidade, art direction e experiência.

O segundo provavelmente terá muito mais peso em IA, eficiência de tarefas, densidade informacional, padrões de interação, permissões, estados, erros e testes de usabilidade.

**O workflow adapta o processo ao problema, em vez de aplicar uma estética pré-fabricada ao problema.**

E isso é exatamente o antídoto para o AI slop que você vem percebendo."

---

Eu enviei: "Show demais, então crio o fork como? E quando eu puxar do git (puxo em que pasta? Na home geral do meu macbook?),  eu chamo o claude code na minha "~/"? Além disso, curti demais tudo que você falou, e sobre design system, realmente é muito importante planejar tudo isso, e se de repente couber de forma inteligente para alguma solução, talvez seja legal adotar algum design system já feito, ou alguma biblioteca de componentes para adicionar algo que precisamos, ou montar o nosso próprio design system, tudo isso vem de uma sequência de planejamentos e questionamentos sobre o produto, e se realmente faz sentido cada decisão, ao invés de simplesmente ditar se vai ser uma biblioteca específica ou não. Quero passar tudo que conversamos aqui para o Claude Code, e já pedir para ajeitar o terreno para mim, atualizar as coisas (se for realmente compatível e não for quebrar nada) e baixar o mcp necessário, e aí começamos a ajeitar o workflow para que fique completo nessa questão, aí depois que estiver tudo certo, eu já testo tentando idealizar e prototipar meu portfólio, e se necessário fazendo ajustes para melhorar o workflow, e preciso muito da ajuda e da capacidade de julgamento do claude nesse processo, para criarmos algo realmente maduro, funcional e consistente (tanto no incremento do workflow, quanto no meu portfolio), e aí vou sempre avaliando, e assim, quero fazer tudo realmente bem feito, um figma profissional, bem organizado e completo, com as melhores práticas de figma, tomadas de decisões profissionais e tudo mais, nada retirado do nada, sempre com boas pesquisas de vários estudos, vários artigos, profissionais da área relevantes também, e verificando tudo isso."

o GPT respodeu: "Exatamente. Eu faria o fork **antes de instalar**, usaria o Claude Code dentro do próprio fork para auditar/atualizar o workflow e só depois instalaria a versão já adaptada para você.

## 1. Onde deixar esse repositório no Mac

Eu **não colocaria diretamente em `~/`**. Tecnicamente funciona, mas mistura ferramenta/configuração com arquivos pessoais.

Eu organizaria assim:

```text
~/Developer/
├── tools/
│   └── workflow-ai/          ← seu fork desse workflow
│
└── projects/
    └── portfolio/            ← futuramente seu portfólio
```

Então:

```bash
mkdir -p ~/Developer/tools
mkdir -p ~/Developer/projects
```

O workflow fica em:

```text
~/Developer/tools/workflow-ai
```

Seu portfólio será outro repositório completamente separado.

---

# 2. Faça o fork no GitHub primeiro

Abra:

[workflow-claude-codex-etc no GitHub](https://github.com/whosbea/workflow-claude-codex-etc?utm_source=chatgpt.com)

Clique em **Fork**.

Eu manteria inicialmente o nome:

```text
workflow-claude-codex-etc
```

ou, se quiser assumir como sua configuração pessoal:

```text
workflow-ai
```

Eu particularmente gosto mais de `workflow-ai`.

Depois clone **seu fork**, não o da Bea:

```bash
cd ~/Developer/tools

git clone git@github.com:<SEU-USUARIO>/workflow-ai.git

cd workflow-ai
```

Se mantiver o nome original:

```bash
git clone git@github.com:<SEU-USUARIO>/workflow-claude-codex-etc.git workflow-ai
cd workflow-ai
```

Agora mantenha o original da Bea como `upstream`:

```bash
git remote add upstream git@github.com:whosbea/workflow-claude-codex-etc.git

git remote -v
```

Você deve ter aproximadamente:

```text
origin    git@github.com:SEU-USUARIO/workflow-ai.git
upstream  git@github.com:whosbea/workflow-claude-codex-etc.git
```

Isso é importante porque depois você consegue continuar absorvendo as melhorias dela sem perder as suas.

---

# 3. Crie uma branch para nossa evolução

Não faria tudo diretamente na `main`.

```bash
git switch -c feat/design-workflow-v1
```

Agora:

```bash
pwd
```

deve mostrar algo como:

```text
/Users/felipe/Developer/tools/workflow-ai
```

E **aqui** você abre:

```bash
claude
```

### Não:

```bash
cd ~
claude
```

Isso daria ao Claude um escopo de projeto absurdamente grande e pouco semântico.

O instalador do projeto já cuida da parte global: ele liga `AGENTS.md` a `~/.claude/CLAUDE.md`, skills a `~/.claude/skills/`, agentes a `~/.claude/agents/` etc. :chatgpt-content-reference{index="1"}

Portanto funciona assim:

```text
Claude global behavior
       ↑
~/.claude/CLAUDE.md
       ↑ symlink
~/Developer/tools/workflow-ai/AGENTS.md


Claude project context
       ↑
diretório de onde você executou "claude"
```

Essa separação é ótima.

---

# 4. Depois, quando formos fazer seu portfólio

Você fará:

```bash
cd ~/Developer/projects/portfolio
claude
```

E não:

```bash
cd ~/Developer/tools/workflow-ai
claude
```

para trabalhar no portfólio.

As skills globais continuarão disponíveis, mas Claude terá:

```text
global workflow
+
contexto local do portfolio
+
CLAUDE.md local do portfolio
+
PRODUCT.md
+
UX.md
+
DESIGN.md
+
DDRs
+
Figma
```

É exatamente o que queremos.

---

# 5. Eu NÃO rodaria `install.sh` ainda

Esse é um detalhe importante.

A versão atual ainda tem, por exemplo:

```text
Graphify 0.9.67
``` :chatgpt-content-reference{index="2"}


e a `0.9.68` foi publicada em **25 de setembro de 2026** com, entre outras coisas, uma correção de segurança envolvendo um caminho inserido pelo agente em comando shell. :chatgpt-content-reference{index="3"}

Além disso, o projeto atualmente documenta Figma como configuração manual do MCP. :chatgpt-content-reference{index="4"}

Hoje a própria documentação oficial do Figma recomenda para Claude Code:

```bash
claude plugin install figma@claude-plugins-official
```

porque o plugin já inclui:

```text
Figma MCP
+
Agent Skills
+
regras para workflows do Figma
``` :chatgpt-content-reference{index="5"}


Então eu faria Claude **auditar o fork antes da primeira instalação**.

---

# 6. Esse é o prompt que eu passaria agora ao Claude Code

Cole isso com Claude aberto em:

```text
~/Developer/tools/workflow-ai
```

Estamos trabalhando no meu fork pessoal do repositório `whosbea/workflow-claude-codex-etc`.

Quero transformar este projeto gradualmente no meu workflow pessoal de engenharia e criação assistida por IA.

IMPORTANTE: nesta etapa nosso foco principal é preparar corretamente o terreno e construir uma vertical extremamente madura para Product Design, UX, UI, Design Systems, Figma e validação de interfaces.

Não comece a criar meu portfólio ainda.

Primeiro precisamos garantir que o próprio workflow esteja correto, atualizado, seguro, simples, documentado e capaz de sustentar esse processo.

# PRINCÍPIO CENTRAL

Não quero aumentar complexidade simplesmente porque ferramentas existem.

Prefira sempre:

necessidade comprovada → solução mais simples que resolve corretamente → validação → evolução.

Evite:

- agent sprawl;
- dezenas de skills sobrepostas;
- regras conflitantes;
- abstrações prematuras;
- frameworks de agentes sem necessidade;
- dependências simplesmente porque são populares;
- mudanças de versão sem análise;
- instalar ferramentas antes de entender por que são necessárias.

Quero capacidade de julgamento, não apenas execução literal.

# FASE 0 — ENTENDER O REPOSITÓRIO ANTES DE ALTERAR

Leia integralmente e analise a estrutura relevante:

- `README.md`
- `AGENTS.md`
- `install.sh`
- `third-party.lock`
- `agents/`
- `skills/`
- `commands/`
- `scripts/`
- `harden/`

Inspecione também o estado Git.

Não faça afirmações sobre arquivos que não abriu.

Mapeie:

1. arquitetura atual;
2. filosofia atual;
3. agentes existentes;
4. skills próprias;
5. skills de terceiros;
6. routing atual;
7. configuração Claude;
8. configuração Codex;
9. MCPs;
10. política de atualização;
11. segurança;
12. conflitos potenciais;
13. redundâncias;
14. lacunas.

Preserve boas decisões existentes.

Não reescreva o projeto do zero.

# FASE 1 — AUDITORIA DO MEU AMBIENTE

Antes de instalar ou sobrescrever qualquer configuração global, verifique de maneira não destrutiva:

- versões de `git`;
- `claude`;
- `codex`;
- `node`;
- `npm`/`npx`;
- `uv`;
- `python3`;
- MCPs atualmente registrados;
- plugins Claude já instalados;
- existência de `~/.claude/CLAUDE.md`;
- existência e conteúdo relevante de `~/.claude/settings.json`;
- configurações do Codex;
- symlinks existentes;
- possíveis configurações minhas que seriam substituídas.

Não exponha secrets.

Se existir configuração global anterior, compare antes de substituir.

Não destrua nem descarte configuração existente silenciosamente.

# FASE 2 — VERIFICAR ATUALIZAÇÕES, NÃO ATUALIZAR CEGAMENTE

Pesquise fontes atuais e preferencialmente primárias:

- documentação oficial;
- releases;
- changelogs;
- commits;
- issues relevantes quando necessário.

Para cada dependência que parece desatualizada:

1. identificar versão atualmente fixada;
2. identificar versão candidata;
3. ler changelog;
4. verificar breaking changes;
5. verificar alterações de comportamento;
6. verificar implicações de segurança;
7. verificar compatibilidade com nosso instalador;
8. inspecionar diff quando apropriado;
9. decidir se a atualização realmente vale a pena;
10. registrar a justificativa.

`latest` nunca significa `upgrade automaticamente`.

## Graphify

O workflow atualmente aponta para Graphify 0.9.67.

Existe pelo menos a 0.9.68, publicada posteriormente, contendo inclusive correção relacionada a segurança.

Verifique diretamente upstream.

Se 0.9.68 for compatível e apropriada:

- atualize corretamente o lock;
- preserve pinning por commit;
- preserve verificações existentes;
- rode os testes/checks relevantes;
- documente a decisão.

Não faça upgrade apenas porque eu disse que existe uma versão nova.

## Figma

O workflow atualmente documenta configuração manual do Figma MCP.

A documentação atual do Figma recomenda para Claude Code o plugin oficial:

`figma@claude-plugins-official`

Esse plugin pode fornecer o próprio MCP e Agent Skills oficiais.

Confirme isso na documentação atual antes de modificar qualquer coisa.

Verifique também:

- se já existe Figma MCP;
- se já existe plugin Figma;
- se poderia ocorrer registro duplicado;
- qual escopo é mais apropriado para um workflow global;
- como autenticação funciona atualmente;
- comportamento no Claude Code;
- impacto sobre Codex, que pode continuar precisando da configuração própria.

Quero preferir integração oficial quando ela realmente for a opção mais apropriada.

## Playwright

Verifique a versão atualmente fixada e a versão upstream.

Não atualize automaticamente.

Leia changelog/diff quando houver mudança relevante.

Playwright será fundamental futuramente para Visual QA e UX QA, portanto estabilidade importa mais do que perseguir números de versão.

# FASE 3 — AVALIAR A ARQUITETURA DE DESIGN EXISTENTE

Quero que analise profundamente tudo que atualmente existe relacionado a:

- frontend;
- UI;
- UX;
- design;
- prototyping;
- Impeccable;
- Taste;
- skills de Emil Kowalski;
- Humanizer;
- Playwright;
- Figma;
- pesquisa;
- product strategy.

Identifique:

- sobreposição;
- conflito de instruções;
- lacunas;
- skills excessivamente opinativas;
- habilidades que deveriam atuar somente em determinadas fases;
- oportunidades de orchestration.

Não quero que todas as skills de design sejam aplicadas simultaneamente.

Uma coleção de especialistas sem roteamento pode produzir uma média de opiniões e gerar exatamente o design genérico que queremos evitar.

# FASE 4 — PROJETAR A VERTICAL DE PRODUCT DESIGN

Quero construir uma vertical que trate design como processo completo de resolução de problemas e não simplesmente como geração de interface bonita.

O workflow deve conseguir se adaptar a:

- landing pages;
- portfólios;
- SaaS;
- dashboards;
- ferramentas internas;
- produtos B2B;
- produtos B2C;
- aplicações mobile;
- fluxos complexos;
- interfaces densas;
- experiências editoriais.

Não presuma que todos esses produtos precisam do mesmo processo ou do mesmo nível de formalidade.

## O processo deve contemplar, quando aplicável

Discovery
→ problem framing
→ product understanding
→ user goals
→ jobs/tasks
→ constraints
→ research
→ information architecture
→ user flows
→ simplification
→ divergent exploration
→ art direction
→ interaction design
→ design-system strategy
→ component strategy
→ prototyping
→ usability evaluation
→ accessibility
→ measurable validation
→ implementation handoff
→ implementation
→ visual QA
→ UX QA
→ production metrics
→ iteration

Mas não quero burocracia obrigatória.

Determine quais etapas são necessárias conforme risco, escala e natureza do produto.

# UX ANTES DE UI

Nunca parta diretamente de:

"dados → tabela"

ou:

"informação → card"

ou:

"produto → dashboard"

Primeiro avalie:

- qual tarefa o usuário está tentando realizar;
- qual decisão precisa tomar;
- o que precisa comparar;
- o que precisa reconhecer;
- o que precisa lembrar;
- frequência da tarefa;
- urgência;
- densidade necessária;
- progressive disclosure;
- frequência de erros;
- capacidade de recuperação;
- contexto desktop/mobile;
- acessibilidade;
- experiência de usuários iniciantes e experientes.

Somente então determine representação e padrão de interação.

Tabela, card, carousel, tabs, timeline, master-detail, command palette, inline editing, wizard, kanban, visualization, drawer etc. são instrumentos.

Nenhum deles deve ser considerado bom ou ruim fora do contexto.

# SIMPLIFICAÇÃO

Pergunte continuamente:

- esta etapa precisa existir?
- este campo precisa existir?
- esta tela precisa existir?
- esta escolha pode ser inferida?
- esta informação precisa estar simultaneamente visível?
- podemos reduzir carga cognitiva?
- podemos evitar navegação?
- podemos prevenir o erro em vez de explicar o erro?
- existe uma representação melhor desse dado?

Não confunda minimalismo visual com simplicidade de uso.

Uma interface vazia também pode ser ruim.

Uma interface densa também pode ser excelente quando densidade corresponde à tarefa.

# DESIGN SYSTEM

Não quero que o workflow determine previamente:

"use shadcn"
"use Radix"
"use Base UI"
"use Material"
"use X"

A decisão deve nascer do produto.

A estratégia pode ser:

- design system próprio;
- sistema existente;
- biblioteca headless;
- biblioteca visual;
- combinação/híbrido;
- primitives existentes + camada visual própria;
- componentes totalmente específicos do domínio.

Avalie, conforme o problema:

- acessibilidade;
- interação;
- flexibilidade visual;
- comportamento;
- theming;
- suporte a tokens;
- customização;
- capacidade de criar identidade própria;
- qualidade da implementação;
- performance;
- bundle;
- manutenção;
- maturidade;
- compatibilidade;
- velocidade;
- custos de longo prazo;
- requisitos de produto.

Shadcn pode ser excelente quando fizer sentido, mas não deve ser utilizado cru simplesmente porque agentes conhecem a biblioteca.

Componentes base devem ser adequadamente transformados para refletir a identidade e as necessidades do produto.

Também distinga:

Foundations
Primitives
Components
Patterns
Domain Components

Um conjunto de Button/Input/Card não constitui sozinho um design system profissional.

# IDENTIDADE E ANTI-AI-SLOP

Queremos combater convergência prematura e design fixation.

Durante ideação:

maximize diversidade.

Durante convergência:

maximize intenção.

Durante implementação:

maximize consistência.

Durante revisão:

maximize espírito crítico.

Não trate como direções diferentes soluções que mudam apenas:

- cores;
- fonte;
- radius;
- sombras;
- ornamentação.

Direções distintas precisam possuir conceitos distintos.

Evite defaults recorrentes de AI-generated UI quando não forem justificáveis pelo produto.

Mas também não transforme "anti-AI" em outro preset estético.

# REFERÊNCIAS

Prefira referências concretas a adjetivos vagos.

Permita decompor referências em:

- typography;
- composition;
- hierarchy;
- spacing;
- density;
- layout;
- navigation;
- interaction;
- motion;
- imagery;
- storytelling.

Mantenha também anti-references.

Nunca copie cegamente um produto.

Entenda por que a referência funciona.

# FIGMA PROFISSIONAL

Quero que o workflow seja capaz de produzir um arquivo Figma que um designer profissional consiga abrir e entender.

Pesquise práticas atuais e oficiais do Figma.

Considere estrutura semelhante a:

- Cover / Documentation
- Foundations
- Variables
- Styles
- Components
- Patterns
- Explorations
- User Flows
- Desktop
- Mobile
- Prototype
- Archive / Deprecated

Mas não imponha essa estrutura se houver organização melhor para determinado projeto.

Aplique corretamente, quando pertinente:

- variables;
- collections;
- modes;
- semantic tokens;
- component properties;
- variants;
- nested components;
- Auto Layout;
- constraints;
- responsive behavior;
- naming;
- documentation;
- reusable components;
- accessibility considerations;
- prototype states;
- error states;
- loading states;
- empty states;
- edge cases.

Evite criar apenas screenshots bonitas dentro do Figma.

Queremos design editável, estruturado, sistemático e prototipável.

# PROTOTYPE VALIDATION

Protótipos devem permitir validar tarefas quando o risco justificar.

Não valide somente aparência.

Considere medir:

- task completion;
- time on task;
- critical errors;
- recoverable errors;
- backtracking;
- assistance required;
- perceived task ease;
- qualitative observations.

Não invente "UX Score 94/100".

Não crie precisão fictícia.

Métricas precisam possuir definição e contexto.

# HEURISTIC REVIEW

Quando apropriado, faça avaliações sistemáticas de usabilidade utilizando princípios consolidados como as heurísticas de Nielsen.

Um finding deve carregar algo como:

- ID;
- fluxo;
- tela;
- evidência;
- princípio violado;
- impacto;
- severidade;
- hipótese de melhoria;
- status.

Se severidade for usada, defina claramente a escala.

Não trate julgamento heurístico como evidência de usuário real.

# ACCESSIBILITY

Considere WCAG atual e documentação primária.

Automatize o que puder ser determinado automaticamente.

Não use LLM para resolver aquilo que uma regra determinística resolve melhor.

Exemplos:

- contrast;
- target sizing;
- focus visibility;
- keyboard navigation;
- semantic markup;
- reduced motion;
- resize/reflow.

Mas reconheça que várias questões de acessibilidade continuam exigindo avaliação humana/contextual.

# DECISION RECORDS

Quero evitar que decisões importantes sejam esquecidas e reinventadas.

Avalie criar Design Decision Records — DDRs — ou estrutura equivalente.

Exemplo conceitual:

DDR-004
Context
Problem
Decision
Alternatives
Evidence
Trade-offs
Consequences
Revisit when

Não transforme toda decisão trivial em documento.

Use somente para decisões relevantes ou difíceis de reverter.

# ARTEFATOS DURÁVEIS

Avalie uma estrutura adaptativa de documentação que possa incluir:

- PRODUCT.md
- UX.md
- FLOWS.md
- REFERENCES.md
- DESIGN.md
- DESIGN-SYSTEM.md
- VALIDATION.md
- DDR/

Esses nomes são propostas, não imposições.

Evite produzir documentação vazia somente para preencher template.

Documente conhecimento que será realmente útil para humanos e agentes futuros.

# CRIAÇÃO ≠ CRÍTICA

Evite que o mesmo raciocínio simplesmente gere algo e imediatamente confirme que ficou bom.

Avalie separar conceitualmente:

Generator
Critic
Auditor

Mas não crie três agentes se skills, subagents ou prompts isolados resolverem melhor.

Quero a estrutura mínima que preserve independência crítica suficiente.

# VISUAL QA E PLAYWRIGHT

Visual QA deve ser parte do workflow de implementação quando houver frontend executável.

Considere:

- screenshots;
- multiple viewport sizes;
- overflow;
- spacing;
- typography;
- state coverage;
- interaction;
- keyboard;
- responsive behavior;
- visual regression quando adequado.

Use Playwright como ferramenta de verificação, não apenas automação de browser disponível.

# PESQUISA

Não baseie decisões importantes simplesmente no treinamento do modelo.

Quando apropriado, pesquise.

Priorize:

1. documentação oficial;
2. padrões oficiais;
3. literatura científica / estudos;
4. instituições/profissionais reconhecidos;
5. estudos de caso relevantes;
6. evidência comunitária como complemento.

Diferencie:

- fato;
- recomendação;
- heurística;
- opinião;
- preferência;
- hipótese.

Não use um artigo isolado para transformar preferência de um designer em lei universal.

# GRAPHIFY

Graphify já existe neste workflow.

Não o transforme automaticamente no "cérebro do sistema".

Avalie:

- quando realmente ajuda;
- tamanho mínimo de projeto onde faz sentido;
- custo operacional;
- custo de indexação;
- precisão;
- manutenção;
- economia de tokens;
- latência;
- qualidade de recuperação.

Conhecimento canônico deve continuar existindo em documentos, código e testes.

Graphify deve ser derivado e descartável, não a única fonte de verdade.

Se fizer sentido no futuro, podemos benchmarkar:

Claude normal
versus
Claude + Graphify

medindo:

- tokens;
- tool calls;
- files opened;
- tempo;
- qualidade;
- dependências perdidas;
- suposições incorretas.

Não faça essa integração mais complexa agora sem evidência de benefício.

# JEV

Não adicione Jev nesta primeira versão.

Apenas documente uma possível extensão futura caso decisões tipadas ou context compaction tragam benefício verificável.

Não quero:

Claude
→ router
→ Jev
→ orchestrator
→ agent
→ skill
→ outro agent

sem necessidade demonstrada.

Primeiro use routing simples.

Depois medimos.

# PRINCÍPIO DE CUSTO/COMPLEXIDADE

Use o mecanismo mais simples que consegue resolver corretamente:

deterministic rule
→ project knowledge
→ heuristic/check
→ classifier
→ specialized reasoning
→ expensive frontier model
→ human judgment

Não use um LLM grande para verificar coisas que matemática, lint, testes ou ferramentas determinísticas conseguem verificar melhor.

# ORCHESTRATION

Avalie criar uma camada pequena como `design-director`.

Ela não deve ser mais uma skill de gosto visual.

Seu papel deve ser:

- entender o tipo de tarefa;
- determinar quais etapas são necessárias;
- escolher especialistas/skills;
- impedir convergência prematura;
- manter artefatos consistentes;
- aplicar gates;
- organizar validação.

Avalie também se realmente precisamos de especialistas separados como:

- UX/product;
- art direction/UI;
- design system;
- design critic/QA.

Prefira a quantidade mínima de agentes/skills necessária para obter separação de responsabilidade sem overengineering.

# GATES

Considere gates conceituais como:

Problem
UX
Direction
System
Prototype
Validation
Build
QA
Production

Um gate não é aprovado apenas porque um arquivo foi produzido.

Ele precisa ter evidência suficiente proporcional ao risco.

Não transforme isso em processo burocrático obrigatório para uma pequena landing page.

Adapte.

# DOCUMENTAÇÃO DO PRÓPRIO WORKFLOW

Depois de definir a arquitetura:

- implemente-a;
- documente como ela funciona;
- documente quando cada parte deve ser usada;
- documente quando NÃO deve ser usada;
- atualize README/AGENTS somente quando necessário;
- mantenha descriptions das skills suficientemente precisas para routing;
- evite duplicação de regras entre global instructions e skills.

O `AGENTS.md` global deve permanecer relativamente pequeno e conter princípios e routing.

Conhecimento especializado deve ficar nas skills adequadas.

# TESTES DO WORKFLOW

Crie formas razoáveis de verificar:

- parsing das skills;
- conflitos de nomes;
- destinos duplicados;
- instalação;
- symlinks;
- conversão Claude → Codex;
- idempotência;
- configuração dos MCPs;
- ausência de regressões no instalador.

Não quebre compatibilidade com Codex sem justificativa explícita.

# EXECUÇÃO SEGURA

Antes de qualquer alteração substancial:

- crie/valide uma branch de trabalho;
- registre baseline;
- mantenha `git status` sob controle.

Mudanças locais reversíveis são permitidas.

Não faça:

- `git push`;
- force push;
- remoções destrutivas;
- reset hard;
- publicação;
- alterações remotas;

sem minha autorização.

Commits locais pequenos e coerentes são bem-vindos se ajudarem a manter checkpoints.

# RESULTADO DESTA ETAPA

Quero terminar esta etapa com:

1. auditoria clara do workflow atual;
2. dependências relevantes verificadas;
3. incompatibilidades conhecidas registradas;
4. atualizações seguras aplicadas;
5. Figma oficial corretamente integrado;
6. workflow de Product Design implementado;
7. routing simples e compreensível;
8. documentação adequada;
9. testes/checks executados;
10. `./install.sh --dry-run` limpo;
11. instalação real somente depois de verificar o dry-run;
12. configuração endurecida quando compatível;
13. MCPs/plugins validados;
14. plano de teste usando meu portfólio como primeiro caso real.

Depois disso, meu portfólio será nosso primeiro grande teste do Design Workflow.

NÃO crie o portfólio durante esta etapa.

Ao final, deixe explícito:

- o que existia;
- o que mudou;
- por que mudou;
- quais alternativas foram rejeitadas;
- riscos restantes;
- dívidas técnicas;
- como reverter;
- como sincronizar futuramente com o upstream da Bea;
- como testar o workflow com meu portfólio.

Trabalhe de forma incremental.

Investigue antes de afirmar.

Pesquise antes de assumir que algo atual permanece atual.

Não concorde automaticamente com as minhas ideias: critique quando houver alternativa tecnicamente superior ou quando estivermos adicionando complexidade sem retorno.

Esse é exatamente o tipo de tarefa em que vale deixar Claude trabalhar bastante no código e na documentação **antes** de pedir interface.

---

# 7. O que eu esperaria que ele faça

A sequência saudável seria aproximadamente:

```text
READ
 ↓
AUDIT
 ↓
RESEARCH
 ↓
PROPOSE
 ↓
PATCH
 ↓
TEST
 ↓
DRY RUN
 ↓
INSTALL
 ↓
VERIFY
```

e não:

```text
"boa ideia!"
 ↓
instala 28 coisas
 ↓
reescreve AGENTS.md
 ↓
quebra Codex
```

😄

Um detalhe importante: a própria Anthropic hoje recomenda, para tarefas longas, manter estado em arquivos, fazer progresso incremental e fornecer ferramentas de verificação para trabalhos de UI; browser automation é citada explicitamente como útil para verificar implementações. :chatgpt-content-reference{index="6"}

Isso combina muito bem com a arquitetura que estamos montando.

---

# 8. Quando ele chegar à instalação

Depois que o Claude tiver auditado e ajustado o fork, eu esperaria algo nesta linha:

```bash
./install.sh --dry-run
```

Só se o resultado estiver correto:

```bash
./install.sh
./install.sh --harden
```

O próprio projeto foi feito para isso: `--dry-run`, backups, instalação idempotente e hardening opt-in. :chatgpt-content-reference{index="7"}

Para Figma, após a auditoria:

```bash
claude plugin install figma@claude-plugins-official
```

Esse é atualmente o método preferido documentado oficialmente pelo Figma para Claude Code. :chatgpt-content-reference{index="8"}

Depois:

```bash
claude mcp list
```

e dentro do Claude:

```text
/mcp
```

para autenticar/verificar o Figma se necessário.

Eu faria o Claude checar antes se já há uma integração registrada para evitar duplicidade.

---

# 9. Depois disso, seu fluxo diário fica muito simples

### Para modificar o workflow global

```bash
cd ~/Developer/tools/workflow-ai
claude
```

### Para trabalhar no portfólio

```bash
cd ~/Developer/projects/portfolio
claude
```

### Para trabalhar em um SaaS

```bash
cd ~/Developer/projects/meu-saas
claude
```

O workflow global acompanha todos eles.

---

# 10. E upstream da Bea continua utilizável

De tempos em tempos:

```bash
cd ~/Developer/tools/workflow-ai

git fetch upstream
```

Antes de puxar qualquer coisa:

```bash
git log --oneline HEAD..upstream/main
git diff HEAD...upstream/main
```

Isso é bem melhor que simplesmente:

```bash
git pull upstream main
```

porque você primeiro entende o que mudou.

Depois você decide entre merge/rebase conforme o histórico do fork.

Essa filosofia é exatamente a mesma que estamos aplicando às dependências: **upstream é fonte de melhorias, não autoridade para sobrescrever suas decisões.**

---

E a parte que eu mais gosto desse plano é que **seu portfólio vira o benchmark real do workflow**, não apenas um projeto qualquer. Vamos conseguir observar onde o Claude ainda converge cedo demais, onde o Figma fica mal organizado, onde as skills brigam entre si, onde faltam métricas/validação e então corrigir o workflow com evidência. Depois dessa primeira execução, teremos uma Design Workflow v1 testada em algo concreto — e aí ela pode amadurecer para SaaS e produtos bem mais complexos."

---

Eu enviei: "Inclusive, eu tava vendo alguns vídeos sobre a questão do processo critativo, e você mesmo citou também que fotos são essenciais para poder idealizar e ter as referências necessárias para a montagem do design, do fluxo, das telas e muito mais da aplicação, e assim, eu vi um cara falando sobre o mcp do mobbin, e achei isso interessante porque dá acesso a diversas telas que são feitas por profissionais da área, e designs reais realmente validados, além de dar flexibilidade para o próprio workflow pesquisar por referências, encontrar as melhores, avaliar o que é bom e o que não é, ter uma variabilidade de referencias a qualquer instante, e poder ver como o design é aplicado no produto e aí sim poder modelar qualquer tela para fugir do AI Slop, e isso é muito interessante, só que o do mobbin é pago né? Quanto é por mês e como funciona?  É realmente interessante adotar (tô pensando aqui se faz sentido eu pagar)? E tem alternativas para isso? Inclusive, alternativas gratuitas?"

o GPT respodeu: "Sim — **Mobbin faz bastante sentido para o workflow que estamos montando**, mas eu faria uma distinção importante: ele deve entrar como uma **fonte de evidência/referência**, não como uma máquina de “me diga o design certo”.

E achei uma alternativa gratuita bem interessante que eu colocaria no workflow **antes mesmo de você decidir pagar Mobbin**.

### Quanto custa o Mobbin hoje?

Em **27 de setembro de 2026**, o plano individual Pro custa **US$ 10/mês no anual**, ou seja, US$ 120 cobrados pelo ano. O Mobbin não oferece cobrança mensal de verdade: os ciclos são anual ou trimestral. O trimestral está atualmente em **US$ 15/mês equivalente, cobrado como US$ 45 a cada trimestre**. :chatgpt-content-reference{index="0"}

O Pro inclui justamente o que nos interessa:

| Recurso | Free | Pro |
|---|---:|---:|
| Apps/sites | limitado | completo |
| Flows | não | sim |
| Animations | não | sim |
| Search | não | sim |
| Deep Search | não | sim |
| Collections | até 3 | ilimitado |
| MCP | não | **sim** |
| Copy/download | limitado | sim | :chatgpt-content-reference{index="1"}


E tem uma informação **muito relevante para você**: estudantes e educadores de instituições reconhecidas recebem **50% de desconto no Pro por até 2 anos**, tanto no anual quanto no trimestral. A verificação é feita pelo e-mail institucional. :chatgpt-content-reference{index="2"}

Ou seja, antes de pagar o preço cheio, **eu definitivamente tentaria o programa Education**.

[Mobbin for Education](https://help.mobbin.com/en/articles/693312?utm_source=chatgpt.com)

---

## E o MCP é realmente interessante?

Sim. Aqui não acho hype vazio.

O MCP oficial é:

```text
Claude Code
      ↓
Mobbin MCP
      ↓
search real product screens
search real user flows
search website sections
      ↓
actual screenshots + metadata
      ↓
Claude vision/reasoning
```

É um servidor oficial hospedado pelo próprio Mobbin, usa OAuth e não depende daqueles projetos antigos que faziam engenharia reversa na plataforma. :chatgpt-content-reference{index="4"}

O próprio Mobbin mostra o caso:

> “Design a paywall…”

e o agente consegue procurar dezenas de paywalls existentes e comparar abordagens de produtos como Revolut, Duolingo e Uber antes de propor algo. :chatgpt-content-reference{index="5"}

Hoje o MCP está em **beta com uso ilimitado**, mas o Mobbin já avisa que limites serão aplicados futuramente. :chatgpt-content-reference{index="6"}

E para Claude Code a configuração oficial é literalmente:

```bash
claude mcp add mobbin \
  --scope user \
  --transport http \
  https://api.mobbin.com/mcp
```

Depois autentica via `/mcp`. :chatgpt-content-reference{index="7"}

---

# Mas tem uma correção conceitual importante

Você falou algo como:

> “telas feitas por profissionais e designs reais realmente validados”

A primeira parte está correta.

A segunda precisa de cuidado.

### `shipped ≠ validated`

Só porque Airbnb, Linear, Spotify ou Revolut colocou alguma coisa em produção não significa automaticamente:

```text
essa solução é ótima
```

Muito menos:

```text
essa solução é ótima para o nosso produto
```

Uma tela real pode ser:

- legado;
- experimento A/B;
- compromise de negócio;
- solução específica para determinado público;
- influenciada por restrições internas;
- ruim em acessibilidade;
- otimizada para monetização em detrimento de UX;
- apenas uma das versões daquele produto.

Portanto o processo não pode ser:

```text
Mobbin encontrou Linear
        ↓
Linear faz assim
        ↓
vamos fazer assim
```

Tem que ser:

```text
PROBLEMA
   ↓
pesquisar múltiplas referências
   ↓
observar padrões recorrentes
   ↓
entender diferenças
   ↓
formular hipóteses
   ↓
comparar com nossos usuários e constraints
   ↓
heuristics / research / accessibility
   ↓
prototype
   ↓
validate
```

Esse detalhe é **muito importante** para evitar trocar:

> “AI slop”

por:

> “clone slop”.

---

# E achei uma alternativa gratuita excelente: Pablooo

Essa eu colocaria no nosso workflow praticamente já.

O **Pablooo.club** oferece um MCP completamente gratuito com **8.000+ screenshots reais de produtos mobile e desktop**. Não exige conta nem API key. :chatgpt-content-reference{index="8"}

Ele oferece ferramentas para:

- buscar screenshots;
- pesquisar por produto/tipo de tela;
- obter dados estruturados;
- buscar a própria imagem;
- entregar a screenshot para a visão do Claude;
- comparar seu design com referências. :chatgpt-content-reference{index="9"}


E no Claude Code:

```bash
claude mcp add \
  --transport http \
  pablooo \
  --scope user \
  https://mcp.pablooo.club
``` :chatgpt-content-reference{index="10"}


Isso significa que podemos ter:

```text
Claude Code
├── Figma MCP
├── Playwright MCP
└── Pablooo MCP ← gratuito
```

antes de pagar qualquer coisa.

---

# Pablooo vs Mobbin

Aqui está a diferença real:

| | Pablooo | Mobbin |
|---|---:|---:|
| Preço | **grátis** | US$10/mês anual |
| MCP | **grátis** | Pro+ |
| Screens | 8.000+ | **621.500+** |
| Mobile | sim | sim |
| Desktop/Web | sim | sim |
| User flows | algum suporte | **muito forte** |
| Profundidade por produto | menor | **muito maior** |
| Histórico/versões | limitado | forte |
| Search sofisticado | razoável | **forte** |
| Collections/ecossistema | básico | **maduro** |

O Pablooo é impressionante pelo preço.

Mas não é substituto completo do Mobbin.

Mobbin tem quase **duas ordens de magnitude** a mais de conteúdo.

---

# Tem também o Refero, e esse ficou MUITO interessante

Essa talvez seja a alternativa paga mais relevante para o nosso caso.

O Refero agora possui **MCP oficial** e se posiciona exatamente como:

> design research for AI agents.

Ele informa atualmente:

- **142.000+ screens**;
- **12.000+ user flows**;
- Web;
- iOS;
- atualização semanal;
- Figma plugin;
- MCP;
- uma própria **Refero Skill** para agentes. :chatgpt-content-reference{index="11"}


Mais interessante ainda: as referências carregam metadados estruturados sobre:

```text
UX patterns
UI patterns
layouts
descriptions
```

antes mesmo da análise visual. :chatgpt-content-reference{index="12"}

Isso pode ser bom para economia de tokens.

Em vez de Claude precisar “olhar” 80 screenshots completas, pode fazer:

```text
metadata search
     ↓
filter
     ↓
10 candidates
     ↓
vision on 10
     ↓
3–5 references
```

Isso é exatamente o tipo de estratégia que queremos no workflow.

A skill deles também pode ser instalada separadamente:

```bash
npx skills add https://github.com/referodesign/refero_skill
``` :chatgpt-content-reference{index="13"}


Eu **não instalaria agora automaticamente**, porque quero primeiro comparar com Taste/Impeccable/Design Director para não gerar sobreposição.

Mas merece análise.

---

# Outra boa: Page Flows

Page Flows resolve uma coisa diferente.

Ao invés de focar principalmente em screenshots, foca muito em **gravações de fluxos reais**.

Exemplo:

```text
signup
 ↓
verification
 ↓
onboarding
 ↓
permission
 ↓
home
```

Você vê a interação acontecendo.

Isso é particularmente útil para:

- onboarding;
- checkout;
- login;
- subscription;
- cancelamento;
- search;
- recovery;
- microinteractions.

Hoje custa aproximadamente **US$8,25/mês no anual, US$99/ano**, ou **US$13/mês equivalente no trimestral**, com trial de 5 dias. :chatgpt-content-reference{index="14"}

Não tem a vantagem do MCP oficial como Mobbin/Refero, então para **nosso workflow agentic** eu colocaria abaixo dos dois.

Mas para estudo humano de UX, é muito interessante.

---

# Para portfólio especificamente, eu também não ignoraria Landbook

O Mobbin é mais forte para:

```text
product UX
SaaS
apps
flows
patterns
```

Para seu **portfolio**, também precisamos de:

```text
art direction
editorial composition
web typography
storytelling
motion
hero
case studies
experimental layout
```

Aí entram referências como **Landbook**.

Ele tem acesso gratuito limitado e Pro de US$9/mês ou US$6/mês anual. Possui categorias, sections, motion, mobile previews e versões históricas. :chatgpt-content-reference{index="15"}

E eu usaria também gratuitamente:

```text
Landbook
Lapa Ninja
Godly
Awwwards
Figma Community
actual portfolio sites
actual studio sites
```

Mas com papéis diferentes.

---

# Essa distinção é importante

Não existe uma “biblioteca de referência definitiva”.

Eu classificaria as fontes assim:

```text
PRODUCT UX
────────────────────────

Mobbin
Refero
Pablooo
Page Flows


WEB / ART DIRECTION
────────────────────────

Landbook
Godly
Awwwards
Lapa Ninja


EDITABLE SYSTEMS
────────────────────────

Figma Community
Design-system repositories
official design systems


IMPLEMENTATION
────────────────────────

shadcn
Base UI
Radix
21st.dev
React Aria
etc.
```

Perceba que:

> `21st.dev` não substitui Mobbin.

E:

> `Mobbin` não substitui Figma Community.

E:

> `Awwwards` não substitui user-flow research.

São evidências diferentes.

---

# O que eu colocaria no nosso workflow

Eu criaria algo como um:

```text
reference-research
```

dentro do Design Director.

Ele poderia fazer:

```text
DESIGN TASK
      ↓

classify research need

      ↓

┌──────────────┬──────────────┬──────────────┐
│ Product UX   │ Art Direction│ Components   │
│              │              │              │
│ Mobbin       │ Landbook     │ DS docs      │
│ Refero       │ Godly        │ Figma        │
│ Pablooo      │ Awwwards     │ shadcn etc.  │
│ PageFlows    │ actual sites │              │
└──────────────┴──────────────┴──────────────┘

      ↓

broad exploration

      ↓

reference clusters

      ↓

patterns

      ↓

differences

      ↓

hypotheses

      ↓

project-specific decisions
```

---

# E as referências virariam documentação

Por exemplo:

```markdown
## Reference — Linear Settings

Source:
Mobbin

Relevant because:
Dense B2B settings surface for experienced users.

Observed pattern:
Two-level navigation with persistent local sidebar.

Useful:
- fast navigation
- hierarchy remains visible
- good scanning

Not appropriate for us:
- assumes expert/high-frequency users
- density excessive for our onboarding audience

Takeaway:
Consider persistent secondary navigation after onboarding,
but use lower initial density.
```

Observe o que não fazemos:

```text
"Linear ficou bonito. Copie."
```

Fazemos:

```text
observation
→ rationale
→ applicability
→ adaptation
```

Isso alimenta:

```text
REFERENCES.md
```

e eventualmente:

```text
DDR-007
```

---

# Eu também colocaria uma regra interessante

Para decisões significativas, a IA não pode se apoiar em uma única referência.

Algo conceitualmente como:

```text
Never treat one reference as evidence of a pattern.

For consequential interaction decisions:
search diverse comparable products,
identify similarities and disagreements,
then reason from product constraints.
```

Não precisa ser:

> “sempre exatamente 10 exemplos”.

Isso seria burocracia falsa.

Mas Claude precisa saber que:

```text
Stripe faz isso
```

é uma observação.

Enquanto:

```text
Stripe
Linear
Notion
Slack
GitHub

apresentam variações do mesmo modelo
```

começa a ser um padrão interessante de investigar.

---

# E eu faria outra separação ainda mais importante

### Inspiration reference

Serve para:

```text
"isso me interessa visualmente"
```

### Pattern reference

Serve para:

```text
"produtos resolvem frequentemente este problema assim"
```

### Evidence

Serve para:

```text
"temos dados mostrando que isso funciona no nosso contexto"
```

Essas três coisas NÃO são equivalentes.

Isso deveria estar explicitamente ensinado ao agente.

---

# Então vale pagar Mobbin?

Para **fazer só o portfólio**, eu não compraria imediatamente uma assinatura anual apenas por isso.

Testaria primeiro:

```text
Pablooo MCP
+
Landbook
+
Figma Community
+
pesquisa web
+
as skills que já temos
```

Isso já é muito poderoso.

Agora, para o que você está montando — um workflow reutilizável para:

- seu portfólio;
- SaaS;
- dashboards;
- sistemas web;
- projetos pessoais;
- projetos profissionais;
- Product Design;
- UX research;
- IA projetando interfaces continuamente —

**Mobbin começa a fazer bastante sentido.**

E se você conseguir o **desconto educacional de 50%**, a relação custo/benefício fica ainda mais atraente. :chatgpt-content-reference{index="16"}

Eu faria portanto:

```text
AGORA
────────────────────
Pablooo MCP       ✅
Figma MCP         ✅
Playwright MCP    ✅
web references    ✅

ANALISAR
────────────────────
Refero Skill/MCP

DEPOIS, SE O PROCESSO PROVAR VALOR
────────────────────
Mobbin Pro + MCP
```

E eu não colocaria:

```text
Pablooo + Mobbin + Refero + 12 MCPs
```

todos sendo consultados toda vez.

O Design Director deve decidir **qual fonte resolve aquela pesquisa**.

---

## E tem uma ótima maneira de decidir se você deve pagar

Podemos inclusive transformar seu **portfólio no benchmark do Mobbin**.

Primeiro rodamos a fase de pesquisa de referências usando:

```text
Pablooo
+ fontes abertas
+ pesquisa web
```

e observamos:

- relevância das referências;
- variedade;
- qualidade;
- quantas pesquisas falham;
- profundidade dos flows;
- quanto trabalho manual você ainda precisa fazer;
- quão bem Claude entende as referências.

Se a cobertura gratuita deixar lacunas claras, aí existe uma razão mensurável para adicionar Mobbin.

Isso é muito melhor do que assinar porque:

> “parece uma ferramenta maneira”.

E tem um detalhe que eu colocaria no prompt que vamos mandar ao Claude Code: **antes de instalar permanentemente Pablooo, Refero ou Mobbin no workflow, ele deve pesquisar a documentação atual, termos, privacidade, limites, sobreposição com as skills existentes e decidir onde cada fonte entra no `design-director`**. Assim a nossa arquitetura continua seguindo a regra que estamos construindo desde o começo: ferramenta entra porque resolve uma lacuna demonstrável, não porque apareceu num vídeo."

---

Eu enviei: "eu deixo aqui então né?

Welcome to fish, the friendly interactive shell
Type help for instructions on how to use fish

~ 
❯ ls
 Applications       go        󰉏 Pictures                   app-dashboard-dark.png     painel-situacao.md
 DataGripProjects   Library    Postman                    audit-charts-dark.png
 Desktop           󰿎 Movies     Public                     audit-data-dark.png
󰲂 Documents         󱍙 Music      Workspace                  audit-data-light.png
󰉍 Downloads          OrbStack   android-camera-check.png   audit-surfaces-empty.png

~ 
❯ cd Workspace/

~/Workspace 
❯ claude

~/Workspace took 28s 
❯ ls
 annotations   Casa-de-Sistemas   estudos     Obsidian   proposicoes-web   tt             prod_backup.dump
 backups       CodeSpace          minecraft   projetos   seplan            TT_Solutions

~/Workspace 
❯ mkdir tools

~/Workspace 
❯ cd tools/

~/Workspace/tools 
❯ ls

~/Workspace/tools 
❯"

o GPT respodeu: "Sim, **é exatamente aí que eu deixaria**.

Seu layout já ficou bem organizado:

```text
~/Workspace/
├── tools/
│   └── workflow-ai/        ← nosso fork
├── projetos/
├── seplan/
├── estudos/
├── minecraft/
└── ...
```

Ou seja, agora você já está no lugar certo:

```bash
~/Workspace/tools
```

A partir daqui, o próximo passo é **clonar o seu fork** para essa pasta.

Se você ainda não criou o fork no GitHub, crie primeiro a partir do repositório da Bea. Depois:

```bash
cd ~/Workspace/tools

git clone git@github.com:SEU-USUARIO/workflow-claude-codex-etc.git workflow-ai

cd workflow-ai
```

Eu gosto de clonar localmente com o nome `workflow-ai`, mesmo que no GitHub continue chamado `workflow-claude-codex-etc`, porque fica mais limpo:

```text
~/Workspace/tools/workflow-ai
```

Depois confira:

```bash
pwd
git remote -v
git status
```

E adicione o repositório original da Bea como `upstream`:

```bash
git remote add upstream git@github.com:whosbea/workflow-claude-codex-etc.git
git remote -v
```

O resultado esperado é algo parecido com:

```text
origin    git@github.com:SEU-USUARIO/workflow-claude-codex-etc.git
upstream  git@github.com:whosbea/workflow-claude-codex-etc.git
```

Aí crie nossa branch:

```bash
git switch -c feat/design-workflow-v1
```

E **só então**:

```bash
claude
```

Ou seja:

```text
~/Workspace/tools/workflow-ai
❯ claude
```

Esse é o local certo para mandar aquele superprompt que preparamos.

Um detalhe: você executou antes:

```bash
~/Workspace
❯ claude
```

Não aconteceu nada grave, mas eu evitaria trabalhar assim. `~/Workspace` contém muitos projetos diferentes, então o Claude pode ter um escopo desnecessariamente amplo. Para cada tarefa, abra o Claude na raiz **do projeto específico**.

Fica como regra:

```bash
# Evoluir o workflow
cd ~/Workspace/tools/workflow-ai
claude
```

```bash
# Futuro portfólio
cd ~/Workspace/projetos/portfolio
claude
```

```bash
# Projeto da SEPLAN
cd ~/Workspace/seplan/<projeto>
claude
```

O comportamento global continuará vindo de:

```text
~/.claude/CLAUDE.md
```

quando o workflow estiver instalado, então você **não precisa abrir Claude na home** para ele enxergar as skills/instruções globais.

E eu manteria a instalação em espera por enquanto. A ordem agora seria:

```text
1. Fork no GitHub
2. Clone em ~/Workspace/tools/workflow-ai
3. Adicionar upstream
4. Criar feat/design-workflow-v1
5. Abrir Claude dentro do workflow-ai
6. Mandar o superprompt de auditoria
7. Claude pesquisa/audita/corrige
8. ./install.sh --dry-run
9. revisar
10. instalar
11. verificar Figma/Playwright/etc.
12. começar o portfólio
```

Essa estrutura está bem melhor do que jogar o repositório diretamente em `~/`."

---

Eu enviei: "tá assim:

~/Workspace/tools 
❯ git clone git@github.com:FelipeDuan/workflow-claude-codex-etc.git workflow-ai
Cloning into 'workflow-ai'...
remote: Enumerating objects: 155, done.
remote: Counting objects: 100% (155/155), done.
remote: Compressing objects: 100% (98/98), done.
remote: Total 155 (delta 19), reused 151 (delta 19), pack-reused 0 (from 0)
Receiving objects: 100% (155/155), 98.61 KiB | 427.00 KiB/s, done.
Resolving deltas: 100% (19/19), done.

~/Workspace/tools took 2s 
❯ cd workflow-ai/

workflow-ai on  main 
❯ ls
 agents     harden    skills      install.sh  󰂺 README.md
 commands   scripts   AGENTS.md   LICENSE      third-party.lock

workflow-ai on  main 
❯ pwd
  git remote -v
  git status
/Users/felipe/Workspace/tools/workflow-ai
origin	git@github.com:FelipeDuan/workflow-claude-codex-etc.git (fetch)
origin	git@github.com:FelipeDuan/workflow-claude-codex-etc.git (push)
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean

workflow-ai on  main 
❯ git remote add upstream git@github.com:whosbea/workflow-claude-codex-etc.git
  git remote -v
origin	git@github.com:FelipeDuan/workflow-claude-codex-etc.git (fetch)
origin	git@github.com:FelipeDuan/workflow-claude-codex-etc.git (push)
upstream	git@github.com:whosbea/workflow-claude-codex-etc.git (fetch)
upstream	git@github.com:whosbea/workflow-claude-codex-etc.git (push)

workflow-ai on  main 
❯ git switch -c feat/design-workflow-v1
Switched to a new branch 'feat/design-workflow-v1'

workflow-ai on  feat/design-workflow-v1 
❯ 



Agora eu quero tudo que vou passar ao claude, bem completo, por favor"

o GPT respodeu: "Perfeito. Seu Git está exatamente onde eu queria: fork próprio, `origin` seu, `upstream` da Bea, working tree limpa e uma branch isolada `feat/design-workflow-v1`.

Agora eu passaria **um único briefing mestre** ao Claude Code, já aberto em:

```bash
cd ~/Workspace/tools/workflow-ai
claude
```

Esse prompt abaixo incorpora praticamente tudo que construímos: auditoria do workflow, segurança, atualizações, Figma, UX/UI, design system, pesquisa de referências, Mobbin/Pablooo/Refero, métricas, documentação, Graphify, Jev, QA, prevenção de AI Slop, gates, testes e o seu portfólio como benchmark — mas sem deixar o Claude transformar isso em overengineering.

Estamos trabalhando no meu fork pessoal do projeto `whosbea/workflow-claude-codex-etc`.

## Estado atual do repositório

Diretório local:

`~/Workspace/tools/workflow-ai`

Git:

- `origin`: `git@github.com:FelipeDuan/workflow-claude-codex-etc.git`
- `upstream`: `git@github.com:whosbea/workflow-claude-codex-etc.git`
- branch atual: `feat/design-workflow-v1`

O fork acabou de ser criado.

A working tree estava limpa no início desta tarefa.

Ainda não quero trabalhar no meu portfólio.

Primeiro quero evoluir este workflow de forma segura, profissional e incremental.

---

# MISSÃO PRINCIPAL

Quero transformar este fork gradualmente no meu workflow pessoal de engenharia, pesquisa, desenvolvimento e criação assistida por IA.

Nesta primeira evolução, o foco principal é construir uma vertical realmente madura de:

- Product Design;
- UX;
- UI;
- Interaction Design;
- Information Architecture;
- Design Systems;
- Visual Design;
- Art Direction;
- Prototyping;
- Figma;
- Accessibility;
- Usability;
- Visual QA;
- UX QA;
- research-driven design;
- métricas e validação;
- documentação de decisões.

Não quero simplesmente adicionar mais algumas "skills de design".

Quero um processo profissional completo que ajude agentes como Claude Code e Codex a:

1. entender corretamente um produto e o problema;
2. questionar requisitos ruins ou soluções prematuras;
3. investigar usuários, objetivos, tarefas e constraints;
4. explorar múltiplas soluções realmente diferentes;
5. pesquisar referências concretas;
6. raciocinar sobre UX antes de UI;
7. decidir conscientemente como representar informação;
8. construir identidade visual coerente;
9. decidir corretamente entre design system próprio, existente ou híbrido;
10. construir protótipos profissionais em Figma;
11. validar fluxos e interfaces;
12. medir o que for possível medir;
13. implementar sem destruir a intenção do design;
14. verificar visualmente a implementação;
15. registrar decisões importantes;
16. aprender com resultados sem acumular complexidade desnecessária.

O objetivo final não é "fazer telas bonitas".

É aumentar significativamente a qualidade das decisões de produto e design.

---

# PRINCÍPIO FUNDAMENTAL

Não quero complexidade por entusiasmo tecnológico.

Use sempre esta ordem mental:

necessidade comprovada
→ solução mais simples capaz de resolver corretamente
→ implementação
→ validação
→ evidência
→ só então evolução

Evite:

- agent sprawl;
- skill sprawl;
- MCP sprawl;
- dezenas de agentes conversando entre si;
- ferramentas duplicadas;
- instruções conflitantes;
- abstrações prematuras;
- frameworks de orchestration sem necessidade;
- "AI architecture astronautics";
- novos bancos ou knowledge graphs sem benefício demonstrado;
- dependências escolhidas por hype;
- atualizações automáticas para `latest`;
- adoção de bibliotecas porque "é o padrão";
- design orientado pela biblioteca escolhida;
- documentação burocrática sem valor;
- métricas inventadas;
- falsos scores de UX;
- processos tão rígidos que atrapalhem tarefas simples.

Quero maturidade, não quantidade.

Quero que você exerça julgamento profissional e critique inclusive minhas próprias ideias quando houver alternativa melhor.

---

# REGRA DE TRABALHO

Não comece fazendo mudanças grandes.

Trabalhe nesta sequência:

OBSERVE
→ UNDERSTAND
→ RESEARCH
→ MODEL
→ PROPOSE
→ IMPLEMENT
→ TEST
→ REVIEW
→ DOCUMENT

Investigue antes de afirmar.

Leia arquivos antes de descrever seu conteúdo.

Pesquise antes de assumir que uma integração, versão, API ou prática atual continua igual.

---

# FASE 0 — BASELINE E SEGURANÇA

Antes de qualquer alteração:

1. confirme branch atual;
2. confirme `git status`;
3. registre SHA atual;
4. confirme `origin`;
5. confirme `upstream`;
6. não faça `git push`;
7. não use `git reset --hard`;
8. não faça force push;
9. não remova configurações globais do usuário;
10. não apague arquivos sem entender sua finalidade.

Commits locais pequenos e coerentes são permitidos e desejáveis como checkpoints, caso façam sentido.

Não publique nada remotamente sem minha autorização.

---

# FASE 1 — ENTENDER INTEGRALMENTE O WORKFLOW ATUAL

Antes de propor arquitetura nova, leia integralmente ou em profundidade suficiente:

- `README.md`
- `AGENTS.md`
- `install.sh`
- `third-party.lock`
- `scripts/`
- `harden/`
- `agents/`
- `skills/`
- `commands/`

Mapeie:

## Estrutura

- como o projeto instala conteúdo;
- como Claude Code recebe instruções;
- como Codex recebe instruções;
- como `AGENTS.md` vira configuração global;
- como agents são convertidos;
- como commands são convertidos;
- como skills próprias são instaladas;
- como skills de terceiros são instaladas;
- symlinks;
- cópias;
- caches;
- backups;
- hardening;
- MCPs;
- validações existentes.

## Filosofia

Identifique os princípios arquiteturais atuais do workflow.

Não destrua boas decisões já existentes.

## Routing

Mapeie:

- como uma skill é descoberta;
- como agentes são escolhidos;
- possíveis colisões;
- redundâncias;
- descrições fracas;
- instruções sobrepostas;
- comportamentos globais excessivos.

## Design existente

Encontre absolutamente tudo relacionado a:

- design;
- frontend;
- UX;
- UI;
- Figma;
- Impeccable;
- Taste;
- Emil Kowalski;
- Humanizer;
- product strategy;
- research;
- Playwright;
- accessibility;
- prototypes;
- testing.

Antes de criar algo novo, diga o que já existe e por que não é suficiente.

---

# FASE 2 — INSPECIONAR MEU AMBIENTE LOCAL

Antes de executar o instalador, faça auditoria não destrutiva do ambiente.

Investigue:

- `git --version`
- shell atual;
- `claude --version`
- `codex --version`
- `node --version`
- npm/npx;
- `uv --version`
- `python3 --version`
- outros requisitos do instalador.

Verifique também:

- `claude mcp list`
- plugins Claude instalados;
- MCPs já existentes;
- configurações atuais do Codex;
- `~/.claude/CLAUDE.md`
- `~/.claude/settings.json`
- `~/.claude/skills`
- `~/.claude/agents`
- `~/.codex/`
- `~/.agents/skills`

Não exponha tokens, credentials, cookies ou secrets.

Não sobrescreva configuração existente silenciosamente.

Quando já houver algo instalado, determine:

- quem criou;
- se é equivalente;
- se há conflito;
- se deve ser preservado;
- se deve ser migrado.

---

# FASE 3 — COMPARAR COM UPSTREAM

Antes de modificarmos o fork significativamente:

```bash
git fetch upstream
```

Compare nossa base com `upstream/main`.

Verifique:

- commits que surgiram depois do fork;
- correções recentes;
- alterações em skills;
- mudanças no instalador;
- mudanças no lock;
- atualizações do README.

Não faça merge automático simplesmente porque há diferenças.

Avalie individualmente.

Nossa versão pode divergir conscientemente no futuro.

---

# FASE 4 — AUDITORIA DE DEPENDÊNCIAS

Para cada integração relevante, identifique:

- versão atual;
- SHA atual;
- upstream atual;
- changelog;
- breaking changes;
- segurança;
- compatibilidade;
- relevância da atualização.

## Regra

`latest` não significa `upgrade`.

O fluxo deve ser:

current
→ candidate
→ changelog
→ diff
→ compatibility
→ security
→ benefit
→ decision

Documente decisões significativas.

---

# GRAPHIFY

O workflow atualmente fixa uma versão do Graphify.

Temos indicação de que o lock utilizado originalmente apontava para `graphifyy 0.9.67` e que uma versão posterior `0.9.68` foi publicada com correções, inclusive uma possível correção relacionada a construção/quoting de path em comando shell.

NÃO aceite isso como verdade automaticamente.

Confirme diretamente no upstream atual:

- release atual;
- commit;
- changelog;
- segurança;
- compatibilidade;
- formato de instalação;
- necessidade de alterar SHA;
- necessidade de alterar versão;
- impacto no `install.sh`.

Se houver atualização segura e adequada, faça corretamente mantendo:

- pinning;
- verificabilidade;
- rollback;
- comportamento idempotente.

---

# GRAPHIFY COMO ARQUITETURA

Não transforme Graphify automaticamente em memória global ou "cérebro".

Avalie separadamente:

### O que ele resolve?

- code graph?
- docs?
- relações?
- recuperação contextual?
- impacto no consumo de tokens?
- qualidade das relações?
- risco de conhecimento inferido incorreto?

### Quando vale a pena?

Talvez:

- monorepos;
- projetos grandes;
- documentação extensa;
- muitas dependências internas.

Talvez não:

- landing page;
- pequeno portfólio;
- projeto com poucas dezenas de arquivos.

Quero conhecimento canônico mantido em:

- documentação;
- código;
- testes;
- decision records.

Graphify, se usado, deve ser um índice/estrutura derivada e descartável.

Nunca a única fonte de verdade.

Prepare uma futura hipótese de benchmark:

A:
Claude sem Graphify

B:
Claude + Graphify

Métricas possíveis:

- input tokens;
- output tokens;
- tool calls;
- arquivos abertos;
- tempo;
- dependências esquecidas;
- suposições incorretas;
- correção da resposta.

Não precisamos executar esse benchmark nesta primeira etapa se não houver necessidade.

---

# JEV

Não instale Jev agora.

Existe interesse futuro em investigar modelos/sistemas de decisões tipadas para:

- routing;
- gating;
- relevance;
- context compaction;
- classificações simples.

Mas Jev é muito novo e não quero adicioná-lo por hype.

Apenas crie, se fizer sentido, uma pequena nota de "future investigation".

Não adicione agora:

Claude
→ Jev
→ router
→ orchestrator
→ subagent
→ skill

Prefira regras simples.

Se no futuro houver problema mensurável de routing/contexto, podemos benchmarkar.

---

# FASE 5 — FIGMA

Quero integração profissional com Figma.

O workflow existente possui instruções para Figma MCP.

Existe indicação de que atualmente há um plugin oficial:

`figma@claude-plugins-official`

que pode incluir:

- integração oficial;
- MCP;
- agent skills específicas do Figma.

Confirme isso na documentação oficial atual antes de agir.

Verifique:

- plugin atual;
- versão atual;
- instalação recomendada;
- diferença entre plugin e MCP manual;
- possibilidade de duplicidade;
- escopo;
- autenticação;
- comportamento em Claude Code;
- impacto no Codex.

Se plugin oficial for a opção recomendada para Claude, prefira-o.

Para Codex, mantenha a integração apropriada compatível.

Não deixe duas integrações Figma redundantes sem motivo.

---

# FIGMA COMO FERRAMENTA DE DESIGN

Não quero que Claude use Figma apenas como ferramenta de screenshot.

O workflow deve ensinar agentes a criarem arquivos que um designer profissional consiga abrir e continuar trabalhando.

Considere boas práticas atuais de:

- pages;
- sections;
- frames;
- Auto Layout;
- constraints;
- variables;
- collections;
- modes;
- semantic tokens;
- styles;
- components;
- variants;
- component properties;
- instances;
- nested components;
- naming;
- responsive behavior;
- prototyping;
- interactions;
- states;
- documentation.

Estrutura possível:

00 — Cover / Readme
01 — Foundations
02 — Variables / Tokens
03 — Components
04 — Patterns
05 — Exploration
06 — User Flows
07 — Desktop
08 — Mobile
09 — Prototype
99 — Archive

Mas NÃO imponha essa estrutura universalmente.

Pesquise práticas atuais.

Adapte ao projeto.

---

# FIGMA NÃO É SÓ UI FINAL

O workflow deve conseguir usar Figma para:

- visual exploration;
- divergent concepts;
- comparison boards;
- reference boards;
- user flows;
- wireframes;
- high fidelity;
- components;
- prototypes;
- documentation;
- handoff.

Não converta imediatamente qualquer problema em high-fidelity UI.

---

# FASE 6 — PLAYWRIGHT

Playwright será fundamental.

Audite:

- versão atual;
- integração;
- MCP;
- atualização upstream;
- breaking changes;
- segurança;
- estabilidade.

Não atualize cegamente.

Posteriormente Playwright será usado para:

- browser inspection;
- screenshots;
- viewport testing;
- visual QA;
- responsive QA;
- interaction;
- keyboard;
- flows;
- accessibility support;
- regression testing.

Trate-o como ferramenta real de verificação.

Não apenas "mais um MCP disponível".

---

# FASE 7 — RESEARCH LAYER PARA DESIGN

Um dos problemas mais importantes de IA aplicada a design é tentar criar interfaces sem referências concretas.

Não quero que o modelo dependa apenas de padrões memorizados.

O workflow deve ser capaz de fazer pesquisa visual estruturada.

Precisamos distinguir:

## Inspiration Reference

"Isso é visualmente interessante."

## Pattern Reference

"Múltiplos produtos resolvem este problema dessa forma."

## Evidence

"Temos dados relevantes indicando que esta solução funciona em nosso contexto."

Esses três conceitos NÃO são equivalentes.

---

# REFERÊNCIAS CONCRETAS

Pesquise diferentes classes de fontes.

## Product / UX references

Avalie:

- Mobbin;
- Refero;
- Pablooo;
- Page Flows;
- produtos reais;
- design systems oficiais.

## Art direction / web references

Considere fontes como:

- Land-book;
- Godly;
- Awwwards;
- portfolios reais;
- sites de studios;
- sites editoriais;
- produtos relevantes.

## Components / implementation

Considere:

- Figma Community;
- design systems oficiais;
- Radix;
- Base UI;
- React Aria;
- shadcn;
- outros ecossistemas relevantes conforme necessidade.

Não trate essas categorias como intercambiáveis.

Mobbin não substitui Figma Community.

Awwwards não substitui UX research.

Shadcn não substitui design system.

---

# PABLOOO

Há indicação de existência de um MCP gratuito chamado Pablooo com screenshots reais de aplicações.

Pesquise e verifique:

- projeto atual;
- ownership;
- documentação;
- disponibilidade;
- privacidade;
- uptime;
- licenciamento;
- escopo;
- qualidade;
- quantidade;
- MCP;
- autenticação;
- riscos.

Se for realmente:

- gratuito;
- seguro;
- útil;
- não redundante;

considere integrá-lo como fonte inicial de referências.

Mas não adicione MCP por impulso.

Explique exatamente onde ele entra.

---

# MOBBIN

Mobbin parece uma fonte muito rica de:

- real-world screens;
- real user flows;
- patterns;
- desktop;
- mobile.

Existe um MCP oficial associado a planos pagos.

Não precisamos assinar Mobbin nesta fase.

Prepare o workflow para poder aproveitá-lo no futuro sem depender dele.

Se o MCP gratuito disponível cobrir nosso primeiro benchmark, ótimo.

Se encontrarmos lacunas reais, Mobbin poderá ser avaliado depois.

Não crie hard dependency em serviço pago.

---

# REFERO

Também investigue Refero como possível fonte de referências / MCP / skill.

Analise especialmente:

- screenshots;
- flows;
- metadata;
- integração com agentes;
- sobreposição com Mobbin/Pablooo;
- custos;
- limites;
- benefícios;
- riscos.

Não instale tudo.

Queremos routing.

---

# REFERENCE RESEARCH SKILL

Avalie criar uma pequena skill ou capability chamada conceitualmente:

`reference-research`

Seu papel não é copiar referências.

Deve:

1. entender o problema;
2. determinar que tipo de referência precisa;
3. pesquisar múltiplas fontes quando apropriado;
4. coletar referências diferentes;
5. identificar padrões;
6. identificar divergências;
7. separar observação de hipótese;
8. documentar applicability;
9. identificar anti-references;
10. alimentar o design process.

Nunca:

"Stripe faz assim → vamos fazer igual."

Quero:

problema
→ múltiplas referências
→ observações
→ pattern
→ constraints locais
→ hipótese
→ prototype
→ validation

---

# REFERÊNCIAS E DESIGN FIXATION

Não permita que referência vire cópia.

Precisamos usar referências para aumentar o espaço de soluções, não diminuí-lo.

Durante exploração:

- busque referências heterogêneas;
- evite uma única referência dominante;
- gere múltiplas direções conceituais.

Uma direção não é diferente da outra se apenas muda:

- cor;
- tipografia;
- radius;
- shadows;
- ornamentação.

Cada território precisa possuir:

- ideia;
- narrativa;
- composition model;
- information hierarchy;
- interaction philosophy;
- visual language.

---

# FASE 8 — PRODUCT DESIGN WORKFLOW

Quero uma vertical adaptativa.

Não uma checklist burocrática obrigatória.

O Design Director deve avaliar risco, escala e natureza da tarefa.

Um portfolio não exige o mesmo processo de um SaaS financeiro.

Uma landing page não exige o mesmo processo de uma aplicação operacional com 400 usuários.

Possível pipeline:

Discovery
→ Problem framing
→ Product understanding
→ Users
→ Jobs/tasks
→ Constraints
→ Research
→ Information architecture
→ User flows
→ Simplification
→ Divergent exploration
→ Art direction
→ Interaction design
→ Design system strategy
→ Components
→ Prototype
→ Usability review
→ Accessibility
→ Validation
→ Build
→ Visual QA
→ UX QA
→ Production data
→ Iteration

Cada etapa deve poder ser:

- required;
- lightweight;
- skipped.

Com justificativa.

---

# DESIGN DIRECTOR

Avalie criar uma skill ou agente central como:

`design-director`

IMPORTANTE:

Ele não é outra skill de "bom gosto".

Sua função é orchestration.

Ele deve:

1. classificar o tipo de problema;
2. estimar risco;
3. determinar profundidade necessária;
4. escolher fases;
5. selecionar skills especializadas;
6. impedir convergência prematura;
7. garantir artefatos coerentes;
8. controlar gates;
9. organizar pesquisa;
10. organizar crítica;
11. determinar quando precisamos de intervenção humana.

Quero o mínimo possível de lógica hardcoded.

Mas também não quero delegar absolutamente tudo a um LLM caro.

---

# POSSÍVEIS ESPECIALIDADES

Avalie a necessidade de separar conceitualmente:

### Product / UX

- problema;
- usuários;
- tarefas;
- journeys;
- IA;
- flows;
- simplificação;
- usability.

### Art Direction / UI

- referências;
- territories;
- composition;
- visual identity;
- typography;
- art direction;
- motion philosophy.

### Design System

- foundations;
- primitives;
- components;
- patterns;
- domain components;
- tokens;
- governance.

### Design Critic / QA

- heuristic review;
- accessibility;
- consistency;
- visual QA;
- UX QA;
- implementation fidelity.

Mas NÃO crie quatro agentes simplesmente porque listei quatro responsabilidades.

Compare:

- agents;
- skills;
- subagents;
- prompt modes;
- commands.

Escolha a arquitetura mais simples.

---

# UX ANTES DE UI

Essa regra deve ser estrutural.

Nunca assuma automaticamente:

lista → table

informação → card

muitos valores → dashboard

navegação → sidebar

landing page → hero + 3 cards + CTA

Antes pergunte:

- qual tarefa?
- qual decisão?
- qual informação?
- frequência?
- importância?
- temporalidade?
- comparação?
- exploração?
- leitura?
- descoberta?
- criação?
- edição?
- monitoramento?
- recuperação de erro?
- contexto?
- experiência?
- densidade?
- dispositivo?
- acessibilidade?

Só então represente.

---

# REPRESENTAÇÃO DA INFORMAÇÃO

Tabela, cards, charts, list, timeline, carousel, tabs, master-detail, wizard, search, command palette, filters, kanban, calendar etc. são soluções possíveis.

Nenhuma delas é universalmente correta.

A escolha deve vir de:

task
+ information structure
+ frequency
+ density
+ comparison needs
+ interaction
+ constraints.

Quero que o agente considere explicitamente alternativas antes de selecionar estruturas importantes.

---

# SIMPLIFICAÇÃO

Uma das funções mais importantes do workflow deve ser questionar o próprio produto.

Pergunte:

- essa tela precisa existir?
- essa etapa precisa existir?
- esse campo precisa existir?
- essa decisão precisa ser feita pelo usuário?
- o sistema já possui informação suficiente?
- podemos inferir?
- podemos automatizar?
- podemos mostrar progressivamente?
- podemos prevenir erro?
- podemos reduzir contexto?
- podemos consolidar etapas?
- podemos melhorar o modelo mental?

Não confunda:

minimal visual design

com:

simple UX.

Uma tela vazia pode ser péssima.

Uma tela densa pode ser excelente.

---

# DESIGN SYSTEM STRATEGY

Não quero:

"este workflow usa shadcn".

Nem:

"este workflow usa Radix".

Nem:

"sempre crie do zero."

Quero decisão contextual.

Possibilidades:

1. existing design system;
2. visual component library;
3. headless primitives;
4. custom system;
5. hybrid system;
6. foundations próprias + primitives externas;
7. domain-specific layer sobre base existente.

Avalie:

- accessibility;
- flexibility;
- semantics;
- interaction;
- customization;
- identity;
- performance;
- bundle;
- theming;
- tokens;
- maintenance;
- ecosystem;
- maturity;
- framework compatibility;
- long-term cost;
- speed;
- required components;
- required behavior.

---

# SHADCN

Não considero shadcn ruim.

O problema é usá-lo cru e tratá-lo como identidade.

Se fizer sentido usar shadcn:

- customize;
- adapte;
- crie tokens;
- crie patterns;
- crie domain components;
- revise anatomy;
- mantenha a identidade própria.

Não aceite:

Button
Input
Card
Table
Dialog

como "design system finalizado".

---

# CAMADAS DO DESIGN SYSTEM

Considere:

## Foundations

- color;
- typography;
- spacing;
- dimensions;
- grid;
- radius;
- elevation;
- motion;
- breakpoints;
- iconography;
- imagery.

## Primitives

Elementos básicos.

## Components

Combinações reutilizáveis.

## Patterns

Soluções de interação recorrentes.

Ex.:

- filter + search;
- bulk actions;
- empty states;
- confirmation;
- errors;
- permission handling;
- onboarding.

## Domain Components

Ex.:

- ContractStatus;
- EmployeeComparison;
- PriceHistory;
- TrainingSession;
- PipelineStage.

Esses componentes são frequentemente onde surge identidade real do produto.

---

# DESIGN SYSTEM NÃO É SÓ VISUAL

Inclua:

- behavior;
- keyboard;
- accessibility;
- states;
- anatomy;
- interaction contracts;
- content rules;
- motion;
- responsiveness.

---

# DESIGN DOCUMENTATION

Avalie artefatos adaptativos como:

- `PRODUCT.md`
- `UX.md`
- `FLOWS.md`
- `REFERENCES.md`
- `DESIGN.md`
- `DESIGN-SYSTEM.md`
- `VALIDATION.md`
- `DDR/`

Não crie todos por obrigação.

Crie quando houver conhecimento real.

---

# DESIGN.md

Não quero um arquivo com:

primary blue
radius 8
use shadcn

Quero, quando apropriado:

- Design Thesis
- Product personality
- Experience principles
- Information hierarchy
- Density strategy
- Navigation model
- Visual grammar
- Typography philosophy
- Color semantics
- Shape language
- Spatial system
- Motion philosophy
- Interaction principles
- Imagery
- Illustration
- Data visualization
- Responsive behavior
- Accessibility contract
- Anti-patterns
- signature elements
- rationale.

---

# DESIGN DECISION RECORDS

Avalie um formato de DDR:

`DDR-XXX`

Campos possíveis:

- Context
- Problem
- Constraints
- Decision
- Alternatives
- Evidence
- Trade-offs
- Consequences
- Revisit when
- Status

Não registre:

"radius virou 10".

Registre decisões relevantes como:

"card vs row"

"modal vs page"

"sidebar vs command navigation"

"custom DS vs headless primitives"

---

# ANTI-AI-SLOP

Quero combater o que normalmente aparece em interfaces geradas por IA:

- generic SaaS landing page;
- hero centralizado por padrão;
- gradient blobs;
- excesso de glow;
- glassmorphism gratuito;
- bento sem razão;
- cards dentro de cards;
- excesso de rounded containers;
- badges decorativos;
- icon boxes;
- grandes áreas vazias sem função;
- "premium dark mode" genérico;
- "AI startup" visual;
- layout que poderia pertencer a qualquer empresa;
- texto abstrato;
- "Empowering your workflow";
- "Transform your experience";
- excesso de microinterações sem significado.

Mas cuidado:

não transforme "anti-AI-slop" em outro preset.

O objetivo não é banir cards ou gradients.

É exigir intenção.

---

# DIVERGENT DESIGN

Quando uma tarefa exigir direção visual importante:

não crie uma solução imediatamente.

Explore aproximadamente 5–7 territórios quando o risco justificar.

Não precisam sempre ser exatamente 5 ou 7.

Direções devem ser conceitualmente distintas.

Para cada uma:

- concept;
- metaphor;
- narrative;
- content model;
- layout grammar;
- typography philosophy;
- visual language;
- interaction model;
- motion;
- imagery;
- signature element;
- strengths;
- risks;
- anti-patterns.

Depois compare.

Não escolha automaticamente "a melhor".

Humano participa da convergência.

---

# CRIAÇÃO ≠ CRÍTICA

Evite:

Claude cria
→ Claude olha
→ Claude diz "está excelente"

Avalie alguma separação crítica.

Pode ser:

- subagent;
- critic skill;
- fresh context;
- screenshot-only review;
- heuristic review.

O crítico não precisa conhecer toda justificativa do criador.

Quero reduzir confirmation bias.

Mas não quero triplicar custo sem necessidade.

---

# UX HEURISTICS

Quando adequado, faça avaliação heurística sistemática.

Pode usar heurísticas consolidadas como Nielsen, mas confirme fontes atuais.

Um finding pode ter:

- ID;
- area;
- screen;
- flow;
- evidence;
- heuristic;
- severity;
- consequence;
- possible hypothesis;
- status.

Se usar severidade, documente escala.

Não confunda heuristic evaluation com user research.

---

# USABILITY METRICS

Quando houver teste de tarefas, considere:

- task completion;
- task success;
- median time on task;
- critical errors;
- recoverable errors;
- backtracking;
- assistance required;
- perceived ease;
- qualitative notes.

Pesquise instrumentos existentes antes de criar escala nova.

SEQ pode ser uma opção.

Não invente:

"UX score: 92".

Evite falsa precisão.

---

# ACCESSIBILITY

Accessibility deve existir desde foundations.

Não como checklist final.

Use WCAG atual e fontes primárias.

Automatize quando possível:

- contrast;
- target size;
- focus visibility;
- focus order;
- keyboard;
- semantics;
- ARIA;
- reduced motion;
- responsive/reflow;
- text resizing.

Mas reconheça questões qualitativas.

Não declare "WCAG compliant" apenas porque um scanner não encontrou erro.

---

# MOTION

Skills do Emil Kowalski parecem relevantes especialmente para refinement de motion.

Use no momento adequado.

Não deixe motion determinar direção de produto.

Motion deve:

- comunicar;
- orientar;
- contextualizar;
- dar feedback;
- preservar continuidade;
- aumentar compreensão.

Não deve existir apenas para impressionar.

---

# IMPECCABLE

Avalie profundamente como Impeccable já funciona.

Queremos aproveitar:

- critique;
- audit;
- polish;
- anti-pattern detection;
- design documentation;
- deterministic checks quando existirem.

Não duplique funcionalidade se Impeccable já resolve corretamente.

Determine quando deve entrar:

talvez:
- prototype review;
- visual QA;
- polish.

Não necessariamente:
- product discovery.

---

# TASTE

Taste pode ser útil para pressão criativa/art direction.

Mas verifique:

- versão;
- filosofia;
- overlap;
- riscos de opinionated defaults.

Não quero Taste + Impeccable + Emil + Frontend Design disputando decisão simultaneamente.

Crie routing.

---

# ANTHROPIC FRONTEND DESIGN

Investigue o plugin/skill oficial atual de frontend design da Anthropic, se ainda existir e for compatível.

Analise se agrega ao conjunto.

Não adicione automaticamente.

Compare overlap com:

- Taste;
- Impeccable;
- design-director.

---

# HUMANIZER

Humanizer pode ser útil para:

- copy;
- microcopy;
- headings;
- narrative;
- explanations.

Não use como ferramenta de Product UX principal.

---

# FASE 9 — GATES

Considere gates adaptativos.

Exemplo conceitual:

G0 Problem
G1 UX
G2 Direction
G3 System
G4 Prototype
G5 Validation
G6 Build
G7 QA
G8 Production

IMPORTANTE:

Gate não passa porque:

`PRODUCT.md` existe.

Gate passa porque existe evidência suficiente proporcional ao risco.

Para uma landing page pessoal:

processo leve.

Para ferramenta financeira:

processo rigoroso.

---

# FASE 10 — MÉTRICAS DO PRÓPRIO WORKFLOW

Quero eventualmente avaliar se o workflow realmente melhora resultados.

Pense em benchmarks possíveis.

Ex.:

### Baseline

"Claude, faça uma dashboard"

### Workflow

Claude usando:
- discovery;
- reference research;
- UX reasoning;
- design system;
- critique.

Avaliar:

- diversidade inicial;
- number of iterations;
- accessibility findings;
- flow errors;
- design consistency;
- subjective quality from independent reviewers;
- task completion;
- implementation defects;
- design-to-code mismatch;
- tokens;
- cost.

Não precisamos construir um laboratório agora.

Mas o workflow deve ser testável.

---

# FASE 11 — NOSSO PORTFÓLIO COMO PRIMEIRO BENCHMARK

Depois de terminar este trabalho, meu portfólio pessoal será o primeiro grande teste.

NÃO comece o portfólio agora.

Prepare apenas o plano.

O teste do portfolio deve validar principalmente:

- discovery;
- identity extraction;
- storytelling;
- reference research;
- divergent art direction;
- anti-AI-slop;
- typography;
- composition;
- design system;
- Figma organization;
- prototyping;
- motion;
- accessibility;
- responsive behavior;
- design-to-code fidelity.

Como é um portfolio, art direction e narrativa terão peso maior que fluxos operacionais complexos.

---

# PROCESSO FUTURO DO PORTFÓLIO

Quando chegarmos nele, quero aproximadamente:

1. personal/professional discovery;
2. content audit;
3. goals;
4. audiences;
5. differentiators;
6. reference research;
7. anti-references;
8. visual territories;
9. comparison;
10. human convergence;
11. DESIGN.md;
12. content architecture;
13. Figma foundations;
14. Figma components;
15. exploratory frames;
16. desktop;
17. mobile;
18. prototypes;
19. critique;
20. accessibility;
21. implementation;
22. Playwright visual review;
23. refinement.

Mas isso será em tarefa futura.

---

# FASE 12 — MCP STRATEGY

Não quero que todos os MCPs rodem sempre.

Precisamos de routing.

Possíveis capacidades:

### Figma
design/prototype/write/read.

### Playwright
browser QA.

### Pablooo/Mobbin/Refero
reference research.

### Outros
apenas se justificáveis.

MCP deve resolver uma capacidade clara.

Documente:

- purpose;
- when to use;
- when not to use;
- data/privacy considerations;
- authentication;
- cost;
- fallback.

---

# CUSTO E PRIVACIDADE

Para qualquer serviço externo, considere:

- o que é enviado;
- se código é enviado;
- se screenshots são enviados;
- retenção;
- telemetry;
- account requirements;
- paid/free;
- rate limits;
- licensing;
- terms;
- secrets.

Não precisamos fazer auditoria jurídica profunda, mas não instale ferramenta obscura sem avaliar riscos básicos.

---

# FASE 13 — ARCHITECTURE PRINCIPLE

Use o mecanismo mais barato e determinístico capaz de resolver corretamente o problema.

Preferência:

deterministic rule
→ static analysis
→ test
→ existing project knowledge
→ heuristic
→ specialized lightweight model
→ reasoning model
→ human judgment

Exemplos:

Contraste:
math/tool.

Broken link:
test.

Spacing inconsistency:
visual/static detection.

Art direction:
human + model.

Product tradeoff:
reasoning + evidence.

Não desperdice frontier model em problema determinístico.

---

# FASE 14 — IMPLEMENTAR A VERTICAL

Depois da análise, proponha a arquitetura mínima.

Possivelmente:

```text
skills/
  design-director/
  reference-research/
  ...
```

ou outra estrutura melhor.

Não assuma nomes.

Antes de implementar, explique:

- componentes;
- responsabilidades;
- routing;
- dependências;
- razão de cada nova parte;
- o que ficou fora.

Então implemente.

---

# AGENTS.md GLOBAL

Mantenha relativamente pequeno.

Idealmente contém:

- princípios globais;
- routing;
- safety/process;
- simplicity;
- high-level expectations.

Não despeje manual completo de UX dentro dele.

Conhecimento especializado deve estar em skills específicas.

Evite duplicação.

---

# SKILL DESCRIPTIONS

Descriptions são fundamentais para routing.

Escreva-as de forma precisa.

Inclua:

- triggers;
- scope;
- anti-triggers;
- relation to other skills.

Evite descrições:

"Use this for design."

Prefira:

"Use when the task requires product/UX discovery, interaction modeling, visual direction or Figma design; do not invoke for implementation-only frontend bug fixes unless design decisions are involved."

---

# TESTES E VALIDAÇÕES DO WORKFLOW

Quero testes possíveis para:

- frontmatter;
- skill names;
- duplicate destinations;
- agent conversion;
- command conversion;
- install script;
- dry-run;
- harden;
- idempotency;
- symlink behavior;
- TOML correctness;
- settings merge;
- plugin/MCP configuration;
- broken symlinks.

Se o projeto já possui checks, reutilize.

Não construa framework gigante de testes shell se simples scripts resolverem.

---

# INSTALAÇÃO

Somente depois de:

1. audit;
2. patches;
3. tests;
4. review.

Execute:

```bash
./install.sh --dry-run
```

Analise cuidadosamente.

Se estiver correto, podemos realizar instalação real.

Você tem autorização para executar instalação local não destrutiva após validar o dry-run, desde que:

- backups estejam funcionando;
- configuração existente tenha sido analisada;
- não haja conflitos graves;
- rollback esteja claro.

Use `--harden` quando for seguro e compatível.

---

# FIGMA PLUGIN/MCP

Depois de validar documentação atual:

- instale/configure integração oficial adequada;
- evite duplicidade;
- autentique somente quando necessário;
- valide que ferramentas aparecem;
- registre procedimento.

---

# REFERENCE MCP GRATUITO

Se Pablooo for validado como:

- legítimo;
- gratuito;
- útil;
- seguro o suficiente;
- sem conflito;

você pode propor instalação.

Antes de instalar, explique em uma frase:

- benefício;
- risco;
- razão.

Se houver ambiguidade material, deixe documentado em vez de instalar.

---

# MOBBIN / REFERO

Não assine, compre ou crie planos.

Apenas deixe o workflow compatível/consciente dessas fontes.

---

# DOCUMENTAÇÃO DO WORKFLOW

Ao final atualize documentação necessária.

Quero conseguir entender:

## Architecture

Como tudo funciona.

## Design Workflow

Quando ele é ativado.

## Phases

Como são escolhidas.

## Skills

Para que serve cada uma.

## Tools

Figma, Playwright, references.

## Artifacts

Quando criar cada documento.

## Gates

Como funcionam.

## Examples

Exemplos concretos.

## Anti-patterns

O que NÃO fazer.

## Troubleshooting

Problemas comuns.

---

# NÃO QUEBRE CODEX

Esse repositório serve múltiplos agentes.

Sempre que criar skill/agent/command:

- verifique compatibilidade;
- conversão;
- destino;
- naming;
- limitations.

Se algo for Claude-only, registre explicitamente.

---

# UPSTREAM FUTURO

Documente como sincronizar:

```bash
git fetch upstream
```

e avaliar:

```bash
git log HEAD..upstream/main
git diff HEAD...upstream/main
```

Não recomende merge cego.

Nosso fork poderá divergir.

---

# COMMITS

Faça commits locais semanticamente coerentes quando ajudar.

Exemplo:

- `chore: audit and update third-party integrations`
- `feat: add product design orchestration`
- `feat: add reference research workflow`
- `docs: document design workflow`

Esses nomes são apenas exemplos.

Não faça commits enormes misturando tudo se puder evitar.

Não faça push.

---

# RELATÓRIO FINAL

Quando terminar, me entregue relatório estruturado com:

## 1. Baseline

O que existia.

## 2. Research

Fontes relevantes consultadas.

## 3. Findings

Problemas, lacunas e riscos.

## 4. Updates

Dependências/integrations atualizadas.

## 5. Architecture

Nova arquitetura de design.

## 6. Files changed

Arquivo por arquivo.

## 7. Skills

Novas/alteradas e routing.

## 8. MCPs/plugins

Estado final.

## 9. Tests

Comandos e resultados.

## 10. Installation

Dry-run e instalação.

## 11. Decisions

Principais decisões e alternativas rejeitadas.

## 12. Risks

O que ainda merece atenção.

## 13. Technical debt

O que decidimos conscientemente postergar.

## 14. Rollback

Como desfazer.

## 15. Upstream

Como manter sincronizado.

## 16. Portfolio benchmark

Passo seguinte para iniciar meu portfólio.

---

# CRITÉRIOS DE QUALIDADE

O resultado desta tarefa deve ser:

- simples;
- compreensível;
- extensível;
- seguro;
- reversível;
- testável;
- documentado;
- consistente;
- compatível com Claude;
- compatível com Codex quando aplicável;
- baseado em evidência;
- sem dependências inúteis;
- sem duplicação de responsabilidades;
- sem arquitetura multiagente teatral.

---

# DEFINITION OF DONE

Só considero esta primeira versão concluída quando tivermos, na medida em que fizer sentido:

- workflow atual auditado;
- upstream analisado;
- ambiente analisado;
- dependências importantes verificadas;
- atualizações seguras feitas;
- Graphify verificado;
- Figma profissionalmente integrado;
- Playwright verificado;
- estratégia de reference research definida;
- fontes gratuitas avaliadas;
- design-director ou equivalente implementado;
- UX-before-UI incorporado;
- design system strategy incorporada;
- anti-AI-slop incorporado sem virar preset;
- design decisions documentáveis;
- validation/metrics strategy;
- accessibility;
- visual QA;
- routing claro;
- documentação;
- testes;
- dry-run bem-sucedido;
- instalação validada;
- plano do portfolio benchmark.

---

# COMPORTAMENTO ESPERADO DE VOCÊ

Não seja apenas executor literal.

Atue como:

- senior product designer;
- UX architect;
- senior UI designer;
- design systems architect;
- senior frontend engineer;
- software architect;
- developer tooling engineer;
- AI workflow engineer;
- researcher;
- critic.

Mas sem roleplay vazio.

O importante é aplicar os critérios dessas disciplinas.

Questione premissas.

Mostre trade-offs.

Não crie certeza onde não existe.

Não trate opinião como estudo.

Não transforme estudo isolado em lei.

Não reproduza popularidade como evidência técnica.

Não use buzzwords para preencher lacunas.

Não otimize prematuramente.

Não faça overengineering.

---

# PRINCÍPIO FINAL

Quero que este workflow ajude a transformar ideias abstratas em produtos concretos sem eliminar a parte humana do processo criativo.

A IA deve ampliar:

- exploração;
- análise;
- pesquisa;
- execução;
- comparação;
- crítica;
- validação.

Ela não deve simplesmente gerar a primeira solução plausível e refiná-la até parecer profissional.

O objetivo não é automatizar criatividade.

É criar um ambiente em que humanos e agentes consigam tomar decisões de design significativamente melhores.

Comece agora pela auditoria e compreensão profunda do repositório.

Trabalhe incrementalmente e mantenha-me informado quando encontrar decisões arquiteturalmente importantes, riscos, conflitos ou evidências que mudem significativamente o plano.

Você possui autonomia para fazer alterações locais reversíveis, pesquisar, testar e melhorar o fork dentro das restrições descritas acima.

Não comece meu portfólio ainda.

### Depois de colar isso

Eu deixaria o Claude trabalhar **nesse mesmo `feat/design-workflow-v1`** e observaria principalmente se ele começa corretamente por leitura/auditoria em vez de sair criando arquivos.

Se ele começar dizendo algo como:

> “Vou criar `design-director`, `ux-researcher`, `visual-designer`, `figma-master`, `accessibility-agent`...”

antes de estudar o que já existe, eu interromperia. O comportamento que queremos é primeiro algo próximo de:

```text
repo atual
    ↓
inventário
    ↓
overlap existente
    ↓
pesquisa upstream
    ↓
lacunas reais
    ↓
arquitetura mínima
```

E tem uma segunda coisa importante: **não mande ainda aquele prompt do portfólio**. Primeiro vamos ver o que esse processo produz no fork. Quando o Claude terminar, me traga o relatório dele, o `git diff --stat`, os arquivos/skills que ele adicionou e, se possível, a resposta final completa. Aí conseguimos fazer uma **code/design-workflow review independente** antes de aceitar que essa V1 está boa o suficiente para ser instalada e usada no seu portfólio."

---
