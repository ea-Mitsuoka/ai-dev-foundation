---
id: documentation
title: Documentation Rules
authority: 4
read_when: [documentation, feature, review]
---

# Documentation Rules

Documentation is code (Documentation as Code): versioned, reviewed in PRs, checked in CI,
and **optimized for AI readers** — explicit, structured, unambiguous.

## DOC-001: Writing style for AI readers

- One fact in one place; link (`[text](path)`) instead of repeating. Duplication causes
  contradiction drift.
- Match form to content using DOC-003. Use absolute dates ("2026-07-02"), never
  "recently".
- Every doc starts with YAML frontmatter (`id`, `title`, plus `status`/`updated` where
  meaningful) and states its purpose in the first paragraph.
- Concrete examples for every rule or API. Fake credentials only (GR-002).
- Foundation-owned instructions and documentation remain English. The only Japanese
  foundation-document exceptions are the descriptive, human-facing
  `docs/foundation/guides/usage.ja.md` and
  `docs/foundation/guides/ai-instruction-files.ja.md`; they never override their English
  authorities, and another exception requires a superseding ADR (ADR-0008). After
  template instantiation, AI agents MUST write new project-specific documents under
  `docs/` in Japanese unless the repository owner or an external contract explicitly
  requires another language. Do not create another translated sibling solely to
  duplicate the same facts (ADR-0005).
- In a leaf repository — one that consumes a template without publishing a contract
  root of its own — pull-request bodies MUST also be Japanese; the title keeps
  Conventional Commits with an English type and scope and a Japanese summary. The
  foundation and the template repositories keep English PR text. Trusted automation
  is exempt, and a reviewer MAY exempt one PR with the `review:language-exception`
  label when the body states the reason. `pr-quality` enforces this through the
  inherited `scripts/pr_language_policy.py` (ADR-0020).
- Files use kebab-case names; headings form a strict hierarchy (one `#`, then `##`...).

## DOC-002: Objective, structured prose

Governs all AI-authored explanatory prose, including `.ai/`, `docs/`, code comments,
commit and pull-request text, issue updates, reviews, and messages to users. Quoted source
text and established domain terms that must be reproduced accurately are outside this
scope. `.skills/requirements.skill.md` and `docs/foundation/templates/requirements.md`
build on this rule.

- **Objective basis.** State each claim with its basis — a measurement, a cited source, a
  standard, or explicit reasoning. Separate established fact, inference, and open
  question; never present an impression as a conclusion.
- **Literal by default; prohibit non-instructive metaphor.** AI authors MUST NOT use
  metaphor, analogy, imagery, personification, or other figurative language merely for
  tone, emphasis, novelty, or decoration. A metaphor MAY be used only when a literal
  explanation alone would be materially less clear and the comparison materially
  improves technical understanding. When used, state the mapped technical elements, the
  specific insight it adds, and where the comparison stops. If all three cannot be stated
  concisely, replace the metaphor with a literal description.
  - Prohibited: "The queue is a shock absorber that protects the system."
  - Required: "The queue buffers temporary request bursts so workers can process requests
    at bounded concurrency; it does not reduce total work and can fill to capacity."
- **No decoration or softening.** Name the thing directly. No filler intensifiers
  ("powerful", "seamless") and no softening ("just", "simply", "a bit").
- **Conclusion first.** State the requested result or action before supporting detail
  when it is known. Do not add a generic narrative introduction.
- **Define once, reference after.** Each term, assumption, and constraint is defined a
  single time, in a dedicated section near the top, then referenced by name. Restating a
  definition is a defect (this is DOC-001 applied to prose).

## DOC-003: Reader-centered logical documentation

Apply this rule when authoring or substantially revising a document. A clear document
lets its intended reader identify the purpose, answer or required action, basis, and
next step with low ambiguity, then update the document from authoritative sources.

- **Start from the reader's task.** State the audience, purpose, scope, and successful
  outcome when they are not obvious. A reader without conversation history must be able
  to use the document.
- **Choose the opening by document type.** Analytical and decision documents lead with
  the answer, then reasons and evidence. Procedures lead with the task outcome,
  prerequisites, ordered actions, verification, and recovery. References lead with the
  contract and then lookup details. Situation–Complication–Question–Answer is optional;
  use it only when the context is needed to understand the answer.
- **Make the logic testable.** A parent statement summarizes its children. Peer sections
  use one classification criterion and level of abstraction, and follow a deliberate
  order such as dependency, time, structure, or importance. Minimize overlap and cover
  what the reader needs; label representative or incomplete sets instead of claiming
  they are mutually exclusive and collectively exhaustive (MECE).
- **Separate statement status.** Distinguish verified fact, inference, accepted decision,
  proposal, assumption, and unresolved question. Give claims their measurement, source,
  standard, or explicit reasoning (DOC-002).
- **Write direct, parallel prose.** Prefer active voice when the actor matters, place an
  applicability condition before its instruction, and keep terms and grammar parallel
  within a list. Use one main claim per sentence and paragraph without separating an
  applicable condition from its action.
- **Match representation to the relationship.** Use numbered lists for ordered actions,
  bullets for peer items, tables for repeated multi-attribute comparisons, and prose for
  reasoning. Use a Mermaid diagram only when it makes a relationship materially easier
  to understand; state its conclusion and essential conditions in equivalent text.
- **Keep hierarchy shallow and semantic.** Headings answer recognizable questions and
  do not skip levels. Group content only by a meaningful reader task or logical category;
  do not create empty headings or deep indentation solely to shorten items.
