---
id: skills-index
title: Agent Skill Library
---

# .skills/ — Agent Skill Library

Vendor-neutral task procedures. Each `*.skill.md` is a self-contained playbook an agent
loads **when the task matches** (routing table: `.ai/README.md`). Plain Markdown — works
with Claude Code, ChatGPT, Gemini, Codex, or a human.

Foundation-owned skills that must propagate without adding a new manifest path MAY use
`.ai/contracts/foundation/skills/<name>/SKILL.md` as their canonical body under
ADR-0014. The routing table names that body directly; runtime-native entries remain thin
wrappers. `.skills/*.skill.md` remains the canonical body for the skills stored in this
directory.

## Format contract

Every `*.skill.md` playbook in this directory has YAML frontmatter (`name`,
`description`, `triggers`, `reads`) and these sections, in order:

1. **Purpose** — what outcome this skill produces
2. **Inputs** — what must exist/be known before starting (and how to get it)
3. **Process** — numbered steps
4. **Decision criteria** — how to choose when the process forks
5. **Outputs** — artifacts that must exist when done
6. **Checklist** — final verification (all boxes must pass)

## Inventory

| Skill | Use when |
| -- | -- |
| [requirements.skill.md](requirements.skill.md) | defining what to build (requirements definition) |
| [feature.skill.md](feature.skill.md) | implementing new functionality |
| [bugfix.skill.md](bugfix.skill.md) | fixing incorrect behavior |
| [refactor.skill.md](refactor.skill.md) | restructuring without behavior change |
| [architecture.skill.md](architecture.skill.md) | changing structure/boundaries/tech (needs ADR) |
| [test.skill.md](test.skill.md) | adding/improving tests |
| [security.skill.md](security.skill.md) | security hardening, vuln response, audits |
| [documentation.skill.md](documentation.skill.md) | writing/maintaining docs |
| [review.skill.md](review.skill.md) | reviewing a PR or self-reviewing |
| [release.skill.md](release.skill.md) | preparing a release |

The inherited [presentation skill](../.ai/contracts/foundation/skills/presentation/SKILL.md)
creates or revises slide decks and requires render-based visual verification.

## Claude Code native integration

Every skill above, including the inherited presentation skill, is exposed as a native
Claude Code skill under `.claude/skills/<name>/SKILL.md`, so it is invokable directly
(e.g. `/requirements`). Each wrapper is only frontmatter plus one instruction that loads
its canonical body. Never fork procedure content into a wrapper.

When you add a new skill here, add its matching `.claude/skills/<name>/SKILL.md` wrapper in
the same PR. Other agents (ChatGPT/Gemini/Codex) ignore the wrappers and read `.skills/`
directly via the routing table.
