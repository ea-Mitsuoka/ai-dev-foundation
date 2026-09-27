---
id: adr-0026
title: ADR-0026 — Replace the canonical make interface with go-task
status: accepted
updated: 2026-09-27
---

# ADR-0026: Replace the canonical make interface with go-task

| Field | Value |
| -- | -- |
| Status | accepted |
| Date | 2026-09-27 |
| Deciders | repository owner (approved 2026-09-27) |
| Author | Claude Opus 5.5 (AI agent) |
| Supersedes / Superseded by | Amends ADR-0024 (the contract file moves) and LOG-0002 (the runner changes); supersedes none |

## Context

The canonical command interface is a set of `make` targets. Their semantics live in the
inherited `.ai/contracts/foundation/make-targets.md` (ADR-0024), and automation calls them
by literal command:

| Caller | Ownership in descendants | Dependency on `make` |
| -- | -- | -- |
| `.claude/hooks/post-edit-quality.sh` | inherited | `make format FILE=…`, `make lint FILE=…` |
| `.pre-commit-config.yaml` local hooks | inherited | `make lint`, `make test-unit` |
| `scripts/actions/release-gates` | inherited | `make setup`, `make test`, `make build` |
| `scripts/template-check.sh` (`doctor`) | inherited | `scripts/makefile_profile.py` reads the root `Makefile` and fails when it is missing |
| CI workflows, `.claude/settings.json` allow list, dev container | protected | `make <target>` |

On 2026-09-27 the repository owner asked to replace `make` with go-task (the `task`
command, configured by `Taskfile.yml`) in the foundation and in every descendant, including
each descendant's project-specific targets. The stated reasons:

- YAML is easier to read than Makefile syntax (tab-indented recipes, `$$` escaping, `ifneq`
  blocks, a `help` target that parses `##` comments with grep and awk), and the owner wants
  to follow the runner the owner regards as the industry standard.
- One entry command on every operating system. Task publishes binaries for Linux, macOS,
  Windows, and FreeBSD (v3.53.1 release assets).
- The same entry point as repositories that already use Task: four projects under
  `ea-ai-demo` keep a root `Taskfile.yml`.

`just` (its own recipe syntax) and mise tasks (TOML) do not meet the YAML requirement.
go-task is MIT-licensed; v3.53.1 was released on 2026-08-18, the fifth minor release since
2026-03-08. Its one published advisory, GHSA-g8jx-8vm6-phr8 (medium, path traversal
through remote Git Taskfiles), affects 3.52.0 and earlier.

Task differs from `make` where the contract depends on runner behavior. Verified with
task 3.53.1 and GNU Make 3.81 on 2026-09-27:

| Behavior | make | task |
| -- | -- | -- |
| Unknown target | exit 2 | exit 200 |
| Catch-all | a `%:` rule accepts any name | a `"*"` task accepts any name and exits 0 |
| Prerequisites | run in order | `deps:` run in parallel; `task:` entries in `cmds:` run in order |
| Recipe shell | `/bin/sh` | embedded interpreter `mvdan.cc/sh` |
| Remote code | none | a URL in `includes:` is downloaded without an opt-in flag |

The fleet has six active descendants: four direct children and two children of
terraform-gcp-template. Each keeps a root `Makefile` with project-specific targets. Three
facts constrain the order of any migration:

1. If inherited automation calls only `task`, every descendant without a `Taskfile.yml`
   fails its post-edit hook, pre-commit hooks, `doctor`, and release gate after its next
   sync.
2. If a descendant deletes its `Makefile` before it receives new automation, its inherited
   `makefile_profile.py` fails closed and `doctor` fails.
3. A root `Taskfile.yml` added by a parent is unowned in every child manifest, so
   `finalize-sync` stops on `ownership_review` until the child declares the path.

Two descendants need more than the standard steps. secure-ai-controls inherits its
`Makefile` from terraform-gcp-template. The `setup`, `inspect`, and `remediation-draft`
targets of secure-ga4-bq-template are called by the external reusable workflow
`ea-Mitsuoka/gcp-cicd-workflows/.github/workflows/bq-inspect.yml`.

## Options considered

### Option 1: Do nothing

- Pros: no migration work; `make` is already present on GitHub-hosted Ubuntu runners (the
  current CI calls it without an install step) and with the macOS command-line tools.
- Cons: meets none of the stated reasons.

### Option 2: Add a Taskfile that delegates to make

Each task calls the matching `make` target; `make` stays canonical.

- Pros: small change; `task --list` works.
- Cons: two entry points for one action; implementations stay in Makefile syntax, so the
  readability reason is not met; the two files can drift apart.

### Option 3: Replace make in one coordinated cutover

Every descendant first adds a `Taskfile.yml` next to its `Makefile`, the foundation then
switches inherited automation to `task` only, and descendants delete their `Makefile`.

- Pros: inherited automation never contains code for two runners.
- Cons: the foundation cannot merge until all six descendants are prepared; a descendant
  that is not prepared fails after its next sync (fact 1); the external caller of
  secure-ga4-bq-template holds back the whole fleet; the intermediate foundation state is
  not releasable on its own.

### Option 4: Replace make through expand, migrate, and contract phases

The foundation first supports both runners, each descendant migrates on its own schedule,
and the foundation removes `make` support after the last descendant has migrated.

- Pros: every repository keeps green checks at every step; one slow descendant delays only
  the final cleanup.
- Cons: inherited automation checks which runner applies until the contract phase; each
  descendant needs two migration pull requests and two sync pull requests.

