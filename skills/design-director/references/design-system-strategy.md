# Design-system strategy

Pick a library only after the visual language and the behavioral requirements are defined. Otherwise the library becomes the design.

## Options

| Option | Fits when | Watch out for |
|---|---|---|
| Existing design system (company or public, e.g. Material, Carbon) | Identity is already set or not a goal; team needs speed and proven a11y | Fighting it to get a different identity costs more than building |
| Visual component library (styled out of the box) | Internal tools, prototypes, low identity needs | Every product looks the same; theming limits |
| Headless primitives (Radix, Base UI, React Aria) | Custom identity with solid behavior and a11y | You still own all visuals, states and docs |
| Fully custom | Unusual interaction model; mature team | Accessibility and behavior bugs; high maintenance |
| Hybrid | Existing base plus a few custom areas | Two visual languages leaking into each other |
| Own foundations + external primitives | Most custom-identity products | Needs discipline in tokens and naming |
| Domain layer over a base | Products with recurring domain objects | Domain components drifting from the base |

Decision criteria: accessibility and behavior quality (focus, keyboard, ARIA), identity needs, theming and token support, bundle size, maintenance and upgrade path, framework fit, and whether it has the components the flows actually require.

## shadcn/ui

It is code copied into the project that you own and must adapt; it is not a design system by itself. Since July 2026, `shadcn init` defaults to Base UI primitives; Radix is still supported with `-b radix`, and React Aria with `-b aria` (checked in `shadcn init --help`, v4.21.0, 2026-09-27). Do not migrate an existing app just to switch primitives.

## Layers

1. Foundations: tokens for color, type, space, radius, elevation, motion.
2. Primitives: behavior-only building blocks (popover, dialog, listbox).
3. Components: Button, Input, Select, Table, Dialog with states and variants.
4. Patterns: forms with validation, filtering, empty states, bulk actions.
5. Domain components: ContractStatus, PriceHistory, the objects that make this product this product.

Button/Input/Card/Table/Dialog is not a finished design system. A system also defines behavior, keyboard interaction, states, anatomy, content rules, motion and responsive behavior.

## What a good DESIGN.md contains

Written before the build as a contract, updated after it.

- Design thesis: one paragraph on what this product should feel like and why.
- Experience principles: 3-5 rules that settle disagreements.
- Information hierarchy: what is always primary, secondary, on demand.
- Density strategy: where dense, where airy, and why.
- Navigation model.
- Visual grammar: the recurring structural rules.
- Typography: roles, scale, and the reasoning.
- Color semantics: what each color means (status, action, emphasis), not just values.
- Shape: radius, borders, elevation and what they signal.
- Spatial system.
- Motion: when things move and what motion communicates.
- Interaction principles: feedback, confirmation, undo, destructive actions.
- Imagery and iconography.
- Data visualization rules, if any.
- Responsive behavior: what changes, what never changes.
- Accessibility contract: WCAG 2.2 AA targets and the checks that prove them.
- Anti-patterns: what this product must not do.
- Signature elements.
- Rationale: why the main choices were made, with links to DDRs.

A DESIGN.md that says "primary blue, radius 8, use shadcn" is a settings dump, not a design contract.
