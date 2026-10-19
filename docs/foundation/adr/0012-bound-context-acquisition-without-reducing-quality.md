---
id: adr-0012
title: ADR-0012 — Bound context acquisition without reducing quality
status: accepted
updated: 2026-07-29
---

# ADR-0012: Bound context acquisition without reducing quality

| Field | Value |
| -- | -- |
| Status | accepted |
| Date | 2026-07-29 |
| Deciders | repository owner (approved 2026-07-29) |
| Author | Codex (AI agent) |
| Supersedes / Superseded by | Refines the routing model in ADR-0002 |

## Context

The foundation routes each task to a small set of rules and one skill, but some route
declarations still name complete directories. On 2026-07-29, `docs/` contains
approximately 17,424 whitespace-delimited words, while the foundation ADR set and
append-only decision log contain approximately 9,458 words. Both sets grow over time.
Reading every file adds context that is unrelated to most tasks.

The mandatory entry documents also contain approximately 2,625 words. `CLAUDE.md`
repeats summaries of domain rules that the routing table requires an agent to read from
their authoritative `.ai/` files. Review and security skills can also name guardrails
that the baseline already loaded.

Reducing context must not permit an agent to miss a binding rule, relevant decision,
module contract, security constraint, or contradictory source. Model-specific token
counts are unstable, persistent AI summaries can become stale, and deleting historical
records would remove decision evidence. The change therefore needs deterministic
selection, complete reading after selection, and a fallback that expands context when
relevance is uncertain.

## Options considered

### Option 1: Keep the current routes

Continue naming directories and repeated baseline files. This requires no migration and
maximizes immediate recall, but cost and latency grow with documentation history, and
unrelated content can reduce attention available for the current task.

### Option 2: Replace source documents with compact summaries

Create small context packs for each task and let agents rely on them instead of the
authoritative rules and decisions. This reduces initial context, but duplicates facts,
can become stale, and makes correctness depend on a lossy summary.

### Option 3: Discover narrowly, then read selected sources completely

Keep authoritative documents unchanged. Use compact indexes, filenames, headings,
frontmatter, affected paths, symbols, domain terms, and repository search to identify
candidates. Read each selected rule, skill, contract, and decision completely. Expand
the search and reading scope whenever evidence is incomplete or ambiguous. Prevent
directory-wide routes and context-budget regressions with local checks.

| Criterion | Option 1 | Option 2 | Option 3 |
| -- | -- | -- | -- |
| Decision quality | Complete but diluted by unrelated context | Depends on lossy summaries | Complete selected sources with broad fallback |
| Growth | Unbounded with repository history | Bounded but duplicated | Bounded declared routes; history remains searchable |
| Reversibility | Immediate | Requires restoring source-based routes | Restore previous route declarations |
| Operational cost | No new maintenance | Maintain every summary | Maintain indexes and regression checks |
| Security posture | Preserved | Summary drift can omit controls | Complete guardrails remain mandatory |

## Decision

Adopt Option 3.

Every task MUST fully read the mandatory baseline defined by the context router. The
complete guardrails remain in that baseline. Entry documents SHOULD route to
authoritative rules instead of restating their contents. An unchanged document whose
complete content remains available in the active context MUST be reused rather than read
again. If compaction or another context transition removes that content, the agent MUST
read it again. Agents MUST NOT replace normative sources with generated summaries.

A skill route MUST name individual mandatory files, not a directory. A variable
collection such as project documents, ADRs, or module contracts MUST use bounded
discovery:

1. inspect the collection index or file list without loading every body;
2. search titles, headings, frontmatter, decision-log lines, affected paths, symbols,
   module names, domain terms, and relevant glossary synonyms;
3. read every matching document completely;
4. follow relevant links and every supersedes or superseded-by chain completely; and
5. record the selected sources in the task or pull-request evidence when the selection
   affects an architectural, security, or contract decision.

The agent MUST broaden discovery and reading until uncertainty is resolved when any of
these conditions applies:

- no candidate matches a task that should have documented context;
- terminology, ownership, or authority conflicts;
- the change is cross-cutting or hard to reverse;
- authentication, authorization, secrets, personal data, destructive operations, or a
  security posture change is involved; or
- an index is missing, stale, or does not expose supersession.

Efficiency MUST NOT override completeness, the authority order, or a skill's requirement
to read a selected instruction file fully. Persistent historical sources remain intact.
The append-only decision log and accepted ADRs are searched and selected, never truncated
or deleted to meet a context target.

Context regression checks MUST use model-independent byte and word measurements. They
MUST reject directory-valued `reads` declarations, verify that every task still reaches
its mandatory authorities, and report baseline and task-route growth. A budget increase
requires explicit justification in the pull request. Budgets govern declared mandatory
routes, not the additional sources discovered for a specific task. Measurements
constrain accidental growth; they do not authorize skipping a relevant source.

## Consequences

**Positive:** routine tasks avoid unrelated documents while selected authorities remain
complete; context growth becomes measurable; historical evidence remains available; and
uncertainty causes broader review instead of an unsupported assumption.

**Negative:** agents perform additional index and search steps; indexes and supersession
metadata must remain current; byte and word counts are only token-cost proxies; and a
poor search vocabulary can require a broader fallback.

**Migration and rollback:** first add the acquisition protocol and regression reporting,
then replace directory-valued routes and redundant rereads, and finally reduce duplicated
entry-point summaries. Every phase keeps the existing full sources. Rollback restores the
previous route declarations and entry text; no source document or decision history needs
reconstruction.

**Follow-ups:** update `.ai/README.md`, `CLAUDE.md`, and affected skills; add searchable
scope and supersession data to ADR indexes without editing accepted ADR bodies; add
model-independent context-budget tests to `make doctor`; document the measured before
and after values; and distribute each accepted phase through reviewed Template Sync PRs.
