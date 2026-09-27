#!/usr/bin/env bash
# PostToolUse hook: after any Edit/Write, format and lint the touched file via the
# canonical interface (ADR-0026: `task`, or `make` in a repository without a root
# Taskfile.yml). Non-blocking on template (targets are no-ops until a project wires them)
# and when the runner is not installed; lint failures are surfaced to the agent.
# Contract: hook JSON on stdin; exit 0 = ok; exit 2 = feed stderr back to the agent.

set -u

payload="$(cat)"
file_path=""
if command -v jq >/dev/null 2>&1; then
  file_path="$(echo "$payload" | jq -r '.tool_input.file_path // empty')"
fi
[ -z "$file_path" ] && exit 0

# Skip non-code artifacts to keep the loop fast.
case "$file_path" in
  *.md|*.txt|*.json|*.yml|*.yaml|*.toml|*.lock) exit 0 ;;
esac

canonical_target="$(dirname "$0")/../../scripts/canonical-target.sh"

bash "$canonical_target" format FILE="$file_path" >/dev/null 2>&1

lint_output="$(bash "$canonical_target" lint FILE="$file_path" 2>&1)"
lint_status=$?
# 127: the runner (or the dispatcher itself) is missing — stay non-blocking.
[ "$lint_status" -eq 127 ] && exit 0
if [ "$lint_status" -ne 0 ]; then
  echo "Lint failed for $file_path (COD-001 — fix before proceeding):" >&2
  echo "$lint_output" | tail -n 30 >&2
  exit 2
fi

exit 0
