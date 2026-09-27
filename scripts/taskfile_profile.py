#!/usr/bin/env python3
"""Reject unresolved canonical task placeholders outside Foundation (ADR-0026)."""

import argparse
import sys
from pathlib import Path


REQUIRED_TARGETS = (
    "setup",
    "format",
    "lint",
    "test",
    "test-unit",
    "coverage",
    "build",
)


class TaskfileProfileError(ValueError):
    """Raised when a repository has no valid Taskfile profile."""


def _command(line):
    """Return the shell command on one Taskfile line without YAML list or quote syntax."""
    text = line.strip()
    if text.startswith("- "):
        text = text[2:].lstrip()
    if text.startswith("cmd:"):
        text = text[4:].lstrip()
    return text.strip("'\"")


def unresolved_targets(content):
    """Return required targets whose task still echoes the exact template placeholder."""
    commands = [_command(line) for line in content.splitlines()]
    return [
        target
        for target in REQUIRED_TARGETS
        if any(
            command.startswith("echo ") and f"[template] {target}: not wired yet" in command
            for command in commands
        )
    ]


def validate_taskfile(root, *, allow_template_placeholders=False):
    """Validate one repository Taskfile.yml and return unresolved target names."""
    taskfile = Path(root) / "Taskfile.yml"
    try:
        content = taskfile.read_text(encoding="utf-8")
    except OSError as error:
        raise TaskfileProfileError(f"Taskfile.yml cannot be read: {error}") from error

    unresolved = unresolved_targets(content)
    if unresolved and not allow_template_placeholders:
        joined = ", ".join(unresolved)
        raise TaskfileProfileError(
            "Taskfile.yml required tasks still use the template 'not wired yet' "
            f"placeholder: {joined}; wire each task or mark it explicitly not applicable"
        )
    return unresolved


def main(argv=None):
    parser = argparse.ArgumentParser(description="validate required canonical task implementations")
    parser.add_argument("--root", default=".", help="repository root")
    parser.add_argument(
        "--allow-template-placeholders",
        action="store_true",
        help="allow placeholders only for the canonical Foundation template",
    )
    args = parser.parse_args(argv)
    try:
        validate_taskfile(
            args.root,
            allow_template_placeholders=args.allow_template_placeholders,
        )
    except TaskfileProfileError as error:
        print(f"taskfile profile: ERROR: {error}", file=sys.stderr)
        return 1
    print("taskfile profile: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
