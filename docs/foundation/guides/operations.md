---
id: operations-docs
title: Operations Documentation
---

# Operations

Defines what an instantiated repository records under `docs/operations/` to keep the
project healthy day-to-day: observability, SLOs, alerts, and maintenance.

**Update triggers (DOC-030):** new critical path (needs metrics + alert), new alert,
changed SLO, new scheduled maintenance task, post-incident action items.

## Structure

| File | Content |
| -- | -- |
| `docs/operations/observability.md` | Where logs/metrics/traces go; how to query them; correlation IDs |
| `docs/operations/slo.md` | SLIs and SLO targets per critical path; error budget policy |
| `docs/operations/alerts.md` | Alert catalog: condition → severity → runbook link |
| `docs/operations/maintenance.md` | Recurring tasks (rotation, cleanup, upgrades) with schedule and owner |

## Related binding rules

- Logging and data handling follow [`.ai/architecture.md`](../../../.ai/architecture.md)
  (ARC-010) and [`.ai/security.md`](../../../.ai/security.md) (SEC-011).
- Reliability review follows
  [`.ai/review-checklist.md`](../../../.ai/review-checklist.md) (REV-REL).
- Project alert severity and escalation policy belong in `docs/operations/alerts.md`.
