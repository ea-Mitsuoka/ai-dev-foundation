---
name: requirements
description: Produce a requirements definition document — purpose-driven, zero-based, objective, complete
triggers: [requirements definition, 要件定義, spec a feature, write requirements, scope a project, interrogate the plan, grill me]
reads: [.ai/mission.md, .ai/documentation.md, docs/foundation/templates/requirements.md]
---

# Skill: Requirements Definition

## Purpose

Derive an objective, complete requirements definition from the goal rather than from an
existing solution, so design and acceptance testing can proceed without re-asking.

## Inputs

- Goal, affected users, and measurable success definition from the human or issue.
- Scope boundaries from [.ai/mission.md](../.ai/mission.md).
- The required structure and field guidance in
  [docs/foundation/templates/requirements.md](../docs/foundation/templates/requirements.md).

## Process

1. **Fix the purpose.** State one objective and measurable success metrics first. Every
   requirement must trace to one of them.
2. **Resolve open decisions one fork at a time.** Start with the fork whose alternatives
   would produce the most divergent implementations: scope, users, owned data,
   constraints, success thresholds, then risky edge cases. Present a recommended draft
   answer for correction, not a blank or bulk questionnaire. Investigate factual
   codebase questions yourself. Continue until no unresolved fork materially changes the
   purpose; escalate materially ambiguous goals under CLAUDE.md §13. When a confirmed
   answer fixes the meaning of a term, record it in `docs/glossary.md` at that moment,
   with rejected synonyms in the *Avoid* column, and challenge wording that conflicts
   with an existing entry. Write only confirmed meanings; proposals stay in the
   conversation.
3. **Derive the ideal set zero-based.** Use only the purpose and resolved decisions.
   Existing implementation must not define the ideal requirements.
4. **Trace, then reconcile.** Delete candidates that trace to no purpose or metric. Only
   after the ideal set exists, inspect existing assets, constraints, and platform limits;
   record every forced deviation and its reason.
5. **Classify and prioritize.** Assign stable FR-00x/NFR-00x IDs and MoSCoW priority with
   a one-line basis. State what must hold and why; move unsupported technology choices to
   design.
6. **Instantiate the template completely.** Follow every embedded instruction and retain
   every applicable section. Define terms once, keep unresolved items only under Open
   questions, and apply the placement and project-language rules in `.ai/documentation.md`.
7. **Verify and self-review.** Check the completed document against the template and the
   checklist below, then `.ai/review-checklist.md`. Open a `docs:` PR or include it in the
   initiating feature PR.

## Decision criteria

| Decision | Rule |
| -- | -- |
| Functional or non-functional | System behavior is FR; a measurable property is NFR. |
| Scope | No purpose or metric trace means non-scope unless the human decides otherwise. |
| Priority | Must means the purpose fails; rank Should/Could by metric contribution and record Won't as deferred. |
| Requirement or design | Technology requires a recorded constraint; otherwise specify outcomes. |
| Sensitive area | Escalate CLAUDE.md §13 triggers before finalizing. |

## Outputs

- A complete template instance at the singleton or initiative path defined by DOC-011,
  written in Japanese unless an explicit exception applies.
- Unique, prioritized, traced FRs/NFRs; open questions and escalations kept explicit.

## Checklist

- [ ] Open decisions resolved one fork at a time with recommended drafts
- [ ] Confirmed terms recorded in `docs/glossary.md` when confirmed; conflicts with
  existing entries raised
- [ ] Ideal requirements derived before reconciliation with the implementation
- [ ] Every requirement has an ID, priority, trace, and objective verification method
- [ ] Every applicable template section completed; non-scope and open questions explicit
- [ ] DOC-002/DOC-003 prose, structure, and project language/placement rules satisfied
