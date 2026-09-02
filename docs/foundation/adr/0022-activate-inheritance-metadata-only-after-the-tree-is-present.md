---
id: adr-0022
title: ADR-0022 — Activate inheritance metadata only after the inherited tree is present
status: accepted
updated: 2026-09-02
---

# ADR-0022: Activate inheritance metadata only after the inherited tree is present

| Field | Value |
|-------|-------|
| Status | accepted |
| Date | 2026-09-02 |
| Deciders | repository owner (approved 2026-09-02, PR #32) |
| Author | Claude Code (AI agent) |
| Supersedes / Superseded by | Partially supersedes ADR-0021 (the "What `adopt-child` writes" and "Copy and acceptance" clauses) |

## Context

ADR-0021 gives an existing repository a route into the fleet: a boundary PR writes the
inheritance metadata, the bot Template Sync copies the inherited tree, and `finalize-sync`
accepts the lock. Its implementation (PR #30) passed CI. A design review against the code
then showed that the **order** creates a state the fleet never otherwise permits.

Between the boundary PR and the first sync:

- `lock.json` names the source commit as accepted while none of its inherited content is
  present. `plan` inspects only commits after the lock, so it reports `up_to_date` for a
  repository that has nothing.
- `agent-profile.json` names `.ai/contracts/foundation/agent-entry.md`, which has not
  arrived. PR #30 hid this behind a new `validate_inheritance(require_agent_inputs=False)`.
- The first sync cannot start. A child's `template-sync.yml` preflight runs
  `python3 scripts/template_sync_auth.py` — itself an inherited file.

`bootstrap-child` has none of these problems because it *requires* the inherited tree to
be byte-identical to the parent commit before it writes any metadata. The invariant
"a lock implies its content is present" holds everywhere in the fleet except in the
ADR-0021 sequence. The 2026-09-02 catch-ups that ADR-0021 generalized from
(secure-ga4-bq-template, nextjs-saas-template) were lock *advances* on repositories that
already held the content; that difference was missed.

One further correction concerns a claim in PR #30, not the design. The ADR-0005 GR-020
exception for bot-authored sync PRs is implemented in each child's **own** policy —
`src/ci/pr_size_policy.py` in terraform-gcp-template, `scripts/pr-size-policy.sh` in
nextjs-saas-template — not in the inherited `scripts/pr_size_policy.py`. An adopted
repository has neither until it ports `pr-quality`, so its bot sync PR is not exempt from
GR-020; it is **unchecked**.

## Options considered

### Option 1: Keep ADR-0021's order and tolerate the window

The window is short and ends at the first sync. But `plan` and `fleet-report` misreport
during it, the profile is knowingly invalid, and the sync it waits for cannot run. A
sequence that needs a validation bypass to exist is the wrong sequence.

### Option 2: Copy the inherited tree in GR-020-sized human PRs, then activate

Proposed in review. It also avoids the false lock, and every batch is mechanically
verifiable. But a typical tree of 130–170 paths becomes seven to nine reviewed PRs, and
each one is a human-authored write of inherited content — the second transport ADR-0007
forbids and ADR-0021 was written to avoid.

### Option 3: Reorder ADR-0021 — transport first, bot copy, metadata last

Split `adopt-child` into two phases. `--prepare` writes only what the transport needs:
`.templatesyncignore` carrying the protect decisions, the `template-sync.yml` payload, and
`scripts/template_sync_auth.py` byte-identical to the parent — the single inherited file
the workflow depends on, delivered the way `finalize-sync` already accepts a manual port.
The bot PR then copies the tree. `--apply` requires every non-protected inherited path to
match the source commit — `bootstrap-child`'s own precondition — and only then writes
manifest, lock, agent profile, README payload, and archive.

No metadata exists until it is true. No validation bypass. Still one transport, still the
two collision outcomes, still no inherited writes by the command beyond the one file the
transport cannot start without.

## Decision

Adopt Option 3. The following replaces ADR-0021's "What `adopt-child` writes" and "Copy and
acceptance" clauses; every other ADR-0021 clause stands.

- **Phase 1 — `adopt-child --prepare`** MUST write only `.templatesyncignore` (with the
  resolved protections), the reviewed `.github/workflows/template-sync.yml` payload, and
  `scripts/template_sync_auth.py` byte-identical to the parent at the source commit. It
  MUST NOT write `manifest.json`, `lock.json`, `agent-profile.json`, the README, or the
  archive, and it MUST refuse while any collision is unresolved.
- **Phase 2 — the bot Template Sync PR** delivers the inherited tree. In a repository that
  has not yet ported `pr-quality`, this PR is **not checked against GR-020**; the adoption
  PR MUST say so and the reviewer MUST compare the PR's file list with the `pending`
  classification from phase 1.
- **Phase 3 — `adopt-child --apply`** MUST require every inherited path that is not
  protected to be byte-identical to the parent at the source commit, exactly as
  `bootstrap-child` does, and MUST refuse otherwise. Only then does it write the manifest,
  lock, agent profile, README payload, and archive. The lock is true at the moment it is
  written and full `validate_inheritance` MUST pass; the `require_agent_inputs=False`
  bypass MUST NOT exist.
- **Source commit.** Phase 3 MUST take the commit the sync actually delivered (the bot
  PR's `Direct-parent-source:` line) rather than the commit phase 1 inspected, because the
  parent's `main` may have advanced in between.
- **Idempotence.** Rerunning either phase after its PR MUST report `already_prepared` or
  `already_adopted` and change nothing.

## Consequences

**Positive:** the "lock implies content" invariant holds at every commit of an adopted
repository; `plan`, `fleet-report`, and `validate_inheritance` never lie during adoption;
the transport bootstraps itself; and the design still has one write path for inherited
content.

**Negative:** adoption remains three PRs, now with the small metadata PR last instead of
first; one inherited file is placed by hand in phase 1 (verified byte-identical, and later
confirmed `synchronized` by `finalize-sync`); and GR-020 is not machine-enforced on the
bot sync PR of an adopted repository — a review obligation the ADR now states rather than
a guarantee it pretended to have.

**Migration and rollback:** no repository has been adopted under ADR-0021, so nothing
migrates. PR #30 is reworked to this order and the `require_agent_inputs` keyword is
removed. Rollback is closing that PR; the accepted route remains ADR-0021 minus the two
superseded clauses, which is to say unusable until this or another ADR completes it.

**Follow-ups:** rework PR #30 (`--prepare` / `--apply`, content-match precondition, remove
the bypass, tests for both phases and both refusals, Scenario C rewritten in phase order);
record the accepted decision in `.ai/decision-log.md`.
