---
name: feature
description: Implement new functionality end-to-end (requirements → design → code → tests → docs → PR)
triggers: [new feature, add functionality, implement issue, 機能追加, 新機能, 機能開発]
reads: [.ai/workflow.md, .ai/architecture.md, .ai/coding-rules.md, .ai/testing.md]
---

# Skill: Feature Implementation

## Purpose

Deliver a working, tested, documented feature as one reviewable PR (or a small series),
meeting the Definition of Done (WF-090).

## Inputs

- A GitHub issue with acceptance criteria. If none exists, write the acceptance
  criteria first and get them confirmed (escalate if ambiguous — CLAUDE.md §13).
- Target module(s): identify via `src/modules/*/MODULE.md`; read the MODULE.md of every
  module you will touch.
- Green baseline: `make test-unit` passes before you start (TST-030).

## Process

01. Restate the goal and acceptance criteria; list assumptions.
02. Classify impact (ARC-020). Architectural → switch to architecture.skill.md first.
03. Define the design checkpoint (MNT-001): responsibility, inputs, outputs, invariants,
    failure modes, owning layer, dependencies, smallest viable design, and expected size
    or decomposition. If MNT-002 or GR-025 applies, resolve it before adding behavior.
    Name the seams the tests will observe (TST-004); ask the human only when a new public
    API shape makes the seam choice diverge materially.
04. Plan the seam: which layer does each piece belong to? New use case in
    `application/`, domain logic in `domain/`, I/O in `infrastructure/` adapters.
05. Create branch `feat/<issue>-<slug>`.
06. Implement in thin vertical slices: domain → application → interface. Within a slice,
    write one failing test for one behavior, then the minimal code that passes it
    (TST-004); commit per slice with tests in the same commit. After the slice is green,
    restructure only the code the slice added; existing code waits for a separate
    refactor PR (COD-021).
07. Cover error paths and boundaries (TST-002), not just the happy path, with expected
    values from a source independent of the implementation (TST-010).
08. Update docs per the doc-update matrix (DOC-030): MODULE.md, `docs/api/`,
    `.env.example`, glossary.
09. Run `make format && make lint && make test`.
10. Self-review with review.skill.md; then open the PR with the template fully filled.

## Decision criteria

- **Where does logic go?** If it needs I/O → infrastructure. If it orchestrates →
  application. If it's a business rule that must hold everywhere → domain.
- **Feature flag?** Yes if the feature ships incomplete across >1 PR, or is risky to
  roll back. Flag default: off.
- **Split the PR?** If diff will exceed GR-020 limits, split: (1) preparation/refactor
  PR, (2) feature PR. Never mix the two (COD-021).
- **Split the component?** Use MNT-002. File count is not the goal: retain a
  cohesive component with a stated reason, or extract a real responsibility and stable
  test boundary. GR-025 is a stop condition, not permission for cosmetic splitting.
- **New dependency?** Only via COD-040 protocol; prefer stdlib/existing deps.

## Outputs

- PR: code + tests + docs, CI green, template complete.
- Updated MODULE.md if the module contract changed.
- Decision-log entry for non-obvious choices (COD-052).

## Checklist

- [ ] Acceptance criteria demonstrably met (state how each is verified)
- [ ] All new public behavior has tests; error paths covered
- [ ] Where TST-004 applies, each slice went red before green at a seam named in step 3;
  no expected value is recomputed from the implementation (TST-010)
- [ ] Dependency direction respected (ARC-002); no cross-module internal imports
- [ ] Complexity checkpoint resolved without cosmetic splitting (MNT-001/MNT-002/GR-025)
- [ ] Doc-update matrix satisfied (DOC-030)
- [ ] Diff within size limits (GR-020); no unrelated changes
- [ ] `make format`, `make lint`, `make test` all green — output reported verbatim
