---
id: adr-0015
title: ADR-0015 — Consolidate inheritance acceptance in one reviewed PR
status: accepted
updated: 2026-08-08
---

# ADR-0015: Consolidate inheritance acceptance in one reviewed PR

| Field | Value |
| -- | -- |
| Status | accepted |
| Date | 2026-08-08 |
| Deciders | repository owner |
| Author | Codex (AI agent) |
| Supersedes / Superseded by | Supersedes ADR-0007 only where it requires a separate workflow-port PR; retains ADR-0004, ADR-0007, and ADR-0014 safety and ownership boundaries |

## Context

ADR-0007 keeps reviewed Template Sync as a least-privilege transport for inherited files
outside `.github/workflows/**`. ADR-0014 moved reusable workflow behavior into synchronized
local actions while retaining repository-owned triggers, permissions, secrets, and the few
literal workflows that external publishers verify. This has made ordinary propagation safe,
but accepting one direct-parent checkpoint can still require three operator actions:

1. review and merge the non-workflow Template Sync PR;
2. prepare and merge a separate maintainer-authenticated workflow-port PR; and
3. update the inheritance lock only after both deltas are accepted.

Repeated fleet migrations have shown that the extra PR boundary increases approval volume
without adding an independent safety boundary. It also makes an early or mistyped lock update
easier. The future transport trigger recorded in LOG-0037 permits reconsidering an exclusive
hybrid when manual-port and review burden become material, but requires proof that no path can
be inherited twice.

Constraints are: every parent delta remains human reviewed; direct-parent order and exact
source provenance remain mandatory; project overlays, local workflow security boundaries, and
repository identity remain protected; no PAT, write-capable GitHub App, auto-merge, or mutable
remote workflow is introduced; and a failed or repeated operation must not leave a partially
accepted lock.

## Options considered

### Option 1: Do nothing

Keep separate ordinary-sync and workflow-port PRs, followed by a manual lock update. This is
already safe and requires no implementation. It preserves avoidable approval volume and leaves
the most important acceptance invariant dependent on a manual sequence.

### Option 2: Replace Template Sync with full local materialization

Complete the ADR-0004 local-first reconciler and use it for every inherited path. This creates
one deterministic transport and can update workflows, but replaces a stable scheduled path,
increases local operator responsibility, and removes automatic early propagation. The present
forcing problem does not justify that migration.

### Option 3: Grant the scheduled transport workflow-write authority

Use a PAT or GitHub App so Template Sync can update every inherited path in one PR. This is
convenient, but adds a credential, rotation, cross-repository authorization, and a larger
unattended write boundary. It is disproportionate to the remaining manual workflow surface.

### Option 4: Finalize the existing Template Sync PR locally by exclusive path ownership

Keep Template Sync as the only scheduled writer for ordinary inherited paths. A deterministic
local command operates on that existing PR branch, materializes only inherited paths classified
as approved manual-port boundaries, proves the complete child state against the exact parent
checkpoint, and then advances the lock. The maintainer commits and pushes the result to the same
PR through the normal authenticated Git workflow.

This adds one bounded local write operation but neither a second PR nor a second writer for any
path. It reduces approval volume while preserving least privilege and reviewed convergence.

## Decision

Adopt Option 4.

Reviewed Template Sync remains the sole scheduled write and PR-creation transport. A local,
idempotent `finalize-sync` operation MAY complete the existing Template Sync PR branch. It MUST
NOT create or merge a PR, push a commit, fetch a remote, call GitHub, or apply repository
governance. Normal maintainer Git authentication remains responsible for commit and push.

The operation MUST:

- require a clean non-default-branch worktree, the declared direct-parent worktree, and the exact
  full source commit recorded by the Template Sync PR;
- verify manifest ownership, parent identity, lock ancestry, file content, executable mode, and
  the accepted lock-to-source range before writing;
- write only inherited paths currently classified as `pending_manual_port` with an explicitly
  supported reason; the initial supported reason is `workflow-security-boundary`;
- refuse `protected_review`, project or template overlays owned by the child, unowned paths,
  candidate deletions, symlinks, source mismatch, unexpected worktree changes, and any path that
  Template Sync is permitted to write;
- run a complete steady-state comparison after materialization and update the lock only when no
  pending sync, pending manual port, ownership, or deletion attention remains; and
- produce no file change when repeated with the same inputs.

Template Sync and `finalize-sync` path sets MUST be disjoint and validated by regression tests.
The resulting PR MUST identify the direct parent and exact source commit and show the ordinary
sync, manual-port, and lock changes together. It remains subject to normal CI, PR-size policy,
human review, and one merged direct-parent hop before any descendant proceeds.

Deletions remain outside the default finalizer because GR-031 requires explicit per-command
human approval. A future deletion mode requires its own exact path confirmation and may update
the same PR, but MUST NOT be inferred from this decision.

## Consequences

**Positive:**

- One accepted parent checkpoint normally needs one PR review and one merge.
- The lock cannot advance before the accepted inherited state is complete.
- Workflow writes use local maintainer authority without storing a CI credential.
- Disjoint path ownership prevents duplicate inheritance and conflicting PRs.
- Idempotent local operation makes retries and interrupted work safe.

**Negative:**

- A maintainer must check out and update the Template Sync PR branch when a manual port exists.
- The finalizer needs strict Git-state and source-provenance tests, increasing local tool code.
- PRs containing workflow changes have a larger review surface than ordinary sync-only PRs.
- Deletions still require a separate explicit approval step.

Migration is expand-first. Add preview and failing-first validation tests, then bounded local
materialization, then lock finalization. Keep the existing separate manual-port procedure valid
until one direct child proves the finalizer. After that proof, update the runbook to make the
single acceptance PR the default. Rollback disables the finalizer and returns to ADR-0007's
separate manual-port PR without changing Template Sync, repository settings, or accepted locks.

**Follow-ups:** Track implementation in Issue #159. After this ADR is approved, add the
finalizer and review report first; then implement idempotent child bootstrap, parent-side
propagation-impact classification, and explicit active/paused/retired fleet lifecycle states as
separate bounded changes.
