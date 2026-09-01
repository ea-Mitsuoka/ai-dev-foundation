---
id: ai-context-guide
title: AI Context Acquisition and Budgets
updated: 2026-09-01
---

# AI Context Acquisition and Budgets

This guide records how the foundation measures declared AI context. The binding
acquisition and quality fallback live in
[`.ai/README.md`](../../../.ai/README.md); accepted ADR-0012 records the decision.

## Measurement boundary

Measurements use UTF-8 bytes and whitespace-delimited words because they are stable
across model providers. They are regression proxies, not exact token counts.

| Measurement | Included | Excluded |
|-------------|----------|----------|
| Baseline | `AGENTS.md`, `CLAUDE.md`, `.ai/README.md`, the `.ai/guardrails.md` adapter, its canonical foundation guardrails, the agent profile, and every ordered profile input | Active handoff and runtime-owned instructions, including `.claude/README.md` |
| Declared task route | Baseline, selected skill, every file in its `reads` declaration | Task-specific sources found through bounded discovery |
| Conditional authority | One authority selected by an explicit trigger contract | Baseline and unrelated declared task routes |

Discovered sources are excluded from the ceiling because quality requires reading every
relevant source. A budget cannot justify omitting one.

## Recorded change

`requirements` remains the largest declared task route. `—` means the existing evidence
did not record that dimension for the stated point.

| State | Baseline bytes | Baseline words | `requirements` bytes | `requirements` words |
|-------|---------------:|---------------:|---------------------:|---------------------:|
| Before ADR-0012 route implementation | 18,565 | 2,625 | — | — |
| After PR #88 | 17,561 | 2,472 | — | — |
| Before requirements skill/template separation | — | — | 44,231 | 6,245 |
| After requirements skill/template separation | — | — | 41,298 | 5,776 |
| After entry-point deduplication | 16,553 | 2,323 | 40,290 | 5,627 |
| After Claude-specific routing | 16,329 | 2,288 | 40,066 | 5,592 |
| After AI inventory unification | 16,156 | 2,258 | 39,893 | 5,562 |
| After conditional project-document routing | 16,300 | 2,272 | 37,121 | 5,151 |
| After profile entry activation | 16,645 | 2,260 | — | — |
| After canonical guardrail separation | 17,222 | 2,329 | 38,097 | 5,209 |

ADR-0013 also changed the declared `documentation` route and introduced a separately
measured conditional authority:

| State | `documentation` bytes | `documentation` words | Conditional bytes | Conditional words |
|-------|----------------------:|----------------------:|------------------:|------------------:|
| Before conditional routing | 33,799 | 4,640 | — | — |
| After conditional routing | 31,273 | 4,257 | 4,368 | 572 |

The after measurements exclude `.ai/project-document-maintenance.md` from unrelated
requirements and documentation routes. A matching handoff, roadmap, root README,
onboarding, or inheritance trigger loads its complete 572-word authority.

Before ADR-0012, `docs/` contained approximately 17,424 words and the foundation ADR set
plus decision log contained approximately 9,458 words. They are now discovered through
indexes and search instead of declared as directory-wide reads.

## Enforced ceilings

| Metric | Ceiling |
|--------|--------:|
| Baseline bytes | 20,000 |
| Baseline words | 2,800 |
| Any declared task-route bytes | 46,000 |
| Any declared task-route words | 6,500 |

`make doctor` rejects a directory, glob, missing file, traversal path, redundant
baseline read, or missing mandatory authority in any skill route. When an agent profile
exists, it also validates schema version 1, `strengthen-only`, exact input order, bounded
file paths, and duplicates, then includes the profile and every input in baseline
measurement. It enforces the ceilings in the canonical foundation repository.
Descendants always receive structural validation and measurement output, but budget
excess is initially a warning because their protected entry documents can legitimately
differ. Exact canonical adapter and contract wording is validated only in the
foundation; descendants retain their protected local profile and project overlay. The
strict foundation validation also pins all obligations in `.claude/README.md`, although
that conditional runtime file is excluded from baseline measurement.

The validator also rejects a missing conditional authority, routing reference, or
required rule marker. It reports each conditional authority separately and does not add
that measurement to a declared route unless the skill lists the file as unconditional.

At 90% of either ceiling, `make doctor` emits a warning before the hard limit becomes a
failure. It also rejects an incomplete or stale foundation ADR/guide index because
bounded discovery depends on those indexes. A project-owned
`docs/development-handoff.md` remains outside the hard context budget, but receives a
warning when it exceeds 1,500 words, has an invalid or future `updated` date, or has not
been updated for more than 30 days. These handoff findings never justify skipping the
document.

Canonical guardrails still load once through their stable adapter. Compact routing and
inventory prose keeps the baseline below the soft-warning threshold without removing a
mandatory source, rule, marker, or discovery condition.

These changes removed no mandatory source and did not alter Claude Code obligations. A PR
that intentionally increases a ceiling states the reason and confirms that no narrower
route preserves completeness.

The baseline ceilings rose from 18,500 bytes and 2,600 words when GR-033 made untrusted
content a baseline-resident prohibition. No narrower route preserves completeness: SEC-050
defends the feature and bugfix work that reads issue text, dependency READMEs, and tool
output, so routing the rule to the security task alone would leave the exposed routes
undefended. The previous ceilings left 28 bytes under the 90% band, which had turned the
warning threshold into a hard gate against adding any guardrail; the new pair restores a
usable warning band rather than authorizing further growth.

**Update trigger:** update this guide and the budget constants or conditional contracts
together whenever the baseline file set, mandatory skill routes, conditional
authorities, measurement method, or ceiling changes.
