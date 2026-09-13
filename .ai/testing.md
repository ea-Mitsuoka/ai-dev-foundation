---
id: testing
title: Testing Policy
authority: 4
read_when: [feature, bugfix, refactor, test, review]
---

# Testing Policy

Canonical commands: `make test` (all), `make test-unit` (fast suite), `make coverage`.

## TST-001: Test pyramid

| Level | Location | Scope | Speed budget | Share |
| -- | -- | -- | -- | -- |
| Unit | `tests/modules/<ctx>/unit/` | one class/function, no I/O | < 100ms each | ~70% |
| Integration | `tests/modules/<ctx>/integration/` | module + real adapter (DB, HTTP) | < 5s each | ~25% |
| E2E | `tests/e2e/` | user-visible flow through real stack | minutes | ~5%, critical paths only |

Tests mirror `src/` structure exactly so the test for any file is findable mechanically.

## TST-002: What must be tested

Every PR that changes behavior MUST include (GR-021):

- Happy path for each new/changed public function of a module.
- Error paths: invalid input, dependency failure, boundary values (empty, max, zero, null).
- For bug fixes: a regression test that **fails on the pre-fix code** (see
  `.skills/bugfix.skill.md` — write the failing test first, then fix).

Do not test: private functions directly, framework behavior, generated code.

## TST-003: Coverage gate

Line coverage MUST NOT decrease on `main` (ratchet). New modules target ≥ 80% for
`domain/` and `application/`. Coverage is a floor detector, not a goal — 100% coverage
with weak assertions violates GR-040 in spirit.

## TST-004: Test-first slices

For new behavior, write one failing test for one behavior, then the minimal
implementation that makes it pass, then the next behavior (red → green, one slice at a
time). A batch of tests written after a batch of code verifies the shape of the code,
not its behavior, and does not substitute for this rule.

Applies when all three hold: the behavior has a concrete expected outcome; a stable
public boundary (seam, ARC-005) exists to observe it; and the expected value has a source
independent of the implementation (specification, known-good literal, external standard,
or invariant). Not required for documentation, mechanical configuration, generated code,
investigation, or throwaway prototypes.

Name the seams the tests will observe at the MNT-001 design checkpoint, before writing
code. Existing public boundaries are the agent's choice; ask the human only when a new
public API shape makes the seam choice diverge materially. After a slice is green, the
code added in that slice MAY be restructured while tests stay green; restructuring
existing code is a separate `refactor` change (COD-021, MNT-003).

## TST-010: Test quality rules

- **Deterministic**: no real network, no real clock, no shared mutable state, no
  order-dependence. Inject time and randomness.
- **Independent expected values**: never compute the expected value the way the
  implementation computes it (`assert total(items) == sum(i.price for i in items)`).
  Such a test is tautological: it passes by construction and does not satisfy GR-021.
  Take expected values from a known-good literal, a worked example, or the specification.
- **Arrange-Act-Assert** with one behavioral assertion focus per test.
- **Name = specification**: `test_expired_token_is_rejected`, not `test_token_2`.
  A failing test's name alone should identify the broken behavior.
- **Independent fixtures**: builders/factories over shared fixtures; a test must be
  readable without opening other files.
- **Flaky tests** are quarantined with a linked issue within one day — never retried
  into green (GR-040).

## TST-020: Doubles policy

- Mock only at port boundaries (the interfaces defined in `application/`). Never mock
  the domain layer.
- Prefer fakes (in-memory implementations) over mocks for repositories.
- Integration tests use real infrastructure via containers, not mocks.

## TST-030: AI agent test protocol

1. Run `make test-unit` before starting work to confirm a green baseline. If the
   baseline is red, report it; do not build on a broken baseline.
2. Run affected tests after every meaningful change; run `make test` before opening a PR.
3. Report results verbatim — full failure output, never a summary of what you expected
   (GR-042).
4. When tests fail, fix the code, not the test — unless the test itself is proven wrong,
   which must be stated explicitly in the commit message.
