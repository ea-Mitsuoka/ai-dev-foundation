---
id: project-documentation-guide
title: Project Documentation Guide
---

# Project Documentation Guide

This guide defines where an instantiated repository stores project-owned documentation.
Binding rules live in [`.ai/`](../../../.ai/); inherited decisions live in the
[foundation ADRs](../adr/), project decisions live in `docs/adr/`, and writing rules live in
[`.ai/documentation.md`](../../../.ai/documentation.md).

| Directory | Content | Primary reader task |
| -- | -- | -- |
| [docs/foundation/adr/](../adr/) | Synchronized foundation Architecture Decision Records (**normative** when accepted) | "why does the inherited foundation work this way?" |
| `docs/adr/` | Project Architecture Decision Records (**normative** when accepted) | "why is this project built this way?" |
| [docs/foundation/](../) | Synchronized foundation-owned guidance and document templates | use inherited documentation support |
| `docs/inheritance/readmes/<owner>/<repository>.md` | Repository-owned snapshots of inherited ancestor READMEs | retain parent context without misidentifying the current repository |
| `docs/requirements.md`, `docs/requirements/` | Project-owned whole-project and initiative requirements | determine what must be built and why |
| `docs/architecture/` | System structure, C4 diagrams, data flows | understand before changing structure |
| `docs/domain/` | Domain model, bounded contexts, ubiquitous language | understand the business rules |
| `docs/api/` | API contracts (OpenAPI/schema + commentary) | integrate with or change an API |
| `docs/deployment/` | Environments, deploy procedure, configuration | ship it |
| `docs/operations/` | Monitoring, alerts, SLOs, maintenance | keep it running |
| `docs/runbook/` | Step-by-step incident/ops procedures | 3am emergency |
| `docs/troubleshooting/` | Known failure modes → diagnosis → fix | "it's broken, what now?" |
| `docs/roadmap.md` | Direction and planned milestones | prioritize work |
| `docs/development-handoff.md` | Current resumable snapshot for active work spanning sessions or agents | resume work safely |
| `docs/glossary.md` | Project ubiquitous language dictionary | name things correctly |

Internal development follows [the workflow](../../../.ai/workflow.md) and
[the usage guide](usage.md). The private foundation does not ship a repository-level
open-source license or public contribution guide. Do not recreate those files during
initialization or synchronization without an explicit owner decision. Preserve
third-party license notices and dependency license checks.

## Choose a project-owned path by scope

Use the singleton-and-collection rule from DOC-011 and
[ADR-0009](../adr/0009-place-project-document-singletons-and-collections.md):

| Question | Placement |
| -- | -- |
| Is this the one authoritative document for the whole project? | `docs/<category>.md` |
| Can independently maintained documents repeat by initiative, component, audience, or operational subject? | `docs/<category>/<subject>.md` |
| Are both scopes needed? | Keep both; the singleton links to the subject documents without copying their facts |

For requirements, the resulting structure is:

```text
docs/
├── requirements.md
└── requirements/
    ├── account-recovery.md
    └── subscription-billing.md
```

`docs/requirements.md` owns the project purpose, overall scope, cross-initiative
constraints, and project-wide success criteria. Each file below `docs/requirements/`
owns requirements and acceptance criteria that can be reviewed independently for its
named initiative. The whole-project document links to those files and does not restate
their details.

This pairing is not required for every category. Keep unique cross-project documents
such as `docs/roadmap.md` and `docs/glossary.md` at the top level. Use categorized paths
such as `docs/architecture/data-flow.md` and `docs/runbook/credential-rotation.md` for
repeatable or task-specific documents. Do not add an empty directory or local index in
anticipation of future content.

## Keep direction, tasks, and handoff separate

| Concern | Authoritative location | Content |
| -- | -- | -- |
| Project direction | `docs/roadmap.md` | `Now` / `Next` / `Later`, milestone outcomes, completion evidence |
| Live task status and checklists | GitHub issues and milestones | owners, task-level progress, acceptance and completion checklists |
| Resumable current snapshot | `docs/development-handoff.md` | active references, blockers, next actions, last verified baseline |
| Durable decisions | `docs/adr/`, `.ai/decision-log.md` | decision, rationale, consequences |

Create `docs/development-handoff.md` from the foundation template when active work will
continue across sessions or agents. Read it at task intake and update it before transfer
or when its active references, blockers, next actions, or verification status change.
Keep it short and link to the authoritative sources above.

Roadmaps are reviewed weekly while a project is active unless the repository declares a
different cadence. Each current outcome links to a milestone or tracking issue that owns
its completion checklist. A roadmap review checks completed outcomes, records an
absolute completion date plus evidence link, re-sequences direction, and removes stale
detail; it does not copy individual completed tasks from GitHub.

## Own the root README

The root README is a singleton owned by the current repository. It contains the marker
defined by
[DOC-014](../../../.ai/project-document-maintenance.md#doc-014-root-readme-ownership):

```html
<!-- repository-readme-owner: owner/repository -->
```

During repository initialization, replace inherited parent content with a README for
the new repository. Before replacement, preserve each inherited README at the
owner-qualified lowercase path:

```text
README.md
docs/
└── inheritance/
    └── readmes/
        └── parent-owner/
            └── parent-repository.md
```

Add this frontmatter above the preserved content:

```yaml
---
id: inherited-readme-parent-owner-parent-repository
title: Inherited README — parent-owner/parent-repository
source-repository: parent-owner/parent-repository
source-commit: 0123456789abcdef0123456789abcdef01234567
---
```

Use the accepted direct-parent lock or other verified Git provenance for
`source-commit`; use `unknown` when the exact commit is unavailable. Preserve the source
language and substantive content, then repair links relative to the archive location.
Review an existing archive before replacing it. Multiple ancestors coexist because the
owner-qualified paths do not collide.

Run `task doctor` after changing the README or inheritance configuration. For
compatibility with existing repositories, a missing marker produces a migration warning.
A present marker that names another repository is an error. The audit never moves,
rewrites, or deletes files.

Archived READMEs are not normal task context. Do not load or summarize
`docs/inheritance/readmes/**` during routine intake or broad documentation discovery.
Read one only to migrate or review README ownership, or to trace inheritance provenance.

The guides in this directory define structure and **update triggers** without placing
foundation-owned README files in project-owned paths. The doc-update matrix (DOC-030)
tells you which project directory a given change must touch.
