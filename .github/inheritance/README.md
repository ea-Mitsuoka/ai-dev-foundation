---
id: template-inheritance-contract
title: Template Inheritance Contract
---

# Template Inheritance Contract

This directory defines the child-owned, direct-parent contract from
[ADR-0004](../../docs/foundation/adr/0004-harden-multi-level-template-inheritance.md)
and the bounded legacy transport from
[ADR-0007](../../docs/foundation/adr/0007-constrain-transitional-template-sync.md).
ADR-0014 adds ordered agent-contract validation. Validation, local history planning, and
fleet auditing are read-only. Reviewed Template Sync remains the only write transport;
no materialization or second inheritance transport is active.

## Schema version 1

`.github/inheritance/manifest.json` declares intent:

```json
{
  "schema_version": 1,
  "parent": {"repository": "acme/parent-template", "branch": "main"},
  "lock_file": ".github/inheritance/lock.json",
  "inherited_paths": [".ai/", "scripts/template_inheritance.py"],
  "protected_paths": [".gitignore", ".github/governance/repository.json", ".github/inheritance/lock.json", ".github/inheritance/manifest.json", ".github/workflows/template-sync.yml", ".templatesyncignore"]
}
```

The lock records the exact accepted parent commit:

```json
{"schema_version": 1, "parent": {"repository": "acme/parent-template", "commit": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}}
```

Schema version 1 remains valid during migration and has no agent profile.

## Schema version 2 agent profile

Manifest version 2 keeps the version 1 fields and requires the protected file
`.github/inheritance/agent-profile.json`:

```json
{
  "schema_version": 1,
  "authority_policy": "strengthen-only",
  "inputs": [
    {"layer": "foundation", "repository": "acme/ai-foundation", "path": ".ai/contracts/foundation/agent-entry.md"},
    {"layer": "template", "repository": "acme/stack-template", "path": ".ai/contracts/templates/acme/stack-template/agent-overlay.md"},
    {"layer": "project", "repository": "acme/product", "path": ".ai/project/agent-overlay.md"}
  ]
}
```

The loader order is exactly one foundation input, zero or more template inputs in
parent-to-child order, then exactly one project input. Foundation and template files
must be inherited; the project file and profile must be protected. Template paths are
owner-qualified, and the last template repository must be the direct parent unless the
foundation itself is the direct parent. Every reference is a bounded, existing,
non-symlink file. `strengthen-only` prohibits later layers from weakening foundation
MUST, guardrail, or security controls.

Validation proves the declared policy, layer order, bounded references, and ownership;
it does not claim to decide whether arbitrary natural-language statements are
semantically equivalent. Guardrails therefore keep one authority body under
`.ai/contracts/foundation/guardrails.md`, and `.ai/guardrails.md` is a stable entry
adapter. Higher authority wins and a semantic conflict in an overlay fails closed for
human review.

An ownership root is either a literal file or a directory prefix ending in `/`. Globs,
absolute paths, traversal, `.git`, duplicates, and overlap within or across ownership
classes are invalid. Protected roots must cover the manifest, selected lock file,
`.gitignore`, `.templatesyncignore`, local governance policy, and sync workflow.

During the transitional Template Sync period, `.templatesyncignore` must also:

- cover every manifest `protected_paths` root;
- contain `.github/workflows/**`; and
- contain no `:!` exception that re-includes a protected root or workflow.

Entries ending in `/**` are treated as directory roots. The `:!` prefix is a Git
pathspec exclusion used by `actions-template-sync`, not `.gitignore` negation. The
intentional `:!docs/foundation/**` exception permits only the inherited foundation
documentation namespace.

`actions-template-sync@v2` exposes an abbreviated source hash even though its action
metadata calls the value a Git hash. The workflow must expand that exact abbreviation
through the GitHub commits API and validate the resulting 40-character commit before
writing PR provenance. Resolving only the current parent branch head is insufficient
because the parent can move while synchronization runs.

## Validate

```bash
python3 scripts/template_inheritance.py validate --root .
```

