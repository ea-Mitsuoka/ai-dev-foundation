---
id: adr-0023
title: ADR-0023 — Integrate test-first slices and inline domain-term capture
status: accepted
updated: 2026-09-13
---

# ADR-0023: Integrate test-first slices and inline domain-term capture

| Field | Value |
| -- | -- |
| Status | accepted |
| Date | 2026-09-13 |
| Deciders | repository owner (approved 2026-09-13) |
| Author | Claude Fable 5.1 (AI agent) |
| Supersedes / Superseded by | Extends TST-002, TST-010, MNT-001, COD-021, COD-052, GR-022, and the requirements and architecture skills; supersedes none |

## Context

The foundation was compared against three externally published agent skills,
`grill-with-docs`, `implement`, and `tdd` from the `mattpocock/skills` repository
(read on 2026-09-13 as untrusted content under GR-033). The earlier `grill-me` interview
is already integrated as the fork-by-fork step of `.skills/requirements.skill.md`.

The comparison found four behaviors the foundation does not yet state, and two it
already states more strictly:

- Feature work requires tests in the same commit (GR-021, TST-002) but does not fix the
  order. Only the bug-fix skill requires a failing test first. An agent may write a batch
  of tests after a batch of code, which verifies the shape of the code rather than one
  behavior at a time.
- No rule names the tautological test: an assertion whose expected value is computed the
  same way the implementation computes it, so the test passes by construction. The
  existing "verify each test can fail" step catches it only indirectly.
- ARC-005 defines the seam and MNT-001 lists design-checkpoint fields, but no step records
  which seams the tests will observe before code exists.
- `docs/glossary.md` has an *Avoid* column and a resolved-ambiguities log, and DOC-030
  requires new domain terms in the same PR, but no interview step writes a term at the
  moment it is confirmed or challenges new wording against the existing glossary.
- The external `implement` procedure commits to the current branch without an issue,
  branch, PR, or documentation step. `.skills/feature.skill.md` already covers the same
  work under WF-001, WF-010, WF-030, and DOC-030.
- The external ADR filter (hard to reverse, surprising without context, real trade-off)
  is a weaker trigger than GR-022, which requires an ADR for every architectural scope.

Constraints: the change propagates to every descendant through Template Sync, so it must
not add a new always-loaded file, a new skill or manifest path, or a second glossary
format. ADR-0012 bounds the per-route context budget. The published external skills
change frequently and delegate between one-line files that their own documentation
reports as failing to load; the foundation cannot depend on them.

## Options considered

### Option 1: Do nothing

Keeps the routes unchanged. Agents continue to decide test order, expected-value source,
and glossary timing case by case, and the four gaps above stay open.

### Option 2: Import the external skills as vendor files

Add `tdd`, `grill-with-docs`, and `implement` under `.skills/` or `.claude/skills/`.
This duplicates TST, ARC, COD, and WF rules in a second voice (DOC-001), adds a
`CONTEXT.md` document type beside `docs/glossary.md` (DOC-010), weakens the branch and
PR obligations of feature work, and ties the foundation to an external release cadence.

### Option 3: Fold the missing behaviors into existing rules and skills

State each missing behavior once, in the rule file or skill that already owns the
subject, with explicit applicability conditions, and pin the text with a contract test.
Add no file to any route except the glossary rows the change itself needs.

### Option 4: Add one new foundation skill for test-driven work

Discoverable, but optional in the feature and bug-fix routes, and it duplicates the
testing policy the routes already load. ADR-0017 rejected the same shape for
maintainability.

## Decision

Adopt Option 3. The following rules are added or extended; wording lives only in the
named files.

1. **Test-first slices (TST-004, new).** For new behavior, the agent MUST write one
   failing test for one behavior, then the minimal implementation that passes it, and
   repeat one slice at a time. The rule applies when the behavior has a concrete expected
   outcome, a stable public boundary to observe it at, and an expected value with a source
   independent of the implementation (specification, known-good literal, external
   standard, or invariant). It does not apply to documentation, mechanical configuration,
   generated code, investigation, or throwaway prototypes.
2. **Independent expected values (TST-010, extended).** An assertion MUST NOT derive its
   expected value by the same computation as the implementation. Such a test is
   tautological and does not satisfy GR-021.
3. **Seams recorded at the design checkpoint (MNT-001 via the feature skill).** The
   design checkpoint names the seams the tests will observe. The agent asks the human only
   when a new public API shape makes the seam choice diverge materially; existing public
   boundaries are the agent's call.
4. **Post-green refactor bounded to the slice.** After a slice is green, the agent MAY
   restructure the code it added in that slice while tests stay green. Restructuring
   existing code remains a separate `refactor` change under COD-021 and MNT-003.
5. **Inline domain-term capture.** In the requirements and architecture skills, when a
   fork is confirmed and it fixes the meaning of a term, the agent records the term in
   `docs/glossary.md` in the same session rather than at PR time, and challenges new
   wording that conflicts with an existing glossary entry. Only confirmed meanings are
   written; proposals stay in the conversation. `CONTEXT.md` is not introduced.
6. **ADR routing for non-architectural decisions.** A decision outside GR-022 scope
   SHOULD become an ADR when it is hard to reverse, surprising without context, and the
   result of a real trade-off; otherwise it is a decision-log entry (COD-052). This
   routing never waives GR-022.
7. **No `implement` skill.** `.skills/feature.skill.md` remains the single procedure for
   building decided work.

The review checklist gains the matching REV-TST items. A contract test pins the rule
text and the cross-references so descendants receive the complete change through
Template Sync.

## Consequences

**Positive:**

- Feature tests are written against one behavior at a time, so a passing suite means the
  behaviors were observed, not that the code shape was mirrored.
- Tautological tests are named and rejected at review with a stable rule ID.
- Seams are chosen before code exists and recorded where a reviewer can find them,
  without a mandatory human confirmation on every task.
- Domain terms enter the glossary when the meaning is confirmed, so later design and
  PR text reuse one word.
- No new always-loaded file, skill, or document type; the inherited route set is unchanged.

**Negative:**

- The applicability conditions of TST-004 require judgment and are enforced by review,
  not by a linter.
- The requirements, architecture, feature, and test skills and the testing policy grow by
  a few lines each within the ADR-0012 budgets.
- Recording a term mid-session adds a small write to `docs/glossary.md` in the same PR
  that DOC-030 already requires; a term confirmed and later reversed needs a
  resolved-ambiguities entry.

Migration is prospective: the rules apply to new work. Rollback removes the added rule
text and checklist items through a superseding ADR.

**Follow-ups:** Track implementation and acceptance in
[Issue #38](https://github.com/ea-Mitsuoka/ai-dev-foundation/issues/38).
