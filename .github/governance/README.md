---
id: github-governance-policy
title: GitHub Governance Policy
---

# GitHub Governance Policy

These JSON files are the deterministic enforcement projection defined by ADR-0003 and
extended for direct-parent template families by ADR-0004.
Normative requirements remain in `.ai/`; every foundation minimum references its source
rule ID.

## Ownership

| File | Owner | Inheritance |
| -- | -- | -- |
| `foundation.json` | ai-dev-foundation | Inherited globally |
| `profiles/*.json` | Declaring template family | Inherited through each direct child |
| `repository.json` | Downstream repository | Protected; never overwritten |

Repository overrides may set `target_branch`, `enforcement_backend`, approval count,
last-push approval, one dependency-update provider, and merged-branch deletion. They may
also add required check names and select Discussions availability and the default squash
commit title/message formats. Squash-only merge availability is an immutable WF-030
foundation minimum. Unknown fields and attempts to override foundation minimums fail.

## Template profile chain

An optional profile adds template-family checks without copying the child-owned
`repository.json`:

```json
{
  "schema_version": 1,
  "id": "terraform-gcp",
  "parent": "ai-dev-foundation",
  "required_checks": ["iac-scan"]
}
```

The resolver discovers up to 32 regular, non-symlink JSON files in
`.github/governance/profiles/`. Profile IDs and explicit parent IDs must form one chain
rooted at `ai-dev-foundation`; file names and discovery order do not define precedence.
Each additional family profile names the preceding profile as its parent.

Required checks merge in foundation → profile chain → repository order. A name repeated
across layers is retained once at its first position, preserving existing repository
policies that repeat foundation checks. Duplicates inside one layer remain invalid. No
profile or repository layer can remove a foundation check. Add a profile check only after
its uniquely named workflow result runs on every pull request.

## Solo-friendly foundation defaults

The foundation starts from the ADR-0004 solo-maintainer profile: zero required
approvals, no last-push approval, automatic deletion of merged branches, Discussions
disabled, squash-only merge, no administrator bypass, and Renovate as the selected
dependency updater. A repository policy may opt into team-oriented operational values
such as approvals or Discussions, but it cannot weaken a foundation minimum.

Existing repository overrides that repeat a foundation default remain valid. This lets
repositories adopt the new foundation file without first coordinating a local-policy
cleanup; redundant overrides can be removed later through normal reviewed PRs.

## Validate, plan, audit, and apply

Python 3 is required; no third-party package is used.

```bash
python3 scripts/github_governance.py validate --root .
python3 scripts/github_governance.py plan --root . --repo OWNER/REPOSITORY
python3 scripts/github_governance.py audit --root . --repo OWNER/REPOSITORY
python3 scripts/github_governance.py apply --root . --repo OWNER/REPOSITORY \
  --confirm-repo OWNER/REPOSITORY
```

`validate` resolves all configured layers without authentication or network access.
`plan` and `audit` require authenticated `gh` read access and print the same stable,
redacted JSON comparison. They also verify that every required check name is observed on
the target branch head; unrelated observed checks do not create drift. These three
commands make no GitHub setting change.

`apply` requires the exact target to be repeated before any GitHub read. It uses local
`gh` authentication with repository Administration write access, applies one owned-field
action, reads it back, and replans before continuing. Failure emits redacted partial
evidence and stops without retry or automatic rollback. Never run `apply` in CI or store
its administrator credential in Actions.

| Command | Exit 0 | Exit 1 | Exit 2 |
| -- | -- | -- | -- |
| `validate` | Policy valid | — | Invalid policy or input |
| `plan` | Comparison completed, including drift or unknown state | — | Policy, input, or GitHub read failure |
| `audit` | All controls compliant | Drift or unknown state | Policy, input, or GitHub read failure |
| `apply` | All owned controls verified compliant | — | Policy, confirmation, write, read-back, verification, or replanning failure |

`scripts/setup-github.sh` is a thin compatibility wrapper. A non-empty `DRY_RUN` delegates
to read-only `plan`; normal execution requires the repository twice in the form
`OWNER/REPOSITORY --confirm-repo OWNER/REPOSITORY` before delegating to `apply`. It makes
no direct `gh` call, owns no fixed settings, and preserves the reconciler exit code.
The former no-argument apply and inline onboarding reminders are intentionally removed;
callers must migrate to the explicit target form and use the
[foundation usage guide](../../docs/foundation/guides/usage.md) for onboarding.

## Apply action planning boundary

The internal pure-data planner converts a complete comparison into ordered GitHub REST
requests. The public CLI invokes the execution boundary only after exact confirmation. It
requires exact target confirmation, sends one action, reads it back, verifies it, and
replans from fresh state before selecting the next action. A repeated action or any
write, read-back, verification, or replanning failure stops with redacted partial
evidence; it never retries or weakens protection through automatic rollback.

The planner may create only `ai-dev-foundation: branch-governance` as a repository
ruleset. Organization and unrelated rules remain unmanaged, even when they have the same
name.

For API fields absent from policy schema version 1, new rulesets require up-to-date
checks and resolved review threads, but do not dismiss stale approvals or require code
owners. Changing these defaults requires a reviewed schema migration.

Each action records controls, side effects, method, endpoint, and body. Planning fails
closed on unknown state, unobserved checks, or unsafe backend updates. Discovery lists
inactive repository rulesets to prevent duplicate creation. Existing managed rulesets
may be updated only with the generated branch condition and supported rule types. The
planner preserves stricter stale-review, code-owner, merge-method, and check-integration
constraints. Extra rules, active reviewer restrictions, unknown parameters, or missing
detail block the update.

Repository merge methods, squash commit defaults, Discussions, and merged-branch
deletion share one PATCH action so one read-back verifies the repository settings
together. Squash-only is fixed by WF-030; the other values remain downstream-overridable.

## GitHub discovery boundary

The Python module now has an internal, GET-only discovery boundary for repository,
branch, effective-rules, all repository rulesets, legacy-protection, and security. It pins GitHub
REST API version `2026-03-10`, validates repository and branch targets before invoking
`gh api`, uses a 30-second timeout, and retains only fields needed for governance.
Ruleset bypass identities are reduced to a boolean and never retained. Check runs and
commit statuses are reduced to names before comparison.

Administrator-only fields that the current token cannot read are reported as `unknown`;
mandatory repository, branch, or effective-rules reads fail closed. The module compares
this inventory with resolved policy as deterministic `compliant`, `drift`, or `unknown`
controls and reports unmanaged effective rules without changing them.

Private vulnerability reporting status needs Metadata read; enabling it needs
Administration write. Vulnerability-alert status needs Administration read. A 404 is
treated as disabled only when the repository response confirms admin access; otherwise
it is `unknown`. Apply only enables these foundation minimums and never disables them.