Exit `0` prints deterministic JSON; exit `2` reports invalid input on stderr. The command
performs no network request, file write, deletion, Git operation, or GitHub API call.
`make doctor` runs this validation automatically when the repository contains a child
manifest; the foundation root has no manifest and skips only this child-specific check.
It also rejects the exact template `not wired yet` implementation for required Make
targets outside the canonical Foundation repository. A target that does not apply must
use an explicit repository-owned `not applicable` implementation; silent template
no-ops are not valid downstream checks.

`scripts/template-check.sh` runs the complete Foundation regression suite by default.
A descendant that owns a reviewed `scripts/foundation_test_runner.py` may set
`FOUNDATION_TEST_SUITE=fast` or `slow` from its protected Makefile or workflow. The
inherited selector accepts only `all`, `fast`, or `slow`, requires the local runner for
a non-default value, and never evaluates a command supplied through the environment.
The descendant must execute every excluded slow test through another required check; a
faster `doctor` must not reduce test coverage.

## Propagate a parent change

Apply each row in order. Do not prepare a grandchild from an unmerged intermediate
template.

The transitional workflow is scheduled daily at 07:17 UTC and may also be started with
`workflow_dispatch`. A schedule shared by every repository does not collapse
multiple inheritance hops: a grandchild run at the same time still sees the previously
merged intermediate parent. After the intermediate template PR merges, either start its
children manually or wait for their next daily schedule. Every resulting PR remains a
separate review and must not auto-merge.

Each repository runs Template Sync as a single-flight operation. Scheduled and manual
runs never overlap. If exactly one `chore/template_sync_*` PR is already open, the run
ends successfully and identifies that PR in the job summary instead of creating another
review. More than one open synchronization PR fails closed for human reconciliation.
No run force-pushes, closes, or merges an existing PR. Parent changes that arrive while
one PR is open are collected by the next daily or manual run after it merges.

| Step | Required evidence |
|------|-------------------|
| 1. Update a direct child | Template Sync PR names the direct parent and the exact 40-character source commit |
| 2. Review inherited files | Accepted lock-to-source range reviewed; no protected path changed by transport |
| 3. Finalize the same PR | `finalize-sync --apply` materializes supported manual ports and advances the lock only after complete convergence |
| 4. Merge and continue | Only the merged child commit becomes the source for its direct children |

Template Sync must never auto-merge or apply repository governance. If validation fails,
disable `TEMPLATE_SYNC_ENABLED` until the manifest and local ignore contract agree.

## Authenticate a private direct parent

Private-source authentication is opt-in per inheritance edge. The dedicated GitHub App
has repository `Contents: read` and platform-required `Metadata: read`, no write or
organization permission, and access only to approved parent repositories. The App token
reads the declared direct parent; the child's repository-scoped `GITHUB_TOKEN` alone
writes the synchronization branch and pull request.

Before enabling one edge:

1. Manually port the current protected `template-sync.yml` into the child and verify its
   literal `source_repo_path` and `SOURCE_REPOSITORY` equal the manifest parent.
2. Install the approved source-reader App on that parent repository.
3. Store the App client ID as a child repository variable and its private key as a child
   repository secret. Never copy either value into a file, log, issue, or PR.
4. Confirm the child allows GitHub Actions to create pull requests. Branch rules and
   human review still control merging; the workflow never approves or merges its PR.
5. Configure and enable the edge:

```bash
gh variable set TEMPLATE_SYNC_SOURCE_AUTH --body github-app
gh variable set TEMPLATE_SYNC_SOURCE_APP_CLIENT_ID --body <client-id>
gh secret set TEMPLATE_SYNC_SOURCE_APP_PRIVATE_KEY
gh variable set TEMPLATE_SYNC_ENABLED --body true
```

The secret command prompts for the private key. The workflow passes only boolean
presence to the local validator, scopes each short-lived installation token to the one
declared parent repository, and lets the official token action revoke it at job end.
Missing credentials, unsupported authentication modes, and workflow-to-manifest parent
mismatches fail before synchronization. A public direct parent uses the default
`public` mode and does not require App configuration.

