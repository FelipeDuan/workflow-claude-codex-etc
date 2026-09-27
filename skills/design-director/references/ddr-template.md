# Design Decision Records (DDR)

A DDR records a design decision someone will want to question later. Store as `docs/ddr/DDR-NNN-short-slug.md`.

## Deserves a DDR

- Cards vs. rows for a core list
- Modal vs. dedicated page for a key task
- Sidebar navigation vs. command-based navigation
- Custom design system vs. headless primitives vs. an existing library
- Removing a feature or step from a flow

## Does not deserve a DDR

- Radius changed from 8 to 10
- A color token tweak
- Copy edits
Anything cheap to reverse and without consequences for other decisions.

## Template

```
# DDR-NNN: <decision in a few words>

Status: proposed | accepted | superseded by DDR-XXX | revisited
Date:

## Context
## Problem
## Constraints
## Decision
## Alternatives considered
## Evidence
## Trade-offs
## Consequences
## Revisit when
```

## Worked example

```
# DDR-004: Compact rows with expandable detail for employee comparison

Status: accepted

## Context
Managers review 20-60 employees per cycle to decide raises.

## Problem
They need to compare the same 5 attributes across everyone and open details for a few.

## Constraints
Desktop-first use; must work at 1280px; keyboard users; data changes weekly.

## Decision
A table of compact rows, sortable by each attribute, with an expandable detail row.

## Alternatives considered
Cards per employee: good for browsing, but comparing values across 40 cards needs memory and scrolling.
Master-detail: keeps context but hides the comparison columns.

## Evidence
Task walkthrough: comparing 3 attributes across 40 employees took visible back-and-forth in the card prototype. 4 of 5 pilot managers asked to sort by salary band.

## Trade-offs
Less visual warmth; mobile needs a separate list pattern.

## Consequences
Need a table component with sort, sticky header, expandable rows, keyboard support.

## Revisit when
Teams exceed ~150 people, or mobile use becomes significant.
```

The evidence in the example is illustrative. In a real DDR, write only evidence that was actually collected, and say "no evidence yet" when that is the case.
