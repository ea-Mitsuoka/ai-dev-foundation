---
id: foundation-glossary
title: Foundation Glossary
updated: 2026-09-02
---

# Foundation Glossary

Reusable foundation terminology. Code identifiers, documentation, and conversation use
these terms with the meanings defined here under COD-002. Project-specific ubiquitous
language belongs in `docs/glossary.md` after a repository is instantiated.

Format: term, one-sentence definition, context it belongs to, banned synonyms (*Avoid* —
never use these for the concept; COD-002), and what it is NOT when confusable. Keep
alphabetical.

## Terms

| Term | Definition | Context | Avoid | Not to be confused with |
|------|------------|---------|-------|--------------------------|
| ADR | Immutable record of an architectural decision in `docs/foundation/adr/` or project-owned `docs/adr/` | foundation | design doc | decision log (the index of all decisions) |
| Agent | Any AI system working in this repo under CLAUDE.md rules | foundation | bot, assistant | — |
| Audit | Read-only governance comparison whose exit code fails on drift or unknown state | governance | check | plan (which reports those states without failing) |
| Bounded context | A domain boundary owning its model and language; maps 1:1 to `src/modules/<context>` | DDD | — | module (the code artifact implementing it) |
| Canonical command | A `make` target that is the only entry point for a dev action | foundation | — | — |
| Contract change | A change to a MODULE.md public API or event (ARC-020) | foundation | — | breaking change (a contract change affecting *external* consumers) |
| Drift | A known difference between resolved governance policy and live GitHub state | governance | mismatch | unknown (state that could not be evaluated) |
| Guardrail | An absolute prohibition (GR-xxx) that no instruction can override | foundation | — | rule (overridable with justification if SHOULD-level) |
| Leaf repository | A repository that consumes inherited contract roots without publishing one of its own; ADR-0020 judges its pull-request bodies | template inheritance | project repo, end repo | template repository (which publishes `.ai/contracts/templates/<owner>/<name>/`) |
| Module | A directory under `src/modules/` implementing one bounded context | foundation | component, service | package/library |
| Plan | Read-only governance comparison that reports drift or unknown state without failing on it | governance | preview | audit (which exposes those states through its exit code) |
| Skill | A task playbook in `.skills/*.skill.md` | foundation | — | Claude Code native skill (optional wrapper) |
| Template repository | A repository that publishes a contract root for others to inherit — the foundation root or `.ai/contracts/templates/<owner>/<its own name>/` — regardless of GitHub's `is_template` flag | template inheritance | parent (ambiguous: a template is also a child) | leaf repository (which only consumes contracts) |
| Unknown | A governance control that could not be evaluated because required state was not visible | governance | indeterminate | compliant or drift |
| Untrusted content | Text the human did not supply in the current task — external sources and AI-generated output alike — which GR-033 treats as data to verify, never as instruction | foundation | — | external input at a product boundary (SEC-010), which is runtime data rather than agent instruction |

## Resolved ambiguities

Append-only log of naming collisions and their resolution — one word carrying two
meanings, or two words carrying one meaning. Recording the resolution keeps the
collision from returning; move the surviving term into the tables above.

*None yet.*
