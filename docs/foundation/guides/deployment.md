---
id: deployment-docs
title: Deployment Documentation
---

# Deployment

Defines what an instantiated repository records under `docs/deployment/` to explain how
the project reaches each environment. All infrastructure is code (IaC); manual console
changes are configuration drift and get reverted.

**Update triggers (DOC-030):** new environment variable (also `.env.example`), new
environment, changed deploy procedure, new infrastructure component, changed rollback
procedure.

## Structure

| File | Content |
| -- | -- |
| `docs/deployment/environments.md` | Environment matrix: name, purpose, URL, who may deploy, data class allowed (SEC-011) |
| `docs/deployment/procedure.md` | Deploy pipeline: trigger → stages → verification → rollback; who/what approves (REL-010) |
| `docs/deployment/configuration.md` | Every config variable: name, purpose, per-env source (secret manager path — never values, GR-001) |
| `docs/deployment/provisioning.md` | How to create/modify infrastructure via IaC (`infra/`), state management, review flow |

## Related binding rules

- Environments: at minimum `staging` (production-like, safe for DAST) and `production`.
- Production deployment and rollback follow
  [`.ai/release.md`](../../../.ai/release.md) (REL-010, REL-040).
- Deployment secrets follow [`.ai/guardrails.md`](../../../.ai/guardrails.md)
  (GR-001/003).
- Record smoke verification and rollback procedures under `docs/deployment/` and
  `docs/runbook/`.
