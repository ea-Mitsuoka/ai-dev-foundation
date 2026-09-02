---
id: adr-0021
title: ADR-0021 — Adopt the foundation into an existing repository
status: proposed
updated: 2026-09-02
---

# ADR-0021: Adopt the foundation into an existing repository

| Field | Value |
|-------|-------|
| Status | proposed |
| Date | 2026-09-02 |
| Deciders | repository owner |
| Author | Claude Code (AI agent) |
| Supersedes / Superseded by | Extends ADR-0004, ADR-0007, ADR-0015; relies on ADR-0005, ADR-0020 |

## Context

Every documented entry into the fleet begins with GitHub "Use this template"
(`docs/foundation/guides/usage.md`, Scenario A). `bootstrap-child` then writes the
inheritance metadata — manifest, lock, agent profile, `.templatesyncignore` — plus three
reviewed project payloads and the parent README archive. It writes nothing else, and it
refuses to run unless the child's inherited tree is already byte-identical to the parent
commit (`child inherited template copy does not match exact parent commit`). That
precondition is what "Use this template" provides.

An existing repository — one with its own history, code, CI, and documentation — can never
meet it. So today such a repository has no supported route into the foundation, although
the repository owner wants one.

Three facts constrain any answer:

- **`bootstrap-child` does not copy inherited content.** The open questions for an
  existing repository are therefore *who performs the first copy* (130–170 inherited paths
  in current children) and *what happens to existing files that collide* with inherited
  paths — `.editorconfig`, `SECURITY.md`, `AGENTS.md`, `.pre-commit-config.yaml`,
  `renovate.json`, `.github/labels.yml`, `scripts/`, and similar.
- **The manifest is a partition.** A path is inherited or protected, never both
  (`_reject_overlaps`; ADR-0004: "A path cannot be both inherited and protected"). There is
  no way to keep a child's copy of an inherited path *and* keep receiving updates to it.
- **Template Sync is the sanctioned transport and carries the size exception.**
  ADR-0004 and ADR-0007 make the bot's `chore/template_sync_*` PR the one write path for
  inherited content, and ADR-0005 grants only that bot-authored PR the GR-020 hard-limit
  exception. A human-authored PR carrying 150 files fails `pr-quality`.

