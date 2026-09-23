---
id: adr-0025
title: ADR-0025 — Declare the direct parent with an adoption marker until activation
status: accepted
updated: 2026-09-24
---

# ADR-0025: Declare the direct parent with an adoption marker until activation

| Field | Value |
| -- | -- |
| Status | accepted |
| Date | 2026-09-24 |
| Deciders | repository owner (approved 2026-09-24) |
| Author | Claude Opus 5.5 (AI agent) |
| Supersedes / Superseded by | Amends ADR-0022 (phase 1 writes one more file; phase 3 removes it); supersedes none |

## Context

ADR-0021 lets an existing repository join the fleet with `adopt-child`, and ADR-0022
orders the work in three phases: phase 1 writes the transport (`.templatesyncignore`,
`template-sync.yml`, and `scripts/template_sync_auth.py`), phase 2 lets the bot Template
Sync pull request deliver the inherited tree, and phase 3 writes the manifest, lock, and
agent profile only after the tree is present.

The first real adoption, `ea-Mitsuoka/gc-project-move`, stopped at phase 2. The sync
workflow's first step runs `scripts/template_sync_auth.py`, which refuses with
`Template Sync requires a child inheritance manifest`. The script checks that the
workflow's source repository equals the parent declared in the child's manifest, so a
tampered workflow cannot pull from another repository. ADR-0022 forbids that manifest
until phase 3. The two rules cannot both hold, so phase 2 can never run.

The adopt-child test suite did not catch this. It simulated the bot sync with `git show`
instead of running the transport script, and its placeholder script was not the real one.

## Options considered

### Option 1: Do nothing

Adoption stays unusable for every repository. Rejected.

### Option 2: Write the manifest in phase 1

The existing check passes unchanged. But `make doctor` validates any manifest it finds and
fails without a lock, so the repository's CI is red for the whole of phase 2, and the
ADR-0022 ordering (metadata only after the tree) is broken.

### Option 3: Deliver the tree locally instead of through the bot

`adopt-child` copies the tree from the parent commit and phase 3 re-proves every byte. No
script change. But the bot-delivered provenance ADR-0021 chose is lost, and the delivery
pull request is human-authored, so the GR-020 hard limit applies to it without the
ADR-0005 exception; a real adoption exceeds it.

### Option 4: An adoption marker that only declares the parent

Phase 1 also writes `.github/inheritance/adoption.json`, whose only content is the direct
parent repository. `template_sync_auth.py` reads the parent from the manifest when one
exists and from the marker otherwise, and applies the same rule to either: the declared
parent must equal the workflow source. A repository holding both is refused, so a stale
marker cannot outlive activation. Phase 3 deletes the marker in the same change that
writes the manifest.

- Pros: the security property is unchanged; the ADR-0022 ordering holds (the marker is not
  inheritance metadata: no lock, no ownership, no agent inputs); CI stays green through
  phase 2 because `make doctor` validates only a manifest.
- Cons: one more file with a lifetime of a few pull requests; the transport script, which
  every descendant inherits, gains a second input.

## Decision

Option 4. During adoption, and only then, a repository MUST declare its direct parent in
`.github/inheritance/adoption.json` containing exactly
`{"schema_version": 1, "parent": {"repository": "<owner>/<name>"}}`. `adopt-child --prepare`
MUST write it; `adopt-child` activation MUST delete it in the same change that writes the
manifest. `scripts/template_sync_auth.py` MUST read the declared parent from the manifest
when present and from the marker otherwise, MUST refuse a repository that has both or
neither, and MUST keep refusing any source that differs from the declared parent. A test
MUST run the real transport script against a repository right after phase 1.

## Consequences

**Positive:**

- Adoption works end to end; phase 2 runs the real transport check rather than skipping it.
- Repositories that already have a manifest see no change in behavior.

**Negative:**

- Existing descendants receive a longer `template_sync_auth.py` with a code path they never
  take.
- A repository adopted before this decision cannot exist, so there is no migration; a
  repository that ran phase 1 under ADR-0022 alone (gc-project-move) must re-run phase 1
  to gain the marker and the new script.

**Follow-ups:**

- Implementation: marker constant and payload in `adopt-child`, deletion on activation,
  `prepared` requires the marker; `template_sync_auth.py` reads the marker; tests for both,
  including one that runs the real script after phase 1; Scenario C in
  `docs/foundation/guides/usage.md` and the inheritance README list the marker.
- gc-project-move: re-run phase 1 after the release, then phases 2 and 3.