## Decision

Option 4.

**Interface.** The canonical interface MUST be `task <target>`, run at the repository root
against the root `Taskfile.yml` (`version: "3"`). Target names and semantics stay as the
contract defines them; `FILE=<path>` passes as a Task variable (`task format FILE=<path>`).
The contract MUST move to `.ai/contracts/foundation/task-targets.md`, and ADR-0024's rules
apply to that file. The contract MUST add these rules:

- Every canonical task has a `desc:`, and the default task runs `task --list`; this
  replaces `make help` and the `##` convention.
- No task name accepts arbitrary input: no `"*"` task and no wildcard task that exits 0 for
  an unknown name.
- Ordered steps use `task:` entries in `cmds:`; `deps:` lists only independent steps.
- `includes:` references local files only (GR-030, GR-032).
- Shell logic beyond simple commands belongs in a script called with `bash`, because
  `cmds:` run in Task's embedded interpreter.

**Provisioning.** The Task version MUST be pinned in one place: the inherited composite
action `scripts/actions/setup-task`, which downloads the official release archive, verifies
a pinned SHA-256, and adds `task` to `PATH`. Protected workflows MUST run it before their
first `task` step, and `release-gates` MUST run it itself. The action MUST NOT use a
third-party action; `go-task/setup-task` would add a GPL-3.0 dependency with the same
pinning work. Developer machines and dev containers install the same version by the method
the usage guide documents.

**Transition.** The migration MUST follow these phases in order:

1. Expand (foundation). Inherited automation runs `task` when a root `Taskfile.yml` exists
   and `make` otherwise: the post-edit hook, the pre-commit hooks, `release-gates`, and
   `doctor`, which validates a `Taskfile.yml` with a new `scripts/taskfile_profile.py` and
   falls back to `makefile_profile.py`. The foundation replaces its root `Makefile` and
   `profiles/*/Makefile` with Taskfiles, switches its own CI, settings, dev container, and
   documents, adds `Taskfile.yml` to the export's protected paths, and reduces
   `make-targets.md` to a pointer to `task-targets.md`.

2. Migrate (each descendant). A parent completes all three steps before its children start
   step 2.

   1. Declare `Taskfile.yml` in the manifest with the ownership class of the repository's
      `Makefile`, and in `.templatesyncignore` when it is protected.
   2. Accept the parent sync, including `finalize-sync --apply`.
   3. Replace the `Makefile` with a `Taskfile.yml` that keeps every target, and switch the
      protected callers in the same pull request.

   A descendant that inherits its `Makefile` makes its protected callers accept both
   runners in step 1 and deletes the inherited `Makefile` in the step 2 sync pull request
   that delivers the parent's `Taskfile.yml`. An external caller MUST switch to `task`
   before the repository it calls deletes its `Makefile`.

3. Contract (foundation). After `fleet-audit` is green and no active descendant has a root
   `Makefile`, remove the `make` fallback; delete `makefile_profile.py`, its test, and
   `make-targets.md`; and remove the `Makefile` entries from the export, `.editorconfig`,
   and `.gitattributes`. Each descendant deletes those inherited files in the sync pull
   request that delivers this phase.

## Consequences

**Positive:**

- Canonical targets are written in YAML, and `task --list` is generated from `desc:`
  fields instead of parsed comments.
- A mistyped target still fails (exit 200), which preserves the property the no-catch-all
  rule protects.
- One pinned Task version reaches the CI of every descendant through ordinary sync.
- Fleet repositories and the `ea-ai-demo` projects use one entry command.

**Negative:**

- Task becomes a required tool on every developer machine, dev container, and CI job;
  `make` needed no installation on macOS or GitHub-hosted Ubuntu runners. Some community
  packages install the binary as `go-task`, and the Homebrew formula `task` is Taskwarrior
  (go-task is the formula `go-task`).
- On Windows the entry command is the same, but targets that run `bash scripts/…`,
  including `doctor` and the hook tests, still need bash. This decision does not port them.
- Makefile conditionals (`ifneq`, `$(if …)`, `$(origin …)`) must be rewritten as Go
  template conditions in each descendant.
- Exit codes change (200 for an unknown task, 201 for a failed command, instead of 2);
  callers that check only for success or failure are unaffected.
- The migration takes about 30 pull requests across the seven fleet repositories and
  `gcp-cicd-workflows`. `finalize-sync` refuses to finalize while a file the parent
  deleted remains in the child (`deletion_review`), so each descendant deletes the files
  removed in the contract phase by hand in that sync pull request.
- A version update is a manual pull request that changes the version and checksums
  together; Renovate cannot compute the checksums.

**Follow-ups:**

- Foundation expand pull requests: provisioning action, `taskfile_profile.py`, and runner
  selection in inherited automation; the contract move and the `agent-entry.md`,
  `AGENTS.md`, and test updates; the root `Taskfile.yml` with CI, settings, dev container,
  export, and profiles; the guides and the glossary entry "Canonical command".
- Descendants, in fleet order: the migration steps above for nextjs-saas-template,
  terraform-gcp-template, writing-style, and gc-project-move, then secure-ga4-bq-template
  and secure-ai-controls.
- `gcp-cicd-workflows`: release a `bq-inspect.yml` version that installs Task and calls
  `task` targets before secure-ga4-bq-template deletes its `Makefile`; check whether the
  repository variable `BQ_COST_GATE_COMPILE_COMMAND` names a `make` target.
- Foundation contract pull request after the last descendant migrates.
