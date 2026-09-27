# AI Runtime Adapter

Read [CLAUDE.md](CLAUDE.md) completely and follow it before acting; it loads the explicit
agent profile.

| Capability | Runtime equivalent |
| -- | -- |
| Hooks | Run `task format && task lint` after edits (`make` without a root `Taskfile.yml`); guard commands with `.ai/guardrails.md` |
| Skills | Read matching `.skills/*.skill.md` completely |
| Memory | Use runtime context; never store secrets |

Do not duplicate or replace the profile inputs.
