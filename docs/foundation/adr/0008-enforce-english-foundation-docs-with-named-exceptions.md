---
id: adr-0008
title: ADR-0008 — Enforce English foundation docs with two named Japanese exceptions
status: accepted
updated: 2026-07-22
---

# ADR-0008: Enforce English foundation docs with two named Japanese exceptions

| Field | Value |
| -- | -- |
| Status | accepted |
| Date | 2026-07-22 |
| Deciders | repository owner |
| Author | Codex (AI agent) |
| Supersedes / Superseded by | Narrows the localized-sibling permission in ADR-0002; clarifies ADR-0005 |

## Context

ADR-0002 permits localized siblings for human-facing documents. ADR-0005 later requires
foundation-owned documentation to remain English while project-owned documents are
written in Japanese after template instantiation. The binding rule in DOC-001 follows
ADR-0005, but `docs/foundation/guides/` intentionally contains two Japanese guides:

- `usage.ja.md`
- `ai-instruction-files.ja.md`

The repository owner approved both files as human-facing exceptions on 2026-07-22.
However, the exceptions are not named in a binding decision or deterministic check.
An agent can therefore interpret them as violations and delete them, or treat them as a
precedent for adding more localized foundation documents. Either outcome weakens the
ownership and language boundary that `docs/foundation/` provides to downstream repos.

The decision must preserve the two approved guides, keep normative foundation content
English, avoid an open-ended bilingual maintenance obligation, and leave Japanese
project documentation under `docs/` unchanged.

## Options considered

### Option 1: Do nothing

Keep the general English rule and the two undocumented exceptions. This has no migration
cost, but agents must infer intent from filenames and can make opposite decisions.

### Option 2: Remove every Japanese foundation document

Make `docs/foundation/` mechanically English-only and provide Japanese explanations only
on demand. This gives the smallest policy surface, but removes two guides that the
repository owner explicitly requires. Rejected.

### Option 3: Allow exactly two named Japanese human-facing exceptions

Keep English as the default and allow only the two existing `.ja.md` guides. Name them in
the binding rule and enforce the allowlist in CI. This preserves the approved human
guidance without permitting additional translations by analogy.

### Option 4: Allow localized siblings for any human-facing foundation guide

Continue the broad ADR-0002 permission. This improves language accessibility but creates
an unbounded translation surface and contradiction risk across every downstream repo.

## Decision

Adopt Option 3. Every document under `docs/foundation/` MUST be written in English except
for these two repository-owner-approved, human-facing files:

1. `docs/foundation/guides/usage.ja.md`
2. `docs/foundation/guides/ai-instruction-files.ja.md`

The exceptions MUST remain descriptive. They MUST link to the authoritative English
rules or sources and MUST NOT establish or extend normative behavior. When an exception
conflicts with an English source, the English source wins. No other Japanese or localized
foundation document may be added without a superseding ADR.

Project-owned documents in instantiated repositories remain Japanese under the direct
`docs/` namespace according to ADR-0005. This decision does not change their language or
placement. Historical Japanese quotations inside immutable ADR-0002 are evidence within
an English decision record, not additional Japanese-language documents, and remain
unchanged.

CI MUST enforce the exact `.ja.md` allowlist. Human and AI review continue to enforce the
language of ordinary English-named Markdown because filename checks cannot reliably
classify prose language.

## Consequences

**Positive:** the default language and both exceptions are unambiguous; agents cannot
delete approved guides as accidental violations; new localized siblings fail CI; and
downstream project documentation keeps its Japanese authoring policy.

**Negative:** two descriptive Japanese documents still require maintenance against their
English authorities; filename validation cannot prove that every sentence in other files
is English; and any third exception requires a new ADR.

**Migration and rollback:** migration is additive: record the decision, name the
exceptions in DOC-001 and the foundation guide index, then add an allowlist regression
test. No document moves or deletions are required. Rollback requires a superseding ADR
that either removes the exceptions or reopens the general localized-sibling policy.

**Follow-ups:** update `.ai/documentation.md`, `docs/foundation/README.md`, and
`docs/foundation/guides/README.md`; add the two-path allowlist to `make doctor`; document
the ordered direct-parent propagation runbook; and distribute the accepted change in
reviewed PRs without auto-merge.
