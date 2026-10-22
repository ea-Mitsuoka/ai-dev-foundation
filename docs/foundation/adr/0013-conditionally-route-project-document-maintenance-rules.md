---
id: adr-0013
title: ADR-0013 — Conditionally route project-document maintenance rules
status: accepted
updated: 2026-07-29
---

# ADR-0013: Conditionally route project-document maintenance rules

| Field | Value |
| -- | -- |
| Status | accepted |
| Date | 2026-07-29 |
| Deciders | repository owner (approved 2026-07-29) |
| Author | Codex (AI agent) |
| Supersedes / Superseded by | Refines ADR-0010, ADR-0011, and ADR-0012 |

## Context

The `requirements` and `documentation` task routes read `.ai/documentation.md`
completely. That authority currently contains DOC-012 through DOC-014: development
handoff, roadmap review, and root README ownership. Those three sections contain 527
whitespace-delimited words on 2026-07-29 and remain mandatory even when a task touches
none of those concerns. The current `requirements` route contains 5,562 words.

ADR-0010 and ADR-0011 require the three rules to remain complete and authoritative.
ADR-0012 permits bounded discovery but prohibits summaries that replace normative
sources or budgets that justify skipping relevant rules. Any reduction must therefore
preserve the existing rule text, expose deterministic triggers, load the complete
authority when a trigger matches, and broaden discovery under uncertainty.

The implementation must synchronize through the existing Template Sync boundary.
`.ai/documentation.md`, new `.ai/` authorities, skills, validation scripts, tests, and
`docs/foundation/**` are synchronized. Protected descendant entry files such as
`CLAUDE.md` are not required for this change.

## Options considered

### Option 1: Keep all documentation rules in one authority

Continue loading DOC-012 through DOC-014 for every requirements and documentation task.
This has no migration cost and cannot miss a conditional rule, but every unrelated task
pays the 527-word input cost and the file continues to mix general writing rules with
project-maintenance operations.

### Option 2: Shorten or remove the conditional rules

Replace the three sections with compact summaries or delete their operational detail.
This would reduce context with little routing work, but it would weaken accepted
ADR-0010 and ADR-0011 behavior and create a second, lossy description of the rules.

### Option 3: Move all three rules to one conditional authority

Move DOC-012 through DOC-014 unchanged to `.ai/project-document-maintenance.md`.
Keep explicit trigger links in `.ai/documentation.md` and its update matrix. Require
documentation tasks to read the conditional authority completely when work reads or
changes a development handoff, roadmap, root README, onboarding documentation, or
inheritance configuration.

This removes the three sections from unrelated requirements and documentation routes
while adding one authority, one inventory entry, and one validation boundary. A task
matching any trigger loads all three rules, so the design favors simple reliable routing
over the smallest possible conditional context.

### Option 4: Use one conditional authority per concern

Move handoff, roadmap, and README ownership into three separate rule files. This gives
the narrowest matching context, but adds three authorities, three inventory entries,
more routing branches, and more regression cases. The additional precision is small
because each file is already limited to one short rule section.

## Decision

Adopt Option 3.

DOC-012 through DOC-014 MUST move without semantic edits to
`.ai/project-document-maintenance.md`, which remains an authority-4 source.
`.ai/documentation.md` MUST retain an explicit conditional-routing table that names
every trigger and links to the new authority. The documentation skill MUST require a
complete read when any trigger matches and the broader fallback when relevance is
uncertain. Requirements tasks MUST NOT load the conditional authority unless their
actual scope matches a trigger.

Local validation MUST fail when the conditional authority or routing link is missing and
MUST pin all three rule IDs. It MUST measure the resulting declared routes without
counting conditional context in unrelated tasks. The implementation records actual
before-and-after measurements; it MUST NOT claim the full 527-word theoretical maximum
because routing text and the new inventory entry add context.

## Consequences

**Positive:** unrelated requirements and documentation tasks stop loading three complete
maintenance rules; accepted rule text and IDs remain intact; one explicit routing
boundary reduces discovery ambiguity; and synchronized files propagate without editing
protected descendant entry documents.

**Negative:** agents must follow one additional conditional link; a task touching only
one concern still loads all three rules; the baseline inventory gains one row; and the
validator gains a conditionally routed authority contract.

**Migration and rollback:** first add generic conditional-route validation and fixture
tests without changing the active authority. Then atomically move DOC-012 through
DOC-014, add the trigger link and inventory entry, enable the repository contract, and
record actual measurements. Every commit remains green and no commit contains two
normative copies. Rollback restores the three sections to `.ai/documentation.md`,
removes the conditional file and repository contract, and restores the previous
measurements.

**Follow-ups:** after approval, implement the move in a separate PR; update
`.ai/README.md`, `.skills/documentation.skill.md`, the context validator and tests, and
`docs/foundation/guides/ai-context.md`; then propagate the accepted implementation
through reviewed Template Sync PRs.
