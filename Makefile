# Canonical command interface (CLAUDE.md §11).
# Every agent, hook, and CI job calls ONLY these targets, so automation stays stable
# across stacks. TEMPLATE: replace each no-op with your project's real commands and
# delete the placeholder echo — or start from a reference implementation in profiles/
# (contract semantics: .ai/contracts/foundation/make-targets.md). Optional FILE=<path>
# narrows format/lint to one file.

.PHONY: setup format lint test test-unit test-integration coverage build run \
        security-scan sbom clean help doctor fleet-audit

FILE ?=
FLEET_WORKSPACE_ROOT ?= ..

help: ## List available targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-18s %s\n", $$1, $$2}'

setup: ## Install toolchain and dependencies
	@echo "[template] setup: not wired yet — add your install commands here"

format: ## Auto-format code (all, or FILE=<path>)
	@echo "[template] format: not wired yet (e.g. ruff format / prettier --write / gofmt)"

lint: ## Lint code, zero warnings allowed — COD-001 (all, or FILE=<path>)
	@echo "[template] lint: not wired yet (e.g. ruff check / eslint / golangci-lint)"

test: test-unit test-integration ## Full test suite (unit + integration) — TST-001
	@bash .claude/hooks/tests/guard-bash.test.sh

test-unit: ## Fast unit suite only, used by pre-commit — TST-001
	@python3 -m unittest discover -s scripts/tests -p 'test_*.py'

test-integration: ## Integration suite (may use containers)
	@echo "[foundation] test-integration: not applicable — no external integration surface"

coverage: ## Test with coverage report — TST-003 ratchet
	@rm -rf coverage
	@python3 -m trace --count --missing --summary \
		--ignore-dir '/usr:/opt:/Library' --coverdir coverage \
		--module unittest discover -s scripts/tests -p 'test_*.py'
	@bash .claude/hooks/tests/guard-bash.test.sh

build: ## Produce deployable artifact
	@echo "[template] build: not wired yet"

run: ## Run the application locally
	@echo "[template] run: not wired yet"

security-scan: ## Local security sweep (secrets + deps + config)
	@if command -v gitleaks >/dev/null 2>&1; then gitleaks detect --no-banner; else echo "[template] gitleaks not installed — CI still enforces SEC-002"; fi
	@if command -v trivy >/dev/null 2>&1; then trivy fs --scanners vuln,misconfig,secret --exit-code 1 .; else echo "[template] trivy not installed — CI still enforces SEC-030"; fi

sbom: ## Generate SBOM (SPDX + CycloneDX) into ./dist — REL-020
	@mkdir -p dist
	@if command -v syft >/dev/null 2>&1; then syft . -o spdx-json=dist/sbom.spdx.json -o cyclonedx-json=dist/sbom.cdx.json && echo "SBOM written to dist/"; else echo "[template] syft not installed — release workflow generates the authoritative SBOM"; fi

clean: ## Remove build artifacts
	@rm -rf dist coverage

doctor: ## Self-check the template: metadata invariants + guard-hook tests (foundation-level, stack-independent)
	@bash scripts/template-check.sh
	@bash .claude/hooks/tests/guard-bash.test.sh

fleet-audit: ## Audit every configured local inheritance relationship without writes
	@python3 scripts/template_inheritance.py fleet-audit \
		--config docs/foundation/inheritance-fleet.json \
		--workspace-root "$(FLEET_WORKSPACE_ROOT)"
