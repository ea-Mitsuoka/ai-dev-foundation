---
id: adr-0011
title: ADR-0011 — Own the root README in the current repository
status: accepted
updated: 2026-07-28
---

# ADR-0011: Own the root README in the current repository

| Field | Value |
| -- | -- |
| Status | accepted |
| Date | 2026-07-28 |
| Deciders | repository owner (approved 2026-07-28) |
| Author | Codex (AI agent) |
| Supersedes / Superseded by | Refines ADR-0006 and ADR-0009 |

## Context

The root `README.md` is copied when a repository is created from a template. Template
Sync later protects that path, so the copied file can continue to describe the parent
instead of the current repository. The current rules state that `README.md` describes
the project, but they do not identify its owner or define how to preserve a copied
parent README.

In multi-level inheritance, replacing the copied file without a preservation rule loses
parent context. Keeping every README at the root is impossible because the path is a
singleton. Reusing one archive filename also allows different ancestors to overwrite
each other.

The rule must keep the current repository identifiable at the root, preserve inherited
content, support multiple owners and ancestors, remain compatible with the reviewed
Template Sync boundary, and avoid an immediate fleet-wide migration.

## Options considered

### Option 1: Keep ownership implicit

Continue protecting `README.md` and let each repository decide whether to replace a
copied parent README. This requires no migration, but agents cannot determine whether
the root file is current, and parent content is preserved inconsistently.

### Option 2: Replace the parent README without preserving it

Require each child to write its own root README and delete the copied parent file. This
keeps the root accurate with little structure, but removes inherited context and does
not meet the preservation requirement.

### Option 3: Preserve parent READMEs in the synchronized foundation namespace

Move copied files below `docs/foundation/readmes/`. This identifies them as inherited
material, but `docs/foundation/**` is explicitly synchronized under ADR-0006. A local
archive there would have conflicting ownership and could be changed by Template Sync.

### Option 4: Preserve parent READMEs in a protected inheritance archive

Keep only the current repository README at the root. Move each copied parent README to
`docs/inheritance/readmes/<owner>/<repository>.md`, with repository provenance in YAML
frontmatter. The existing `docs/**` Template Sync exclusion protects this
repository-owned inheritance record without another local ignore-file migration.

The path distinguishes archived inheritance records from both synchronized foundation
documentation and active project documentation. Owner and repository path components
prevent collisions across multiple inheritance levels.

## Decision

Adopt Option 4.

The root `README.md` MUST describe and be maintained by the current repository. It MUST
contain an invisible ownership marker in the form
`<!-- repository-readme-owner: owner/repository -->`. The marker MUST match the current
GitHub repository. `ai-dev-foundation` therefore keeps its own README at the root with
`Yukihide-Mitsuoka/ai-dev-foundation` as the owner.

When an agent finds that the root marker or the README subject identifies an ancestor,
it MUST preserve the inherited file at
`docs/inheritance/readmes/<owner>/<repository>.md` before replacing the root file. Path
components MUST be lowercase. The archived file MUST record the full source repository
and source commit in YAML frontmatter, retain the source language and substantive
content, and repair relative links for its new location. If the exact source commit
cannot be established from inheritance provenance, the file MUST state `unknown`; an
agent MUST NOT invent it.

For example, after `terraform-gcp-template` replaces a copied foundation README, the
ownership layout is:

```text
README.md
docs/inheritance/readmes/yukihide-mitsuoka/ai-dev-foundation.md
```

The root marker is
`<!-- repository-readme-owner: Yukihide-Mitsuoka/terraform-gcp-template -->`. The
archive frontmatter records
`source-repository: Yukihide-Mitsuoka/ai-dev-foundation` and the accepted 40-character
`source-commit`. An existing archive MUST be reviewed before replacement; different
ancestor versions MUST NOT be discarded silently.

In a multi-level chain, each repository performs the same operation for its direct
parent. Existing ancestor archives remain at their owner-qualified paths. The result is
one current-repository README at the root and at most one preserved README per ancestor
repository.

Archived READMEs are historical records, not routine task context. Agents MUST NOT load
or summarize `docs/inheritance/readmes/**` during normal intake or general documentation
discovery. They read a snapshot only while migrating or reviewing root README ownership,
or when tracing inheritance provenance. The automated audit examines the ownership
marker locally and sends no README content to an AI.

This rule applies during new-repository initialization. Existing repositories do not
require a bulk migration. When an agent reads or changes the root README, onboarding
documentation, or inheritance configuration and discovers a mismatch, it MUST repair
the ownership in the same PR when the change remains within GR-020; otherwise it MUST
open a migration issue.

## Consequences

**Positive:** the root README always identifies the current repository; inherited
README content is retained; provenance and collision handling are deterministic; and
legacy repositories can migrate when relevant work exposes the mismatch.

**Negative:** every current root README needs an ownership marker; archived links may
need updates; `docs/inheritance/` adds a repository-owned administrative documentation
namespace; and archived snapshots do not receive later parent README updates
automatically.

**Migration and rollback:** implementation first adds the marker and binding rule to
`ai-dev-foundation`, then adds a non-destructive audit. New repositories apply the rule
during initialization. Existing repositories migrate only when an agent detects a
mismatch. Rollback removes the marker requirement; preserved files remain until a
separate reviewed change decides their disposition.

**Follow-ups:** add the binding README ownership rule to `.ai/documentation.md`; explain
the archive in the project documentation guide and foundation index; add the foundation
root marker; and add regression tests that detect a mismatched marker without moving
downstream files automatically.
