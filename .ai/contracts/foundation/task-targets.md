---
id: foundation-task-targets
title: Canonical Task Target Contract
---

# Canonical `task` target contract

Hooks, pre-commit, CI, and agents call only the targets below and depend on these exact
semantics (ADR-0024, ADR-0026). This file is inherited: every descendant receives it
unchanged and its root `Taskfile.yml` MUST implement each target or leave an explicit
repository-owned result such as `[project] build: not applicable — no deployable artifact`. Project-specific tasks may be added freely after them.

Run a target at the repository root as `task <target>` and pass a variable as
`task format FILE=<path>`. A repository without a root `Taskfile.yml` has not completed its
ADR-0026 migration: it runs the same targets as `make <target>` from its `Makefile`, and
the inherited automation reaches either runner through `scripts/canonical-target.sh`.

## The canonical targets (binding)

| Target | Semantics | Mutates files? | Called by |
| -- | -- | -- | -- |
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
2. **No task accepts arbitrary names.** Task exits 200 for an unknown name, so a typo
   (`task lnit`) fails. Define no `"*"` task and no wildcard task that exits 0 for an
   unknown name: either makes every typo succeed silently and breaks the feedback loop
   agents depend on (GR-042 in spirit). Pass extra arguments through variables
   (`task destroy DESTROY_ARGS="--from-layer=3"`).
3. **Destructive tasks follow GR-031:** guarded by an explicit opt-in flag (config value
   or variable), marked DANGEROUS in their `desc:`, and still subject to per-command human
   approval when an agent runs them.
4. **Network access belongs in `setup`,** not in `lint`/`test` (for example
   `tflint --init`, plugin downloads), so the inner loop stays fast and offline-safe.
5. **No next-step nudges in output.** Output such as "passed! Next: run task deploy"
   steers agents toward actions the result does not justify. State the result; the rules
   decide the next step.
6. **`task --list` is the help.** Every canonical task has a `desc:`, so the listing is
   generated from the tasks and cannot drift from them; the default task runs
   `task --list`.
7. **Ordered steps are `task:` entries in `cmds:`.** Task runs `deps:` in parallel, so
   `test` calls `test-unit` and then `test-integration` as `cmds:` entries; `deps:` lists
   only steps that are independent of each other.
8. **Only local includes.** `includes:` references files in the repository. Task
   downloads a URL include without an opt-in flag, which would run unreviewed content
   (GR-030, GR-032).
9. **Shell logic beyond simple commands lives in scripts.** `cmds:` run in Task's embedded
   interpreter (`mvdan.cc/sh`), not the system shell; call a script with `bash` for
   anything longer than a simple command.

## Verifying an implementation

The `doctor` target runs `scripts/taskfile_profile.py`, which rejects a `Taskfile.yml` that
still carries the template `not wired yet` placeholder for a required target; a
repository without a root `Taskfile.yml` is checked by `scripts/makefile_profile.py`
instead. Beyond that, check by hand: `task lint` on dirty code fails; `task format` fixes
it; `task nonexistent` fails; `task test-unit` finishes in seconds.

## Reference implementations

Stack-specific reference implementations are repository-owned examples, not part of this
contract. The foundation ships them under `profiles/` (Terraform on GCP, TypeScript on
Node, Python with uv); a descendant receives that directory once at creation and may keep,
change, or delete it. This contract does not depend on it.
