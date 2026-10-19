# ADR-0007: Constrain transitional Template Sync

| Field | Value |
| -- | -- |
| Status | accepted |
| Date | 2026-07-22 |
| Deciders | repository owner (approved in PR #53 on 2026-07-22) |
| Author | Codex (AI agent) |
| Supersedes / Superseded by | Extends the migration rules of ADR-0004 |

## Context

ADR-0004 selects a manifest-driven, local-first reconciler and disables scheduled
write-capable Template Sync by default. Materialization is not implemented yet, so the
current repository fleet still uses `actions-template-sync` to open reviewed migration
PRs. The transitional configuration has drifted between repositories: some children do
not protect every manifest-owned path, some allow inherited workflow changes that the
GitHub App cannot push without Workflows permission, and some PRs do not identify the
exact parent commit being reviewed.

This has produced failed sync pushes and makes it possible to merge an ambiguous or
unsafe parent delta. Multi-level inheritance adds an ordering constraint: a grandchild
must review the intermediate template's merged result, not bypass it or advance its lock
to an unmerged upstream commit.

Constraints are: every propagation remains a human-reviewed PR; no privileged PAT or
GitHub App credential is introduced; repository-owned files and project documentation
remain protected; workflow changes still propagate through an explicit review path; and
the interim mechanism must remain compatible with the ADR-0004 local-first destination.

## Options considered

### Option 1: Do nothing

Keep each repository's current ignore list and PR metadata. This has no migration cost,
but repeats known permission failures and leaves ownership safety dependent on manually
remembered exceptions. Rejected.

### Option 2: Grant Template Sync Workflows permission

Use a PAT or GitHub App that can update workflow files. This gives one automatic
transport for all inherited files, but increases credential scope and still does not
prove that protected paths match the inheritance manifest. Rejected.

### Option 3: Bound the transitional transport by the inheritance contract

Keep Template Sync only as a PR-producing transport for non-workflow inherited files.
Exclude all workflows and every protected manifest root, include the exact direct-parent
commit in the PR, and port workflow changes through a separate reviewed PR. Validate the
ignore/manifest relationship in CI and propagate multi-level changes one merged hop at a
time. This adds a manual workflow-update step but has the smallest credential and
overwrite blast radius.

## Decision

Adopt Option 3 until ADR-0004 materialization replaces `actions-template-sync`.

- A child MUST name only its direct parent. Multi-level propagation MUST proceed in
  parent-to-child order, and each hop MUST merge before the next hop is prepared.
- `.templatesyncignore` MUST protect every `protected_paths` root in the child manifest.
  CI MUST fail when the two contracts diverge. The manifest, lock, ignore file, local
  governance policy, `.gitignore`, and Template Sync workflow remain child-owned.
- `.github/workflows/**` MUST be excluded from legacy Template Sync. Inherited workflow
  changes MUST be ported in an explicit reviewed PR using maintainer authentication and
  verified against the direct parent's exact commit.
- Every sync PR MUST identify the direct parent repository and full 40-character source
  commit. A reviewer MUST compare the accepted lock-to-source range before merging.
- The inheritance lock MUST advance only in the reviewed PR that accepts the parent
  delta. It MUST NOT advance past an unmerged direct-parent commit.
- Template Sync MUST NOT auto-merge or apply GitHub governance. Its only permitted write
  outcome is a reviewable branch and PR.

Git pathspec and ignore-file syntax MUST be treated as different contracts. In
particular, `actions-template-sync` restores ignored files with `git reset --`, so the
existing `:!docs/foundation/**` Git pathspec exception is intentional and MUST NOT be
rewritten as `.gitignore` negation without an implementation change and regression test.

## Consequences

**Positive:** legacy sync cannot overwrite manifest-protected paths; ordinary inherited
files still arrive as reviewable PRs; workflow-write failures are removed from the
automated path; reviewers can reproduce the exact parent delta; and multi-level
inheritance preserves the direct-parent boundary.

**Negative:** workflow updates require a second, maintainer-authenticated PR; every child
must maintain and test its local ignore contract; a stale lock remains possible until a
reviewer accepts the delta; and propagation latency increases at each inheritance hop.

Migration is expand-first: add validation and PR provenance, protect all workflows and
manifest-owned paths, then run one reviewed sync per direct child. After direct-child
merges, repeat from each intermediate template to its children. Rollback disables
`TEMPLATE_SYNC_ENABLED`; protected files and accepted locks remain unchanged. The final
contract-and-apply implementation from ADR-0004 can replace this transport without
changing path ownership or direct-parent topology.

**Follow-ups:** add the reusable ignore/manifest validator and tests; update the
inheritance guide with the ordered fleet runbook and the permission/provenance lessons;
migrate every enabled child; and audit the complete repository graph after all PRs merge.
