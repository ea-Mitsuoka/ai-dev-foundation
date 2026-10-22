---
id: docs-templates-index
title: Document Templates
---

# docs/foundation/templates/ — Document Templates

Reusable skeletons for standard project documents. Copy a template out of this directory,
fill it, and delete the guidance comments. Each template names the skill that drives it.

| Template | Produces | Driven by |
| -- | -- | -- |
| [adr.md](adr.md) | A project architecture decision record under `docs/adr/` | [.skills/architecture.skill.md](../../../.skills/architecture.skill.md) |
| [glossary.md](glossary.md) | `docs/glossary.md` with project-specific ubiquitous language | [.ai/coding-rules.md](../../../.ai/coding-rules.md) |
| [requirements.md](requirements.md) | A requirements definition document | [.skills/requirements.skill.md](../../../.skills/requirements.skill.md) |
| [roadmap.md](roadmap.md) | `docs/roadmap.md` with project direction and sequencing | [.ai/documentation.md](../../../.ai/documentation.md) |
| [development-handoff.md](development-handoff.md) | `docs/development-handoff.md` with the resumable current snapshot | [.ai/documentation.md](../../../.ai/documentation.md) |

Templates follow the documentation rules ([.ai/documentation.md](../../../.ai/documentation.md)),
especially the objective prose in DOC-002 and document structure in DOC-003. After
template instantiation, AI agents translate the copied structure and write
project-specific documents in Japanese. The
foundation-owned template files remain English (ADR-0005).

**Update trigger:** add a row here whenever a new template lands in this directory.
