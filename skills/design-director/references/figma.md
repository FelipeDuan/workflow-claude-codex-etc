# Working in Figma

Applies when the official Figma MCP server or plugin is available.

## Before anything

- Load the figma-use skill before any use_figma call. It is mandatory.
- Run whoami to check the plan and seat. MCP rate limits depend on the seat: Starter plans and View or Collab seats get only about 6 tool calls per month. Create working files in a team where the user has a Full or Dev seat. If that is not available, tell the user before spending calls.
- Creating a file (figma-create-new-file) or writing into a shared team file is a human checkpoint.

## Working style

- Incremental: inspect (get_metadata, get_screenshot, get_variable_defs) before editing, change one area, check the screenshot, continue.
- Never rebuild what exists. Search the file and libraries (search_design_system, get_libraries) first.
- Use real content, not lorem ipsum, in exploration and flows.

## Suggested page structure

A starting point to adapt to the project size, not to impose:

Cover/Readme · Foundations · Variables/Tokens · Components · Patterns · Exploration · Flows · Desktop · Mobile · Prototype · Archive

A personal landing page may need only Exploration, Desktop, Mobile.

## Structure inside the file

- Variables in collections with modes (light/dark, density, brand). Semantic tokens (`color/text/primary`, `color/status/danger`) reference primitive ones (`blue/600`). Components use semantic tokens only.
- Styles for text and effects where variables do not cover them.
- Components with variants and component properties (boolean, text, instance swap) instead of duplicated frames.
- Auto layout everywhere content can change; constraints for responsive frames.
- Naming: `Component/Variant`, slash-grouped, matching code names where they exist.
- Prototype interactions for the main flows, including states (loading, error, empty, success), not only the happy path.

## Figma beyond hi-fi

- Exploration boards: territories side by side with the same content (see territories.md).
- Flows: user flows and IA as diagrams (figma-use-figjam or generate_diagram for FigJam).
- Screens: figma-generate-design to translate an existing page or layout.
- Libraries: figma-generate-library to build a design system in Figma from code.

## Handoff

- Map Figma components to code components with figma-code-connect so implementers get the real component, not a guess.
- Implementers read with get_design_context before coding.
- Keep DESIGN.md as the source of intent; Figma holds the visuals and specs.
