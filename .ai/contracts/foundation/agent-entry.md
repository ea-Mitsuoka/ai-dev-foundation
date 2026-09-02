---
id: foundation-agent-entry
title: Foundation Agent Entry Contract
authority: 3
read_when: [agent-entry, task-intake]
---

# Foundation Agent Entry Contract

Identity-free, vendor-neutral instructions; identity and stack facts belong in overlays.

## Authority and intake

Apply instructions in this order: `.ai/guardrails.md`, security rules, this contract,
routed `.ai/` rules, then `docs/`. Apply the higher rule and report conflicts.

1. Read `.ai/guardrails.md` and `.ai/README.md` completely.
2. Read `docs/development-handoff.md` completely for continuing work when present.
3. Read every routed rule and matching skill completely before acting.
4. Discover through indexes and search, then read selected sources completely. Broaden
   discovery whenever relevance or correctness is uncertain.

## Composition

Profile order: foundation, owner-qualified templates oldest-to-parent, then project.
`strengthen-only` forbids weakening a foundation MUST, guardrail, or security control.

## Change protocol

- Use an issue, task branch, reviewed PR, and `.ai/workflow.md`. Land code, tests, and
  required docs together; accept an ADR before structural implementation.
- Complete the PR template. Titles and commits use Conventional Commits, releases use
  SemVer, and merges use squash. In a leaf repository — one that publishes no contract
  root of its own — write the PR body in Japanese (ADR-0020). Self-review with
  `.ai/review-checklist.md`.
- After every edit run `make format` and `make lint`; use only canonical `make` targets.
- Preserve unrelated changes and checks. Never push to protected main, bypass checks,
  fabricate results, or perform destructive work without specific approval.

## Canonical commands

```text
make setup   make format   make lint   make test   make test-unit
make test-integration   make coverage   make build   make run
make security-scan   make sbom   make clean   make doctor
```

Binding semantics live in `profiles/README.md`; documented no-ops may remain until wired.

## Runtime integration

Claude Code reads `.claude/README.md` completely. Other runtimes use `AGENTS.md` and
provide equivalent formatting, linting, guards, skills, and secret handling.

## Escalation

Stop for conflicts, blocked guardrails, an unaccepted architecture ADR, materially
different interpretations, or a third attempt at one failure. Also stop for
authentication, payments, personal-data schema, data deletion, production configuration,
spending money, new authority, irreversible work, or material scope expansion. Report
context, options, recommendation, and required decision.

## Definition of done

WF-090 requires acceptance criteria, green tests and lint, current docs, self-review, a
complete green PR, and no guardrail violation. Report exactly what was and was not
verified.
