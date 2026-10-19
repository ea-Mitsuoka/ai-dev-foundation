# ADR-0006: Reserve a foundation documentation namespace

| Field | Value |
| -- | -- |
| Status | accepted |
| Date | 2026-07-18 |
| Deciders | repository owner (approved 2026-07-18) |
| Author | Codex (AI agent) |
| Supersedes / Superseded by | Refines ADR-0005 |

## Context

PR #39 added foundation-owned placement guidance at
`docs/requirements/README.md` while reserving `docs/requirements/<initiative>.md` for
downstream project documents. This mixes files with different owners in one directory.
It also places downstream project content below inherited foundation content, although
the downstream project is the primary subject of an instantiated repository.

The current Template Sync configuration excludes `docs/**` to protect downstream
content. Consequently, foundation-owned guidance and templates under `docs/` cannot
propagate automatically unless each file is selectively exempted. Adding individual
exceptions does not establish a durable ownership boundary for future foundation
documents.

The structure must keep binding agent rules in `.ai/`, task procedures in `.skills/`,
and downstream project documentation at conventional paths under `docs/`. It must also
make sync ownership understandable from the path alone and avoid overwriting downstream
documents.

## Options considered

### Option 1: Keep the mixed requirements directory

Retain foundation guidance at `docs/requirements/README.md`, downstream whole-project
requirements at `docs/requirements.md`, and downstream initiative requirements below
`docs/requirements/`. This requires no migration, but ownership remains ambiguous and
every future synchronized foundation document needs another ignore-file exception.

### Option 2: Put downstream project documents under `docs/project/`

Keep inherited foundation documents at their current paths and move downstream content
to `docs/project/requirements.md` and `docs/project/requirements/`. This separates
ownership but makes the downstream repository's primary documents subordinate to the
template implementation and changes conventional project paths.

### Option 3: Reserve `docs/foundation/` for inherited foundation documents

Move reusable foundation guidance and templates below `docs/foundation/`. Keep
downstream project documents at `docs/requirements.md` and
`docs/requirements/<initiative>.md`. Template Sync can protect `docs/**` by default and
allow only `docs/foundation/**`, creating one stable synchronization boundary.

This adds one directory level only to inherited support material. Binding rules and
procedures remain at `.ai/` and `.skills/`, so the new directory does not become a second
normative source.

### Option 4: Synchronize all of `docs/`

Remove `docs/**` from `.templatesyncignore`. This is operationally simple but permits
foundation updates to overwrite downstream requirements, architecture, ADRs, and
runbooks. The risk violates the ownership and local-first constraints accepted in
ADR-0004.

## Decision

Adopt Option 3. `docs/foundation/` MUST contain descriptive guidance and document
templates owned and synchronized by `ai-dev-foundation`. Downstream project documents
MUST remain directly under `docs/` at task-oriented paths such as
`docs/requirements.md` and `docs/requirements/<initiative>.md`.

The binding source for AI behavior remains `.ai/`, and executable task procedures remain
`.skills/`; documents under `docs/foundation/` MUST link to those sources instead of
duplicating their rules. Template Sync MUST continue to exclude `docs/**` by default and
MAY synchronize only the explicit `docs/foundation/**` namespace.

## Consequences

**Positive:** path ownership is visible without reading file contents; downstream
project documents keep the shortest and most conventional paths; foundation documents
gain one stable synchronization boundary; and future foundation templates do not require
per-file sync exceptions.

**Negative:** inherited guidance moves and all references must be updated; instantiated
repositories contain a dedicated foundation subtree; existing downstream repositories
must adopt the `.templatesyncignore` exception once because that file is protected from
sync; and migrating every existing foundation-owned document may require multiple PRs to
stay within GR-020.

**Migration and rollback:** first add `docs/foundation/` and update references, then move
the requirements placement guide and templates, then remove the old foundation-owned
paths. Every intermediate commit must keep links valid. Existing downstream repositories
adopt the new ignore exception in a reviewed migration PR before running Template Sync.
Rollback restores the previous paths and removes the namespace exception; downstream
project documents remain untouched in either direction.

**Follow-ups:** document the ownership boundary in DOC-010; migrate requirements guidance
to `docs/foundation/requirements.md`; migrate reusable templates to
`docs/foundation/templates/`; update every reference and update trigger; add a selective
Template Sync exception for `docs/foundation/**`; and define a phased plan for other
foundation-owned documents that remain outside the namespace.
