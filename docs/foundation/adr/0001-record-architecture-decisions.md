# ADR-0001: Record architecture decisions

| Field | Value |
| -- | -- |
| Status | accepted |
| Date | 2026-07-02 |
| Deciders | repository owner |
| Author | Claude (AI agent) |
| Supersedes / Superseded by | — |

## Context

AI agents perform most implementation work in this repository. Agents (and humans)
joining later cannot infer *why* the system is shaped as it is from code alone; without
recorded reasoning, agents re-litigate settled decisions, or worse, silently reverse
them. The project mandates that architectural changes be deliberate and reviewable
(GR-022).

## Options considered

### Option 1: Do nothing (decisions live in PR discussions)

Pros: zero process. Cons: reasoning scattered and unsearchable; agents cannot load it
as context; decisions effectively lost after squash-merge.

### Option 2: Single evolving architecture document

Pros: one place. Cons: history of *why* is overwritten by each edit; conflicts with
the append-only audit trail agents need.

### Option 3: ADRs (Michael Nygard style) + lightweight decision log

Pros: immutable, numbered, diff-reviewed like code, ideal AI context units; industry
standard. Cons: small process overhead per decision.

## Decision

Adopt Option 3. Architectural decisions (ARC-020 "Architectural" scope) MUST be
recorded as an ADR in `docs/adr/` using `0000-template.md`, approved by a human before
implementation (GR-022), and indexed in `.ai/decision-log.md`.

## Consequences

**Positive:** durable reasoning; agents can check "was this already decided?" before
proposing changes; supersession chain shows evolution.

**Negative:** friction for large changes (intended); requires discipline to keep the
index current (enforced by DOC-030 and review checklist REV-DOC).

**Follow-ups:** template created; process wired into `.skills/architecture.skill.md`.
