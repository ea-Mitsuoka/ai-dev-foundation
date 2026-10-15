---
name: release
description: Prepare and verify a release; humans approve, agents prepare
triggers: [release, ship, publish version, prepare release, リリース, リリース準備]
reads: [.ai/release.md, .ai/security.md]
---

# Skill: Release Preparation

## Purpose

Get a release candidate to the point where the human's approval is the only remaining
step — all gates verified, risk summarized, rollback ready.

## Inputs

- The release-please Release PR (or the commit range since the last tag).
- Gate definitions: REL-020. Current CI/scan status on `main`.

## Process

1. Verify `main` is green end-to-end; no quarantined tests hiding failures (GR-040).
2. Audit the changelog the automation generated: does every entry match an actual
   commit? Is the version bump correct per REL-001 (especially: any breaking change
   missed because a commit lacked `!`)? Fix by correcting commits/PRs, not by editing
   generated output.
3. Run the gate table (REL-020): tests, CodeQL, Trivy, gitleaks, licenses, SBOM,
   container scan. Record each result verbatim (GR-042).
4. Docs sweep: README quickstart still true? `docs/deployment/` current? New env vars
   in `.env.example`? Migration notes written for any breaking change?
5. Rollback readiness: is the release revertible (REL-040)? For risky releases, write
   the rollback steps into `docs/runbook/` before, not after.
6. Write the risk summary on the Release PR: what changed, blast radius, gates status,
   rollback plan, anything the human should weigh.
7. Hand off: request human approval. **Do not merge the Release PR yourself** (REL-010).
8. After the human merges: verify the release workflow completed — tag, artifacts,
   SBOM attached; smoke-check per runbook. Report completion.

## Decision criteria

- **Gate failed?** Fix-forward on `main` and re-run; never waive a gate (GR-012/GR-030).
  If truly a false positive, fix the gate config in a reviewed PR first.
- **Breaking change discovered late?** Stop; ensure MAJOR bump + migration notes; flag
  prominently in the risk summary.
- **Partial release / cherry-pick request?** Not in GitHub Flow — escalate; the answer
  is usually "revert on main, then release".

## Outputs

- Release PR annotated with gate results + risk summary, ready for human approval.
- Post-merge verification report: tag, artifacts, SBOM, smoke-check.

## Checklist

- [ ] All REL-020 gates green, results recorded verbatim
- [ ] Version bump matches commit history semantics (REL-001)
- [ ] Breaking changes have migration notes; changelog audited
- [ ] Rollback path confirmed (and runbook'd if risky)
- [ ] Human approved the Release PR — not merged by an agent