Pilot one edge with `workflow_dispatch`. Accept it only when it creates one reviewed PR,
records the exact 40-character parent commit, leaves protected paths unchanged, passes
normal CI, and a second run creates no duplicate PR. Record its runner duration and an
approved monthly Actions budget in the tracking issue before adding another edge.

For key rotation, create a replacement App key, update the repository secret, verify one
manual run, then revoke the old key. To roll back, set `TEMPLATE_SYNC_ENABLED=false`,
suspend or remove the App installation, and return to local `fleet-audit` plus reviewed
local inheritance operations. ADR-0016 keeps any scheduled fleet audit disabled until a
separate read-only proposal is approved.

## Plan the next parent commit

```bash
python3 scripts/template_inheritance.py plan --root . --parent-root ../parent-template
```

`--parent-root` must be the top level of a local Git worktree whose credential-free
GitHub `origin` matches the manifest. The local `origin/<branch>` ref must already be
available. Plan never fetches, checks out, writes, deletes, or calls GitHub.

Plan verifies that the lock is on that ref's first-parent history and selects only the
commit immediately after it. The report classifies that commit's paths:

| Field | Meaning |
|-------|---------|
| `add` | Inherited parent file is absent in the child |
| `modify` | Inherited content or executable mode differs |
| `candidate_delete` | Parent removed an inherited file; no deletion is performed |
| `already_current` | Child already matches the candidate state |
| `protected` | Child-owned path is reported and skipped |
| `unowned` | Path is outside both ownership lists and is skipped |

Exit `0` prints the deterministic plan, including candidate and branch-head commits.
Exit `2` reports invalid metadata, parent identity/history, Git state, or child path.
See [template inheritance troubleshooting](../../docs/foundation/troubleshooting/template-inheritance.md).

## Plan direct-child bootstrap

A parent publishes its child contract as `inheritance-export.json` under its
owner-qualified agent contract. Before writing initialization metadata, preview the exact
template source from a clean non-default child branch:

```bash
python3 scripts/template_inheritance.py bootstrap-child \
  --root /path/to/child \
  --parent-root /path/to/direct-parent \
  --source-commit <40-character-template-source> \
  --repository owner/child
```

The read-only plan verifies both GitHub origins, source ancestry, the published ownership
contract, agent input order, and byte-for-byte inherited template content. It emits the
desired manifest, lock, agent profile, and Template Sync exclusions.

Prepare reviewed project-owned payloads outside the child worktree:

```text
payload/
├── README.md
├── .ai/project/agent-overlay.md
├── .github/workflows/template-sync.yml
└── docs/inheritance/readmes/<parent-owner>/<parent-repository>.md
```

The root README must name the child ownership marker. The archive must retain the parent
marker and exact `source-repository` and `source-commit` frontmatter. The project overlay
must identify the child without placeholders. The workflow must retain the opt-in guard
and name the direct parent in both `source_repo_path` and `SOURCE_REPOSITORY`. Apply only
after reviewing those protected files:

```bash
python3 scripts/template_inheritance.py bootstrap-child \
  --root /path/to/child --parent-root /path/to/direct-parent \
  --source-commit <40-character-template-source> --repository owner/child \
  --apply --payload-root /path/to/payload \
  --confirm-repository owner/child \
  --confirm-source <40-character-template-source>
```

Apply accepts only exact parent-copy or already-desired targets, refuses a differing
archive or unrelated managed edit, writes no deletion, and validates the complete
inheritance contract afterward. Commit the result before repeating; the same confirmed
operation then returns `already_bootstrapped` without changing files. Enabling the
repository variable remains a separate authenticated step after review and merge.

## Report fleet propagation boundaries

Run `fleet-report` against explicit local child/parent worktree pairs. Repeat
`--repository` for each child; the command never discovers repositories recursively.

```bash
python3 scripts/template_inheritance.py fleet-report \
  --repository acme/terraform-template ../terraform-template ../foundation \
  --repository acme/product ../product ../terraform-template
```

The command reuses validation and one-first-parent planning for every pair and emits
deterministic JSON. When a next parent commit exists, it reports that bounded checkpoint.
When the lock already equals the parent branch head, it compares every parent file with
the child's Git-tracked and non-ignored untracked files below each `inherited_paths`
root. That steady-state audit detects missing files, content differences,
executable-mode differences, and child remnants deleted by the parent. Ignored build
artifacts do not create false drift. `audited_inherited_files` reports the number of
inherited paths examined.

