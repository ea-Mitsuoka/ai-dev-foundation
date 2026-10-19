---
id: adr-0010
title: ADR-0010 — Separate roadmap, work tracking, and handoff
status: accepted
updated: 2026-07-28
---

# ADR-0010: Separate roadmap, live work tracking, and development handoff

| Field | Value |
| -- | -- |
| Status | accepted |
| Date | 2026-07-28 |
| Deciders | repository owner (approved 2026-07-28) |
| Author | Codex (AI agent) |
| Supersedes / Superseded by | Refines ADR-0009 |

## Context

The foundation provides durable project direction in `docs/roadmap.md`, decisions in
ADRs and `.ai/decision-log.md`, and live task state in GitHub issues and pull requests.
It does not define one resumable snapshot for an AI or human taking over active work.
The roadmap template also updates on milestone completion, but does not require a
completion checklist or a periodic reconciliation cadence.

Combining all of this information in one document would duplicate live GitHub state and
become stale. Keeping it fully distributed makes another agent reconstruct the current
state from several sources before it can act. The foundation needs a clear ownership
boundary between direction, live task tracking, durable decisions, and handoff context.

## Options considered

### Option 1: Keep the current distributed model

Continue relying on roadmaps, issues, pull requests, and decision records without a
handoff document or review cadence. This adds no maintenance, but leaves restart context
implicit and permits stale roadmaps.

### Option 2: Turn the roadmap into the task and handoff document

Put detailed task checklists, current branches, blockers, verification, and direction in
`docs/roadmap.md`. This offers one entry point, but duplicates GitHub state and mixes
short-lived execution details with durable direction.

### Option 3: Put all project state in a handoff document

Make `docs/development-handoff.md` the complete task ledger and project history. This
improves restart discovery, but creates another work tracker and an unbounded document
that is difficult to keep current.

### Option 4: Separate each concern and link between them

Keep detailed task checklists and status in GitHub issues or milestones, direction and
milestone outcomes in the roadmap, durable decisions in ADRs, and only the resumable
current snapshot in a development handoff. Reconcile the roadmap periodically while a
project is active.

## Decision

Adopt Option 4. GitHub issues and milestones MUST remain the authoritative work queue and
task-level completion checklist. `docs/roadmap.md` MUST remain the project direction and
milestone-outcome view; every current outcome SHOULD link to an explicit completion
checklist or milestone. Active projects SHOULD review the roadmap at a declared cadence,
weekly by default, and whenever a milestone completes or direction changes.

Projects whose work continues across sessions or agents SHOULD maintain the
project-wide singleton `docs/development-handoff.md`. It MUST contain only the current
resumable snapshot: active references, material progress, blockers, ordered next
actions, last verified baseline, and required reading. It MUST link to authoritative
issues, pull requests, roadmaps, requirements, and decisions instead of copying their
history. Every agent MUST read it during task intake when it exists.

## Consequences

**Positive:** a new agent gets one restart point; the roadmap becomes auditable without
becoming a task queue; task completion stays in the system that owns it; and durable
decisions remain separate from temporary status.

**Negative:** active projects gain one mutable document and a periodic review action;
contributors must distinguish snapshot facts from durable facts; and an abandoned
handoff can mislead agents unless freshness is enforced.

**Migration and rollback:** existing projects create a handoff only when work actually
spans sessions or agents. They add a roadmap review cadence during the next roadmap
update; no existing project document moves. Rollback removes the conditional intake and
maintenance rules while leaving any project-owned handoff as an ordinary descriptive
document.

**Follow-ups:** add binding documentation and workflow rules, add a synchronized handoff
template, update the roadmap template, and distribute the change through reviewed
direct-parent Template Sync PRs.
