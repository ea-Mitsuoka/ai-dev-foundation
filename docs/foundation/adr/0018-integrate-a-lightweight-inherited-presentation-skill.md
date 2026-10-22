---
id: adr-0018
title: ADR-0018 — Integrate a lightweight inherited presentation skill
status: accepted
updated: 2026-08-29
---

# ADR-0018: Integrate a lightweight inherited presentation skill

| Field | Value |
| -- | -- |
| Status | accepted |
| Date | 2026-08-29 |
| Deciders | repository owner (approved 2026-08-29) |
| Author | Codex (AI agent) |
| Supersedes / Superseded by | Extends ADR-0014 |

## Context

Repositories based on this foundation sometimes need presentation decks. An agent needs
more than prose guidance to produce a usable deck: it must establish the audience and
decision, build a coherent story, support claims with evidence, create the requested
artifact, render every slide, and inspect the rendered result. Runtime-specific slide
tools already provide different generation capabilities, but relying on them alone does
not establish a common quality or verification contract.

Bundling a complete slide toolchain in every repository would add package managers,
renderers, fonts, images, binary templates, and update obligations to projects that may
never create a deck. A separate mandatory repository would reduce the foundation's
self-contained value and introduce another access and version boundary. The procedure
must also propagate through existing Template Sync without adding a new individually
owned path to every descendant manifest.

## Options considered

### Option 1: Do nothing

Use whichever presentation instructions happen to be available in the current runtime.
This adds no repository weight, but deck quality, evidence handling, and visual
verification vary by runtime and session.

### Option 2: Bundle a complete presentation toolchain

Add generators, renderers, fonts, brand assets, and deck templates to the foundation.
This gives a reproducible local implementation, but increases dependency, license,
security, and maintenance costs for every descendant. It also couples a stack-neutral
foundation to presentation technologies that can change independently.

### Option 3: Maintain all presentation support in a separate repository

Keep both the quality contract and implementation outside the foundation. This isolates
release cadence and large assets, but makes a common capability unavailable when the
separate repository is inaccessible or not installed.

### Option 4: Inherit a lightweight contract and use available runtime adapters

Store one tool-neutral, end-to-end skill under the existing inherited Foundation
contract root. Route only presentation tasks to it. Runtime-specific wrappers invoke
the same body, while the agent selects an already available presentation renderer.
Keep generators, fonts, image collections, binary templates, and other heavy assets out
of the foundation.

## Decision

Adopt Option 4.

The Foundation MUST provide one routed presentation skill that covers task framing,
story design, evidence, artifact generation, complete-slide rendering, visual
inspection, iteration, and delivery. It MUST preserve the requested output format and
existing authorization boundaries; it MUST NOT install dependencies, call an external
service, or fabricate missing evidence without applicable permission.

The canonical skill body lives below `.ai/contracts/foundation/skills/`, which is
already owned and synchronized as a directory under ADR-0014. `.ai/README.md` routes
presentation tasks directly to that body. Runtime-native entry files MAY remain thin
wrappers and MUST NOT duplicate the procedure.

The foundation MUST NOT include presentation runtimes, fonts, image libraries, large
brand assets, or binary deck templates by default. A project may add its own protected
overlay or assets. A separate toolkit becomes appropriate only when a substantial
implementation has an independent release cadence, supports multiple rendering
engines, carries large or licensed assets, needs specialized CI, or has a distinct
access boundary.

## Consequences

**Positive:**

- All descendants receive the same presentation quality and verification contract
  through their existing reviewed Template Sync path.
- Repositories that never create slides gain no runtime dependency or binary weight.
- Agents may use the best presentation capability already available in their runtime
  without changing the expected outcome.
- Complete-slide rendering catches visual defects that source-only review cannot show.

**Negative:**

- Exact visual output may differ across available renderers.
- A repository still needs an authorized local or connected renderer to produce a deck.
- Brand-specific templates and assets remain project-owned and need separate review.
- Runtime wrappers require small compatibility updates when an integration changes.

Rollback removes the route and wrapper while retaining this ADR as decision history.
The skill body can remain harmlessly synchronized until a later reviewed cleanup.

**Follow-ups:**

1. Add the canonical skill, task route, thin Claude Code wrapper, and structural tests.
2. Evaluate an external toolkit only after concrete size, licensing, or release-cadence
   evidence meets the extraction criteria above.
