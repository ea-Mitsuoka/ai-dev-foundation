# ai-dev-foundation

<!-- repository-readme-owner: ea-Mitsuoka/ai-dev-foundation -->

**AI-native development foundation** — a template repository for projects where AI
agents (Claude Code, ChatGPT, Gemini, Codex, ...) are the primary developers and humans
direct, decide, and review.

> **AI agents:** stop reading this file. Your entry point is [CLAUDE.md](CLAUDE.md)
> (Claude Code) or [AGENTS.md](AGENTS.md) (everyone else).

## What this template provides

| Layer | Location | Purpose |
|-------|----------|---------|
| Rules (single source of truth) | [`.ai/`](.ai/) | Guardrails, security, architecture, coding, testing, release, docs, review — every rule has a stable ID (GR-010, SEC-020, ...) |
| Agent entry | [`CLAUDE.md`](CLAUDE.md), [`AGENTS.md`](AGENTS.md), [agent profile](.github/inheritance/agent-profile.json) | Thin runtime adapters load the ordered foundation, template, and project instructions |
| Task playbooks | [`.skills/`](.skills/) | 10 vendor-neutral skills: requirements, feature, bugfix, refactor, architecture, test, security, documentation, review, release — also exposed as native Claude Code skills under `.claude/skills/` |
| Enforcement L1 | [`.claude/`](.claude/) | Claude Code hooks (command guard + auto format/lint), a read-only command allow-list, native skill wrappers, and a read-only `code-reviewer` subagent |
| Enforcement L2 | [`.pre-commit-config.yaml`](.pre-commit-config.yaml) | Any committer: secret scan, branch guard, lint, unit tests |
| Enforcement L3 | [`.github/workflows/`](.github/workflows/) | CI, CodeQL, secrets/deps/license scan, container, IaC, DAST, Scorecard, release+SBOM |
| Stable command interface | [`Makefile`](Makefile) | `make test` etc. — the only entry points automation uses |
| Stack profiles | [`profiles/`](profiles/) | Reference Makefile implementations per stack + the canonical target contract |
| Decisions | [`docs/foundation/adr/`](docs/foundation/adr/) | Synchronized foundation ADRs + decision log |
| Knowledge | [`docs/`](docs/) | Architecture, domain, API, deployment, operations, runbook, troubleshooting, roadmap, glossary |
| GitHub scaffolding | [`.github/`](.github/) | Issue forms, PR template, CODEOWNERS, labels-as-code, and Dependabot security settings; version updates use `renovate.json` exclusively |
| GitHub governance | [`.github/governance/`](.github/governance/) + [`scripts/github_governance.py`](scripts/github_governance.py) | Layered policy with `plan`/`audit` and explicitly confirmed administrator `apply` |
| Update distribution | [`template-sync.yml`](.github/workflows/template-sync.yml) + [`.templatesyncignore`](.templatesyncignore) | Foundation updates reach downstream repos as PRs |

## Using this template

1. **Create the repo** from this template (GitHub → "Use this template").
2. **Set project facts**: replace every `{{...}}` placeholder, then update
   [`.ai/project/agent-overlay.md`](.ai/project/agent-overlay.md) with this repository's
   identity and stack. In the [agent profile](.github/inheritance/agent-profile.json),
   keep the foundation input and change the final project input's `repository` value to
   the new `OWNER/REPOSITORY`.
3. **Wire the Makefile**: copy the closest [`profiles/`](profiles/) Makefile to the
   root (or implement `setup/format/lint/test/build` yourself) — everything else
   (hooks, CI) starts working automatically.
4. **Inspect GitHub governance**: run `python3 scripts/github_governance.py plan --root .
   --repo OWNER/REPOSITORY` after `gh auth login`. It reports policy drift without
   changing settings. Use `audit` for a CI-suitable nonzero drift result. After reviewing
   the plan, run `apply` with an exact `--confirm-repo OWNER/REPOSITORY`. The existing
   [`scripts/setup-github.sh`](scripts/setup-github.sh) is a compatibility wrapper for
   the same policy-driven `plan` and explicitly confirmed `apply` paths.
5. **Install local gates**: `make setup && pre-commit install --hook-type pre-commit
   --hook-type pre-push`.
6. **Point your agent at it**: open the repo with Claude Code (reads the thin
   `CLAUDE.md` adapter automatically) or tell any other agent to read `AGENTS.md`.
   The adapter loads the exact ordered files declared by the agent profile. Assign it
   an issue.
   Run the agent inside the [Dev Container](.devcontainer/README.md) so host credentials
   stay out of its reach; customize `.devcontainer/devcontainer.json` for your stack.

Full walkthrough (new machine, different account, gotchas):
[foundation usage guide](docs/foundation/guides/usage.md).

## Design principles

AI First · Secure by Default · Least Privilege · Defense in Depth · Everything as Code
(docs, policy, infra) · Convention over Configuration · Clean Architecture · DDD ·
SOLID · Twelve-Factor · GitHub Flow · Conventional Commits · SemVer.

Why it's built this way: [foundation ADRs](docs/foundation/adr/). How agents behave here:
[.ai/README.md](.ai/README.md).
