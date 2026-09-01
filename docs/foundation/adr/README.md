---
id: adr-index
title: Architecture Decision Records
---

# Foundation Architecture Decision Records (ADR)

Immutable records of decisions owned by `ai-dev-foundation` and synchronized to
downstream repositories. Project-specific decisions belong in `docs/adr/`. Both use the
process in `.skills/architecture.skill.md`.

## Rules

- Numbered sequentially: `NNNN-kebab-case-title.md`. Copy the
  [foundation ADR template](../templates/adr.md).
- Status flow: `proposed → accepted | rejected`; later `deprecated` or
  `superseded by ADR-NNNN`. **Accepted ADRs are never edited** — supersede them.
- One decision per ADR. Keep it under ~2 pages.
- The ADR PR is approved by a human before implementation starts (GR-022).
- Every ADR gets a line in [.ai/decision-log.md](../../../.ai/decision-log.md).

## Index

Use the Scope column for bounded discovery. Read every matching ADR completely and
broaden the search under ADR-0012 when relevance is uncertain.

| # | Title | Scope | Status | Date |
|---|-------|-------|--------|------|
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions | ADR process, governance | accepted | 2026-07-02 |
| [0002](0002-ai-facing-docs-in-english.md) | AI-facing docs are written in English | AI context, documentation language | accepted | 2026-07-02 |
| [0003](0003-reconcile-github-governance-from-inherited-policy.md) | Reconcile GitHub governance from inherited policy | GitHub governance, repository policy | accepted | 2026-07-15 |
| [0004](0004-harden-multi-level-template-inheritance.md) | Harden multi-level template inheritance | GitHub governance, template inheritance | accepted | 2026-07-16 |
| [0005](0005-separate-foundation-and-project-document-languages.md) | Separate foundation and project document languages | documentation language, template instantiation | accepted | 2026-07-18 |
| [0006](0006-reserve-a-foundation-documentation-namespace.md) | Reserve a foundation documentation namespace | documentation ownership, Template Sync | accepted | 2026-07-18 |
| [0007](0007-constrain-transitional-template-sync.md) | Constrain transitional Template Sync | Template Sync, template inheritance | accepted | 2026-07-22 |
| [0008](0008-enforce-english-foundation-docs-with-named-exceptions.md) | Enforce English foundation docs with two named Japanese exceptions | documentation language, foundation docs | accepted | 2026-07-22 |
| [0009](0009-place-project-document-singletons-and-collections.md) | Place project document singletons and collections by scope | documentation placement | accepted | 2026-07-26 |
| [0010](0010-separate-roadmap-work-tracking-and-handoff.md) | Separate roadmap, work tracking, and handoff | handoff, roadmap, work tracking | accepted | 2026-07-28 |
| [0011](0011-own-the-root-readme-in-the-current-repository.md) | Own the root README in the current repository | AI context, inheritance, README ownership | accepted | 2026-07-28 |
| [0012](0012-bound-context-acquisition-without-reducing-quality.md) | Bound context acquisition without reducing quality | AI context, task routing, token efficiency | accepted | 2026-07-29 |
| [0013](0013-conditionally-route-project-document-maintenance-rules.md) | Conditionally route project-document maintenance rules | AI context, documentation rules, task routing | accepted | 2026-07-29 |
| [0014](0014-separate-inherited-agent-contracts-from-project-overlays.md) | Separate inherited agent contracts from project overlays | AI context, template inheritance, workflow ownership | accepted | 2026-07-29 |
| [0015](0015-consolidate-inheritance-acceptance-in-one-reviewed-pr.md) | Consolidate inheritance acceptance in one reviewed PR | template inheritance, workflow ownership, review operations | accepted | 2026-08-08 |
| [0016](0016-gate-private-fleet-automation-on-split-credentials.md) | Gate private fleet automation on split credentials | private repositories, template inheritance, fleet audit, credentials | accepted | 2026-08-09 |
| [0017](0017-bound-implementation-complexity-with-meaningful-decomposition.md) | Bound implementation complexity with meaningful decomposition | code quality, maintainability, complexity, AI implementation | accepted | 2026-08-29 |
| [0018](0018-integrate-a-lightweight-inherited-presentation-skill.md) | Integrate a lightweight inherited presentation skill | presentation authoring, AI context, template inheritance | accepted | 2026-08-29 |
| [0019](0019-repoint-the-inheritance-fleet-identity-to-the-current-account.md) | Repoint the inheritance fleet identity to the current account | template inheritance, repository identity, README ownership | accepted | 2026-09-01 |

<!-- Append new ADRs to this table (newest last). -->
