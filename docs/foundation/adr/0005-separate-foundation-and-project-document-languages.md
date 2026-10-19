# ADR-0005: Separate foundation and project document languages

| Field | Value |
| -- | -- |
| Status | accepted |
| Date | 2026-07-18 |
| Deciders | repository owner (approved 2026-07-18) |
| Author | Codex (AI agent) |
| Supersedes / Superseded by | Partially supersedes ADR-0002 |

## Context

ADR-0002 requires English for all AI-facing and `docs/` content. That rule is suitable
for the reusable governance and instructions maintained in this foundation, but it also
applies to project-specific documents created after the template is instantiated.

The repository owner requires AI agents in instantiated repositories to write project
documents, including requirements definitions, in Japanese. Without an explicit
lifecycle boundary, agents cannot determine whether to follow the foundation's English
maintenance policy or the instantiated project's Japanese documentation policy.

The decision must preserve one source of truth (DOC-001), avoid maintaining bilingual
copies, and keep foundation rules consistent across downstream repositories.

## Options considered

### Option 1: Keep English for all AI-facing and project documents

This retains ADR-0002 unchanged. It has the smallest foundation change and keeps token
cost low, but it does not meet the repository owner's language requirement for project
documents.

### Option 2: Make all foundation and downstream content Japanese

This creates one language rule and is easy for the repository owner to review. It has a
large blast radius, increases divergence from existing foundation documents, and removes
the cross-vendor and token-cost benefits recorded in ADR-0002.

### Option 3: Keep foundation instructions in English and require downstream project documents in Japanese

The reusable foundation rules, agent instructions, skills, templates' maintenance
instructions, and foundation-owned documentation remain English. After instantiation,
AI agents write new project-specific content under `docs/` in Japanese unless an
external contract requires another language. Existing inherited foundation guidance is
not translated solely to satisfy this rule.

This option adds a lifecycle distinction but limits the change to authoring policy. It
is reversible by changing one binding documentation rule and does not affect runtime,
security posture, dependencies, or vendors.

### Option 4: Maintain English and Japanese siblings for every project document

This serves both AI agents and Japanese readers, but duplicates facts, increases
maintenance cost, and creates contradiction risk prohibited by DOC-001.

## Decision

Adopt Option 3. Foundation-owned normative content MUST remain English. In an
instantiated repository, AI agents MUST write new project-specific documents under
`docs/` in Japanese unless the repository owner or an external contract explicitly
requires another language. Agents MUST NOT create an English sibling solely as a
translation. This decision partially supersedes ADR-0002 only for project-specific
documents authored after template instantiation.

## Consequences

**Positive:** downstream project documents use the repository owner's working language;
the foundation retains a single cross-vendor governance source; bilingual drift is
avoided; and agents receive an explicit rule instead of inferring language from nearby
files.

**Negative:** instantiated repositories contain inherited English guidance and newly
authored Japanese project documents; agents must distinguish foundation-owned guidance
from project-specific content; non-Japanese collaborators may require an explicitly
approved language exception.

**Migration and rollback:** existing downstream project documents are not translated
automatically. A repository may migrate them in a separate documentation change. Rollback
requires a superseding ADR and restoration of the ADR-0002 language rule.

**Follow-ups:** update DOC-001 with the lifecycle boundary; add `docs/requirements/` and
its placement rules; update the documentation inventory and update matrix; update the
requirements skill and template guidance if necessary; and record the accepted decision
in `.ai/decision-log.md`.
