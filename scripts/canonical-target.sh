#!/usr/bin/env bash
# Run one canonical target through the repository's runner during the ADR-0026
# transition: `task` when the repository root has a Taskfile.yml, otherwise `make`.
# Arguments pass through unchanged: bash scripts/canonical-target.sh format FILE=src/app.py
# Exit 127 means the selected runner is not installed. The contract phase of ADR-0026
# removes this script together with the make fallback.

set -u
cd "$(dirname "$0")/.." || exit 9

if [ "$#" -eq 0 ]; then
  echo "usage: canonical-target.sh <target> [VAR=value ...]" >&2
  exit 2
fi

if [ -f Taskfile.yml ]; then
  runner="task"
else
  runner="make"
fi
if ! command -v "$runner" >/dev/null 2>&1; then
  echo "canonical-target: $runner is not installed (ADR-0026; see scripts/actions/README.md)" >&2
  exit 127
fi

if [ "$runner" = task ]; then
  exec task "$@"
fi
exec make --no-print-directory "$@"
