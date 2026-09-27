#!/usr/bin/env bash
# Install the pinned go-task release into the directory given as $1 (ADR-0026).
# This file is the single version pin for CI and dev containers. To update, change
# TASK_VERSION and every sha256 value together, copying the values from the release's
# task_checksums.txt; the test pin in scripts/tests/test_setup_task_action.py follows.

set -euo pipefail

TASK_VERSION="3.53.1"

install_directory="${1:-}"
if [ -z "$install_directory" ]; then
  echo "usage: install.sh <install-directory>" >&2
  exit 2
fi

platform="$(uname -s)-$(uname -m)"
case "$platform" in
  Linux-x86_64) asset=task_linux_amd64.tar.gz; sha256=a54a408f6861ff921f6e87774180db31bacd8c1e7c944ca696db9fea49a82fc7 ;;
  Linux-aarch64 | Linux-arm64) asset=task_linux_arm64.tar.gz; sha256=e3ad19101493a0112e1f22ae8ccc54bf03e533b1076a0ca1e6c782a09ad2e588 ;;
  Darwin-x86_64) asset=task_darwin_amd64.tar.gz; sha256=7f1a702d54a789cb818a636039a83df071f4179893133afafa4eba351a7e19ef ;;
  Darwin-arm64) asset=task_darwin_arm64.tar.gz; sha256=85d2d96c2380b33d7855b07b3f7a20dc7ca0eda999a26efa0fb5f6f32b366cd7 ;;
  *)
    echo "setup-task: unsupported platform $platform; install go-task $TASK_VERSION by hand" >&2
    exit 1
    ;;
esac

work_directory="$(mktemp -d)"
trap 'rm -rf "$work_directory"' EXIT
archive="$work_directory/$asset"

curl --fail --silent --show-error --location --retry 3 --proto '=https' --tlsv1.2 \
  --output "$archive" \
  "https://github.com/go-task/task/releases/download/v${TASK_VERSION}/${asset}"

if command -v sha256sum >/dev/null 2>&1; then
  actual="$(sha256sum "$archive" | cut -d ' ' -f 1)"
else
  actual="$(shasum -a 256 "$archive" | cut -d ' ' -f 1)"
fi
if [ "$actual" != "$sha256" ]; then
  echo "setup-task: SHA-256 mismatch for $asset: expected $sha256, got $actual" >&2
  exit 1
fi

tar -xzf "$archive" -C "$work_directory"
mkdir -p "$install_directory"
install -m 0755 "$work_directory/task" "$install_directory/task"
"$install_directory/task" --version
