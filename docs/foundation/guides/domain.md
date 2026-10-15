---
id: domain-docs
title: Domain Model Documentation
---

# Domain Model

Defines how an instantiated repository documents the business reality it models (DDD).
Code names follow reusable terms in the [foundation glossary](../glossary.md) and
project terms in `docs/glossary.md` under [COD-002](../../../.ai/coding-rules.md).

**Update triggers (DOC-030):** new domain concept, changed business rule, new bounded
context, changed context relationships, PII-bearing entity added (also SEC-011).

## Structure

| File | Content |
| -- | -- |
| `docs/domain/context-map.md` | Bounded contexts and their relationships (partnership, customer-supplier, ACL...) — Mermaid |
| `docs/domain/<context>.md` | Per context: core entities, value objects, aggregates, invariants, domain events, state machines |

## Per-context file template

```markdown
---
id: domain-<context>
title: <Context> Domain
---

# <Context>

Purpose: <one paragraph — what business capability this context owns>

## Aggregates
| Aggregate | Root entity | Invariants that always hold |
|-----------|-------------|-------------------------------|

## Value objects
| Name | Definition | Validation rules |

## Domain events
| Event | Emitted when | Consumed by |

## Business rules
Numbered, testable statements. Each rule should map to at least one test (TST-002).

## Data classification (SEC-011)
| Entity/field | Class (Secret/PII/Internal/Public) | Handling notes |
```

<!-- TEMPLATE: create context-map.md with the first bounded context. -->
