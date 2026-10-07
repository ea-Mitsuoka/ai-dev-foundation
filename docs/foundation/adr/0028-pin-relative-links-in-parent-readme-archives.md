---
id: adr-0028
title: ADR-0028 — Pin relative links in parent README archives to the source commit
status: accepted
updated: 2026-10-07
---

# ADR-0028: Pin relative links in parent README archives to the source commit

| Field | Value |
| -- | -- |
| Status | accepted |
| Date | 2026-10-07 |
| Deciders | repository owner (approved 2026-10-07, PR #83) |
| Author | Claude Opus 5.5 (AI agent) |
| Supersedes / Superseded by | Amends ADR-0011 (archive content rule); supersedes none |

## Context

ADR-0011 preserves the parent's root README at
`docs/inheritance/readmes/<owner>/<repository>.md` before a child replaces it, and
`bootstrap-child` and `adopt-child` write that archive from a reviewed payload. The parent
README links to repository paths relative to the repository root, such as
`[.ai/](.ai/)`. In the archive those links resolve relative to
`docs/inheritance/readmes/<owner>/`, where none of the targets exist. ADR-0011 records
only that "archived links may need updates".

Measured on 2026-10-07 against the ai-dev-foundation archives in three children:

| Repository | Relative links | Broken | How the links were handled |
| -- | -- | -- | -- |
| writing-style | 27 | 0 | `../../../../` prepended by hand |
| gc-project-move | 27 | 0 | `../../../../` prepended by hand |
| shared-account-retirement | 27 | 27 | copied unchanged; its protected `ci.yml` excludes the archive from link-check |

The `../../../../` rewrite is not written in any guide or ADR. It also changes what the
links mean: they point to the child's current files, not to the parent's files at the
archived commit, and a link to a path the child does not have (for example `profiles/`
in an adopted repository) is still broken. The foundation `link-check` job runs lychee
with `--offline`, so it checks local links and never fetches external URLs.

## Options considered

### Option 1: Do nothing

- Pros: no change.
- Cons: each child repeats the manual rewrite or excludes the archive from link-check; an
  excluded archive hides real breakage.

### Option 2: Document the `../../../../` rewrite

- Pros: matches the two children that already pass link-check.
- Cons: links show the child's current files instead of the archived parent state; links
  to paths the child lacks stay broken; the rule depends on the archive's directory depth.

### Option 3: Rewrite relative links to URLs pinned to the source commit

Each relative link becomes
`https://github.com/<source-repository>/blob/<source-commit>/<path>`, or `/tree/` for a
directory.

- Pros: every link shows the parent at the archived commit, which is what the archive is;
  no link depends on the child's tree; offline link-check skips the URLs.
- Cons: links leave the repository; for a private parent only readers with access can open
  them; a typo in a URL is no longer caught by offline link-check.

## Decision

Option 3.

- **Content rule.** In a parent README archive, every relative link target MUST be
  rewritten to `https://github.com/<source-repository>/blob/<source-commit>/<path>`, using
  `/tree/` instead of `/blob/` when the target is a directory at the source commit.
  `<source-repository>` and `<source-commit>` are the values in the archive frontmatter.
  Links that already carry a scheme and in-page anchors (`#…`) MUST stay unchanged.
- **Validation.** `bootstrap-child` and `adopt-child` MUST refuse an archive payload that
  still contains a relative link target, in Markdown inline links or reference
  definitions.
- **Generation.** `scripts/template_inheritance.py` MUST provide a command that writes the
  archive payload from the parent at the source commit: the frontmatter, the README, and
  the rewritten links, so no one rewrites links by hand.
- **Existing archives.** Validation applies only when a payload is written. Archives already
  committed in children are unchanged and need no migration.

## Consequences

**Positive:**

- New archives pass link-check without an exclusion and without depending on the child's
  tree.
- An archive is a faithful record: its links show the parent as it was at the archived
  commit.
- The payload is generated, which removes one hand-written step from bootstrap and
  adoption.

**Negative:**

- Readers without access to a private parent cannot open the archived links.
- Offline link-check no longer verifies archive links; a target is correct by construction
  only when the generator writes it.
- Existing archives keep the `../../../../` form, so the fleet carries two forms until a
  child regenerates its archive.

**Migration and rollback:** no migration. Rolling back removes the validation and the
generator; archives written in between stay valid Markdown with external links.

**Follow-ups:**

- Implement the generator and the validation in `scripts/template_inheritance.py`, with
  tests.
- Update the bootstrap and adoption steps in `docs/foundation/guides/usage.md` and the
  troubleshooting page.
- shared-account-retirement: regenerate its archive and remove the link-check exclusion
  from its `ci.yml`.
