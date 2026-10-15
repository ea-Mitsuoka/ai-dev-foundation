---
id: api-docs
title: API Documentation
---

# API Documentation

Defines what an instantiated repository records under `docs/api/` for every interface
the project exposes (HTTP, events, CLI).

**Update triggers (DOC-030):** any change to a public endpoint, event schema, CLI
command, or error contract. Breaking contract changes additionally require the
`BREAKING CHANGE:` commit footer (WF-020) and consumer migration notes.

## Recommended project content

- **Schema first**: use the machine-readable contract (OpenAPI 3.x at `openapi.yaml`,
  AsyncAPI for events, JSON Schema for payloads) is the source of truth; prose
  commentary supplements, never contradicts.
- Contract tests verify implementation against the schema (TST-001 integration level);
  drift between schema and implementation is a CI failure, not a doc chore.
- Document each endpoint's auth requirement (SEC-020), inputs with validation rules,
  outputs, error responses with trigger conditions, idempotency, and rate limits.
- Examples use obviously fake credentials (GR-002) and realistic payloads.
- Versioning: breaking API changes follow expand→migrate→contract (REL-040); document
  deprecation windows here.

## Structure

| File | Content |
| -- | -- |
| `docs/api/openapi.yaml` | HTTP API contract (source of truth) |
| `docs/api/events.md` / `docs/api/asyncapi.yaml` | Published/consumed events |
| `docs/api/errors.md` | Error catalog: code → meaning → caller action |
| `docs/api/changelog.md` | Contract-level changes and deprecation schedule |
