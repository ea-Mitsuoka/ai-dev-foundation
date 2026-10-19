---
id: adr-0009
title: ADR-0009 — Place project document singletons and collections
status: accepted
updated: 2026-07-26
---

# ADR-0009: Place project document singletons and collections by scope

| Field | Value |
| -- | -- |
| Status | accepted |
| Date | 2026-07-26 |
| Deciders | repository owner (approved 2026-07-26) |
| Author | Codex (AI agent) |
| Supersedes / Superseded by | Refines ADR-0006 |

## Context

ADR-0006 keeps project-owned documents directly under `docs/` while reserving
`docs/foundation/` for synchronized foundation material. It identifies
`docs/requirements.md` as the whole-project requirements contract and
`docs/requirements/<initiative>.md` as an initiative contract, but it does not state a
general rule for deciding between a file directly under `docs/` and a categorized
directory.

Without that rule, contributors can interpret the paired file and directory as
duplication, place every document at the top level, or introduce extra directory depth
for project-wide documents. The result is inconsistent discovery and a risk that the
same fact is maintained in both an overview and a subject document.

The rule must preserve ADR-0006's ownership boundary, work for small and large
repositories, and avoid creating empty project-owned scaffolding.

## Options considered

### Option 1: Keep the placement rule implicit

Continue listing known paths without defining a selection rule. This avoids migration,
but each new document category requires contributors to infer placement and makes the
`requirements.md` and `requirements/` pairing look accidental.

### Option 2: Put every project document directly under `docs/`

Use filenames such as `docs/requirements-authentication.md` and
`docs/architecture-data-flow.md`. This minimizes directory depth, but produces an
unbounded flat namespace and encodes categories inconsistently in filenames.

### Option 3: Put every project document below a category directory

Use paths such as `docs/requirements/project.md` or
`docs/requirements/README.md` even for a project-wide singleton. This is uniform, but
makes the primary project contracts less discoverable and adds directory depth when no
collection exists. A `README.md` name also does not identify the document contract by
itself.

### Option 4: Distinguish project-wide singletons from repeatable collections

Keep one project-wide document at `docs/<category>.md` and put independently maintained
subject documents at `docs/<category>/<subject>.md`. When both scopes exist, the file
and companion directory coexist. The singleton owns cross-subject facts and links to
the subject documents; it does not repeat their details.

## Decision

Adopt Option 4. A project-wide document that has one authoritative instance MUST use
`docs/<category>.md`. Independently maintained documents that can repeat by initiative,
component, audience, or operational subject MUST use
`docs/<category>/<subject>.md`.

When both scopes are required, the singleton file and companion directory MUST coexist.
The singleton MUST own project-wide facts and link to subject documents; subject
documents MUST own only their narrower facts. Authors MUST NOT repeat the same fact
between them. A project-owned directory or index MUST be created only when it contains
actual maintained project content, never as foundation scaffolding.

This decision does not change ownership: synchronized material remains below
`docs/foundation/`, while project-owned material remains directly below `docs/`.

## Consequences

**Positive:** the path communicates document scope; important project-wide contracts
remain easy to discover; categories scale without producing a flat namespace; and the
same rule explains `docs/requirements.md` alongside `docs/requirements/`.

**Negative:** a file and directory can share a base name, which some contributors may
initially find unusual; authors must decide whether content is project-wide or
subject-specific; and links must be explicit because no generated category index is
required.

**Migration and rollback:** existing correctly scoped documents do not move. A misplaced
document moves only when it is otherwise being maintained, with links updated in the
same PR. Rolling back restores the earlier implicit convention and requires no content
migration.

**Follow-ups:** add the binding selection rule to DOC-011, explain it in the project
documentation and requirements guides, and distribute the accepted rule through the
reviewed direct-parent Template Sync chain.