At most 32 unique children and 10,000 inherited files per child are accepted. Exceeding
either bound fails closed. The reported child repository name comes from the explicit
argument and is labeled `repository_source: explicit-argument`; the command validates
its `OWNER/REPOSITORY` shape but does not call GitHub to verify it.

| Category | Meaning |
|----------|---------|
| `synchronized` | Inherited child content equals the selected candidate or current parent target |
| `pending_sync` | Inherited content is missing or differs and can synchronize through the reviewed parent PR |
| `pending_manual_port` | Inherited content differs but the transitional transport intentionally excludes it; each item reports the manual-port reason |
| `manually_ported` | Content at a manual transport or protected boundary equals the selected candidate or current parent target exactly |
| `protected_review` | Protected child content differs; the reported reason identifies the manual boundary |
| `ownership_review` | An unowned path exists in the current parent target or child and needs an explicit ownership decision |
| `deletion_review` | The parent deleted inherited content; the read-only tool never deletes it |

An inherited path excluded by `.templatesyncignore` is reported as `pending_manual_port`
instead of `pending_sync`; an exact child copy is reported as `manually_ported`.
`workflow-security-boundary` means maintainer authentication is required on the existing
Template Sync PR branch. Manual boundaries are intentional. Protected workflow callers
retain local events, permissions, secrets, and environment selection. Project overlays
and profiles retain repository identity and semantics. Manifests, locks, and ignore files retain accepted
provenance and ownership. Other protected paths remain repository-owned unless a
reviewed contract change moves their ownership. Unowned paths present in the current
parent target or child require a reviewed ownership decision before synchronization. A
transient unowned candidate path absent from both is reported by `plan` for history
visibility but does not create fleet attention because the current transport target
cannot write it.

Workflow implementations normally delegate synchronized local behavior under ADR-0014.
When an external publisher validates the literal workflow for result provenance, its
SHA-pinned approved actions remain direct protected-workflow steps. OpenSSF Scorecard is
the current instance and therefore requires an explicit reviewed port at every child.

GitHub-hosted security features with plan-dependent private-repository support keep an
explicit visibility boundary. Protected CodeQL and OpenSSF Scorecard jobs run only when
`github.event.repository.visibility == 'public'`; every active child MUST receive that
condition through a reviewed manual port. The synchronized release-gates action applies
the same condition only to Artifact Attestation. Portable release tests, Trivy scans,
license checks, SBOM generation, builds, and secret scanning remain enabled for private
repositories. A child with separately approved GitHub Code Security or Enterprise Cloud
may strengthen this protected boundary through its own reviewed policy.

Target comparison recognizes content accepted ahead of its lock during a reviewed
mechanical sync. The report does not advance provenance: every intermediate
first-parent checkpoint still requires its own reviewed lock update.

Fleet reporting performs no fetch, checkout, file write, deletion, GitHub API call, or
network request. Refresh each local `origin/<branch>` explicitly before the report when
current remote state is required.

## Audit the fixed fleet

[`docs/foundation/inheritance-fleet.json`](../../docs/foundation/inheritance-fleet.json)
is the canonical, machine-readable list of direct-parent relationships and their
`active`, `paused`, or `retired` lifecycle. Its location is already inherited by every maintained direct
child, so adding the config does not require a child-specific ownership migration. It
stores repository identities and workspace-relative directory names, never absolute
paths or credentials. Every entry includes a concise reason. The checked-in regression
test pins the complete fleet, including retired `Yukihide-Mitsuoka/repchat` and
`Yukihide-Mitsuoka/chat-chart`. No active entry inherits from the former account's
foundation, so the fleet describes one root.

Place the configured repositories as sibling Git worktrees under one directory, refresh
their remote refs explicitly, then run from the `ai-dev-foundation` worktree:

```bash
make fleet-audit FLEET_WORKSPACE_ROOT=/path/to/worktrees
```

