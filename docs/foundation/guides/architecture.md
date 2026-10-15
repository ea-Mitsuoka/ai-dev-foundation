---
id: architecture-docs
title: Architecture Documentation
---

# Architecture Documentation

Defines what an instantiated repository records under `docs/architecture/`. The *rules*
live in [.ai/architecture.md](../../../.ai/architecture.md); inherited decisions live in
the [foundation ADRs](../adr/), and project decisions live in `docs/adr/`. If a project
architecture document contradicts any of them, that project document is wrong.

**Update triggers (DOC-030):** new module, changed module boundary, new external
dependency/integration, changed data flow, new infrastructure component.

## Structure (create these files as the system grows)

| File | Content | Format |
| -- | -- | -- |
| `docs/architecture/c4-context.md` | System in its environment: users, external systems | Mermaid C4/flowchart |
| `docs/architecture/c4-container.md` | Deployable units and their interactions | Mermaid |
| `docs/architecture/modules.md` | Bounded-context map: every `src/modules/*` + one-line purpose + dependencies between them | Mermaid + table |
| `docs/architecture/data-flow.md` | How data moves for the 3–5 most important flows | Mermaid sequence |
| `docs/architecture/infrastructure.md` | Runtime topology: compute, storage, network | Mermaid + table |

## Conventions

- Diagrams are **Mermaid in Markdown** — diffable, renderable on GitHub, writable by
  agents. No binary diagram files (DOC-001).
- Every diagram is followed by a prose paragraph stating what an agent should conclude
  from it (diagrams alone are ambiguous).
- Keep system-level relationships here. Module-level detail belongs in each module's
  `MODULE.md`.

<!-- TEMPLATE: this directory starts empty except this README. Create modules.md with
     the first real module. -->
