# AI Agent Entry Adapter

Identity-free, vendor-neutral adapter. Every agent reads it completely at task start.

1. Read `.ai/guardrails.md` completely.
2. Read `.github/inheritance/agent-profile.json`; require schema version 1 and
   `strengthen-only` or stop.
3. Read each `inputs[].path` completely in listed order; agents must not recursively
   discover directories.
4. Apply foundation first, parent-to-child templates, then project. Later inputs must
   not weaken a foundation MUST, guardrail, or security control.

The loaded foundation contract governs all work. Higher rules win; report conflicts.

## 13. Escalation

See the contract's `Escalation` section.

## 14. Definition of done

See the contract's `Definition of done` section.
