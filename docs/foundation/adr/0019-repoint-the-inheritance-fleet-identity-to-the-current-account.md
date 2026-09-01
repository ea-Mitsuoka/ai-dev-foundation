---
id: adr-0019
title: ADR-0019 — Repoint the inheritance fleet identity to the current account
status: accepted
updated: 2026-09-01
---

# ADR-0019: Repoint the inheritance fleet identity to the current account

| Field | Value |
|-------|-------|
| Status | accepted |
| Date | 2026-09-01 |
| Deciders | repository owner |
| Author | Claude Code (AI agent) |
| Supersedes / Superseded by | Extends ADR-0004, ADR-0011, ADR-0014 |

## Context

The maintained repositories of this fleet now live under the `ea-Mitsuoka` GitHub
account. Their inheritance metadata still names the former `Yukihide-Mitsuoka` account.

`ea-Mitsuoka/ai-dev-foundation` (repository id 1352737764) and
`Yukihide-Mitsuoka/ai-dev-foundation` (repository id 1287251411) are distinct
repositories owned by distinct accounts. GitHub rename redirection therefore does not
apply: an owner-qualified reference to the former account resolves to a separate
repository whose contents diverge from this one over time.

Two consequences are already observable in this repository on `main`:

- `make doctor` fails. `scripts/readme_ownership.py` compares the ADR-0011 ownership
  marker against `remote.origin.url` and reports that `README.md` belongs to
  `Yukihide-Mitsuoka/ai-dev-foundation`, not `ea-Mitsuoka/ai-dev-foundation`.
- Every canonical-foundation-root check is skipped. `scripts/template-check.sh`
  identifies the root by matching the origin URL against four hard-coded
  `Yukihide-Mitsuoka/ai-dev-foundation` spellings. With that match failing, the ADR-0006
  documentation-namespace ban, the Makefile placeholder allowance, and the ADR-0012
  context-budget ceiling all degrade to reported-only mode. Before this change
  `scripts/context_budget.py` printed `mode=reported`; the ceiling was measured but not
  enforced.

Descendants are affected the same way. Each child names its direct parent in
`.github/inheritance/manifest.json`, `.github/inheritance/lock.json`,
`.github/inheritance/agent-profile.json`, and its Template Sync workflow. While those
name the former account, scheduled synchronization pulls from a repository the owner no
longer maintains.

The fleet also contains repositories that did not move. `Yukihide-Mitsuoka/repchat` and
retired `Yukihide-Mitsuoka/chat-chart` are not present under `ea-Mitsuoka`.

## Options considered

### Option 1: Do nothing

Leave every owner-qualified reference pointing at the former account. This requires no
change, and existing children keep synchronizing from a repository that still exists.

It leaves `make doctor` failing in the canonical repository, leaves the
foundation-root-only invariants unenforced, and makes every child inherit from a
repository the owner no longer updates. The divergence grows silently, because a stale
parent produces no error — only an absence of incoming changes.

### Option 2: Recreate the former account's repositories as forks or mirrors

Keep the recorded identity and satisfy it by maintaining `Yukihide-Mitsuoka` copies that
track `ea-Mitsuoka`. This preserves every existing reference unchanged.

It requires continuous mirroring across two accounts, doubles the release and governance
surface, and leaves the origin-based root detection ambiguous: two repositories would
both claim to be the canonical foundation.

### Option 3: Repoint the recorded identity to the current account

Rewrite owner-qualified references that describe the *current* inheritance graph so they
name `ea-Mitsuoka`: the ADR-0011 README marker, the repository-facts overlay, the agent
profile, the canonical-root detection, the ADR-0015 bootstrap export, the fleet
configuration, the parent-selection table in the usage guides, and the regression tests
that pin those values.

Leave references that record *history* unchanged, because they identify artifacts that
genuinely live in the former account: `CHANGELOG.md` entries, existing
`.ai/decision-log.md` rows, and accepted ADR bodies. The ADR index already forbids
editing an accepted ADR.

Leave repositories that did not move unchanged, so the fleet configuration continues to
describe reality rather than an intended end state.

## Decision

Adopt Option 3.

An owner-qualified reference that describes the current inheritance graph MUST name the
account that currently owns the repository. This covers the ADR-0011 README ownership
marker, the repository-facts overlay, `.github/inheritance/` metadata, the
canonical-foundation-root detection in `scripts/template-check.sh`, the ADR-0015
bootstrap export, `docs/foundation/inheritance-fleet.json`, the parent-selection table in
`docs/foundation/guides/usage.md` and `usage.ja.md`, and every regression test that pins
those values.

An owner-qualified reference that records history MUST NOT be rewritten. Issue links, PR
links, commit links, released `CHANGELOG.md` entries, existing decision-log rows, and
accepted ADR bodies keep the account that hosted them. Owner-qualified examples inside
ADR-0011 and other accepted ADRs therefore continue to read `Yukihide-Mitsuoka`; they
illustrate decisions taken under the former account, and the normative rule they state
("the marker MUST match the current GitHub repository") is account-agnostic and
unchanged.

A fleet entry MUST name the account that owns that repository today.
`Yukihide-Mitsuoka/repchat` and retired `Yukihide-Mitsuoka/chat-chart` therefore keep
their current owner and their current parent until they are migrated.

Descendants apply the same rule in their own reviewed pull requests, parent first:
`ai-dev-foundation`, then `terraform-gcp-template` and `nextjs-saas-template`, then
`secure-ga4-bq-template`. A child's `.github/inheritance/lock.json` commit is unchanged
by the repoint, because the accepted parent commit exists in the repository under the new
account.

## Consequences

**Positive:**

- `make doctor` passes in the canonical repository, and the foundation-root-only
  invariants run again. `scripts/context_budget.py` reports `mode=enforced` instead of
  `mode=reported`.
- Scheduled Template Sync in every descendant reads the repository the owner maintains.
- The ADR-0015 bootstrap export hands new children the correct parent, so a newly
  created child does not reproduce the stale identity.
- One rule — current graph is rewritten, history is not — decides every remaining
  occurrence without a case-by-case judgment.

**Negative:**

- Documentation now contains both spellings. A reader must distinguish a current
  reference from a historical link, and accepted ADRs keep owner-qualified examples that
  no longer match the live repositories.
- The fleet configuration temporarily describes two roots, because `repchat` still
  inherits from the former account's foundation.
- Any external consumer that pinned `Yukihide-Mitsuoka/ai-dev-foundation` keeps
  receiving the former account's content, and this change cannot detect that.
- Rollback means reverting the same set of files in each repository. It is mechanical,
  but it spans four repositories and must again be applied parent first.

**Follow-ups:**

- Migrate or retire `Yukihide-Mitsuoka/repchat`, then update its fleet entry.
- Re-evaluate the `secure-ai-controls` `paused` lifecycle reason, which states that
  owner-level company account access is unavailable. That statement predates the move to
  the company account.
- Verify separately that the `terraform-gcp-modules` and `gcp-cicd-workflows` tags pinned
  by descendants exist under the new account before repointing those sources. They are
  versioned artifact references, not inheritance edges, and are out of scope here.
