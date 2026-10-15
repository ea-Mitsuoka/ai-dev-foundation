---
id: foundation-documentation-guides
title: Foundation Documentation Guides
---

# Foundation Documentation Guides

These guides define the purpose, structure, and update triggers of project-owned
documentation paths without occupying those paths with foundation-owned README files.
They are descriptive mappings. Binding behavior remains in
[`.ai/documentation.md`](../../../.ai/documentation.md) and the rule files it references.

| Guide | Project-owned destination |
| -- | -- |
| [project-documentation.md](project-documentation.md) | `docs/` |
| [architecture.md](architecture.md) | `docs/architecture/` |
| [domain.md](domain.md) | `docs/domain/` |
| [api.md](api.md) | `docs/api/` |
| [deployment.md](deployment.md) | `docs/deployment/` |
| [operations.md](operations.md) | `docs/operations/` |
| [runbook.md](runbook.md) | `docs/runbook/` |
| [troubleshooting.md](troubleshooting.md) | `docs/troubleshooting/` |

## Onboarding references

| Guide | Purpose |
| -- | -- |
| [ai-context.md](ai-context.md) | Acquire complete task-relevant AI context within measured declared-route budgets |
| [usage.md](usage.md) | Create a project from the foundation or develop the foundation itself |
| [usage.ja.md](usage.ja.md) | Repository-owner-approved Japanese human-facing version of the usage guide (ADR-0008 exception) |
| [ai-instruction-files.ja.md](ai-instruction-files.ja.md) | Repository-owner-approved Japanese guide to the reusable AI instruction system (ADR-0008 exception) |

All other foundation guides are English. The two Japanese guides are descriptive and
defer to the English rules and sources they reference. Another localized foundation
guide requires a superseding ADR-0008 decision.

**Update trigger:** update the matching guide whenever the project documentation
inventory, structure, or DOC-030 trigger changes.
