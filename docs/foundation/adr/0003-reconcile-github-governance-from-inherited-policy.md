# ADR-0003: Reconcile GitHub governance from inherited policy

| Field | Value |
| -- | -- |
| Status | accepted |
| Date | 2026-07-15 |
| Deciders | repository owner |
| Author | Codex (AI agent) |
| Supersedes / Superseded by | — (evolves LOG-0003) |

## Context

`scripts/setup-github.sh` implements LOG-0003 as a one-time, imperative bootstrap. It
hard-codes required checks and one approving review, enables both Renovate-oriented
configuration and Dependabot automated fixes, continues after mandatory API failures,
and does not compare later GitHub settings with repository rules. A downstream can
therefore contain the correct `.ai/` rules and bootstrap script while its live settings
remain absent or drifted.

The foundation needs an immediate administrator-operated apply path and a read-only
continuous audit path. It must remain stack-agnostic, preserve explicit human control of
repository-administration credentials, support solo and team repositories, and let
Template Sync distribute stronger foundation defaults without overwriting downstream
choices. Runtime AI interpretation of Markdown is prohibited because it would make
enforcement nondeterministic.

## Options considered

### Option 1: Keep the one-time bootstrap

Pros: no migration or added implementation. Cons: hard-coded choices continue to lock
solo repositories or omit project-specific checks; failures and later drift remain
undetected. Security posture depends on an undocumented manual rerun.

### Option 2: Parameterize the existing shell script

Pros: small change; preserves the Bash plus `gh` runtime contract. Cons: environment
variables do not provide a versioned, validated inheritance model; shell parsing makes
nested policy and safe field ownership difficult; dry-run would still tend to describe
commands instead of a current-versus-desired diff.

### Option 3: Add a layered policy and deterministic reconciler

Pros: versioned intent, explicit foundation minimums and repository overrides,
idempotent plan/audit/apply modes, testable merge semantics, and post-apply evidence.
The existing setup command can remain as a compatibility wrapper. Cons: adds a policy
schema, migration work, and a small local runtime; GitHub API capability differences
must be modeled explicitly.

### Option 4: Enforce centrally with an organization ruleset or GitHub App

Pros: strongest fleet-wide convergence and no per-repository administrator command.
Cons: personal repositories and plan capabilities differ; a GitHub App adds credential,
deployment, permission, and incident-response scope. It exceeds the forcing problem and
reverses LOG-0003's no-service decision without evidence that central scale is needed.

## Decision

Adopt Option 3. The foundation MUST ship a machine-readable foundation policy whose
entries reference normative `.ai/` rule IDs, plus a downstream-owned repository policy.
The machine policy is an enforcement projection, not a second normative source: `.ai/`
retains authority, every referenced rule ID must exist, and a change to a projected MUST
must update its projection and contract tests in the same reviewed PR. The runtime MUST
NOT parse rule prose or invoke an AI model. It MUST apply field-specific merge rules:
repository policy may set operational values such as approval count, required check
names, supported enforcement backend, and exactly one dependency-update provider, but
it may not disable minimums derived from GR-010, GR-011, GR-012, SEC-002, or another
foundation MUST.

The initial machine interface is versioned JSON data:

- `.github/governance/foundation.json` is foundation-owned and Template Sync-managed.
- `.github/governance/repository.json` is downstream-owned and excluded from sync.
- Both declare `schema_version`; projected controls declare `rule_refs`.

JSON is selected so configuration is data rather than executable shell and can be
parsed without adding a YAML/TOML package. The schema must reject unknown fields and
invalid combinations before any GitHub read or write. A future format change is a
versioned migration, not permissive parsing.

The reconciler MUST provide these modes:

- `plan`: authenticate and read current state, validate target/capabilities/check names,
  and print a redacted current-versus-desired diff without writes.
- `audit`: perform the same read-only comparison with machine-readable output and a
  nonzero drift result suitable for CI.
- `apply`: require an explicit repository target confirmation, reject an invalid plan
  before writes, change only owned fields through versioned `gh api` endpoints, and
  verify every result by reading it back.

The foundation-managed branch rule MUST have a stable name and MUST NOT replace or
delete unrelated rulesets. Repository rulesets are preferred; a legacy branch-protection
adapter is allowed only when the selected policy declares it and it enforces the same
minimums. Plan and audit must inventory all effective branch rules and flag stricter or
conflicting unmanaged controls; apply does not silently remove them. Unsupported
mandatory controls are errors, not warnings. Administrator credentials remain in the
human's local `gh` authentication; CI may run `audit` with read-only access but MUST NOT
store a repository-administration token or run `apply`.
When a normal `GITHUB_TOKEN` cannot read an administrator-only setting, audit MUST report
that control as `unknown`, not compliant; a complete audit requires an administrator's
local read access unless a future ADR approves a narrower central credential boundary.

Foundation policy, schema, reconciler, and tests are distributed through Template Sync.
The downstream policy is excluded from sync. Existing downstream repositories require a
one-time reviewed migration because their `.templatesyncignore` files are themselves
downstream-owned. `scripts/setup-github.sh` remains as a documented compatibility wrapper
until migrated repositories use the reconciler directly.

## Consequences

**Positive:** live GitHub governance becomes auditable against repository-owned intent;
security failures stop closed; solo/team differences are explicit; foundation changes
arrive as reviewable PRs and do not mutate downstream settings until an administrator
runs `apply`.

**Negative:** a wrong required-check name or approval policy can block merges. Enabling
secret scanning can create alerts and push protection can reject pushes. GitHub API or
plan capability changes can make a mandatory control unsupported. Policy and external
state can diverge between a sync merge and the next apply. A partial API failure can
leave some settings strengthened and others unchanged.

Mitigations are mandatory: preflight checks must use observed check runs where GitHub
requires them; approval validation must reject solo lockout combinations; dependency
updaters are mutually exclusive; future branch auto-deletion is optional and must be
called out as destructive in the plan; applies emit before/after evidence and stop on
the first failed verification. The reconciler does not automatically roll back security
hardening after a partial failure because that could weaken protection. Recovery is an
idempotent roll-forward rerun; any deliberate weakening requires a separate reviewed
policy change and explicit administrator action.

**Follow-ups:**

1. Add the versioned policy schema, foundation defaults, repository example, and strict
   merge/validation tests without any write-capable adapter.
2. Add read-only GitHub discovery plus deterministic `plan` and `audit` output.
3. Add `apply` adapters, explicit target confirmation, read-back verification, and a
   compatibility wrapper; test all API calls at the process boundary.
4. Update README/usage/Template Sync ownership and migrate one downstream repository as
   a separate reviewed proof before broader rollout.
5. Reconsider Option 4 only after multiple repositories require centralized unattended
   convergence and an owner accepts the additional credential boundary.