- **Do not optimize for mechanical limits.** Item counts, sentence or paragraph length,
  MECE, emphasis, tables, and diagrams are review signals, not mandatory limits. Do not
  split meaning to meet a character count, bold every important phrase, or replace clear
  prose with formatting.

## DOC-010: Document inventory and ownership

| Location | Content | Normative? |
|----------|---------|-----------|
| `.ai/` | rules for agents | yes (authority table) |
| `CLAUDE.md`, `AGENTS.md` | agent entry points | yes |
| `docs/foundation/adr/` | synchronized foundation decisions with context | yes (accepted ADRs) |
| `docs/foundation/` | other synchronized foundation-owned guidance and document templates | descriptive |
| `docs/adr/` | repository-specific decisions with context | yes (accepted ADRs) |
| `docs/inheritance/readmes/<owner>/<repository>.md` | repository-owned snapshots of inherited ancestor READMEs | descriptive |
| `docs/requirements.md`, `docs/requirements/` | whole-project and initiative requirements | contract |
| `docs/glossary.md` | project-specific ubiquitous language | descriptive |
| `docs/roadmap.md` | project direction and sequencing | descriptive |
| `docs/development-handoff.md` | resumable current development snapshot | descriptive |
| `docs/architecture/` | diagrams, flows, C4 | descriptive |
| `docs/domain/` | domain model, ubiquitous language | descriptive |
| `docs/api/` | API contracts (OpenAPI etc.) | contract |
| `docs/deployment/`, `docs/operations/`, `docs/runbook/`, `docs/troubleshooting/` | ops | descriptive |
| `src/modules/*/MODULE.md` | module contracts | yes |
| `README.md` | project front door | descriptive |

The structure and update triggers for project-owned `docs/` paths are defined once in
[`docs/foundation/guides/`](../docs/foundation/guides/). A project-owned documentation
directory MUST NOT contain a foundation-owned placeholder README. A repository MAY add
a local README only when it describes actual project content and is maintained by that
repository.

## DOC-011: Project document singleton and collection placement

Choose a project-owned path by document scope
([ADR-0009](../docs/foundation/adr/0009-place-project-document-singletons-and-collections.md)):

| Scope | Required path | Example |
|-------|---------------|---------|
| One authoritative project-wide document | `docs/<category>.md` | `docs/requirements.md` |
| Independently maintained documents that repeat by subject | `docs/<category>/<subject>.md` | `docs/requirements/account-recovery.md` |
| Both project-wide and subject scopes | Use both paths, with distinct ownership | `docs/requirements.md` and `docs/requirements/account-recovery.md` |

The project-wide singleton MUST own cross-subject facts and link to narrower documents.
A subject document MUST own only its narrower facts. Authors MUST NOT repeat the same
fact between the singleton and collection (DOC-001). Create a project-owned directory or
local index only when it contains actual maintained project content; do not create empty
scaffolding or a foundation-owned placeholder in a project namespace.

## Conditional project-document maintenance rules

Read
[`.ai/project-document-maintenance.md`](project-document-maintenance.md)
completely before acting when any trigger matches. If relevance is uncertain, apply the
broader fallback in [`.ai/README.md`](README.md) and read the authority.

| Trigger | Required rule |
|---------|---------------|
| Read or change `docs/development-handoff.md`; transfer active work; change an active issue, pull request, blocker, next action, or verified baseline | DOC-012 |
| Read or change `docs/roadmap.md`; complete a milestone; change project direction, priority, scope, or roadmap review cadence | DOC-013 |
| Read or change the root README, onboarding documentation, or inheritance configuration; trace inheritance provenance | DOC-014 |

## DOC-030: Doc-update matrix (binding — GR-024)

When a PR contains a change of type X, it MUST update the docs listed:

| Change | Must update |
|--------|-------------|
| New/changed project or initiative requirements | `docs/requirements.md` or `docs/requirements/<initiative>.md` |
| New/changed public API | `docs/api/`, MODULE.md, README if user-facing |
| New module / boundary change | `docs/architecture/`, MODULE.md, ADR |
| New env var / config | `.env.example`, `docs/deployment/` |
| New dependency | PR justification (GR-023); `docs/architecture/` if structural |
| Behavior change visible to users | README, CHANGELOG (via commit type) |
| New error state / failure mode | `docs/troubleshooting/`, `docs/runbook/` if ops action needed |
| New or changed reusable foundation term | `docs/foundation/glossary.md` |
| New domain term | `docs/glossary.md` |
| Root README, onboarding, or inheritance configuration read or changed | Verify [DOC-014](project-document-maintenance.md#doc-014-root-readme-ownership) ownership; repair or open a migration issue when mismatched |
| Active work, blocker, next action, or verified baseline changes when a handoff is maintained | Update `docs/development-handoff.md` per [DOC-012](project-document-maintenance.md#doc-012-development-handoff-snapshot) |
| Milestone completes or project direction, priority, or scope changes | Update `docs/roadmap.md` per [DOC-013](project-document-maintenance.md#doc-013-roadmap-completion-and-review) |
| Decision that constrains the future | ADR + `.ai/decision-log.md` |
| Change to how AI should behave | `.ai/*` (via reviewed PR) |

## DOC-040: Freshness protocol

- If you read a doc that contradicts the code: the code is usually truth for *behavior*,
  the doc for *intent*. Investigate, fix the wrong one in the current PR, note it.
- Docs describing removed features are deleted, not marked "deprecated" forever.
- Use the matching `docs/foundation/guides/` entry for directory structure and update
  triggers. If a repository adds a project-owned README, obey its additional local
  triggers as well.
