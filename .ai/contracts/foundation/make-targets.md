---
id: foundation-make-targets
title: Canonical Make Target Contract
---

# Canonical `make` target contract

Hooks, pre-commit, CI, and agents call only the targets below and depend on these exact
semantics (ADR-0024). This file is inherited: every descendant receives it unchanged and
its `Makefile` MUST implement each target or leave an explicit repository-owned result such
as `[project] build: not applicable — no deployable artifact`. Project-specific targets
may be added freely after them.

## The canonical targets (binding)

| Target | Semantics | Mutates files? | Called by |
|--------|-----------|----------------|-----------|
| `setup` | install toolchain, plugins, git hooks — idempotent | env only | CI (every job), humans |
| `format` | auto-format; honors optional `FILE=<path>` | **yes** | post-edit hook |
| `lint` | **check-only**, zero warnings (COD-001); never fixes | **never** | post-edit hook, pre-commit, CI |
| `test` | full suite (unit + integration) | no | CI, release gate |
| `test-unit` | fast suite, seconds not minutes | no | pre-push hook |
| `test-integration` | slower, real adapters allowed | no | CI |
| `coverage` | tests + coverage report (TST-003 ratchet) | report only | CI |
| `build` | produce/validate the deployable artifact without credentials | artifact only | CI, release |
| `run` | run locally (IaC stacks: alias to plan) | — | humans/agents |
| `security-scan` | local sweep: secrets + deps/misconfig | no | agents, pre-release |
| `sbom` | SBOM into `dist/` (SPDX + CycloneDX) | dist/ only | release, audits |
| `clean` | remove caches/artifacts **inside the workspace only** (GR-031) | yes | humans/agents |
| `doctor` | foundation self-check: metadata invariants + guard-hook tests (stack-independent; keep as-is) | no | CI, agents |

## Implementation rules

1. **`lint` never auto-fixes.** A lint that formats and exits 0 lets CI go green on
   unformatted code and hides the failure from the agent. Fixing is `format`'s job;
   `lint` fails loudly (COD-001).
2. **No catch-all `%:` target.** A `%: @:` pattern makes every typo (`make lnit`) exit 0
   silently and breaks the feedback loop agents depend on (GR-042 in spirit). Pass extra
   arguments through variables (`make destroy DESTROY_ARGS="--from-layer=3"`), never
   through `$(MAKECMDGOALS)`.
3. **Destructive targets follow GR-031:** guarded by an explicit opt-in flag (config
   value or variable), documented as DANGEROUS in `help`, and still subject to
   per-command human approval when an agent runs them.
4. **Network access belongs in `setup`,** not in `lint`/`test` (for example
   `tflint --init`, plugin downloads), so the inner loop stays fast and offline-safe.
5. **No next-step nudges in output.** Output such as "passed! Next: run make deploy"
   steers agents toward actions the result does not justify. State the result; the rules
   decide the next step.
6. **`help` is generated from `##` comments** so it cannot drift from the targets.

## Verifying an implementation

`make doctor` runs `scripts/makefile_profile.py`, which rejects a `Makefile` that still
carries the template `not wired yet` placeholder for a required target. Beyond that,
check by hand: `make lint` on dirty code fails; `make format` fixes it; `make nonexistent`
fails; `make test-unit` finishes in seconds.

## Reference implementations

Stack-specific reference `Makefile`s are repository-owned examples, not part of this
contract. The foundation ships them under `profiles/` (Terraform on GCP, TypeScript on
Node, Python with uv); a descendant receives that directory once at creation and may keep,
change, or delete it. This contract does not depend on it.
