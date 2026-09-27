# Validation

Use the cheapest mechanism that gives reliable evidence, and say what each method can and cannot show.

## Cheapest mechanism first

| Question | Mechanism |
|---|---|
| Text and UI contrast | Contrast math on tokens and computed styles |
| Broken links, missing labels, ARIA errors | Automated test (axe via Playwright, lint) |
| Layout at 320 / 390 / 1440 px, forced states | Playwright screenshots |
| Keyboard order, focus visible and not obscured | Scripted keyboard walk plus human look |
| Usability problems | Heuristic evaluation (design-critic, impeccable critique) |
| Whether real users can complete tasks | Task-based testing with real users |
| Whether the direction is right | Human judgment |

## Heuristic evaluation

Use Nielsen's 10 usability heuristics (https://www.nngroup.com/articles/ten-usability-heuristics/):
1. Visibility of system status
2. Match between the system and the real world
3. User control and freedom
4. Consistency and standards
5. Error prevention
6. Recognition rather than recall
7. Flexibility and efficiency of use
8. Aesthetic and minimalist design
9. Help users recognize, diagnose, and recover from errors
10. Help and documentation

Severity, Nielsen's 0-4 scale:
- 0: not a usability problem
- 1: cosmetic; fix if time allows
- 2: minor; low priority
- 3: major; important to fix, high priority
- 4: catastrophe; must fix before release

Heuristic evaluation is expert inspection. It is not user research and does not tell you what users will do.

impeccable critique/audit report a health score and P0–P3 severities; never relay the score as a design score. Map P0→4, P1→3, P2→2, P3→1 and cite as "impeccable critique/audit" evidence.

## Finding format

```
ID: F-001
Flow/screen:
Heuristic: (number and name, or "Accessibility: WCAG SC x.y.z")
Evidence: what was observed, with screenshot path or steps
Severity: 0-4
Consequence: what happens to the user
Hypotheses / options: possible causes and fixes (not a single prescribed fix)
Status: open | accepted | fixed | won't fix (reason)
```

## Task-based testing

When real users are available, give them realistic tasks and report per task:
- Task success (completed / failed / completed with help)
- Median time on successful tasks
- Errors, split into critical (blocks or causes wrong outcome) and recoverable
- Backtracking (going back, reopening, undoing)
- Assistance required
- SEQ, Single Ease Question: "Overall, how difficult or easy was the task to complete?" on a 7-point scale (https://measuringu.com/seq10/)

Report raw counts with n ("4 of 5 completed"). No composite "UX score". With small n (5-8 users), treat results as problem discovery, not as rates to generalize.

## Accessibility: WCAG 2.2 AA from the start

- Contrast: 4.5:1 for normal text, 3:1 for large text, 3:1 for non-text UI components and meaningful graphics.
- Target size minimum 24×24 CSS px, or enough spacing (SC 2.5.8).
- Focus visible on every interactive element (SC 2.4.7, AA).
- Focus not obscured by sticky headers, banners or overlays (SC 2.4.11).
- Dragging movements have a single-pointer alternative (SC 2.5.7).
- Reflow at 320 CSS px width without two-dimensional scrolling (SC 1.4.10).
- Respect prefers-reduced-motion (good practice; SC 2.3.3 is AAA).

Automate: axe via Playwright, contrast math, target size measurement, reflow screenshots.
Needs manual or qualitative checking: screen reader flow and announcements, meaningful alt text, reading and focus order making sense, error messages being understandable, cognitive load.

An automated scan finds a subset of issues. Never report "WCAG compliant" from a scanner; report what was checked, how, and what remains manual.
