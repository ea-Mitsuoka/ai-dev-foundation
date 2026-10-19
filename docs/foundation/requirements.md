---
id: foundation-requirements-guide
title: Foundation Requirements Guide
---

# Requirements document placement

This foundation-owned guide defines where an instantiated repository stores its
requirements documents. Follow the binding requirements procedure in
[`.skills/requirements.skill.md`](../../.skills/requirements.skill.md) and start from
[`docs/foundation/templates/requirements.md`](templates/requirements.md).

## Placement

| Scope | Location | Example |
| -- | -- | -- |
| Whole project | `docs/requirements.md` | `docs/requirements.md` |
| One initiative, feature, or major change | `docs/requirements/<initiative>.md` | `docs/requirements/account-recovery.md` |

This is the singleton-and-collection rule defined by DOC-011 and
[ADR-0009](adr/0009-place-project-document-singletons-and-collections.md), not duplicate
placement. The whole-project singleton owns the project purpose, overall scope,
cross-initiative constraints, and project-wide success criteria. Initiative documents
own their independently reviewable requirements and acceptance criteria. Link between
the two scopes instead of repeating facts.

Use one initiative document when its scope, decisions, and acceptance criteria can be
reviewed independently. Keep cross-initiative requirements in the whole-project document
and link to them instead of copying them.

## Naming and language

- Use a stable kebab-case initiative name. Do not add dates or sequence numbers; Git
  records history.
- Include the required YAML frontmatter from the template.
- After template instantiation, AI agents MUST write project-specific requirements in
  Japanese. Translate the copied template's headings and table labels as part of filling
  it. A repository-owner instruction or external contract may explicitly require another
  language (ADR-0005).
- Do not create English and Japanese siblings containing the same requirements
  (DOC-001).

## Update triggers

Create or update the applicable requirements document when project scope, success
metrics, functional or non-functional requirements, constraints, priorities, or
acceptance criteria change. A design or implementation change that does not alter a
requirement links to the existing requirement instead of rewriting it.
