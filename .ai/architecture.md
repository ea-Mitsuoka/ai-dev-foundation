---
id: architecture
title: Architecture Rules
authority: 4
read_when: [feature, refactor, architecture-change, review]
---

# Architecture

Style: **modular monolith, Clean Architecture layers inside each module, boundaries by
Domain-Driven Design bounded contexts.** Start as a monolith; extract services only when
an ADR justifies it.

<!-- TEMPLATE: adjust the stack table when instantiating. The layer rules below are stack-agnostic. -->

| Field | Value |
| -- | -- |
| Language / runtime | {{STACK}} |
| Persistence | {{DATABASE}} |
| Deployment target | {{DEPLOY_TARGET}} |
| Architecture docs | `docs/architecture/` |

## ARC-001: Canonical directory layout

```
src/
  modules/<context>/        # one directory per bounded context
    MODULE.md               # module contract: purpose, public API, invariants (mandatory)
    domain/                 # entities, value objects, domain services, domain events
    application/            # use cases; orchestrates domain, defines ports (interfaces)
    infrastructure/         # adapters: DB, external APIs, messaging (implements ports)
    interface/              # inbound: HTTP handlers, CLI commands, consumers
  shared/                   # cross-context primitives only (Result, Money, logging)
tests/                      # mirrors src/ exactly; tests/modules/<context>/...
```

Rationale for AI agents: the module directory is the **context unit**. To work on a
module, read its `MODULE.md` + its `domain/` — nothing else is required for local changes.

## ARC-002: Dependency direction (Clean Architecture)

Dependencies point inward only: `interface → application → domain` and
`infrastructure → application → domain`.

- `domain/` MUST NOT import from any other layer, any framework, or any I/O library.
- `application/` MUST NOT import from `interface/` or `infrastructure/`. It defines
  ports (interfaces); `infrastructure/` implements them (dependency inversion).
- MUST NOT import another module's internals. Cross-module calls go through the other
  module's public API declared in its `MODULE.md` (application layer), or through events.

## ARC-003: Module contract file (MODULE.md)

Every module MUST have a `MODULE.md` containing: purpose (2–3 sentences), public API
(what other modules may call), owned data, published/consumed events, invariants that
must never break. AI agents MUST read it before changing the module and MUST update it
when the contract changes.

## ARC-004: Shared code is a last resort

Code goes to `src/shared/` only if it is domain-free and used by 3+ modules. Duplicating
20 lines twice is better than a wrong abstraction (see COD-020).

## ARC-005: Deep modules

A module's interface is everything a caller must know to use it correctly — the type
signature plus invariants, ordering constraints, error modes, and required configuration.
Design modules **deep** (Ousterhout): a lot of behavior behind a small interface.

- When designing an interface, ask in order: fewer methods? simpler parameters? more
  complexity hidden inside?
- **Deletion test**: imagine deleting the module. If complexity simply vanishes, it was a
  pass-through layer — remove it. If the complexity would reappear spread across its
  callers, the module is earning its keep.
- A seam (a point where an implementation can be swapped without editing call sites —
  Feathers) is real only when something actually varies across it: one adapter is a
  hypothetical seam, a second adapter makes it real (COD-051).
- The interface is the test surface: tests cross the same seam callers do (TST-020).
  Needing to reach past the interface to test a module means the module is the wrong
  shape — fix the interface, not the test.

## ARC-010: State and configuration (Twelve-Factor)

- Configuration comes from environment variables; `.env.example` lists every variable
  with a dummy value and one-line comment. No config files with per-environment branches
  in code.
- Processes are stateless; state lives in backing services.
- Logs go to stdout as structured events, not to files.

## ARC-020: Change impact protocol

Before modifying code, classify the blast radius and act accordingly:

| Scope | Definition | Required action |
| -- | -- | -- |
| Local | inside one module, contract unchanged | proceed |
| Contract | changes a MODULE.md public API or event | update MODULE.md + all consumers in same PR, note in PR |
| Architectural | layers, boundaries, storage, public API shape | ADR first (GR-022) |

To find consumers of a contract: search for the module's public symbols across
`src/modules/*/`; check `docs/architecture/` for documented flows.

## ARC-021: Extension over modification

Prefer adding a new use case / handler / adapter over editing a widely-used one.
When editing shared behavior, list every caller in the PR description.
