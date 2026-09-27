---
id: release
title: Release Policy
authority: 4
read_when: [release]
---

# Release Policy

Versioning: **Semantic Versioning 2.0.0**, derived automatically from Conventional
Commits by release-please (`.github/workflows/release.yml`).

## REL-001: Version derivation

| Commit type since last release | Bump |
| -- | -- |
| any `!` / `BREAKING CHANGE:` | MAJOR |
| any `feat` | MINOR |
| only `fix`/`perf`/others | PATCH |

Never hand-edit version numbers or CHANGELOG — both are generated. Fixing a wrong
version means fixing the commit history convention, not the output.

## REL-010: Release flow

```
merge to main → release-please opens/updates a Release PR (version + changelog)
→ human approves & merges the Release PR          ← human gate, always
→ tag created → release workflow runs gates (REL-020)
→ artifacts + SBOM attached to the GitHub Release
```

AI agents prepare releases (verify gates, summarize risk in the Release PR) but MUST NOT
merge the Release PR — release approval is a human decision (mission.md).

## REL-020: Pre-release gates (all must pass)

| Gate | Tool | Blocking |
| -- | -- | -- |
| Full test suite | `task test` | yes |
| SAST | CodeQL latest run green | yes |
| Dependency vulnerabilities | Trivy (no CRITICAL/HIGH unfixed) | yes |
| Secret scan | gitleaks | yes |
| License check | REL-030 | yes |
| SBOM generated | Syft (SPDX + CycloneDX) | yes |
| Container scan (if image) | Trivy image | yes |
| Docs current | doc-update matrix spot-check | yes |

## REL-030: License policy

Allowed for dependencies: MIT, Apache-2.0, BSD-2/3-Clause, ISC, MPL-2.0 (dynamic use).
Forbidden without explicit ADR: GPL/AGPL family in distributed code, SSPL, BUSL,
no-license packages. CI enforces via license scan; exceptions live in the scanner
config with an ADR link.

## REL-040: Rollback

Every release must be revertible: prefer roll-forward (`revert:` commit → patch
release); keep migrations backward-compatible for one version (expand → migrate →
contract). Document rollback steps for risky releases in `docs/runbook/`.

## REL-050: Hotfix

Branch `fix/...` from `main` (GitHub Flow has no separate hotfix track), minimal diff,
regression test mandatory, expedited review still required — GR-010 has no exceptions.
