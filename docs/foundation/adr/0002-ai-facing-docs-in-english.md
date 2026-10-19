# ADR-0002: AI-facing docs are written in English

| Field | Value |
| -- | -- |
| Status | accepted |
| Date | 2026-07-02 |
| Deciders | repository owner |
| Author | Claude (AI agent) |
| Supersedes / Superseded by | — |

## Context

The primary maintainers are Japanese speakers, but the primary *readers* of `.ai/`,
`CLAUDE.md`, `.skills/`, and `docs/` are AI agents from multiple vendors. This template
must work across 100+ repositories and any current or future agent. Rule documents
demand minimal interpretation variance (mission constraint: "AI向けに最適化").

## Options considered

### Option 1: Do nothing / Japanese only

Pros: most comfortable for the human owner. Cons: higher token cost (Japanese consumes
roughly 1.5–2× tokens for equivalent content on common tokenizers); slightly higher
interpretation variance across models trained predominantly on English technical text;
harder reuse if repos gain non-Japanese collaborators.

### Option 2: Bilingual (English + Japanese siblings)

Pros: best of both. Cons: two sources drift apart — violates one-fact-one-place
(DOC-001); doubles maintenance for 100+ repos.

### Option 3: English for AI-facing docs; Japanese optional for human-facing docs

Pros: lowest token cost and interpretation variance where it matters; single source of
truth; localized `README.ja.md`-style siblings remain allowed for human-facing docs.
Cons: the human owner reviews rules in a second language.

## Decision

Adopt Option 3. All content in `.ai/`, `CLAUDE.md`, `AGENTS.md`, `.skills/`, and
`docs/` MUST be English (DOC-001). User-facing documents MAY add localized siblings
(e.g. `README.ja.md`) that translate — never extend — the English source.

## Consequences

**Positive:** stable cross-vendor interpretation; lower context cost; one source of truth.

**Negative:** review burden for the owner; mitigated because AI agents can translate
any rule file on demand ("この規約を日本語で要約して" works at zero maintenance cost).

**Follow-ups:** if review burden proves too high in practice, supersede with Option 2
limited to `.ai/` only.
