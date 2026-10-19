---
name: review
description: Review a PR (or self-review a diff) against the 10-viewpoint checklist
triggers: [review PR, self-review, code review, レビュー, コードレビュー, PRレビュー, セルフレビュー]
reads: [.ai/review-checklist.md]
---

# Skill: Code Review

## Purpose

Catch defects and rule violations before merge, with findings precise enough to act on
immediately — while keeping review latency low.

## Inputs

- The PR: description, linked issue, full diff, CI results. A PR with an empty
  description or red CI is returned immediately without deep review.
- The relevant rules: identify the change scope (ARC-020) and load the rule files the
  routing table maps to that scope.
- The complete guardrails already loaded by the mandatory baseline; reuse them while
  they remain available in the active context, and reread after compaction.

## Process

1. Read issue + description first; form an expectation of what the diff should contain.
2. First pass — intent: does the diff do what the PR claims, and only that? Unrelated
   changes → finding.
3. Second pass — the checklist (`.ai/review-checklist.md`), all 10 viewpoints; note
   explicitly which viewpoints you skipped as not applicable.
4. Verify, don't trust: for any non-obvious claim ("no behavior change", "covered by
   existing tests"), check the code/tests yourself (GR-042).
5. Guardrail scan: secrets, security downgrades, missing tests, missing ADR/doc updates
   (GR-001..042) — any hit is a Blocker.
6. Write findings: severity (Blocker/Major/Minor), file:line, rule ID, concrete fix.
   Also name what was done well — patterns worth repeating get reinforced (COD-050).
7. Verdict: **Approve** / **Approve with minors** / **Request changes** (any Blocker or
   Major) — plus a 2-sentence summary of the change for the merge record.

## Decision criteria

- **Blocker vs Major?** Guardrail violation, security issue, or would corrupt
  data/break consumers = Blocker. Bug risk or missing tests = Major.
- **Style opinion?** If the linter allows it and COD rules don't forbid it, it's a Nit —
  usually omit (the linter is the law, COD-001).
- **Too big to review?** GR-020 exceeded without declared reason → request split;
  reviewing an unreviewable PR poorly is worse than sending it back.
- **Self-review?** Same process, plus: re-read your own diff as a hostile reviewer;
  list what you did NOT verify honestly in the PR description.

## Outputs

- Review posted: ranked findings with file:line + rule ID + fix, skipped viewpoints
  named, explicit verdict.
- For self-review: corrected diff + honest "not verified" list in the PR body.

## Checklist

- [ ] Reviewed against intent (issue), not just the diff
- [ ] All 10 viewpoints covered or explicitly skipped
- [ ] Every finding has file:line + concrete fix; severities justified
- [ ] Claims in the PR description spot-verified in code
- [ ] Verdict stated; no approval with an unresolved Blocker/Major