On 2026-09-02 the fleet exercised, twice, the sequence this ADR generalizes: a small
human PR declared boundaries, the bot sync then delivered the content under ADR-0005, and
`finalize-sync` accepted the lock (secure-ga4-bq-template #18 → #19,
nextjs-saas-template #16 → #14).

## Options considered

### Option 1: Do nothing

Existing repositories stay outside the fleet, or are migrated by hand with no provenance
record. Each such repository invents its own boundary, drifts, and cannot be audited by
`fleet-report`.

### Option 2: Recreate the repository from the template and move the code in

Preserves every foundation invariant, but discards the repository's history, issues,
pull requests, releases, and settings — or forces a second identity migration of the kind
ADR-0019 has just finished. Unacceptable for a repository that is already in use.

### Option 3: Copier, `git subtree`, or merging the parent as a remote

Each creates a second update path beside Template Sync. ADR-0007 requires exactly one
transport per path and proof that no change can be inherited twice; none of these can
give it, and each ignores the manifest partition entirely.

### Option 4: An `adopt-child` command that generates, classifies, and applies the whole tree

The proposal under review: a read-only classification pass (identical / safe-add /
project-owned / conflict-review / unsupported), then `--apply` writes the metadata **and
the inherited tree** in one adoption PR.

It is the right diagnosis with two defects. "Project-owned" as a resolution for a
collision on an inherited path is not expressible — the partition forces the path into
`protected_paths` and out of transport, which is a decision to *stop inheriting it*, not
to protect it. And the `--apply` step that copies the inherited tree is itself a second
transport for inherited content, carried by a human PR that the GR-020 hard limit blocks
and that ADR-0007 asks us not to create.

### Option 5: An `adopt-child` command that generates and classifies only; the bot copies

`adopt-child` emits exactly what `bootstrap-child` emits — manifest, lock, agent profile,
`.templatesyncignore`, the three payloads, the README archive — **without** requiring the
inherited tree to match, and adds a read-only report of every existing file that collides
with an inherited path. Adoption then proceeds in three reviewed steps, each already
implemented:

1. **Boundary PR** (human, small): the generated metadata with every collision resolved.
2. **Bot sync PR**: `TEMPLATE_SYNC_ENABLED=true`; Template Sync copies the inherited tree
   under the ADR-0005 exception and `.templatesyncignore` keeps every protected path out.
3. **`finalize-sync --apply`** on that branch: proves the 130–170 paths byte-identical,
   reports the protected workflows still to be ported, and fixes the lock (ADR-0015).

No new transport, no new size exception, and the collision decisions live in the two
files the fleet already treats as the contract, so a rerun of `adopt-child` derives the
same classification from them.

## Decision

Adopt Option 5.

- **Direct parent.** The adopting repository MUST select its direct parent by
  `docs/foundation/guides/usage.md` §1 — the closest maintained template whose exported
  contract applies to its primary deliverable now. It MUST NOT bypass an intermediate
  template (ADR-0004). `adopt-child` reads the parent's `inheritance-export.json` exactly as
  `bootstrap-child` does.
- **What `adopt-child` writes.** Only the `bootstrap-child` set: `manifest.json`,
  `lock.json`, `agent-profile.json`, `.templatesyncignore`, the reviewed payloads
  (`README.md` with the ADR-0011 ownership marker, `.ai/project/agent-overlay.md`,
  `.github/workflows/template-sync.yml`), and the parent README archive. It MUST NOT write
  any inherited path, and it MUST refuse to run on the default branch or a dirty worktree.
- **Classification.** The read-only plan MUST list every existing child path that lies
  under an inherited root and differs from the parent blob at the source commit
  (`collision`), every such path that already matches (`identical`), and every inherited
  path absent from the child (`pending`). It MUST stop on anything it cannot classify:
  symlinks, non-regular files, nested Git repositories, or a path under both an inherited
  and a protected root.
- **Collision resolution has exactly two outcomes**, and `--apply` MUST refuse while any
  collision is unresolved:
  - *accept the parent* — the child's copy is left for the bot sync to overwrite; an
    author who wants the old content keeps it under a project-owned name; or
  - *protect the child's copy* — the path moves from `inherited_paths` to
    `protected_paths` and into `.templatesyncignore`. This is a decision to stop
    inheriting that path; parent updates to it will not arrive until the decision is
    reversed. Because the fleet's manifests and ignore files differ per repository, the
    declaration is per repository, never inherited.
- **Copy and acceptance.** The first copy of inherited content MUST arrive through the
  bot Template Sync PR, and the lock MUST advance only through `finalize-sync` on that
  branch (ADR-0004, ADR-0015). `adopt-child` sets the lock to the source commit so the
  first sync covers `lock → source` as an ordinary range.
- **Consequences to state in the adoption PR.** An adopted repository publishes no
  contract root, so it is a **leaf** under ADR-0020: its PR bodies MUST be Japanese and
  the `pr-quality` language step MUST be ported into its protected `ci.yml`. Every other
  protected workflow the parent ships (`ci.yml`, `security.yml`, `codeql.yml`,
  `labels-sync.yml`, `scorecard.yml`, `release.yml`, …) never arrives by sync; the
  adoption PR MUST list which of them will be ported by hand and which existing workflows
  remain. `finalize-sync` reports these as `pending_manual_port`.
- **Idempotence.** Rerunning `adopt-child` after the boundary PR MUST report
  `already_adopted` and change nothing, because every decision it depends on is in the
  manifest and ignore file it generated.

## Consequences

**Positive:** an existing repository joins the fleet with its history intact and a full
provenance record from the first commit; the route reuses three commands that already
exist and were exercised on 2026-09-02 rather than adding a transport; the partition
constraint becomes an explicit, reviewable decision per colliding file instead of a
surprise; and `fleet-report` sees the repository from day one.

**Negative:** adoption is three PRs, not one, and the middle one is bot-authored with no
checks until a human pushes to it; every collision resolved as "protect" is a permanent
manual-port obligation, and a repository with many of them inherits little of value;
protected workflows are still a hand port and remain the main source of drift
(ADR-0019 follow-ups showed exactly this with `contents: read`); and a repository whose
existing layout overlaps heavily with `scripts/`, `docs/foundation/`, or `.ai/` may find
the honest answer is Option 2 after all.

**Migration and rollback:** nothing changes for repositories already in the fleet.
Rolling back an adoption is deleting the four metadata files, the sync workflow, and the
archive, and reverting the sync PR; the repository's own files are never modified by
`adopt-child`, so no restore is needed for them.

**Follow-ups:** implement `adopt-child` in `scripts/template_inheritance.py` with tests
that run in root, template, and leaf shapes (the ADR-0020 lesson); document the
three-step route as Scenario C in `docs/foundation/guides/usage.md`; extend the
inheritance README; record the accepted decision in `.ai/decision-log.md`.
