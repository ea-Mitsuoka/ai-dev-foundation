---
id: profiles
title: Makefile Profiles — Reference Implementations
---

# profiles/ — Makefile Reference Implementations

The root [Makefile](../Makefile) ships as no-op placeholders. A **profile** is a
reference implementation for a concrete stack: copy the profile's Makefile to the repo
root, adjust paths, delete the placeholders — hooks, pre-commit, and CI start working
unchanged.

## The canonical target contract

The binding table and the implementation rules live in the inherited
[.ai/contracts/foundation/make-targets.md](../.ai/contracts/foundation/make-targets.md). This directory holds
reference implementations only; it is repository-owned and a descendant may delete it.

## Available profiles

| Profile | Stack | Source |
|---------|-------|--------|
| [terraform-gcp/](terraform-gcp/) | Terraform (GCP foundations, layered), Python tooling via uv, OPA policies, Excel SSoT generator | adapted 2026-07-02 from a production foundations project |
| [typescript-node/](typescript-node/) | Node.js + pnpm + Prettier + ESLint + tsc + Vitest | authored 2026-07-02 |
| [python-uv/](python-uv/) | Python + uv + Ruff + mypy + pytest | authored 2026-07-02 |

## Creating a new profile

1. Copy the closest existing profile directory.
2. Reimplement the canonical targets for the stack; keep the semantics in `.ai/contracts/foundation/make-targets.md`.
3. Keep project-specific targets in the clearly marked "extensions" section.
4. Verify: `make lint` on dirty code fails; `make format` fixes it; `make nonexistent`
   fails; `make test-unit` finishes in seconds.
