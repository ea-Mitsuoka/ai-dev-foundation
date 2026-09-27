---
id: development-handoff
title: Development Handoff — {{PROJECT_NAME}}
status: active
updated: {{YYYY-MM-DD: null}: null}
---

<!--
  FOUNDATION TEMPLATE. Copy to docs/development-handoff.md, replace every {{...}}, and
  delete the guidance comments. Translate every heading and table label and write the
  project-specific document in Japanese unless the repository owner or an external
  contract requires another language. Keep this template in English (ADR-0005).

  This is a current restart snapshot, not a project history or duplicate task tracker.
  GitHub issues/milestones own task status and checklists; docs/roadmap.md owns direction;
  ADRs own durable decisions. Link to them instead of copying their contents (DOC-012).
-->

# Development Handoff — {{PROJECT_NAME}}

This document lets the next human or AI agent resume active development safely without
the previous conversation. It reflects the state as of {{YYYY-MM-DD}}.

## Current state

| Field | Current value |
| -- | -- |
| Lifecycle phase | {{intake / clarify / design / implement / self-review / PR / close}} |
| Active issue | {{link or none}} |
| Active pull request | {{link or none}} |
| Working branch | `{{branch or none}}` |
| Last verified baseline | `{{commit, branch, or PR head}}` |
| Active roadmap outcome | {{link to roadmap section and milestone}} |

## Material progress since the previous handoff

| Result | Evidence |
| -- | -- |
| {{outcome that affects the next agent}} | {{issue, PR, commit, test, or document link}} |

<!-- Remove completed detail once it no longer affects the next action. Durable history
     remains in GitHub, releases, ADRs, and the decision log. -->

## Work in progress

| Item | Current state | Owner | Next action |
| -- | -- | -- | -- |
| {{linked issue or PR}} | {{objective status}} | {{owner}} | {{one concrete action}} |

## Blockers and decisions needed

| Blocker or question | Impact | Decision owner | Required by |
| -- | -- | -- | -- |
| {{or "None"}} | {{blocked work}} | {{person or role}} | {{absolute date or milestone}} |

## Ordered next actions

1. {{highest-priority action with issue or PR link}}
2. {{next action}}
3. {{next action}}

## Verification status

| Date | Baseline | Command or check | Result | Evidence |
| -- | -- | -- | -- | -- |
| {{YYYY-MM-DD}} | `{{ref}}` | `{{canonical task target or CI check}}` | {{pass / fail / not run}} | {{link or concise output}} |

## Required reading

1. {{requirements, ADR, module contract, issue, or PR link}}
2. {{next required source}}

## Maintenance checklist

- [ ] Active issue, pull request, branch, and baseline references resolve.
- [ ] Blockers and next actions match current GitHub state.
- [ ] Verification results state what was and was not run.
- [ ] Durable facts link to their authoritative source instead of being duplicated.
- [ ] Completed detail that no longer affects resumption has been removed.
- [ ] No secret, credential, personal data, or sensitive incident detail is present.
