---
name: design-director
description: Orchestrates product, UX and UI design work with depth proportional to risk. Use FIRST, before impeccable, frontend-design, design-taste-frontend or redesign-existing-projects, when the request is to create or redesign a whole product, page, portfolio or landing page; those skills are called from here. Also use when a task needs product/UX discovery, information architecture or flow design, visual direction, a design-system strategy, a Figma prototype or validation as part of that work. It triages, plans the phases, gates on evidence and routes each step to a specialist (impeccable, design-taste-frontend, emil-design-eng, humanizer, figma-use, reference-research, design-critic). It is not a taste or style skill and does not write UI code. For a standalone review of an existing UI, use the design-critic agent or impeccable critique/audit. Do not use for implementation-only frontend bug fixes or small tweaks to a settled design; use frontend-ux-ui or impeccable directly.
---

# Design Director

Orchestration, not taste. This skill decides which design work is needed, in what order, how deep, and who does each step. Specialists do the craft.

Run this skill in the main conversation. If you are running as a subagent (for example frontend-ux-ui), do not run it: stop and return to the caller recommending design-director.

Principles that drive every decision below:
- UX before UI. Decide what the product must do before how it looks.
- Adaptive depth. A personal landing page gets a light pass; a financial operations tool gets a rigorous one.
- Cheapest reliable mechanism first. Contrast is math, a broken link is a test, art direction is human judgment helped by the model.
- A gate passes on evidence proportional to risk, never because a file exists.
- The model diverges, the human converges. Creation and critique run in separate contexts.
- No invented metrics, no "UX score", no "WCAG compliant" claimed from a scanner.

## Step 0: triage and plan

1. Read what exists: PRODUCT.md, DESIGN.md, UX.md/FLOWS.md, REFERENCES.md, docs/ddr/, the stack, the component library and tokens in use.
2. Classify the work:
   - marketing, portfolio or landing page
   - product screen or flow
   - design system
   - redesign (the old look becomes evidence, not a constraint)
   - refinement (keep the existing identity; usually route straight to frontend-ux-ui or impeccable and stop here)
3. Estimate risk from:
   - audience size and diversity (one person vs. thousands, assistive technology users)
   - money, personal data or irreversible actions involved
   - novelty (known pattern vs. a new interaction or domain)
   - cost of being wrong (a cosmetic regret vs. users making wrong decisions)
4. Output a plan table and nothing else yet:

| Phase | Depth (required / light / skip) | Why |
|---|---|---|
| Frame | ... | ... |
| UX | ... | ... |
| ... | ... | ... |

5. If any phase is more than light, ask the user to confirm or adjust the plan before starting. For a trivial plan, state it in one line and proceed.

## Phases

Each phase is adaptive. "Light" means a few lines in chat or in an existing doc, not a new file.

1. **Frame.** Problem, users, their tasks or jobs, constraints (tech, brand, legal, deadline), success criteria. Add a content inventory: what real content exists (projects, copy, images, links) and what's missing. Record it in PRODUCT.md. If impeccable is available, its `init` writes PRODUCT.md: reuse that file, do not keep a parallel one. For scope and MVP cuts, use grilling (model-invocable), or suggest the user run /grill-me (/grill-with-docs if CONTEXT.md exists); or the product-strategist agent.
2. **UX.** Task list, information architecture, primary flows, what each screen must let the user decide or do, and how information is represented. Ask the simplification questions before adding anything. Details in [references/ux-representation.md](references/ux-representation.md). Record in UX.md or FLOWS.md when flows are non-trivial; impeccable `shape` can run the discovery interview.
3. **References.** Invoke the reference-research skill. It returns patterns, divergences, anti-references and hypotheses, not things to copy.
4. **Diverge.** Generate conceptually distinct territories (count proportional to risk). See [references/territories.md](references/territories.md).
5. **Converge.** Present a decomposed comparison and stop. The user picks, combines or rejects.
6. **Direction and system.** Turn the chosen territory into a DESIGN.md and a design-system strategy. See [references/design-system-strategy.md](references/design-system-strategy.md) for what a good DESIGN.md contains before anything is built. After a build exists, impeccable `document` can derive DESIGN.md from the shipped code; reconcile the two instead of keeping both.
7. **Prototype.** In Figma when available and when the risk justifies it. See [references/figma.md](references/figma.md). A low-risk page can go straight to code.
8. **Validate.** Heuristic review by the design-critic agent in a fresh context; task-based metrics when real users are available. Capture screenshots/states with Playwright before spawning design-critic, and pass only brief, tasks, DESIGN.md and captures (not the rationale). Without subagents (Codex, or tools without subagents), run the critique in a new session with only the brief, tasks, DESIGN.md and screenshots. See [references/validation.md](references/validation.md).
9. **Build.** Hand off to the frontend-ux-ui agent (or the implementation agent the project uses) with PRODUCT.md, DESIGN.md, flows and accepted findings.
10. **QA.** Playwright screenshots at about 390px and 1440px, forced states (loading, empty, error, success, invalid form, permission denied), keyboard and focus; impeccable `audit` for deterministic checks and `critique` for review; design-critic again in a fresh context. Capture screenshots/states with Playwright before spawning design-critic, and pass only brief, tasks, DESIGN.md and captures (not the rationale); without subagents, use a new session as in Validate.
11. **Iterate.** Fix by severity, record decisions that matter as DDRs, re-run only the checks the change affects.

