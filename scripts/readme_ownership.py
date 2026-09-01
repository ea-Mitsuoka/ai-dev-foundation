#!/usr/bin/env python3
"""Audit root README ownership without modifying repository files."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


MARKER_PATTERN = re.compile(
    r"^<!-- repository-readme-owner: "
    r"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+) -->$",
    re.MULTILINE,
)
GITHUB_ORIGIN_PATTERNS = (
    re.compile(r"^https://github\.com/([^/]+/[^/]+?)(?:\.git)?$"),
    re.compile(r"^git@github\.com:([^/]+/[^/]+?)(?:\.git)?$"),
    re.compile(r"^ssh://git@github\.com/([^/]+/[^/]+?)(?:\.git)?$"),
)


def repository_from_origin_url(origin: str) -> str:
    for pattern in GITHUB_ORIGIN_PATTERNS:
        match = pattern.fullmatch(origin)
        if match:
            return match.group(1)
    raise ValueError("remote.origin.url is not a credential-free GitHub repository URL")


def repository_from_origin(root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), "config", "--get", "remote.origin.url"],
        check=False,
        capture_output=True,
        text=True,
    )
    return repository_from_origin_url(result.stdout.strip())


def audit_readme(
    root: Path,
    current_repository: str,
    *,
    allow_missing_marker: bool = False,
) -> tuple[list[str], list[str]]:
    readme = root / "README.md"
    if not readme.is_file():
        return ["README.md is missing"], []

    content = readme.read_text(encoding="utf-8")
    markers = MARKER_PATTERN.findall(content)
    marker_declarations = [
        line for line in content.splitlines() if "repository-readme-owner:" in line
    ]
    if marker_declarations and not markers:
        return ["README.md contains a malformed repository-readme-owner marker"], []
    if not markers:
        message = (
            "README.md has no repository-readme-owner marker; migrate when DOC-014 "
            "inspection is triggered"
        )
        if allow_missing_marker:
            return [], [message]
        return [message], []
    if len(markers) != 1:
        return [f"README.md contains {len(markers)} ownership markers; expected exactly one"], []

    declared_repository = markers[0]
    if declared_repository != current_repository:
        owner, repository = declared_repository.lower().split("/", 1)
        archive = f"docs/inheritance/readmes/{owner}/{repository}.md"
        return [
            "README.md belongs to "
            f"{declared_repository}, not {current_repository}; preserve it at {archive} "
            "before replacing the root README, then re-audit GitHub governance with "
            "`python3 scripts/github_governance.py audit --repo "
            f"{current_repository}` — rulesets and repository settings live on GitHub "
            "and do not travel with the git history"
        ], []
    return [], []


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    audit = subparsers.add_parser("audit", help="audit README ownership without writes")
    audit.add_argument("--root", type=Path, default=Path("."))
    audit.add_argument(
        "--allow-missing-marker",
        action="store_true",
        help="warn instead of failing for legacy READMEs without a marker",
    )
    audit.add_argument(
        "--allow-unknown-repository",
        action="store_true",
        help="warn instead of failing when no credential-free GitHub origin is available",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        current_repository = repository_from_origin(args.root)
    except (OSError, ValueError) as error:
        if args.allow_unknown_repository:
            print(f"readme ownership: WARNING: {error}")
            return 0
        print(f"readme ownership: ERROR: {error}", file=sys.stderr)
        return 2

    try:
        errors, warnings = audit_readme(
            args.root,
            current_repository,
            allow_missing_marker=args.allow_missing_marker,
        )
    except (OSError, UnicodeError) as error:
        print(f"readme ownership: ERROR: {error}", file=sys.stderr)
        return 2

    for warning in warnings:
        print(f"readme ownership: WARNING: {warning}")
    for error in errors:
        print(f"readme ownership: ERROR: {error}", file=sys.stderr)
    if errors:
        return 2
    print(f"readme ownership: OK: {current_repository}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
