# UX and information representation

Choose how information is represented from the task, not from habit or taste.

## Questions before choosing

- Task: what is the user trying to get done here?
- Decision: what decision does this screen support, and what information does it need?
- Frequency: once, occasionally, or all day? Frequent use favors density and shortcuts; rare use favors guidance.
- Mode: comparing items, browsing, searching for a known item, monitoring for change, or entering data?
- Density: how many items and attributes are realistic (use real data sizes, not 3 samples)?
- Temporality: does order in time matter? Is it live?
- Device and context: phone on the move, desktop with keyboard, shared screen?
- Accessibility: does it work with a screen reader, keyboard only, zoom to 400%, without color?

## Representations

| Representation | Good when | Bad when |
|---|---|---|
| Table | Comparing many items across the same attributes; sorting, filtering | Few items, heterogeneous content, narrow screens without a mobile strategy |
| List | Scanning items with one or two key attributes | Items need side-by-side comparison of many fields |
| Cards | Heterogeneous items, visual content, browsing | Comparing values across items; dense operational data |
| Master-detail | Frequent switching between items while keeping context | Detail is short enough to show inline |
| Timeline | Order and duration in time are the point | Time is incidental metadata |
| Tabs | Parallel, independent views of one object | Steps in a sequence, or content users must compare across tabs |
| Wizard | Long, ordered input with dependencies between steps | Expert repeat use; users need to see everything at once |
| Carousel | Rarely; ambient showcase where missing items is acceptable | Anything users must find, read or compare |
| Kanban | Items move through stages and stage is the main attribute | Many stages, many attributes, or no real workflow |
| Calendar | Date and availability drive the decision | Sparse events; list by date is enough |
| Search / command palette | Large known-item spaces, expert users | Users do not know what exists; discovery is the task |
| Chart | Trend, distribution, comparison of magnitudes | Exact values matter more than shape; few data points |
| Inline edit | Frequent small edits to single fields | Edits with validation across fields or big consequences |
| Progressive disclosure | Advanced options most users skip | Information needed for the main decision |

## Simplification checklist

For every screen, step and field:
- Does it need to exist? What breaks if we remove it?
- Can the system infer it (defaults, previous input, context)?
- Can we prevent the error instead of reporting it?
- Can it be disclosed later, only to those who need it?
- Is the order the order of the user's task, or of our data model?

Minimal visuals do not equal simple UX: hiding controls can make a task harder. Dense interfaces can be excellent when users are experts and the representation matches their task.