## Gates

A gate is a question answered with evidence. For low risk, a sentence of evidence is enough; for high risk, it needs artifacts, checks or user data. Any gate can fail and send work back to an earlier phase. Say so explicitly when it happens.

| Gate | After | Question |
|---|---|---|
| G0 | Triage | Is the triage and depth plan agreed with the user? |
| G1 | Frame | Do we know who the users are, what they must accomplish, and what success looks like? |
| G2 | UX | Do the flows cover the main tasks, errors and edge states, with nothing on screen that lacks a reason? |
| G3 | Converge | Are the territories really distinct, and did the user (not the model) choose? |
| G4 | Direction | Does DESIGN.md state intent, principles and rules someone else could apply, not just values? |
| G5 | Validate | Did validation find no unresolved severity 3-4 issues on critical tasks? |
| G6 | QA | Does the build match the direction, with states, responsiveness, keyboard and automated a11y checks verified, and manual checks listed? |
| G7 | Iterate | Are the decisions worth keeping recorded (DDRs, DESIGN.md updates) and the rest discarded? |

If Prototype is skipped, Validate runs on the first build during QA and G5 is checked there.

## Routing

One specialist per step. Never run two direction skills on the same surface.

| Phase or need | Route to |
|---|---|
| Frame, scope, MVP cuts | grilling (model-invocable), or suggest the user run /grill-me (/grill-with-docs if CONTEXT.md exists); product-strategist agent; impeccable `init` for PRODUCT.md |
| UX discovery for a surface | impeccable `shape`, frontend-screen-design for per-screen goal and states |
| References | reference-research |
| Visual direction, product UI or general | impeccable (new work). frontend-design only if impeccable is unavailable |
| Visual direction, marketing pages only | design-taste-frontend (not for dashboards or multi-step flows) |
| System, typography, layout, color, critique, audit, polish, distill | impeccable (`document`, `extract`, `typeset`, `layout`, `colorize`, `critique`, `audit`, `polish`, `distill`); typeset/layout/colorize only inside the direction already set in DESIGN.md |
| Motion and interaction details | emil-design-eng, animate; only after direction is set |
| Any user-facing copy | humanizer |
| Figma work | figma-use first (mandatory before use_figma), then figma-generate-design, figma-generate-library, figma-code-connect, figma-create-new-file, figma-use-figjam |
| Independent critique | design-critic agent |
| Implementation | frontend-ux-ui agent |

The frontend-ux-ui agent remains the entry point for implementation work. When it receives new or directional work (new product, new surface, redesign), it stops and returns to the caller recommending this skill, which runs in the main conversation.

## Anti-convergence rules

- No UI before Frame and UX when risk is above trivial.
- A territory is invalid if another territory reaches it by changing only color, typeface, radius, shadow or ornament.
- The model never picks the winner. Present strengths per dimension and compatible combinations, then stop for the user.
- Anti-slop means asking "what is the intent of this choice?", not applying a new preset or ban list.
- References widen the solution space; they are never templates.
- Pass DESIGN.md or the chosen territory to the direction skill as the pinned brief. When a routed skill's ban list or default conflicts with the chosen territory, the territory wins; note it in DESIGN.md.

## Artifacts

Create a file only when there is real knowledge to record. Canonical knowledge lives in docs, code, tests and DDRs.

| File | Holds |
|---|---|
| PRODUCT.md | Problem, users, tasks, constraints, success criteria |
| UX.md or FLOWS.md | IA, flows, representation choices |
| REFERENCES.md | Output of reference-research |
| DESIGN.md | Direction and system contract |
| VALIDATION.md | Findings and test results with status |
| docs/ddr/DDR-NNN-slug.md | Decisions worth revisiting; template in [references/ddr-template.md](references/ddr-template.md) |

Tell the user before creating any of these files.

## Human checkpoints

Stop and ask the user when:
- the depth plan is more than light (G0);
- success criteria or a business rule is ambiguous;
- territories are ready for a decision (G3);
- a design-system choice brings a new dependency or replaces the current library;
- validation finds a severity 3-4 issue whose fix changes scope or flow;
- a redesign would drop existing content, features or brand elements;
- a Figma action would create files in a team or consume limited MCP calls.
