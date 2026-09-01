---
id: usage
title: Usage — New Machine, New Account, New Project
updated: 2026-08-30
---

# Usage

> Japanese human-facing version: [usage.ja.md](usage.ja.md) (ADR-0008 exception).

This guide covers using the foundation from a different machine or a different GitHub
account. **First decide which of two scenarios you are in — the steps differ.**

| Scenario | You want to... | Use |
|----------|----------------|-----|
| A | Start a **new project** built on this foundation | GitHub **"Use this template"** (not `git clone`) |
| B | Continue developing **this foundation itself** on another machine | `git clone` |

`git clone` alone is only the right answer for Scenario B. For Scenario A, cloning would
drag this repo's history and identity into your new project; use the template flow.

---

## Scenario A — start a new project from the template

Select the parent by the contract the repository needs now, then initialize its explicit
inheritance metadata.

### 1. Choose the direct parent template

Use the closest maintained template whose exported contract applies to the repository's
**primary deliverable**:

| Current repository role | Direct parent |
|-------------------------|---------------|
| General project with no applicable maintained specialization | `ea-Mitsuoka/ai-dev-foundation` |
| Terraform-managed Google Cloud infrastructure is the primary deliverable and the Terraform family overlay plus `iac-scan` are required | `ea-Mitsuoka/terraform-gcp-template` |
| A Next.js SaaS application needs the maintained Next.js family and SaaS template contract | `ea-Mitsuoka/nextjs-saas-template` |
| Another maintained template exports a family or product contract the repository needs now | That intermediate template |

Incidental use of Terraform or Google Cloud does not select `terraform-gcp-template`.
Likewise, using Next.js does not by itself select `nextjs-saas-template`; the maintained
family and product contract must apply to the repository now. Do not choose a parent for
a possible future need. Do not bypass an applicable intermediate template:
direct-parent provenance and family overlays require every hop.

### 2. Create the new repo from the selected template

Web: open the template repo → **Use this template** → **Create a new repository**.

CLI (equivalent):
```bash
gh repo create <your-account>/<new-project> \
  --template <selected-owner>/<selected-parent> \
  --private --clone
cd <new-project>
```
This gives you a **fresh repo with clean history** under your account.

Record the selected parent's exact 40-character commit at creation. Do not replace that
evidence later with a newer branch head that was not the instantiated source.

### 3. Establish inheritance and repository ownership

Complete these items in one reviewed initialization PR:

1. Set `.github/inheritance/manifest.json` to the selected direct parent and classify
   every path as inherited, protected, or deliberately unowned. Use the schema in the
   [inheritance contract](../../../.github/inheritance/README.md).
2. Set `.github/inheritance/lock.json` to the exact parent commit used for creation.
3. Set `.github/inheritance/agent-profile.json` to foundation, applicable intermediate
   template inputs in parent-to-child order, then the new repository's project input.
   Keep `.ai/project/agent-overlay.md` and the profile protected.
4. Before replacing the copied root README, preserve it under
   `docs/inheritance/readmes/<owner>/<repository>.md`; set the root ownership marker to
   the new `OWNER/REPOSITORY` (DOC-014).
5. Make `.templatesyncignore` cover every protected root and all workflows. Extra
   repository-owned exclusions are allowed; the two lists do not need to be identical.
6. Validate locally before enabling scheduled PR creation:

```bash
make doctor
python3 scripts/template_inheritance.py validate --root .
python3 scripts/template_inheritance.py plan \
  --root . --parent-root ../<selected-parent-worktree>
```

After the initialization PR is green and merged, a repository whose direct parent is
readable by its workflow may opt in to daily reviewed synchronization:

```bash
gh variable set TEMPLATE_SYNC_ENABLED --body true
```

