---
name: test
description: Add or improve tests — coverage gaps, characterization, flaky-test repair
triggers: [write tests, improve coverage, flaky test, characterization tests, テスト作成, テスト追加, カバレッジ]
reads: [.ai/testing.md, .ai/coding-rules.md]
---

# Skill: Testing

## Purpose

Increase confidence per test-second: tests that catch real regressions, read as
specifications, and never flake.

## Inputs

- Target: which module/behavior, and why (coverage gap, upcoming refactor, flaky suite).
- Existing patterns: read 2–3 neighboring test files first and imitate their style,
  fixtures, and naming (COD-050).
- `make coverage` output for the target area.

## Process

1. List the behaviors (not functions) the target promises — from MODULE.md, docstrings,
   issue text. Each behavior = at least one test.
2. Choose the pyramid level (TST-001): default to unit at the use-case level; go up a
   level only when the behavior spans a real boundary.
3. Write tests Arrange-Act-Assert, one behavior each, names as specifications
   (`test_expired_token_is_rejected` — TST-010).
4. Cover the boundary matrix per behavior: empty / one / many / max / invalid type /
   dependency failure (TST-002).
5. Verify each test can fail: mutate the code mentally (or actually) — if no plausible
   bug flips it red, the test is decorative; strengthen or delete it. Reject a
   tautological test whose expected value is computed the way the implementation
   computes it; take expected values from a known-good literal, a worked example, or the
   specification (TST-010).
6. For flaky tests: reproduce (`--repeat` / stress), find the nondeterminism source
   (time, order, shared state, network — TST-010), fix it. Quarantine + issue if not
   fixable today; never blind-retry (GR-040).
7. Run the full suite; check runtime stayed within budgets (TST-001).

## Decision criteria

- **Mock or fake or real?** Ports → fakes preferred, mocks acceptable; domain → never
  mocked; integration level → real dependency in a container (TST-020).
- **Test the private helper?** No — test through the public behavior; if the helper is
  too complex to reach, that's a design smell to report.
- **Snapshot tests?** Only for genuinely presentational output, reviewed like code.
- **Delete a test?** Only if it duplicates another's failure signal or pins behavior
  that no longer exists — state which in the commit.

## Outputs

- Test PR (`test(scope):`), suite green, coverage moved toward TST-003 targets.
- Flaky-test fixes with root cause named in the commit message.

## Checklist

- [ ] Every new test verified able to fail for a real bug
- [ ] Expected values come from a source independent of the implementation (TST-010)
- [ ] Deterministic: injected time/randomness, no order or network dependence
- [ ] Names read as behavior specs; AAA structure
- [ ] Boundary matrix covered, not just happy paths
- [ ] Suite runtime within budget; coverage did not decrease