Descendant Makefiles are protected repository-owned files and do not receive this target.
Use the Foundation worktree as the fleet-wide audit entry point.

The target audits every active relationship exactly once and labels repository identity
as `repository_source: fixed-fleet-config`. It validates each active child's declared
parent against the configuration and the parent's credential-free GitHub origin. A
missing active worktree, mismatched parent, symlink, invalid contract, or content drift
fails closed or produces `status: attention`. Paused and retired worktrees are not
required. Paused entries keep the overall result at `attention`; retired entries remain
visible without claiming convergence. The target is read-only and creates no approval
queue.

## Classify propagation impact before merging a parent change

Use `propagation-impact` with two existing commits in a configured parent worktree:

```bash
python3 scripts/template_inheritance.py propagation-impact \
  --workspace-root /path/to/worktrees \
  --parent-repository acme/foundation \
  --base-commit <40-character-base-commit> \
  --head-commit <40-character-head-commit>
```

The read-only command evaluates every changed path against each active direct child's
manifest and `.templatesyncignore`. It does not evaluate paused or retired children.

| Impact | Required handling |
|--------|-------------------|
| `foundation-only` | The path is repository-owned in the child; no propagation action |
| `schedule-only` | Reviewed Template Sync can carry the inherited path |
| `manual-boundary` | A workflow or legacy transport exclusion requires an authenticated reviewed port |
| `child-migration-required` | The path is unowned or changes a child-owned inheritance/project boundary |

The result status is the strongest observed impact. This classification predicts the
review path; `fleet-audit` remains the post-merge convergence proof.

## Plan single-PR finalization

ADR-0015 consolidates an accepted parent checkpoint into the existing Template Sync PR.
The expand-phase command is read-only and verifies the clean non-default child branch,
credential-free child and parent origins, an exact source commit on the refreshed parent
first-parent range, complete
inherited tree, executable modes, and protected or unowned changes:

```bash
python3 scripts/template_inheritance.py finalize-sync \
  --root /path/to/child-sync-worktree \
  --parent-root /path/to/direct-parent \
  --source-commit <40-character-source-commit>
```

`ready_to_finalize` means every ordinary inherited path already matches and only a
supported `workflow-security-boundary` manual port or lock advance remains.
`already_finalized` means the inherited tree and lock are current. `blocked` reports
the exact pending sync, protected review, ownership review, unsupported manual port, or
deletion review that must be resolved before applying. Without `--apply`, the command
never writes.

Protected ownership is evaluated against the child's remote default branch, not against
the parent's file at the source commit. A parent-only change to a child-owned protected
path therefore remains outside synchronization. Any protected path changed on the sync
branch still blocks finalization, except for the lock update owned by the finalizer.

After a `ready_to_finalize` plan is reviewed, repeat the exact child identity and source
commit to materialize supported workflow ports and atomically advance the lock:

```bash
python3 scripts/template_inheritance.py finalize-sync \
  --root /path/to/child-sync-worktree \
  --parent-root /path/to/direct-parent \
  --source-commit <40-character-source-commit> \
  --apply \
  --confirm-repository OWNER/CHILD \
  --confirm-source <same-40-character-source-commit>
```

Apply refuses ordinary pending sync, protected or ownership review, deletion, unsupported
manual reasons, dirty worktrees, default branches, and mismatched confirmations before
writing. It preloads the exact parent workflow blobs, verifies convergence before
atomically replacing the lock, and is idempotent after its result is committed. It never
fetches, commits, pushes, creates or merges a PR, calls GitHub, or changes repository
governance.

## Future transport review trigger

Reviewed Template Sync remains the sole write and PR transport. Do not add a second
transport while its operational burden remains acceptable. If measurements over a
declared review period show materially excessive manual-port work, propagation latency,
or human review volume, an exclusive hybrid may be reconsidered because it can improve
the balance of safety, propagation speed, and approval effort.

Reconsideration is not approval. A new or superseding ADR must define one transport for
each path, prove that no change can be inherited twice or produce duplicate PRs, state
measurable adoption thresholds, and include migration and rollback evidence before any
write-capable hybrid is enabled.
