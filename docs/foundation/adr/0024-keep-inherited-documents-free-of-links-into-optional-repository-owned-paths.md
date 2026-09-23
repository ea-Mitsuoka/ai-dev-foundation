---
id: adr-0024
title: ADR-0024 — Keep inherited documents free of links into optional repository-owned paths
status: accepted
updated: 2026-09-23
---

# ADR-0024: Keep inherited documents free of links into optional repository-owned paths

| Field | Value |
| -- | -- |
| Status | accepted |
| Date | 2026-09-23 |
| Deciders | repository owner (approved 2026-09-23) |
| Author | Claude Fable 5.1 (AI agent) |
| Supersedes / Superseded by | Extends ADR-0004 and ADR-0014 (inheritance partition); supersedes none |

## Context

The inheritance contract partitions every path into *inherited* (Template Sync overwrites
it, `validate` requires it to match the parent) or *protected* (the descendant owns it and
may change or delete it). `inheritance-export.json` lists `profiles/`, `src/`, and `tests/`
as protected: a descendant receives them once, when the repository is created from the
template, and owns them afterwards.

Three inherited documents nevertheless depend on files inside those protected roots:

| Inherited document | Depends on | Kind of dependency |
| -- | -- | -- |
| `.ai/contracts/foundation/agent-entry.md` | `profiles/README.md` | the binding semantics of the canonical `make` targets |
| `docs/foundation/guides/usage.md`, `usage.ja.md` | `profiles/README.md` | relative link |
| `docs/foundation/guides/ai-instruction-files.ja.md` | `profiles/README.md`, `src/README.md`, `tests/README.md` | relative links, one per file, in two places each |

Two consequences follow. First, the canonical target contract, which hooks and CI in
every descendant depend on, is not itself inherited: a descendant that edits or deletes
`profiles/README.md` changes the contract text its own agents read, and the parent cannot
correct it. Second, a descendant that removes the example directories to keep its root
legible, which the partition explicitly permits, breaks the offline link check that every
descendant runs in CI, because the inherited guides still link into the removed paths.

The foundation already resolved the same problem once for the example module: the
portability test `test_optional_example_module_is_not_a_required_local_link` requires the
guide to mention `src/modules/catalog/MODULE.md` as a code span, not as a link, precisely
because a descendant may not have that file. The rule exists in one test but not as a
stated decision, so the three remaining dependencies were never brought under it.

An earlier proposal moved the example Makefiles and the example module under
`docs/foundation/examples/`. That would turn optional, deletable examples into inherited
payload that every descendant must carry and cannot remove, which inverts the goal.

## Options considered

### Option 1: Do nothing

Descendants keep `profiles/`, `src/README.md`, and `tests/README.md` forever, or accept a
red link check when they remove them. The canonical target contract stays editable by
each descendant.

- Pros: no change.
- Cons: the contract is not inherited; the partition's permission to delete is unusable
  in practice; the rule already applied to the example module is applied inconsistently.

### Option 2: Move the examples into the inherited tree

Relocate `profiles/*/Makefile`, `src/README.md`, `tests/README.md`, and the example module
under `docs/foundation/examples/` so the links stay valid everywhere.

- Pros: links resolve in every descendant without further rules.
- Cons: every descendant receives and must keep a Python example module and three
  Makefiles it does not use; deleting an inherited path is a `deletion_review` blocker in
  `finalize-sync`; the descendant's root gets no shorter, the clutter moves into `docs/`.

### Option 3: Inherit the contract, reference the examples without links

Move the binding parts of `profiles/README.md`, the canonical target table and the profile
rules, into a new inherited file `.ai/contracts/foundation/make-targets.md`. Point
`agent-entry.md` and the guides at it. Where an inherited document mentions an optional
repository-owned file (`profiles/README.md`, `src/README.md`, `tests/README.md`), use a
code span and say the file is repository-owned and may be absent, as the guide already
does for the example module. Leave `profiles/`, `src/`, and `tests/` protected and
optional. Pin the rule with a test over every inherited Markdown file.

- Pros: the contract every descendant depends on becomes inherited and uneditable by
  descendants; descendants may delete the examples without breaking any inherited
  document; the existing precedent becomes a stated rule with a mechanical check.
- Cons: `profiles/README.md` in the foundation shrinks to an example index and must
  point at the contract; descendants created before this decision keep their old copy of
  `profiles/README.md` until they remove or update it themselves.

## Decision

Option 3. The canonical `make` target contract MUST live in
`.ai/contracts/foundation/make-targets.md` and nowhere else; `agent-entry.md` MUST route
to it. An inherited Markdown document MUST NOT contain a relative link whose target is
under `profiles/`, `src/`, or `tests/`; it MAY mention such a file as a code span, and when
it does it SHOULD state that the file is repository-owned and may be absent. Reference
implementations and example layouts remain protected, optional, and deletable by the
descendant.

## Consequences

**Positive:**

- The contract text that hooks and CI depend on arrives with every sync and cannot drift
  per repository.
- A descendant can remove `profiles/`, the example module, and the layout READMEs with a
  repository-local pull request and a green link check.
- The rule is enforced mechanically by `scripts/tests/test_foundation_docs_portability.py`,
  so a future inherited document cannot reintroduce the dependency unnoticed.

**Negative:**

- Existing descendants keep a stale `profiles/README.md` whose contract section duplicates
  the inherited file until they trim it. The duplicate is repository-owned, so the
  foundation cannot remove it for them.
- The foundation's own `profiles/README.md` no longer carries the contract; readers who
  bookmarked it follow one link.

**Follow-ups:**

- Implementation: create `.ai/contracts/foundation/make-targets.md`; repoint
  `agent-entry.md`, `usage.md`, `usage.ja.md`, `ai-instruction-files.ja.md`; reduce
  `profiles/README.md` to an index; update the `Makefile` header comment; extend
  `test_agent_contract_profile.py` and `test_foundation_docs_portability.py`.
- Descendants: after the sync lands, each repository may trim its `profiles/README.md` to
  a pointer or delete `profiles/` outright. The foundation does not do this for them.
