---
name: bugfix
description: Diagnose and fix incorrect behavior with a regression test that pins the fix
triggers: [bug, defect, incorrect behavior, crash, regression, バグ修正, 不具合修正, バグ, 障害]
reads: [.ai/workflow.md, .ai/testing.md]
---

# Skill: Bug Fix

## Purpose

Durable root-cause correction is the default: remove the defect at its owning boundary,
prove the fix with a regression test that fails on the old code, and prevent recurrence.

## Inputs

- Reproduction: exact steps/input → observed vs expected behavior. If not reproducible,
  reproduction **is** the first task — do not patch symptoms of a bug you cannot trigger.
- The issue ID; the module(s) involved (`MODULE.md`).
- Response type: durable correction unless a human explicitly requests the temporary
  mitigation exception below.

## Process

1. Reproduce the bug locally; capture the exact failing observation.
2. Write the regression test that encodes the *expected* behavior. Run it — it MUST
   fail, and fail for the right reason. Commit it first (`test(scope): reproduce #N`).
3. Diagnose the root cause: trace from symptom to cause; state the cause in one
   sentence. If you can't, you're not ready to fix.
4. Implement the smallest complete correction at the cause, not the smallest line count.
   Restore or strengthen the violated invariant at the boundary that owns it; resist
   drive-by refactoring (COD-021) and file separate follow-up issues instead.
5. Evaluate robustness before declaring the fix complete. For a state-changing operation
   that can be retried, resumed, replayed, or scheduled, handle partial failure and make
   repeated execution idempotent: it reaches the same intended state without duplicate
   side effects. Test the relevant retry or repeated-execution path. If idempotence is not
   applicable, state why in the PR instead of adding speculative machinery (COD-051).
6. Run the regression test (now green) + the module's full suite + `task test`.
7. Sweep for siblings: search for the same pattern elsewhere in the codebase; fix in
   the same PR only if identical and small, otherwise open issues.
8. Update `docs/troubleshooting/` if users could hit this; runbook if ops action exists.
9. PR with `fix(scope):` title; description includes root cause, why the correction is
   complete, and robustness/idempotence evidence or the reason it is not applicable.

## Decision criteria

- **Symptom vs cause?** If your fix adds a null-check/try-catch without explaining why
  the value can be invalid, you are patching a symptom — keep digging.
- **Temporary mitigation?** A symptom-level measure is allowed only when a human
  explicitly requests a temporary mitigation. Urgency, production impact, or failure to
  find the cause does not imply permission. The PR MUST label it `TEMPORARY MITIGATION`,
  state the known or unresolved root cause and residual risk, record rollback and removal
  conditions, and link a permanent-fix issue. It MUST NOT be reported as resolved.
  Guardrails, security controls, regression tests, and review remain mandatory.
- **Hotfix?** Production-impacting → REL-050: expedited but real review. A hotfix is not
  automatically a temporary mitigation; the smallest complete root-cause correction
  remains the default.
- **Can't find root cause after 3 approaches?** Escalate with findings (CLAUDE.md §13).
- **Fix reveals a design flaw?** Fix the instance now; propose ADR for the design.

## Outputs

- PR: regression test (committed failing-first) + smallest complete fix + doc updates.
- Root-cause statement in the PR description.
- Robustness/idempotence evidence, or an explicit non-applicability reason.
- Follow-up issues for siblings/refactoring found along the way.
- For an explicitly requested temporary mitigation: mitigation PR + linked permanent-fix
  issue; the defect remains open until the durable correction lands.

## Checklist

- [ ] Regression test demonstrably failed before the fix (show the failing run)
- [ ] Root cause stated in one sentence in the PR
- [ ] Smallest complete correction applied; no mixed refactoring (COD-021)
- [ ] Retry, repeated execution, and partial failure evaluated; idempotence tested or a
  non-applicability reason reported
- [ ] Sibling occurrences searched; results reported
- [ ] Temporary mitigation, if any, has explicit human direction, residual-risk and
  rollback/removal notes, and a linked permanent-fix issue
- [ ] Full test suite green; troubleshooting docs updated if user-visible
