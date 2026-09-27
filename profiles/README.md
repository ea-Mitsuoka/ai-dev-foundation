---
id: profiles
title: Taskfile Profiles — Reference Implementations
---

# profiles/ — Taskfile Reference Implementations

The root [Taskfile.yml](../Taskfile.yml) ships as no-op placeholders. A **profile** is a
reference implementation for a concrete stack: copy the profile's `Taskfile.yml` to the
repo root, adjust paths, delete the placeholders — hooks, pre-commit, and CI start working
unchanged.

## The canonical target contract

The binding table and the implementation rules live in the inherited
[.ai/contracts/foundation/task-targets.md](../.ai/contracts/foundation/task-targets.md).
This directory holds reference implementations only; it is repository-owned and a
descendant may delete it.

## Available profiles

| Profile | Stack | Source |
| -- | -- | -- |
| [terraform-gcp/](terraform-gcp/) | Terraform (GCP foundations, layered), Python tooling via uv, OPA policies, Excel SSoT generator | adapted 2026-07-02 from a production foundations project; Taskfile since 2026-09-27 (ADR-0026) |
| [typescript-node/](typescript-node/) | Node.js + pnpm + Prettier + ESLint + tsc + Vitest | authored 2026-07-02; Taskfile since 2026-09-27 (ADR-0026) |
| [python-uv/](python-uv/) | Python + uv + Ruff + mypy + pytest | authored 2026-07-02; Taskfile since 2026-09-27 (ADR-0026) |

## Creating a new profile

1. Copy the closest existing profile directory.
2. Reimplement the canonical targets for the stack; keep the semantics in `.ai/contracts/foundation/task-targets.md`.
3. Keep project-specific tasks in the clearly marked "extensions" section.
4. Verify: `task lint` on dirty code fails; `task format` fixes it; `task nonexistent`
   fails; `task test-unit` finishes in seconds.
