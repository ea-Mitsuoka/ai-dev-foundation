---
id: adr-0016
title: ADR-0016 — Gate private fleet automation on split credentials
status: accepted
updated: 2026-08-09
---

# ADR-0016: Gate private fleet automation on split credentials

| Field | Value |
| -- | -- |
| Status | accepted |
| Date | 2026-08-09 |
| Deciders | repository owner |
| Author | Codex (AI agent) |
| Supersedes / Superseded by | Refines the private-access boundary of ADR-0004, ADR-0007, and ADR-0015; supersedes none |

## Context

The maintained repository fleet is expected to move from public to private visibility.
The current local `fleet-audit` reads explicitly refreshed sibling worktrees and needs no
stored credential. A future scheduled fleet audit would instead need to read several
private repositories from one workflow. Each child Template Sync workflow also needs to
read its direct private parent after the visibility change.

The repository-scoped `GITHUB_TOKEN` cannot provide either cross-repository read, as
documented by GitHub's
[private multi-repository checkout guidance](https://github.com/actions/checkout#checkout-multiple-repos-private).
Adding one shared credential without an explicit boundary would create a new fleet-wide
trust relationship. A credential that can also write other repositories would
contradict ADR-0007 and ADR-0015, which keep reviewed Template Sync as the sole scheduled
write and PR transport and retain workflow and project ownership in each child.

Private GitHub-hosted Actions runs also consume the repository owner's included or paid
minutes under the
[GitHub Actions billing model](https://docs.github.com/en/billing/concepts/product-billing/github-actions).
A daily read-only audit is expected to be small, but it must not be enabled without a
measured runtime and an owner-approved monthly budget. The design must not use public
visibility as an authentication fallback or create an administrator bypass.

## Options considered

### Option 1: Keep every cross-repository operation local

Continue credential-free `make fleet-audit` and use maintainer-authenticated local
inheritance operations after privatization. This has the smallest remote trust boundary
and no scheduled Actions cost. It loses automatic early propagation because a private
parent cannot be read by the existing child workflow without additional authorization.

### Option 2: Store one fine-grained personal access token

Grant a fine-grained PAT read access to the selected fleet repositories and store it in
each workflow that needs a private source. This is simple to deploy, but the credential
is long-lived, tied to a person, copied across repositories, and dependent on manual
rotation and account lifecycle. Expanding it to target writes would increase its blast
radius further.

### Option 3: Configure a read-only deploy key for each inheritance edge

Give every child a distinct key for its direct parent. This creates a narrow edge-level
read boundary and avoids a personal token. It multiplies key creation, storage,
rotation, revocation, and incident response for every parent-child relationship, and a
central fleet audit would still need all keys.

### Option 4: Split a read-only GitHub App source token from child-local writes

Install one dedicated GitHub App only on explicitly maintained repositories. Generate a
short-lived
[installation token](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-an-installation-access-token-for-a-github-app)
with repository contents read access for parent checkout or fleet inspection. Keep
target branch and PR writes on the executing child's repository-scoped `GITHUB_TOKEN`.
A scheduled fleet audit, if later justified, uses only the read-only installation token
and never receives a target write token.

This adds App ownership, installation review, token generation, and billing monitoring,
but keeps identity lifecycle independent of a person and prevents one unattended token
from writing across the fleet.

## Decision

Adopt Option 4 as the only approved design for private cross-repository automation, but
do not enable it yet.

Until the private-access implementation in Issue #178 is separately approved and
verified, `make fleet-audit` MUST remain local, read-only, and credential-free. No
scheduled fleet audit may be added. Repository visibility MUST NOT be changed back to
public as an automation workaround.

Before a private parent-child edge enables Template Sync, the implementation MUST:

- install the dedicated source-reader App only on explicitly approved maintained
  repositories;
- grant the installation token no more than repository contents read access and the
  platform-required metadata read access;
- keep App key material only in an approved GitHub Actions secret or secret manager,
  document its distribution and rotation owner, and never place it in repository files;
- use that token only for the declared direct-parent read;
- use only the child's repository-scoped `GITHUB_TOKEN` for child content and PR writes;
- keep source-read and target-write inputs distinct and reject a shared token;
- preserve exact source provenance, direct-parent order, protected paths, human review,
  and the prohibition on auto-merge; and
- fail closed when authorization, repository identity, or source provenance cannot be
  proven.

A scheduled fleet audit MAY be proposed after private Template Sync succeeds on one
bounded parent-child pilot. Its approval requires measured billable runtime, an explicit
monthly Actions-minute budget, an installation and revocation owner, no artifact or
cache retention without a separate need, and proof that the audit has no write
permission or write-capable API path.

A fleet-wide write token, administrator token, broadly scoped or long-lived personal
token, or credential shared between source and target roles MUST NOT be introduced by
this decision.

## Consequences

**Positive:**

- Private source access does not require public visibility or an administrator bypass.
- A compromised source credential cannot modify a parent, child, workflow, pull request,
  or governance setting.
- Child writes remain bounded by the existing repository-specific workflow permission.
- The local fleet audit remains available without CI credentials or Actions charges.
- A pilot and measured budget gate prevent speculative scheduled infrastructure.

**Negative:**

- Private scheduled propagation cannot continue until the App is approved, installed,
  and tested.
- GitHub App ownership, installation scope, token issuance, and revocation add an
  operational dependency.
- Private GitHub-hosted runs consume included or paid Actions minutes.
- The source and target token separation requires a compatibility check and may require
  a bounded Template Sync workflow change.
- Organizations with installation restrictions need their administrators to approve the
  App; there is intentionally no fallback credential.

Migration is expand-first. Document and test the distinct token interfaces, validate one
direct parent-child pilot without changing visibility as a workaround, then migrate one
edge at a time. Only after the fleet is private and Template Sync is stable may the
read-only scheduled audit be evaluated. Rollback removes or suspends the App installation,
disables affected schedules, and returns to local `fleet-audit` and reviewed local
inheritance operations; it does not weaken repository visibility or governance.

**Follow-ups:** Track the private-access implementation, pilot evidence, billing budget,
and any later scheduled-audit proposal in
[Issue #178](https://github.com/Yukihide-Mitsuoka/ai-dev-foundation/issues/178).
