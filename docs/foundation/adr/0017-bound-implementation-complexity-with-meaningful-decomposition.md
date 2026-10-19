---
id: adr-0017
title: ADR-0017 — Bound implementation complexity with meaningful decomposition
status: accepted
updated: 2026-08-29
---

# ADR-0017: Bound implementation complexity with meaningful decomposition

| Field | Value |
| -- | -- |
| Status | accepted |
| Date | 2026-08-29 |
| Deciders | repository owner |
| Author | Codex (AI agent) |
| Supersedes / Superseded by | Extends ARC-005, COD-003, COD-020, COD-051, and GR-020; supersedes none |

## Context

The foundation already requires inward dependencies, deep modules, small functions,
non-speculative abstractions, and bounded pull requests. These rules do not yet give an
agent one coherent checkpoint when a handwritten component grows large. An agent may
keep adding behavior to one file because each function is individually acceptable, or
split the file into arbitrary pass-through wrappers merely to reduce a line count.

Line count is an imperfect proxy: a cohesive parser can be larger than a poorly coupled
set of tiny files, while generated and declarative files can be large without increasing
reasoning complexity. The policy must preserve quality without rewarding cosmetic
splitting or requiring a new skill for ordinary feature work.

## Options considered

### Option 1: Enforce a small hard file-size limit

This is easy to automate, but rejects cohesive code and encourages arbitrary splitting.
It mistakes the measurement for the design objective.

### Option 2: Keep qualitative guidance only

This preserves judgment but provides no reliable pause point. Agents can rationalize
continued growth until safe decomposition is expensive.

### Option 3: Use qualitative design rules with two advisory checkpoints

Define maintainability by local reasoning and safe change. Treat roughly 400 handwritten
logical lines as a required decomposition review, and prohibit unreviewed growth beyond
roughly 800 lines unless a meaningful decomposition or documented human-approved
exception applies. Exempt content for which line count is not a useful complexity proxy
and prohibit superficial splitting.

### Option 4: Add a standalone clean-code skill

This makes the guidance discoverable but optional in the feature and bug-fix paths. It
also duplicates architecture, coding, refactoring, and review responsibilities.

## Decision

Adopt Option 3 as a synchronized Foundation maintainability contract and integrate it
into the existing task routing and skill system. Do not add a standalone skill or make
child-owned architecture and coding overlays synchronized.

Maintainable code is correct, locally understandable, safe to change, testable and
deletable through stable boundaries, and no more complex than the current requirement
needs. Before implementation, the agent records the component responsibility, inputs,
outputs, invariants, failure modes, owning layer, dependencies, smallest viable design,
and expected size or decomposition.

Responsibility, coupling, dependency direction, branching, hidden side effects, and test
surface remain the primary design evidence. A handwritten source component approaching
400 logical lines, or a change expected to add that much behavior, triggers a
decomposition review rather than an automatic split. Continued growth past roughly 800
logical lines is prohibited without meaningful decomposition or a human-approved
exception documented in the issue or ADR and PR.

Generated code, declarative schemas or configuration, migrations, fixtures, and static
lookup data are exempt when their size does not conceal behavior. An exception does not
waive correctness, testing, dependency, or review rules. Splitting solely to lower a line
count, introducing pass-through wrappers, or scattering one responsibility across files
does not satisfy this decision.

The inherited context map routes feature, bug-fix, refactor, architecture, and review
tasks through the canonical maintainability contract. Local feature, refactor, and
review procedures reference its stable MNT rule IDs. Contract tests preserve routing,
references, and the inherited guardrail body so descendants receive the complete policy
through existing Template Sync without overwriting their protected overlays.

## Consequences

**Positive:**

- Agents receive an early, consistent signal before a component becomes difficult to
  reason about.
- Design judgment remains based on cohesion and boundaries rather than file length alone.
- Cosmetic file splitting and speculative abstraction are explicitly rejected.
- Existing task routing and inheritance remain unchanged.

**Negative:**

- The checkpoints require judgment and cannot be fully enforced by a generic linter.
- Some cohesive large components require a documented review exception.
- Existing large files are not automatically refactored; they are reviewed when changed.

Migration is prospective. Apply the checkpoint to new work and to the changed area of an
existing component. Do not perform fleet-wide size-only refactors. Rollback removes the
checkpoints and their procedure references through a superseding ADR; it must not restore
cosmetic splitting as an accepted practice.

**Follow-up:** Track implementation and verification in
[Issue #191](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/191).