When the direct parent is private, keep this variable disabled until the protected
workflow has the approved split-credential implementation and that edge has completed the
bounded pilot required by
[ADR-0016](../adr/0016-gate-private-fleet-automation-on-split-credentials.md).
Follow the single source of operational steps in
[Authenticate a private direct parent](../../../.github/inheritance/README.md#authenticate-a-private-direct-parent).
Do not make a repository public as an authentication workaround.

For an intermediate parent, the agent profile MUST include its owner-qualified template
overlay. Propagation then proceeds parent to child one merged hop at a time.

### 3.1. Review and finalize each synchronization PR

Template Sync is single-flight: one repository may have only one open
`chore/template_sync_*` PR. A later scheduled or manual run reports the existing PR
instead of creating duplicate review work. Parent changes that arrive while it is open
are collected after that PR merges.

Review the exact direct-parent source and inherited delta, then use the local
`finalize-sync` preview on the synchronization branch. Apply only after the preview is
`ready_to_finalize`; the apply step completes supported manual boundaries and advances
the lock in the same PR. It never commits, pushes, merges, calls GitHub, or changes
governance. Use the authoritative commands and blocker meanings in the
[inheritance contract](../../../.github/inheritance/README.md#plan-single-pr-finalization).

Every resulting PR still requires normal CI and human review. Merge an intermediate
template before synchronizing its direct children; never skip a hop or auto-merge.

### 4. Replace template placeholders

Every customizable value is a `{{...}}` token. Find them all:
```bash
grep -rn "{{" . --exclude-dir=.git
```
Replace at minimum the `{{...}}` values in `.ai/mission.md`; `{{ORG}}` in
`.github/CODEOWNERS`, `.github/ISSUE_TEMPLATE/config.yml`, and
`.github/workflows/template-sync.yml`; and `{{PACKAGE}}` if you use the Python profile.

Project identity and stack facts do not belong in `CLAUDE.md`. Update
`.ai/project/agent-overlay.md` for the new repository. In
`.github/inheritance/agent-profile.json`, keep the foundation input unchanged and set
the final project input's `repository` to the new `OWNER/REPOSITORY`. Keep the profile
and project overlay protected when you add a child inheritance manifest.

### 5. Fix CODEOWNERS for your account type

`.github/CODEOWNERS` ships with **team** references (`@{{ORG}}/maintainers`). Teams only
exist under **GitHub Organizations**. On a **personal account**, replace them with your
username:
```
*   @your-username
```
Leaving team syntax on a personal repo makes CODEOWNERS silently ineffective —
fix this file before applying governance because account-type inference is outside the
compatibility wrapper.

### 6. Pick a Makefile profile

Copy the closest reference implementation to the repo root and wire it to your stack:
```bash
cp profiles/python-uv/Makefile ./Makefile      # or typescript-node / terraform-gcp
```
See [profiles/README.md](../../../profiles/README.md) for the canonical target contract.
After instantiation, `make doctor` rejects the template `not wired yet` implementation
for required targets. If a target does not apply, replace it with an explicit
repository-owned result such as `[project] build: not applicable — no deployable
artifact`; do not retain the template placeholder.

### 7. Inspect GitHub governance

```bash
python3 scripts/github_governance.py validate --root .
python3 scripts/github_governance.py plan --root . --repo OWNER/REPOSITORY
python3 scripts/github_governance.py audit --root . --repo OWNER/REPOSITORY
python3 scripts/github_governance.py apply --root . --repo OWNER/REPOSITORY \
  --confirm-repo OWNER/REPOSITORY

# Compatibility entry point for the same plan/apply paths:
DRY_RUN=1 bash scripts/setup-github.sh OWNER/REPOSITORY
bash scripts/setup-github.sh OWNER/REPOSITORY --confirm-repo OWNER/REPOSITORY
```

`validate` is offline and automatically resolves the foundation, the single profile
chain in `.github/governance/profiles/`, and repository policy. Required checks are
monotonic: profiles and repository policy add checks but cannot remove foundation
checks. `plan` and `audit` use authenticated, GET-only `gh api` calls and
print the same redacted JSON comparison. The comparison flags a required check name that
is not observed on the target branch head and ignores unrelated observed checks. `plan`
returns 0 after a completed comparison; `audit` returns 1 for drift or permission-limited
unknown state. Both return 2 for policy, input, or GitHub read failures.

See [GitHub governance troubleshooting](../troubleshooting/github-governance.md) for an
`audit` exit 1 diagnosis.

Re-run `audit` whenever the repository identity changes — a transfer, a move to another
account, or a fresh child created from the bootstrap export. Rulesets and repository
settings are GitHub objects, not files, so they do not travel with the history. A move
therefore lands on a repository with no branch ruleset, leaving GR-010, GR-011, and
GR-012 without server-side enforcement while the local hooks still pass.
`scripts/readme_ownership.py` is what detects the identity change, and its failure
message names this command.

Review `plan` before `apply`. Only `apply` changes settings; it requires local repository
Administration access and an exact target confirmation, then verifies each action by
read-back. Policy enforces squash-only merges and lets repository overrides choose
Discussions and squash commit-message defaults. The setup compatibility wrapper makes no
direct `gh` call: `DRY_RUN` maps to `plan`, while normal execution requires the exact
target twice and maps to `apply`. Its exit code is the reconciler exit code.

Migration from the fixed script: the no-argument form is removed, and the wrapper no
longer prints CODEOWNERS or other manual onboarding reminders. Pass the target explicitly
as shown above and use this guide as the onboarding checklist.

### 8. Install local gates and point your agent at it

```bash
make setup                             # installs deps + pre-commit hooks
```
Open the repo with Claude Code (it reads the thin `CLAUDE.md` adapter automatically) or
tell any other agent to read `AGENTS.md`. The adapter validates the explicit agent
profile and loads every listed foundation, template, and project input in order. Assign
it an issue and go.

The template ships a worked example module (`src/modules/catalog/` + `tests/modules/catalog/`)
— imitate its shape (COD-050) or delete both when you start real code. Run `make doctor`
anytime to self-check the template (frontmatter integrity + guard-hook tests).

---

## Scenario B — clone the foundation itself onto another machine

```bash
git clone https://github.com/ea-Mitsuoka/ai-dev-foundation.git
cd ai-dev-foundation
# The bare template's root Makefile is a no-op, so `make setup` does nothing here.
# Install the git hooks directly (needs pre-commit — see prerequisites):
pre-commit install --hook-type pre-commit --hook-type pre-push
make doctor                            # verify the template is intact
```
That is genuinely "just clone" — but each new machine still needs the one-time
**prerequisites** and **auth** below.

### Audit the maintained fleet

Foundation maintainers can verify every configured active direct-parent relationship
from explicitly refreshed sibling worktrees:

```bash
make fleet-audit FLEET_WORKSPACE_ROOT=/path/to/worktrees
```

The command is local, read-only, credential-free, and does not create approval work.
The canonical fleet file records `active`, `paused`, and `retired` relationships. Run it
from the `ai-dev-foundation` worktree; descendant Makefiles do not inherit this target.
See [Audit the fixed fleet](../../../.github/inheritance/README.md#audit-the-fixed-fleet)
for workspace requirements and result semantics. A scheduled private fleet audit remains
disabled under ADR-0016 even after private Template Sync is enabled.

---

## Per-machine prerequisites (both scenarios)

Install once on each new machine:

| Tool | Needed for | Notes |
|------|-----------|-------|
| `git`, `make` | everything | — |
| `gh` (GitHub CLI) | Governance `plan`/`audit`/`apply`, compatibility setup, auth | `gh auth login` |
| `pre-commit` | local commit gates | `make setup` (once a profile is wired) or `pre-commit install` |
| Stack toolchain | build/test | uv (python), pnpm+node (ts), terraform (iac) — per your profile |
| `gitleaks`, `trivy`, `syft` | local `make security-scan` / `sbom` | optional locally; **CI enforces them regardless** |

The scanners are optional on your laptop — the GitHub Actions workflows run them on every
PR, so a missing local tool only means you don't see findings until CI.

---

## Gotchas (read before you hit them)

### `workflow` OAuth scope is required to push
Pushing any change under `.github/workflows/` needs the token's `workflow` scope. If
`git push` is rejected with *"refusing to allow an OAuth App to create or update
workflow ... without workflow scope"*:
```bash
gh auth refresh -h github.com -s workflow
```
This is a **per-account / per-machine** setting — expect to do it once on each new setup.

### Solo developer + branch protection = you can't merge your own PRs
Set `required_approvals` in `.github/governance/repository.json` to match the repository.
Requiring one approval on a repo with no second reviewer prevents self-merge. Choose one:

- **Recommended (keeps the guardrail):** add a second collaborator/reviewer, or enable
  the AI reviewer ([ai-review.yml](../../../.github/workflows/ai-review.yml)) — note an AI
  review comment does not count as a GitHub *approval*, so for true self-merge you still
  need option below.
- **Solo pragmatic:** set `"required_approvals": 0` in repository policy.
  You still branch + PR + green CI (GR-010, GR-021); you just merge it yourself.

`scripts/setup-github.sh` delegates to the same repository policy, so the configured
approval count applies equally through the direct CLI and compatibility entry point.

### Line endings
`.gitattributes` enforces LF repo-wide, so shell hooks and Makefiles stay valid on
Windows. Don't override with a global `core.autocrlf=true` that fights it — the
`.gitattributes` wins for matched files, but keep your Git default sane.

### Placeholders that break automation if left unreplaced
`{{ORG}}` in `template-sync.yml` and `CODEOWNERS`, and the issue-config URLs, are the
ones that cause silent failures (ineffective CODEOWNERS, a sync job that can't find its
source). The template-sync job is gated off by default (`TEMPLATE_SYNC_ENABLED`), so it
stays inert until you deliberately enable it.

---

## Quick answer: "is `git clone` enough on a different account?"

- **To develop this foundation** (Scenario B): yes — `git clone`, install the
  pre-commit hooks directly, run `make doctor`, and refresh the `workflow` OAuth scope
  on that machine when you need to push workflow changes.
- **To start a new project** (Scenario A): no — use "Use this template", then the
  initialization steps above. Cloning would give the new project this repo's history and
  placeholders instead of a clean start.
