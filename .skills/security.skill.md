---
name: security
description: Security hardening, vulnerability response, and security review of changes
triggers: [vulnerability, CVE, security review, hardening, auth change, pentest finding, セキュリティ, 脆弱性, セキュリティレビュー]
reads: [.ai/security.md, SECURITY.md]
---

# Skill: Security Work

## Purpose

Raise or defend the security posture: fix vulnerabilities correctly, harden defaults,
and verify security properties of changes — without ever lowering the bar (GR-030).

## Inputs

- The trigger: scanner finding (CodeQL/Trivy/gitleaks), advisory, review request, or
  hardening goal. For scanner findings: the exact rule ID and location.
- Data classification of what's at stake (SEC-011).
- The complete guardrails already loaded by the mandatory baseline; reuse them while
  they remain available in the active context, and reread after compaction.
- **Confidentiality check first**: if this is an exploitable vulnerability in shipped
  code, work privately (SEC-040) — no public issues/PRs describing the exploit.

## Process

1. Triage: is it real, is it reachable, what's the impact? Rate severity honestly
   (asset × exploitability). False positive → suppress in scanner config with comment
   - justification, never by disabling the rule globally (GR-030).
2. For leaked secrets: rotation FIRST (the secret is compromised forever — SEC-040),
   then history cleanup, then the process fix that prevents recurrence.
3. Fix at the trust boundary: validate input (SEC-010), enforce authZ in the use case
   (SEC-020), parameterize queries, encode output. Prefer platform/library security
   primitives over hand-rolled logic (SEC-012).
4. Add a test that encodes the security property (e.g. "unauthenticated request to X
   returns 401", "path traversal input is rejected").
5. For dependency CVEs: upgrade > patch > mitigate-and-document, in that order (SEC-030).
6. Verify with the scanner that flagged it; run `task security-scan`.
7. Record: decision log entry; `docs/troubleshooting/`/runbook if operational.

## Decision criteria

- **Severity honest?** If exploitation needs 3 unlikely preconditions, say so; if it's
  pre-auth RCE, drop everything and escalate immediately.
- **Compensating control acceptable?** Only with an ADR and an expiry date.
- **Break something vs stay vulnerable?** Escalate to human with both risks quantified
  (CLAUDE.md §13) — availability vs confidentiality is a human call.
- **Disclose?** Timing and content of any public disclosure is a human decision.

## Outputs

- Fix PR with security-property test; scanner green.
- Rotated credentials (via human) where applicable.
- Suppressions, if any, documented in scanner config with justification.

## Checklist

- [ ] Root cause fixed at the trust boundary, not masked
- [ ] Security property pinned by a test
- [ ] No new secrets, no weakened scans/permissions/TLS (GR-001, GR-030)
- [ ] Leaked secrets rotated before history cleanup
- [ ] Confidentiality maintained until fix released (SEC-040)
