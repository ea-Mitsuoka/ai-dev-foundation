---
id: troubleshooting-index
title: Troubleshooting Guide
---

# Troubleshooting

Defines how an instantiated repository records known project failure modes under
`docs/troubleshooting/`: symptom → diagnosis → fix. Unlike runbooks (operational
emergencies), this covers development-time and user-reported problems.

**Update triggers (DOC-030):** every bug fix with a user-visible symptom
(bugfix.skill.md step 7), every support question answered twice, every setup pitfall
discovered.

## Entry format (append to `docs/troubleshooting/known-issues.md`, or use one project

file per area when it grows)

```markdown
## <Exact symptom — the error message or observable behavior, verbatim>

**Affects:** <versions/environments>
**Cause:** <one-sentence root cause>
**Fix:**
1. <exact steps/commands>

**Prevention:** <what stops recurrence, if anything>
**Refs:** #<issue>, <ADR/rule ID if relevant>
```

## Checklist

- Headings are the **verbatim error message** where one exists — that's what agents and
  humans search for.
- Every entry links its issue; entries for fixed bugs state the fixed-in version and
  are deleted once no supported version is affected (DOC-040).
- If diagnosis requires more than 5 steps, it belongs in a runbook — link instead.
