---
name: refactor
description: Restructure code without changing behavior, protected by tests at every step
triggers: [refactor, restructure, clean up, reduce debt, extract module, リファクタ, リファクタリング, クリーンアップ, 構造改善]
reads: [.ai/architecture.md, .ai/coding-rules.md, .ai/testing.md]
---

# Skill: Refactoring

## Purpose

Improve structure (readability, cohesion, coupling, layer compliance) with **provably
unchanged behavior**.

## Inputs

- A stated goal: which quality problem, in which files, and what "better" looks like.
  "Clean up X" is not a goal — convert it into one before starting.
- Behavior lock: the affected code's tests are green AND meaningfully cover the code
  you'll touch. If coverage is weak, **first PR adds characterization tests** (capture
  current behavior, even oddities), refactor is the second PR.

## Process

1. Verify green baseline; assess coverage of the target code specifically.
2. (If needed) add characterization tests — separate PR.
3. For decomposition, name each responsibility, boundary, dependency direction, and
   independent test surface first (MNT-001). Reject extractions that only lower line
   count, scatter one responsibility, or add pass-through wrappers (MNT-002/GR-025).
4. Refactor in small mechanical steps: rename → move → extract → inline. Run
   `task test-unit` after each step; commit each step separately.
5. Keep public contracts frozen: MODULE.md APIs, wire formats, CLI flags, persisted
   data. If a contract must change, that is not a refactor — use architecture.skill.md.
6. Delete what the refactor obsoleted (old helpers, dead branches, stale comments).
7. Run `task test` + `task lint`; confirm coverage did not drop (TST-003).
8. PR titled `refactor(scope): ...`, description states "no behavior change" and the
   structural goal achieved.

## Decision criteria

- **Test change needed?** Only mechanical updates (imports, names). If an assertion
  must change, behavior changed — stop and reclassify.
- **Scope creep?** Found a bug mid-refactor → do NOT fix it here; file an issue, or
  pause the refactor and fix it in its own PR first.
- **How big?** Within GR-020 per PR. Large refactors become a series where every
  intermediate state is green and shippable.
- **Worth it?** Skip refactors that only satisfy taste (COD-050/COD-051): each PR must
  name a concrete maintenance cost it removes.
- **Large but cohesive?** MNT-002 is a review signal, not an automatic split. Record why
  cohesion is safer; beyond GR-025, obtain the documented human-approved exception.

## Outputs

- PR(s) with unchanged behavior, green unchanged tests, structural goal met.
- Updated MODULE.md/docs only where structure descriptions changed.

## Checklist

- [ ] Baseline was green; every intermediate commit is green
- [ ] No public contract changed; no behavior change (assertions untouched)
- [ ] Stated structural goal achieved and named in the PR
- [ ] New boundaries own behavior; no cosmetic split or pass-through layer (MNT-003)
- [ ] Dead code removed; no new TODOs without issues
- [ ] Coverage did not decrease; lint clean
