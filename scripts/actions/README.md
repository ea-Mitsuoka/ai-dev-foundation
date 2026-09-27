---
id: synchronized-workflow-actions
title: Synchronized Workflow Actions
---

# Synchronized Workflow Actions

This directory owns reusable GitHub Actions implementation that can propagate through
the reviewed non-workflow Template Sync transport. Executable callers remain under
`.github/workflows/` and are protected because they own repository events, permissions,
secrets, variables, environments, concurrency, and job-level conditions (ADR-0014).

## Boundary rules

- A caller MUST check out the repository before invoking a local composite action.
- A caller MUST retain every trigger and permission; a composite action MUST NOT select
  repository events or broaden token access.
- Secrets and repository-specific values stay in the caller and cross the boundary only
  as explicit inputs.
- Every external `uses:` reference in a workflow or local action MUST use a full
  40-character commit SHA.
- Add an action path to a caller's path filters when changing the implementation should
  run that workflow. Do not add a pull-request trigger solely to exercise an action that
  requires an approved external target or another privileged environment.

## Downstream migration

1. Merge the reviewed Template Sync PR that adds or updates `scripts/actions/`.
2. Port the protected caller in a separate maintainer-authenticated PR verified against
   the same direct-parent commit.
3. Preserve local triggers, permissions, secrets, and environment selection during the
   port; change them only as a separate security-boundary decision.
4. Advance the inheritance lock only after both inherited implementation and protected
   caller changes have been reviewed and accepted.

After the one-time caller port, implementation-only updates under this directory arrive
through ordinary reviewed Template Sync PRs. Caller-boundary changes remain manual.

`release-please` accepts `release-type` from the protected caller so each downstream
repository retains its release strategy. `ai-review` accepts the API key and pull
request number explicitly; local actions MUST NOT read additional secrets implicitly.

`setup-task` takes no inputs and reads no secrets. Its `install.sh` holds the single
go-task version and SHA-256 pin (ADR-0026); a dev container runs the same script with a
target directory, for example `bash scripts/actions/setup-task/install.sh ~/.local/bin`.
