# ADR-0004: Harden multi-level template inheritance

| Field | Value |
| -- | -- |
| Status | accepted |
| Date | 2026-07-16 |
| Deciders | repository owner |
| Author | Codex (AI agent) |
| Supersedes / Superseded by | Evolves ADR-0003; supersedes LOG-0004 |

## Context

ADR-0003 makes live GitHub governance deterministic and fail-closed, but it assumes one
inherited foundation policy plus one local repository policy. The actual template graph
has both direct and multi-level inheritance:

- `ai-dev-foundation -> terraform-gcp-template -> secure-ga4-bq-template`
- `ai-dev-foundation -> nextjs-saas-template`

The current transport uses a target-owned `.templatesyncignore` denylist and
`actions-template-sync`. All three enabled downstream schedules fail when their standard
`GITHUB_TOKEN` attempts to push a changed workflow file because that token has no
workflow-write permission. A dry-run also shows that the denylist would overwrite each
stack's `.gitignore`; for Next.js this removes `.env*.local`, and for Terraform it
removes state and variable-file exclusions. Because `.templatesyncignore` cannot itself
be synchronized, every newly protected path requires a manual fleet migration.

The two policy layers also cannot express an inheritable Terraform-family requirement
separately from a repository-local override. Copying the parent's `repository.json`
overwrites the child; excluding it drops the family requirement. In addition,
`required_checks` currently replaces the foundation list, so an override can remove a
foundation check. A child that misses several upstream PRs receives one accumulated diff
that may exceed GR-020's hard PR-size gate.

Constraints are: solo maintenance is the normal case; every change remains a reviewed
PR; no repository-administration credential is stored in Actions; workflow files still
need to inherit; local files and secrets must never become trackable because of sync;
and every hop must remain green and reversible.

## Options considered

### Option 1: Do nothing

Keep direct-parent paths, denylist sync, and the two policy layers. This has no migration
cost, but scheduled sync remains red, target-owned files can be overwritten, and the
Terraform family cannot safely pass stack policy to its children. Rejected.

### Option 2: Keep the denylist and add a privileged sync token

Use a PAT or GitHub App with Contents, Workflows, and Pull Requests write permissions.
This restores unattended workflow PRs and is operationally familiar. It does not fix
denylist omissions, policy-layer ambiguity, accumulated oversized diffs, or the need to
hand-update `.templatesyncignore`; it also adds a credential and rotation boundary.

### Option 3: Split automated and manual sync

Exclude workflows from the scheduled action and port workflow changes locally. This
keeps the default token least-privileged and is a small change, but two transports can
drift and still rely on a denylist. Reviewers cannot prove from one plan that all parent
changes and only parent-owned paths were considered.

### Option 4: Use a manifest-driven, local-first inheritance reconciler

Each child declares its direct parent, accepted parent commit, inherited allowlist, and
protected local paths in a local manifest. A deterministic tool plans one parent commit
at a time, refuses ownership overlap, defaults to no deletion, and materializes an
explicitly confirmed change into a non-main worktree for the normal reviewed PR flow.
It can modify workflows because the eventual push uses the maintainer's local GitHub
authentication. Inheritable template-policy fragments separate family requirements from
the leaf repository policy. This adds a schema, tool, and migration work, and unattended
sync is no longer the default.

## Decision

Adopt Option 4. Keep a **direct-parent-only** topology; a child MUST NOT bypass an
intermediate template. Every path MUST have exactly one owner:

- `.github/inheritance/manifest.json` is child-owned and declares the direct parent,
  inherited allowlist, protected paths, and lock-file location.
- `.github/inheritance/lock.json` records the exact accepted parent repository and
  commit. The default plan advances only the next first-parent commit so upstream PR
  review slices and GR-020 limits are preserved.
- `.gitignore`, the manifest, `.templatesyncignore`, the local governance policy, the
  sync workflow, and stack-specific files are protected by default. A path cannot be
  both inherited and protected. Unknown new parent paths are not copied until reviewed
  into the allowlist.
- Plan is read-only and reports adds, modifications, candidate deletions, source commit,
  and ownership. Apply requires exact child and parent-commit confirmation, refuses
  `main`, and defaults to no deletion. Deletion requires a separately confirmed command
  under GR-031. Commit, push, and PR creation remain the normal repository workflow.

Extend ADR-0003's governance projection to ordered layers:

1. the global `ai-dev-foundation` policy and minimums;
2. zero or more inheritable template-family profiles, each with a unique ID and explicit
   parent profile (for example, a Terraform profile);
3. the leaf repository's non-inherited `repository.json`.

Foundation-required checks are monotonic: profiles and repository policy may add unique,
always-reported checks but MUST NOT remove foundation checks. A required check MUST have
a unique context and MUST run for every pull request; a path-filtered workflow is invalid
for a required context. A Terraform-family profile will add `iac-scan` only after its
workflow always reports that uniquely named result.

Use solo-friendly foundation defaults: zero approvals, no last-push approval, automatic
merged-branch deletion, Discussions disabled, squash-only merge, no admin bypass, and
Renovate as the sole dependency updater. Team repositories may raise approval counts,
enable last-push approval when at least one approval is required, and enable Discussions;
they may not weaken foundation minimums or required checks.

The scheduled write-capable Template Sync path is disabled by default. Local owner
authentication is the standard transport and no new secret is introduced. A dedicated
GitHub App restricted to Contents, Workflows, and Pull Requests write permissions may be
considered later only through a separate security decision when unattended convergence
has demonstrated value.

## Consequences

**Positive:** inheritance becomes fail-closed and auditable; new parent files cannot
silently overwrite local files; multi-level policy has explicit semantics; workflow
updates remain possible without a CI admin credential; and missed updates are reviewed
in bounded upstream slices. Next.js application/auth/payment files remain local, while
shared rules and governance can still inherit.

**Negative:** every template needs a manifest and lock; a new inherited path requires an
explicit child review; local sync is a maintainer action; each additional parent hop adds
merge latency; and schema/profile migration is larger than an ignore-file patch.

Migration is expand-only until every child is validated: add the manifest validator and
layered policy support in the foundation; migrate `terraform-gcp-template` and
`nextjs-saas-template`; then migrate `secure-ga4-bq-template` through Terraform. The old
scheduled workflow stays disabled during migration and is removed only after equivalent
read-only drift visibility exists. No live governance setting changes during migration;
each repository receives a separate read-only plan before an explicitly approved apply.

Rollback is a normal PR reverting a manifest lock or implementation slice. Existing
local files and GitHub settings remain unchanged unless a separately confirmed tool
applies them.

**Follow-ups:**

1. Specify and test the inheritance manifest, lock, ownership validation, and one-commit
   planning semantics.
2. Extend the governance resolver to template profiles and monotonic required checks.
3. Change the foundation solo defaults and update comparison/apply tests.
4. Migrate direct children before any broad sync, then migrate the Terraform child.
5. Disable the currently failing scheduled sync variables until a safe replacement is
   accepted and deployed.
