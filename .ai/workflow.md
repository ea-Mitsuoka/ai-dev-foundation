---
id: workflow
title: Development Workflow
authority: 4
read_when: [always-summary, feature, bugfix]
---

# Development Workflow

Model: **GitHub Flow.** `main` is always releasable; all work happens on short-lived
branches merged via PR.

## WF-001: Task lifecycle

Every task follows these phases. Do not skip phases; do report which phase you are in.

```
1. INTAKE     — restate goal; read routing table and handoff if present; locate an issue
2. CLARIFY    — list assumptions & open questions; escalate via the loaded contract
3. DESIGN     — impact classification (ARC-020); ADR if architectural (GR-022)
4. IMPLEMENT  — branch → code + tests together → docs in same PR (GR-024)
5. SELF-REVIEW— run .ai/review-checklist.md against your own diff
6. PR         — open PR per WF-030; respond to review findings
7. CLOSE      — verify DoD; update decision-log and maintained handoff when triggered
```

## WF-010: Branch naming

`<type>/<issue-id>-<slug>` — e.g. `feat/123-user-invitations`, `fix/207-null-avatar`.
Types match Conventional Commit types (WF-020). Branches live days, not weeks.

## WF-020: Commit rules (Conventional Commits 1.0.0)

```
<type>(<scope>)!: <imperative summary ≤ 72 chars>

<body: what & why, wrapped at 100>

Refs: #<issue>
```

- Types: `feat` `fix` `refactor` `perf` `test` `docs` `build` `ci` `chore` `revert`.
- Scope = module name where applicable (`feat(billing): ...`).
- `!` + `BREAKING CHANGE:` footer for anything that breaks a consumer (drives SemVer).
- One logical change per commit; the diff must match the message.
- Commits MUST NOT mix `refactor` with behavior types (COD-021).

## WF-021: AI-authorship trailers (`Co-Authored-By`)

Whether commits carry an AI co-author trailer (e.g.
`Co-Authored-By: Claude <noreply@anthropic.com>`) is a **per-repository decision**,
because GitHub renders the trailer and thereby discloses AI involvement in history and PRs.

- This template's default: **include it** — transparency about how the code was produced.
- Client / engagement repos where disclosure conflicts with the contract MUST turn it off,
  record the decision in `.ai/decision-log.md`, and enforce it. The reliable mechanism is a
  local `commit-msg` git hook that strips the trailer — instructing the agent alone is not
  auditable. Never use this to hide authorship where disclosure is required.
- Whichever way a repo sets it, apply it consistently; do not toggle per commit.

## WF-030: Pull request rules

- Size: within GR-020 limits.
- Title: Conventional Commit format (squash-merge uses it).
- Body: fill every section of `.github/PULL_REQUEST_TEMPLATE.md` — including the
  AI-disclosure block and the dependency-justification block when applicable.
- CI green before requesting review. Never merge with failing or skipped checks (GR-012).
- Merge strategy: squash. Delete branch after merge.

## WF-040: Parallel-agent protocol

Multiple AI agents may work simultaneously. To avoid collisions:

- One branch = one agent = one task. Never commit to another agent's branch.
- Claim work by assigning the GitHub issue / adding `status:in-progress` label.
- Contract changes (ARC-020 "Contract" scope) are serialized: announce in the issue,
  land quickly; other agents rebase.
- Rebase your branch on `main` before opening the PR; resolve conflicts yourself.

## WF-090: Definition of Done

A task is done only when ALL hold:

- [ ] Acceptance criteria of the issue met
- [ ] Tests added/updated and `task test` green (TST rules)
- [ ] `task lint` and `task format` clean
- [ ] Docs updated per doc-update matrix (DOC-030)
- [ ] Maintained `docs/development-handoff.md` updated when active state changed (DOC-012)
- [ ] Self-review against `.ai/review-checklist.md` done
- [ ] PR opened with template fully filled; CI green
- [ ] No guardrail violated
