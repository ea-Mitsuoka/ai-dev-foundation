---
id: coding-rules
title: Coding Rules
authority: 4
read_when: [feature, bugfix, refactor, review]
---

# Coding Rules

Stack-agnostic rules. Language-specific style is delegated to the formatter/linter
configured in this repo (COD-001) — never hand-format against the tool.

## Style & structure

### COD-001: The formatter and linter are the law

Code MUST pass `task format` and `task lint` with zero warnings. Do not debate style
the tools already decide. Suppressions require justification (GR-041).

### COD-002: Naming

- Names state intent, not implementation (`retryDelay`, not `sleepTime2`).
- One concept = one name across the codebase; check reusable terms in
  `docs/foundation/glossary.md` and project terms in `docs/glossary.md` (when present)
  before inventing a term. Add reusable foundation terms to
  `docs/foundation/glossary.md`; add repository-specific terms to `docs/glossary.md`
  (ubiquitous language, DDD).
- The glossary's *Avoid* column lists banned synonyms per term. Those words MUST NOT be
  used for that concept — in identifiers, docs, or discussion. A synonym is how a second
  name for the same concept starts.
- Boolean names read as predicates (`isExpired`, `hasAccess`).

### COD-003: Function size and shape

- Functions SHOULD do one thing; > ~40 lines or > 3 nesting levels is a refactor signal.
- Prefer early returns over nested conditionals.
- No boolean flag parameters that switch behavior — split the function.

### COD-004: Comments explain *why*, never *what*

Comments state constraints, non-obvious reasons, and links to decisions (ADR/issue IDs).
Delete commented-out code — git history keeps it.

## Error handling

### COD-010: No silent failures

MUST NOT swallow exceptions/errors. Every failure path either: handles it meaningfully,
translates it into a domain error, or propagates it. Empty catch blocks are forbidden.

### COD-011: Fail fast, validate at the boundary

Validate all external input (HTTP, CLI, file, message) at the `interface/` layer.
Inside `domain/`, invalid state is a bug, not an input case.

### COD-012: Errors carry context

Error messages include what was attempted and with which identifiers — but never secret
values (GR-003) and never raw user PII.

## Dependencies

### COD-040: Dependency addition protocol

Before adding a library, in this order:

1. Can the standard library / an existing dependency do it? If yes, use that.
2. Check: license compatible (see REL-030)? maintained (release within ~12 months)?
   reasonable transitive footprint? known CVEs?
3. Record purpose + alternatives in the PR description (GR-023).
   Pin versions via lockfile; never install "latest" unpinned.

### COD-041: Isolate dependencies behind ports

Third-party SDKs and frameworks are wrapped in `infrastructure/` adapters. `domain/`
and `application/` MUST NOT import them directly (ARC-002). This keeps the codebase
migratable — vendor lock-in is a decision, not an accident.

## Refactoring & duplication

### COD-020: Rule of three

Extract an abstraction on the third occurrence, not the second. Wrong abstractions cost
more than duplication.

### COD-021: Refactor separately from behavior change

A PR either changes behavior or restructures code — not both. Mark refactor PRs with
`refactor:` commits and state "no behavior change" in the description; tests must pass
unchanged.

## AI-specific rules

### COD-050: Match the surrounding code

Before writing, read neighboring files in the same layer and imitate their idioms,
naming, and test patterns. Consistency beats personal preference.

### COD-051: No speculative generality

Do not add parameters, hooks, or abstraction layers for hypothetical future needs
(YAGNI). Extension points require a current second consumer or an ADR.

### COD-052: Leave breadcrumbs

When a change involves a non-obvious decision too small for an ADR, record it in
`.ai/decision-log.md` (one line) or as a `why`-comment with the issue ID.
