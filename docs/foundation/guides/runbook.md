---
id: runbook-index
title: Runbooks
---

# Runbooks

Defines the step-by-step procedures an instantiated repository stores under
`docs/runbook/`. They must be executable under stress by a human or an AI agent with
operational access, with an expected result and an "if not, then" branch for every step.

**Update triggers (DOC-030):** new alert (every alert links here), new failure mode
discovered in an incident, changed deploy/rollback procedure, risky release (REL-040).

## Entry format (`docs/runbook/<slug>.md`)

```markdown
---
id: runbook-<slug>
title: <symptom or task name>
severity: page | ticket
last-verified: YYYY-MM-DD
---

# <Symptom or task>

**Trigger:** <the alert or situation that brings you here>
**Impact if unhandled:** <what breaks, for whom>
**Safe to execute by agent:** yes / no — <destructive steps require human per GR-031>

## Steps
1. <action — exact command or console path>
   - Expect: <observable result>
   - If not: <next step or escalate to X>
2. ...

## Verification
<how to confirm resolution — exact check>

## Escalation
<who/what, with contact/channel, when steps are exhausted>
```

## Checklist

- Exact commands, no placeholders that require guessing; parameterize with env vars.
- Mark destructive steps and link
  [GR-031](../../../.ai/guardrails.md) so an agent requests explicit human approval.
- Each runbook is re-verified after any related procedure change; stale runbooks are
  worse than none — `last-verified` is mandatory.

## Index

<!-- | Runbook | Trigger | Severity | -->

<!-- populate as runbooks are added -->
