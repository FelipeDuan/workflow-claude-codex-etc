---
name: reference-research
description: Collects and analyzes design references (UI patterns, flows, art direction, component behavior) before exploring or deciding on a design. Use when a design task needs concrete references for a new product, screen, flow, redesign, portfolio or landing page, usually called from the design-director skill before generating territories. Produces a REFERENCES.md with patterns, divergences, hypotheses and anti-references. Not for copying or cloning a specific product, not for visual direction itself (use design-director and its routed direction skill), and not a substitute for user research.
---

# Reference Research

References widen the solution space. They are never templates to copy.

## Three kinds, not interchangeable

| Kind | Says | Can support |
|---|---|---|
| Inspiration | "This is visually interesting" | Art direction ideas, territories |
| Pattern | "Several products solve this problem this way" | A default to start from, and what users may already expect |
| Evidence | "Data suggests this works in a context like ours" | A decision, when the context really matches |

Shipped does not mean validated. Real products carry legacy, running A/B experiments, business compromises and inaccessible patterns. One reference is never evidence of a pattern.

## Process

1. Understand the problem: read PRODUCT.md and the UX flows. Name the task or screen the references are for.
2. Decide what kind of reference is needed (inspiration, pattern or evidence) for each question.
3. Pick source classes from the routing table below.
4. Collect heterogeneous references: different products, domains and scales. Avoid one dominant reference that everything ends up imitating.
5. Write observations: what the reference does, stated neutrally.
6. Extract patterns (what several references share) and divergences (where they disagree, and why that might be).
7. Apply local constraints: our users, content, stack, accessibility needs, brand.
8. Turn it into hypotheses to test, not conclusions.
9. List anti-references: what we will deliberately not do, and why.
10. Hand the result to design-director (territories, UX, direction).

## Source routing

| Need | Source classes |
|---|---|
| Product UX, flows and screens | Mobbin, Refero, Page Flows, Pablooo, real products you can use, official design systems |
| Art direction and web | Land-book, Godly, Awwwards, studio and editorial sites, real portfolios |
| Components and implementation behavior | Official design systems, Radix, Base UI, React Aria, shadcn/ui, Figma Community |

These are not substitutes: Mobbin does not replace Figma Community, Awwwards does not replace UX research, shadcn/ui does not replace a design system.

## Tooling

Default, no setup: web search and fetch, the user's own screenshots, and Playwright to capture live sites (mobile about 390px, desktop about 1440px).

Optional MCP servers. None are installed by default; suggest one only when it clearly helps, and let the user decide:

- **Pablooo** (`https://mcp.pablooo.club`): free, no account, around 8k screenshots. It is a closed hosted service by Graines SAS, with no public repository or license, and its privacy policy does not document query logging. Send only generic search terms, never code, file contents or client data. Install: `claude mcp add --transport http pablooo --scope user https://mcp.pablooo.club` (Codex: `codex mcp add pablooo --url https://mcp.pablooo.club`)
- **Mobbin MCP** (official, `https://api.mobbin.com/mcp`): requires a paid Pro or Team plan.
- **Refero MCP** (`https://api.refero.design/mcp`): paid plans only.

Never make a paid service a hard dependency. Never create accounts or make purchases for the user.

## Save tokens: funnel

1. Search metadata and text first (titles, descriptions, tags, page text).
2. Build a shortlist.
3. Fetch images or screenshots only for the few candidates that survive.

## Output: REFERENCES.md

One entry per reference:

```
### <Reference name>
Source/URL:
Kind: inspiration | pattern | evidence
Relevant because:
Observed pattern:
What to take:
What not to take / why it doesn't fit us:
Takeaway:
```

Then:

```
## Patterns
<pattern> — seen in: <refs> — divergences: <refs and why>

## Hypotheses
<what we will try, and how we would know it works>

## Anti-references
<reference or pattern> — why we are not doing this
```

Rules: attribute every reference; never copy pixels, copy or assets; never cite a single reference as proof of a pattern; mark evidence whose context differs from ours.
