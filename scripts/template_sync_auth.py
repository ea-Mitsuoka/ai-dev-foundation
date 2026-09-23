#!/usr/bin/env python3
"""Validate the non-secret boundary for Template Sync source authentication."""

import argparse
import json
import re
import sys
from pathlib import Path


REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
MAX_MANIFEST_BYTES = 1_000_000
MANIFEST_PATH = ".github/inheritance/manifest.json"
# ADR-0025: during adoption (before phase 3 writes the manifest) the parent is declared here.
ADOPTION_MARKER_PATH = ".github/inheritance/adoption.json"
SUPPORTED_MODES = {"public", "github-app"}


class ConfigurationError(ValueError):
    """A safe-to-report Template Sync configuration failure."""


def configured(value: str, name: str) -> bool:
    if value not in {"true", "false"}:
        raise ConfigurationError(f"{name} presence must be true or false")
    return value == "true"


def _present(path: Path) -> bool:
    if path.is_symlink():
        raise ConfigurationError("Template Sync parent declaration must not be a symlink")
    return path.is_file()


def declared_direct_parent(root: Path) -> object:
    """The parent from the manifest, or from the adoption marker before activation."""
    manifest_path = root / MANIFEST_PATH
    marker_path = root / ADOPTION_MARKER_PATH
    has_manifest = _present(manifest_path)
    has_marker = _present(marker_path)
    if has_manifest and has_marker:
        raise ConfigurationError(
            "Template Sync adoption marker must be removed once the manifest exists"
        )
    if not has_manifest and not has_marker:
        raise ConfigurationError(
            "Template Sync requires a child inheritance manifest or adoption marker"
        )
    declaration = manifest_path if has_manifest else marker_path
    try:
        if declaration.stat().st_size > MAX_MANIFEST_BYTES:
            raise ConfigurationError("Template Sync parent declaration is too large")
        document = json.loads(declaration.read_text(encoding="utf-8"))
        if has_marker and document.get("schema_version") != 1:
            raise ConfigurationError("Template Sync adoption marker schema_version must be 1")
        return document["parent"]["repository"]
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, AttributeError) as error:
        raise ConfigurationError(
            "Template Sync could not read the declared direct parent"
        ) from error


def validate(
    root: Path,
    source_repository: str,
    mode: str,
    has_client_id: bool,
    has_private_key: bool,
) -> dict[str, str]:
    if not REPOSITORY.fullmatch(source_repository):
        raise ConfigurationError(
            "Template Sync source repository must be one owner/repository value"
        )
    declared_parent = declared_direct_parent(root)
    if not isinstance(declared_parent, str) or not REPOSITORY.fullmatch(
        declared_parent
    ):
        raise ConfigurationError("Template Sync declared direct parent is invalid")
    if declared_parent != source_repository:
        raise ConfigurationError(
            "Template Sync declared direct parent does not match its workflow source"
        )
    if mode not in SUPPORTED_MODES:
        raise ConfigurationError("Unsupported Template Sync source authentication mode")
    if mode == "github-app" and not (has_client_id and has_private_key):
        raise ConfigurationError("GitHub App source authentication is incomplete")
    owner, repository = source_repository.split("/", 1)
    return {"mode": mode, "owner": owner, "repository": repository}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--source-repository", required=True)
    parser.add_argument("--mode", required=True)
    parser.add_argument("--has-client-id", required=True)
    parser.add_argument("--has-private-key", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        result = validate(
            args.root,
            args.source_repository,
            args.mode,
            configured(args.has_client_id, "GitHub App client ID"),
            configured(args.has_private_key, "GitHub App private key"),
        )
    except ConfigurationError as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
