---
id: adr-0014
title: ADR-0014 — Separate inherited agent contracts from project overlays
status: accepted
updated: 2026-07-29
---

# ADR-0014: Separate inherited agent contracts from project overlays

| Field | Value |
| -- | -- |
| Status | accepted |
| Date | 2026-07-29 |
| Deciders | repository owner (approved 2026-07-29) |
| Author | Codex (AI agent) |
| Supersedes / Superseded by | Extends ADR-0004 and ADR-0007 |

## Context

ADR-0004 assigns every synchronized path to either the direct parent or the current
repository, and ADR-0007 keeps protected paths out of the transitional Template Sync
transport. That prevents unsafe overwrites, but several protected files currently mix
both kinds of content:

- `CLAUDE.md` combines the reusable task protocol with project identity and stack facts;
- downstream copies of foundation skills combine the reusable procedure with
  repository-specific placement or verification rules;
- child manifests enumerate individual shared files, so each new foundation authority
  requires a fleet-wide manifest edit; and
- workflow files combine repository-owned triggers and permissions with reusable
  implementation steps.

The parent range from `ada82ed598a68d36d6419985a64e31e876996bd8` to
`caae8d9f75b88de785bcaddce164b1410ba6dcec` made this cost concrete. The ordinary
Template Sync delta was deterministic, but `nextjs-saas-template` and `repchat` still
needed separate preparation work for protected contracts and root README ownership.
The README correction is migration debt under ADR-0011. Repeatedly porting shared
clauses in `CLAUDE.md` and skill bodies is a structural ownership problem.

Constraints are: every propagation remains a reviewed direct-parent PR; project
identity, project ADRs, release history, workflow permissions, and repository-owned
rules must not be overwritten; agents must have valid instructions before running a
generator; context acquisition must remain bounded; no remotely mutable code may enter
CI; and every migration step must keep each repository green and releasable.

## Options considered

### Option 1: Do nothing

Continue protecting mixed-ownership files and manually port every relevant parent
change. This is operationally familiar and has no migration cost. It permanently makes
safe propagation depend on repository-by-repository interpretation, however, and the
cost grows with both the number of children and the frequency of foundation changes.

### Option 2: Generate complete local contracts

Store reusable and project fragments separately, then generate `CLAUDE.md`, skill files,
and workflow bodies in each child. This can produce exact local artifacts and makes
composition testable. It also creates a bootstrap problem because agents read
`CLAUDE.md` before generation, adds generated-file drift and merge noise, and requires a
write-capable composition step in every propagation PR.

### Option 3: Keep current paths and add include-style overlays

Make the existing files generic and have them load protected project fragments. This is
simple and reversible for `CLAUDE.md` and skills. It does not give new shared
authorities a stable directory ownership root, so manifests and ignore rules still grow
one file at a time. Intermediate templates also lack an explicit namespace for
family-level extensions.

### Option 4: Use inherited contract namespaces with protected overlays

Separate content by ownership and execution boundary:

- foundation-owned agent rules and skill bodies live under inherited directory roots;
- stable, foundation-owned entry files load those contracts plus explicit protected
  project overlays;
- an intermediate template may publish an owner-qualified template overlay for its
  direct children;
- reusable workflow implementation lives in synchronized local scripts or composite
  actions, while the executable workflow caller retains local triggers and permissions;
  and
- foundation decisions remain in synchronized foundation ADRs instead of being copied
  into each project's decision log.

This requires a staged path migration and deterministic routing tests, but new files
inside an established inherited root no longer require one manifest change per child.

## Decision

Adopt Option 4.

The implementation MUST establish these ownership layers:

1. **Foundation contract:** synchronized, directory-owned agent authorities and skill
   bodies. Child manifests inherit the directory roots rather than enumerating their
   files.
2. **Template overlay:** an optional owner-qualified, direct-parent export for rules a
   stack or product template deliberately passes to its children. The exporting
   template owns this path against its parent; its direct children inherit it.
3. **Project overlay:** protected repository identity, stack facts, local exceptions,
   and optional skill extensions. This layer is never overwritten by Template Sync.

`CLAUDE.md`, `AGENTS.md`, and the task-skill entry files MUST become small
foundation-owned adapters with no project identity. They MUST load the inherited
contract first, declared template overlays in parent-to-child order second, and the
protected project overlay last. The ordered inputs MUST be explicit in a small local
profile; agents MUST NOT recursively discover or load arbitrary directories.
Later layers may specialize or strengthen earlier requirements but MUST NOT weaken a
foundation MUST, guardrail, or security control. The validator MUST reject an authority
order that permits a project overlay to supersede those controls.

Shared workflow behavior SHOULD move into synchronized repository-local scripts or
composite actions. Protected `.github/workflows/*.yml` callers retain events,
permissions, secrets, and environment selection. A mutable remote workflow reference
MUST NOT replace reviewed local propagation. Changes to triggers or permissions remain
an explicit manual port because they change the repository security boundary.

`docs/foundation/adr/` is the sole downstream record of foundation architectural
decisions. A downstream `.ai/decision-log.md` MUST record only decisions owned by that
repository or its explicitly exported template overlay; it MUST NOT duplicate proposed
or accepted foundation ADR entries. Direct-parent source and accepted commit evidence
remain in the inheritance lock and sync PR.

The inheritance validator and regression tests MUST report:

- parent-owned changes that synchronize without a child edit;
- protected project paths that remain unchanged;
- template overlays loaded in declared order;
- stale or missing contract/profile references; and
- any parent change that still requires a manual child port, including the reason.

The target operating condition is not zero manual work. It is that ordinary
foundation-owned content changes produce complete reviewable sync PRs, while manual
ports are limited to deliberate changes in project semantics or security boundaries.

## Consequences

**Positive:**

- Shared contract and skill changes stop requiring repeated edits to protected copies.
- New files within an inherited directory root propagate without fleet-wide manifest
  enumeration.
- Project identity and stack-specific behavior remain locally reviewable.
- Intermediate templates can export family rules without modifying the global
  foundation contract.
- Thin workflow callers preserve least privilege while reusable implementation can
  synchronize normally.
- Project decision logs become smaller and stop duplicating synchronized evidence.

**Negative:**

- The migration temporarily supports old and new paths and adds routing validation.
- Agents read more than one physical file for some task types, although the ordered
  list remains bounded and explicit.
- Each new template layer needs a one-time owner-qualified overlay declaration in its
  direct children.
- Workflow event and permission changes still require manual review and porting.
- A malformed project profile could make instructions incomplete, so validation must
  land before consumers migrate.

Migration uses expand, migrate, then contract:

1. Add the new inherited roots, protected profile schema, ordered loader contract, and
   read-only validation without changing current entry behavior.
2. Migrate `ai-dev-foundation`, then each direct child, then each grandchild. At every
   hop, compare the accepted lock-to-source range and keep both old and new entry paths
   valid.
3. Move reusable workflow steps behind stable protected callers.
4. Stop appending foundation ADRs to project decision logs.
5. Remove compatibility copies only after fleet validation reports no consumer.

Rollback keeps the compatibility entry paths and removes the new profile reference in a
normal PR. No repository setting, accepted lock, project document, or release artifact
is changed by rollback.

**Follow-ups:**

1. Specify the directory and profile schemas and add validator fixtures for a direct
   child and a multi-level child.
2. Migrate one direct child as a proving slice before broad rollout.
3. Add a fleet report that classifies synchronized, protected, and manually ported
   parent changes.
4. Document the remaining intentional manual boundaries in the inheritance runbook.
