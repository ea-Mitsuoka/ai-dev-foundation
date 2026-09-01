---
id: ai-index
title: AI Context Map
authority: 3
read_when: [always]
---

# .ai/ — AI Context Map

This directory is the routed AI rule source. Entry adapters first load the declared
foundation, template, and project profile.

## Authority order (conflict resolution)

Lower numbers win; apply them and report conflicts.

| Authority | Document | Scope |
|-----------|----------|-------|
| 1 | [guardrails.md](guardrails.md) | Absolute prohibitions |
| 2 | [security.md](security.md) | Security policy |
| 3 | Loaded contract / `CLAUDE.md` / `AGENTS.md` / this file | Operating contract |
| 4 | Other `.ai/*.md` | Domain rules |
| 5 | `docs/**` | Informative documentation |

## Rule and file inventory

Cite stable normative rule IDs in commits, PRs, and reviews.

| File | Rule prefix | Content |
|------|-------------|---------|
| [README.md](README.md) | — | Routing |
| [mission.md](mission.md) | — | Purpose and success |
| [guardrails.md](guardrails.md) | GR- | Prohibitions |
| [contracts/foundation/maintainability.md](contracts/foundation/maintainability.md) | MNT- | Maintainable design and complexity |
| [security.md](security.md) | SEC- | Security |
| [architecture.md](architecture.md) | ARC- | Structure and boundaries |
| [coding-rules.md](coding-rules.md) | COD- | Code rules |
| [testing.md](testing.md) | TST- | Test and coverage |
| [release.md](release.md) | REL- | Version and release |
| [documentation.md](documentation.md) | DOC- | Documentation |
| [project-document-maintenance.md](project-document-maintenance.md) | DOC- | Conditional project-doc upkeep |
| [review-checklist.md](review-checklist.md) | REV- | Review checklist |
| [workflow.md](workflow.md) | WF- | Task lifecycle |
| [decision-log.md](decision-log.md) | — | Decision index |

RFC 2119 applies: **MUST / MUST NOT** bind, deviations from **SHOULD / SHOULD NOT** need
justification, and **MAY** is optional.

## Universal AI prose rule

All AI-authored explanatory prose, including code comments and collaboration text, MUST follow
[DOC-002](documentation.md#doc-002-objective-structured-prose): use literal wording and
omit metaphors that do not materially improve technical understanding.

## Context acquisition protocol

Quality takes priority over context reduction ([ADR-0012](../docs/foundation/adr/0012-bound-context-acquisition-without-reducing-quality.md)).
Read every file selected by the baseline or task route completely. Reuse complete,
unchanged active context; reread after compaction or removal.

A route MUST name files, not directories. For variable collections:

1. inspect the index or file list without loading every body;
2. search metadata, decisions, affected paths, symbols, domain terms, and synonyms;
3. read every matching document completely; and
4. follow relevant links and complete supersession chains.

Broaden discovery and reading until uncertainty is resolved for missing or stale
indexes, conflicts, cross-cutting or hard-to-reverse changes, security-sensitive work,
or no expected match. Never use a context budget to skip a relevant source or replace a
normative source with a generated summary.

`read_when: [always-summary, ...]` marks a file whose always-binding core is already
carried by a baseline document; read the full file only on its listed routes.

## Reading protocol by task type

Read only the matching task route.

| Task | Read (in order) | Skill |
|------|-----------------|-------|
| Any task (baseline) | `CLAUDE.md`, guardrails.md, explicit profile inputs, this file, `docs/development-handoff.md` when present | — |
| Requirements definition | mission.md, documentation.md | `.skills/requirements.skill.md` |
| New feature | workflow.md, MNT contract, architecture.md, coding-rules.md, testing.md | `.skills/feature.skill.md` |
| Bug fix | workflow.md, MNT contract, testing.md | `.skills/bugfix.skill.md` |
| Refactoring | MNT contract, architecture.md, coding-rules.md, testing.md | `.skills/refactor.skill.md` |
| Architecture change | MNT contract, architecture.md, foundation ADR index, project ADR index when present, then relevant decisions through bounded discovery | `.skills/architecture.skill.md` |
| Security work | security.md, `SECURITY.md` | `.skills/security.skill.md` |
| Writing tests | testing.md | `.skills/test.skill.md` |
| Documentation | documentation.md, foundation guide index, then the relevant guide through bounded discovery | `.skills/documentation.skill.md` |
| Presentation or slide deck | documentation.md | `.ai/contracts/foundation/skills/presentation/SKILL.md` |
| Code review | MNT contract, review-checklist.md | `.skills/review.skill.md` |
| Release | release.md, security.md | `.skills/release.skill.md` |
