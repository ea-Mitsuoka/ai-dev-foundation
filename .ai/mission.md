---
id: mission
title: Mission
authority: 4
read_when: [onboarding, planning, architecture]
---

# Mission

<!-- TEMPLATE: Replace the {{placeholders}} when instantiating this template for a real project. -->

## What this project is

{{PROJECT_NAME}} — {{ONE_SENTENCE_DESCRIPTION}}

| Field | Value |
| -- | -- |
| Problem being solved | {{PROBLEM}} |
| Primary users | {{USERS}} |
| Core value | {{VALUE}} |
| Explicitly out of scope | {{NON_GOALS}} |

## Success criteria

<!-- Measurable. AI uses these to judge whether a proposed change moves the project forward. -->

1. {{CRITERION_1}}
2. {{CRITERION_2}}

## Role of AI agents in this project

AI agents are long-term team members, not code generators. Expectations:

- **Own the full task lifecycle**: requirements clarification → design → implementation →
  tests → documentation → PR. A task is not done when code compiles; it is done when the
  Definition of Done in `workflow.md` (WF-090) is met.
- **Preserve intent**: when code and documentation disagree, investigate which is correct
  before changing either. Record the resolution.
- **Prefer reversible steps**: small PRs, feature flags, additive migrations.
- **Escalate, don't guess**: for the triggers in the loaded
  [foundation agent contract](contracts/foundation/agent-entry.md#escalation), stop and
  ask the human. For everything else, decide and record the reasoning.

## Human role

Humans own: product direction, priority calls, ADR approval, release approval,
security-sensitive decisions. AI prepares options and recommendations; humans decide.
