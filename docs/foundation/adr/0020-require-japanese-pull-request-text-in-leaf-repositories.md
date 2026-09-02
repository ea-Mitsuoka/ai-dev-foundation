---
id: adr-0020
title: ADR-0020 — Require Japanese pull-request text in leaf repositories
status: accepted
updated: 2026-09-02
---

# ADR-0020: Require Japanese pull-request text in leaf repositories

| Field | Value |
|-------|-------|
| Status | accepted |
| Date | 2026-09-02 |
| Deciders | repository owner (approved 2026-09-02, PR #24) |
| Author | Claude Code (AI agent) |
| Supersedes / Superseded by | Extends ADR-0005; relies on ADR-0014 |

## Context

ADR-0005 draws the document-language boundary: foundation-owned instructions stay
English, and after template instantiation AI agents write project documents in Japanese.
It is silent about pull-request text. A PR in a project repository is therefore accepted
with an English body, and in practice most AI-authored PRs arrive that way while the
person who must review and approve them works in Japanese.

The repository owner requires Japanese pull-request bodies in the repositories that
*use* a template without being a template for anyone else. The foundation and the
template repositories keep English: their reviewers, their inherited content, and the
regression tests that pin that content (`test_foundation_document_language.py`) are
English by ADR-0005 and ADR-0008.

Three facts constrain the design:

- **No existing artifact says which repositories are leaves.** `agent-profile.json`
  has the same shape in a leaf and in a template that merely sits one level down;
  `inheritance-fleet.json` records lifecycle, not role; and GitHub's `is_template` flag
  is `false` on `terraform-gcp-template` and `nextjs-saas-template`, which are templates
  by construction. The scope needs a definition that is derivable offline from the tree.
- **`.ai/workflow.md` is protected downstream** (ADR-0014). A rule written there at the
  foundation never reaches a leaf. Only inherited paths — `.ai/documentation.md`, the
  `.ai/contracts/foundation/` contract, `.github/PULL_REQUEST_TEMPLATE.md`, `scripts/` —
  propagate, and `.github/workflows/` is protected everywhere and moves only by hand.
- **Automation writes English.** Template Sync, release-please, Renovate, and Dependabot
  generate PR bodies the rule cannot reasonably govern, and their PRs must keep merging.

## Options considered

### Option 1: Do nothing

Zero change. The review burden that motivates this ADR stays exactly where it is, and
each repository would have to invent its own local rule, drifting from the fleet.

### Option 2: Require Japanese pull-request text everywhere, templates included

One rule, no scope question. It contradicts ADR-0005 and ADR-0008 for the foundation and
the templates, whose inherited English content is what downstream repositories receive;
their reviewers would read Japanese PRs describing English artifacts. Large blast
radius, no benefit at the layer that most needs stable English.

### Option 3: Scope the rule to leaves, defined by the contract a repository publishes

A repository is a **template** when it publishes a contract root for others to inherit:
`.ai/contracts/foundation/` (the fleet root) or
`.ai/contracts/templates/<owner>/<its own name>/`. A repository that only *consumes*
contract roots is a **leaf**. The classification follows from `agent-profile.json` (the
project layer names the repository) plus the presence of that directory, so one inherited
script yields the same answer in CI and locally, and a leaf that later publishes a
contract becomes a template — and exempt — without touching the rule.

The consequence is stated rather than hidden: `secure-ga4-bq-template` publishes no
contract and has no children, so despite its name it is a leaf under this definition and
the rule applies to it. The repository owner confirmed this on 2026-09-02.

Enforcement is a `pr-quality` step calling an inherited script, so later judgement
improvements travel by ordinary Template Sync while the protected workflow line is ported
once.

### Option 4: Per-repository opt-in flag in the manifest

Each leaf declares `pr_language: ja` in `.github/inheritance/manifest.json`. Explicit,
but the manifest is protected, so every existing and future leaf needs a hand edit, and a
forgotten flag silently disables the rule. It also duplicates a fact — "this repository
is a leaf" — that the contract tree already states.

## Decision

Adopt Option 3.

- In a **leaf** repository, the body of every pull request authored by a human or an AI
  agent MUST be written in Japanese. The title keeps Conventional Commits: the type and
  scope remain English tokens, the summary is Japanese.
- **Template** repositories and the foundation are out of scope and keep ADR-0005's
  English rule for PR text.
- Pull requests authored by trusted automation — `github-actions[bot]`,
  `dependabot[bot]`, `renovate[bot]`, matched by exact login — are exempt.
- A human MAY exempt one pull request by applying the label `review:language-exception`
  and stating the reason in the body; the check then reports a warning and passes.
  Applying the label is a reviewer action, never the author's default.
- The check MUST measure prose, not presence: after removing HTML comments, fenced and
  inline code, URLs, table rows, and checklist markers, the remaining text MUST contain
  at least 60 characters of Japanese script (hiragana, katakana, CJK ideographs) and
  Japanese script MUST account for at least 30 % of all letters. A single Japanese
  character in an otherwise English body fails.
- The check is a required status in `pr-quality`, because GitHub rulesets have no rule
  that reads body language.
- The rule text lives only in inherited paths: DOC-001 in `.ai/documentation.md` beside
  the ADR-0005 rule, and the change protocol of the inherited agent-entry contract. The
  shared `.github/PULL_REQUEST_TEMPLATE.md` keeps its English section headings — they
  are the anchors the templates, the foundation, and the check rely on — and gains
  bilingual guidance comments that state the leaf rule.

## Consequences

**Positive:** reviewers of project repositories read PRs in their working language; the
rule is one fleet definition instead of per-repository folklore; the leaf/template
distinction becomes an explicit, testable concept the fleet lacked; bot operations are
unaffected; and once the workflow line is ported, every refinement of the judgement
arrives through ordinary sync.

**Negative:** existing leaves need a one-time manual port of the `pr-quality` step
because `.github/workflows/` is protected; a threshold-based check can reject a
legitimately terse Japanese body or admit a padded one, so the thresholds are a policy
knob rather than a proof; leaves whose manifests enumerate `scripts/` files one by one
(rather than the whole tree) receive the new script as unowned and must declare it,
which `finalize-sync` will flag; and non-Japanese contributors must ask a reviewer for
the exception label.

**Migration and rollback:** existing open PRs are not re-judged. Rollback is removing the
`pr-quality` step from each leaf's protected workflow and superseding this ADR; the
inherited script and rule text are then dead but harmless until the next sync removes
them.

**Follow-ups:** implement `scripts/pr_language_policy.py` with tests, the DOC-001 and
agent-entry wording, the bilingual template comments, the `review:language-exception`
label in `.github/labels.yml`, and the `pr-quality` step in this repository's `ci.yml`
as the reference; port that step into `secure-ga4-bq-template` and `secure-ai-controls`;
declare the script inherited where a manifest enumerates `scripts/` files; record the
accepted decision in `.ai/decision-log.md`.
