#!/usr/bin/env python3
"""Validate declared AI context routes and model-independent size budgets."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path, PurePosixPath


BASELINE_FILES = (
    "AGENTS.md",
    "CLAUDE.md",
    ".ai/README.md",
    ".ai/guardrails.md",
)
CANONICAL_GUARDRAILS = ".ai/contracts/foundation/guardrails.md"
# Raised with GR-033 (untrusted content is never instruction). ADR-0012 requires a
# justified budget increase rather than dropping an always-binding rule to fit: the old
# 18_500/2_600 pair left 28 bytes under the 90% band, so the warning gate had become a
# hard gate against adding any guardrail.
BASELINE_BYTE_LIMIT = 20_000
BASELINE_WORD_LIMIT = 2_800
ROUTE_BYTE_LIMIT = 46_000
ROUTE_WORD_LIMIT = 6_500
SOFT_BUDGET_RATIO = 0.9
HANDOFF_WORD_WARNING = 1_500
HANDOFF_STALE_DAYS = 30
READS_PATTERN = re.compile(r"^reads:\s*\[(.*)]\s*$", re.MULTILINE)
FRONTMATTER_PATTERN = re.compile(r"^---\n(?P<body>.*?)\n---\n", re.DOTALL)
ADR_ROW_PATTERN = re.compile(
    r"^\| \[(?P<number>\d{4})\]\((?P<target>[^)]+)\)"
    r" \| (?P<title>[^|]+) \| (?P<scope>[^|]*)"
    r" \| (?P<status>[^|]*) \| (?P<updated>[^|]*) \|$",
    re.MULTILINE,
)
GUIDE_ROW_PATTERN = re.compile(
    r"^\| \[(?P<label>[^]]+\.md)\]\((?P<target>[^)]+\.md)\) \| [^|]+ \|$",
    re.MULTILINE,
)
GLOB_CHARACTERS = frozenset("*?[")
REQUIRED_READS = {
    "architecture": {".ai/architecture.md", "docs/foundation/adr/README.md"},
    "bugfix": {".ai/workflow.md", ".ai/testing.md"},
    "documentation": {".ai/documentation.md", "docs/foundation/guides/README.md"},
    "feature": {
        ".ai/workflow.md", ".ai/architecture.md", ".ai/coding-rules.md", ".ai/testing.md",
    },
    "refactor": {".ai/architecture.md", ".ai/coding-rules.md", ".ai/testing.md"},
    "release": {".ai/release.md", ".ai/security.md"},
    "requirements": {
        ".ai/mission.md", ".ai/documentation.md", "docs/foundation/templates/requirements.md",
    },
    "review": {".ai/review-checklist.md"},
    "security": {".ai/security.md", "SECURITY.md"},
    "test": {".ai/testing.md", ".ai/coding-rules.md"},
}
BASELINE_CONTRACT_MARKERS = {
    "AGENTS.md": (
        "CLAUDE.md",
        "completely and follow it before acting",
        "explicit agent profile",
        "make format && make lint",
        ".ai/guardrails.md",
        ".skills/*.skill.md",
        "never store secrets",
        "Do not duplicate or replace the profile inputs",
    ),
    "CLAUDE.md": (
        "Identity-free, vendor-neutral adapter",
        "Every agent reads it completely at task start",
        ".ai/guardrails.md",
        ".github/inheritance/agent-profile.json",
        "schema version 1",
        "strengthen-only",
        "inputs[].path",
        "listed order",
        "must not recursively",
        "foundation first",
        "must not weaken a foundation MUST",
        "loaded foundation contract governs",
        "report conflicts",
    ),
    ".ai/contracts/foundation/agent-entry.md": (
        "Apply instructions in this order",
        "docs/development-handoff.md",
        "Broaden discovery whenever relevance or correctness is uncertain",
        ".ai/workflow.md",
        ".ai/review-checklist.md",
        "Conventional Commits",
        "SemVer",
        "make doctor",
        ".claude/README.md",
        "Claude Code reads",
        "authentication, payments",
        "production configuration",
        "WF-090",
        "Report exactly what was and was not verified",
    ),
    ".claude/README.md": (
        "Hooks in `.claude/settings.json` enforce the command guard",
        "Fix hook failures; never bypass them",
        "`.skills/*.skill.md` is the vendor-neutral skill source",
        "`.claude/skills/` contains only native wrappers",
        "Store only durable, non-derivable, non-secret facts in runtime memory",
        "Follow WF-040 for subagents and parallel work",
        "one task, one branch, one agent",
    ),
    ".ai/guardrails.md": (
        ".ai/contracts/foundation/guardrails.md",
        "Read it completely before any task work",
        "MUST NOT duplicate guardrail rules",
    ),
    ".ai/contracts/foundation/guardrails.md": (
        "Never write secrets into the repository",
        "Never push directly to main/master",
        "Never bypass hooks or checks",
        "Never lower the security level",
        "Never run destructive operations without explicit human approval",
        "Never fabricate results",
    ),
    ".ai/README.md": (
        "Quality takes priority over context reduction",
        "Read every file selected by the baseline or task route completely",
        "Broaden discovery and reading until uncertainty is resolved",
        "Never use a context budget to skip a relevant source",
        "Reading protocol by task type",
    ),
}


@dataclass(frozen=True)
class Counts:
    bytes: int = 0
    words: int = 0

    def __add__(self, other: "Counts") -> "Counts":
        return Counts(self.bytes + other.bytes, self.words + other.words)


@dataclass(frozen=True)
class ConditionalAuthority:
    name: str
    target: str
    references: tuple[tuple[str, tuple[str, ...]], ...]
    target_markers: tuple[str, ...]


CONDITIONAL_AUTHORITIES = (
    ConditionalAuthority(
        name="project-document-maintenance",
        target=".ai/project-document-maintenance.md",
        references=(
            (
                ".ai/documentation.md",
                (
                    "project-document-maintenance.md",
                    "docs/development-handoff.md",
                    "roadmap",
                    "root README",
                    "broader fallback",
                ),
            ),
            (
                ".skills/documentation.skill.md",
                (
                    ".ai/project-document-maintenance.md",
                    "read it completely",
                    "broader fallback",
                ),
            ),
            (
                ".ai/README.md",
                ("project-document-maintenance.md",),
            ),
        ),
        target_markers=("## DOC-012:", "## DOC-013:", "## DOC-014:"),
    ),
)


def count_file(path: Path) -> Counts:
    content = path.read_text(encoding="utf-8")
    return Counts(len(content.encode("utf-8")), len(content.split()))


def parse_reads(skill_file: Path) -> list[str]:
    match = READS_PATTERN.search(skill_file.read_text(encoding="utf-8"))
    if not match:
        raise ValueError(f"{skill_file}: missing one-line reads declaration")
    return [value.strip() for value in match.group(1).split(",") if value.strip()]


def frontmatter_value(path: Path, key: str) -> str | None:
    match = FRONTMATTER_PATTERN.match(path.read_text(encoding="utf-8"))
    if not match:
        return None
    key_match = re.search(
        rf"^{re.escape(key)}:\s*(?P<value>.+?)\s*$",
        match.group("body"),
        re.MULTILINE,
    )
    return key_match.group("value") if key_match else None


def adr_metadata_value(path: Path, key: str) -> str | None:
    frontmatter_key = "updated" if key == "date" else key
    value = frontmatter_value(path, frontmatter_key)
    if value is not None:
        return value

    label = "Date" if key == "date" else key.title()
    match = re.search(
        rf"^\| {re.escape(label)} \| (?P<value>.+?) \|$",
        path.read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    return match.group("value") if match else None


def duplicate_values(values: list[str]) -> list[str]:
    return sorted(value for value, count in Counter(values).items() if count > 1)


def baseline_contract_errors(root: Path) -> list[str]:
    errors: list[str] = []
    for value, markers in BASELINE_CONTRACT_MARKERS.items():
        path = root / value
        if not path.is_file():
            errors.append(f"{value}: canonical contract file is missing")
            continue
        normalized = " ".join(path.read_text(encoding="utf-8").split())
        errors.extend(
            f"{value}: missing canonical baseline marker: {marker!r}"
            for marker in markers
            if marker not in normalized
        )
    return errors


def validate_adr_index(root: Path) -> list[str]:
    directory = root / "docs/foundation/adr"
    index = directory / "README.md"
    if not index.is_file():
        return ["foundation ADR index is missing: docs/foundation/adr/README.md"]

    entries = [match.groupdict() for match in ADR_ROW_PATTERN.finditer(
        index.read_text(encoding="utf-8")
    )]
    actual_targets = {
        path.name for path in directory.glob("[0-9][0-9][0-9][0-9]-*.md")
    }
    indexed_targets = [entry["target"] for entry in entries]
    errors = [
        f"foundation ADR index: duplicate target: {target}"
        for target in duplicate_values(indexed_targets)
    ]
    errors.extend(
        f"foundation ADR index: duplicate number: {number}"
        for number in duplicate_values([entry["number"] for entry in entries])
    )
    errors.extend(
        f"foundation ADR index: missing entry: {target}"
        for target in sorted(actual_targets - set(indexed_targets))
    )
    errors.extend(
        f"foundation ADR index: stale entry: {target}"
        for target in sorted(set(indexed_targets) - actual_targets)
    )

    for entry in entries:
        target = entry["target"]
        if target not in actual_targets:
            continue
        if not target.startswith(f"{entry['number']}-"):
            errors.append(
                f"foundation ADR index: label {entry['number']} does not match {target}"
            )
        if not entry["scope"].strip():
            errors.append(f"foundation ADR index: {target}: Scope is empty")

        adr_path = directory / target
        for field, key in (("status", "status"), ("updated", "date")):
            indexed_value = entry[field].strip()
            actual_value = adr_metadata_value(adr_path, key)
            if not indexed_value:
                errors.append(
                    f"foundation ADR index: {target}: {field.title()} is empty"
                )
            elif actual_value != indexed_value:
                errors.append(
                    f"foundation ADR index: {target}: {field} "
                    f"{indexed_value!r} != document metadata {actual_value!r}"
                )
    return errors


def validate_guide_index(root: Path) -> list[str]:
    directory = root / "docs/foundation/guides"
    index = directory / "README.md"
    if not index.is_file():
        return ["foundation guide index is missing: docs/foundation/guides/README.md"]

    entries = [match.groupdict() for match in GUIDE_ROW_PATTERN.finditer(
        index.read_text(encoding="utf-8")
    )]
    actual_targets = {
        path.name for path in directory.glob("*.md") if path.name != "README.md"
    }
    indexed_targets = [entry["target"] for entry in entries]
    errors = [
        f"foundation guide index: duplicate target: {target}"
        for target in duplicate_values(indexed_targets)
    ]
    errors.extend(
        f"foundation guide index: missing entry: {target}"
        for target in sorted(actual_targets - set(indexed_targets))
    )
    errors.extend(
        f"foundation guide index: stale entry: {target}"
        for target in sorted(set(indexed_targets) - actual_targets)
    )
    for entry in entries:
        if entry["label"] != entry["target"]:
            errors.append(
                "foundation guide index: "
                f"label {entry['label']!r} does not match target {entry['target']!r}"
            )
    return errors


def handoff_warnings(root: Path, *, current_date: date) -> list[str]:
    handoff = root / "docs/development-handoff.md"
    if not handoff.is_file():
        return []

    warnings: list[str] = []
    counts = count_file(handoff)
    if counts.words > HANDOFF_WORD_WARNING:
        warnings.append(
            "development handoff is unusually large: "
            f"{counts.words} words > {HANDOFF_WORD_WARNING}; "
            "remove completed history and link authoritative records"
        )

    updated = frontmatter_value(handoff, "updated")
    try:
        updated_date = date.fromisoformat(updated or "")
    except ValueError:
        warnings.append(
            "development handoff has a missing or invalid ISO updated date"
        )
        return warnings

    age = (current_date - updated_date).days
    if age < 0:
        warnings.append(
            f"development handoff updated date is {abs(age)} days in the future"
        )
    elif age > HANDOFF_STALE_DAYS:
        warnings.append(
            "development handoff may be stale: "
            f"updated {age} days ago > {HANDOFF_STALE_DAYS}"
        )
    return warnings


def route_path_error(root: Path, value: str) -> str | None:
    route_path = PurePosixPath(value)
    if route_path.is_absolute() or ".." in route_path.parts:
        return "must be a repository-relative path without traversal"
    if value.endswith("/") or any(character in value for character in GLOB_CHARACTERS):
        return "must name one file, not a directory or glob"
    resolved = root / route_path
    try:
        canonical = resolved.resolve(strict=True)
    except OSError:
        return "does not exist as a readable file"
    if not canonical.is_relative_to(root.resolve()):
        return "must not resolve outside the repository"
    if canonical.is_dir():
        return "must name one file, not a directory"
    if not canonical.is_file():
        return "does not exist as a readable file"
    return None


def active_baseline_files(root: Path) -> tuple[list[str], tuple[str, ...]]:
    """Resolve an optional explicit agent profile without directory discovery."""
    errors: list[str] = []
    files = list(BASELINE_FILES)
    guardrail_entry = root / ".ai/guardrails.md"
    if (
        guardrail_entry.is_file()
        and CANONICAL_GUARDRAILS
        in guardrail_entry.read_text(encoding="utf-8")
    ):
        files.append(CANONICAL_GUARDRAILS)
    profile_name = ".github/inheritance/agent-profile.json"
    profile_path = root / profile_name
    if not profile_path.is_file():
        return errors, tuple(files)
    files.append(profile_name)

    try:
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return [f"agent profile is not readable JSON: {error}"], tuple(files)
    if not isinstance(profile, dict):
        return ["agent profile must be an object"], tuple(files)
    if set(profile) != {"schema_version", "authority_policy", "inputs"}:
        errors.append(
            "agent profile must contain only schema_version, authority_policy, inputs"
        )
    if (
        type(profile.get("schema_version")) is not int
        or profile.get("schema_version") != 1
    ):
        errors.append("agent profile.schema_version must be 1")
    if profile.get("authority_policy") != "strengthen-only":
        errors.append("agent profile.authority_policy must be strengthen-only")

    inputs = profile.get("inputs")
    if not isinstance(inputs, list) or len(inputs) < 2:
        errors.append(
            "agent profile.inputs must contain foundation and project inputs"
        )
        return errors, tuple(files)

    layers: list[str] = []
    seen_paths: set[str] = set()
    for index, item in enumerate(inputs):
        if not isinstance(item, dict) or set(item) != {"layer", "repository", "path"}:
            errors.append(
                f"agent profile.inputs[{index}] must contain only layer, repository, path"
            )
            continue
        layer = item["layer"]
        path = item["path"]
        if not isinstance(layer, str):
            errors.append(f"agent profile.inputs[{index}].layer must be a string")
        else:
            layers.append(layer)
        if not isinstance(path, str):
            errors.append(f"agent profile.inputs[{index}].path must be a string")
            continue
        reason = route_path_error(root, path)
        if reason:
            errors.append(f"agent profile.inputs[{index}].path {path}: {reason}")
            continue
        if path in seen_paths:
            errors.append(f"agent profile contains duplicate path: {path}")
            continue
        seen_paths.add(path)
        files.append(path)

    if layers and (
        layers[0] != "foundation"
        or layers[-1] != "project"
        or any(layer != "template" for layer in layers[1:-1])
    ):
        errors.append(
            "agent profile input order must be foundation, zero or more templates, project"
        )
    return errors, tuple(files)


def validate_conditional_authorities(
    root: Path,
    contracts: tuple[ConditionalAuthority, ...],
) -> tuple[list[str], dict[str, Counts]]:
    errors: list[str] = []
    measurements: dict[str, Counts] = {}
    for contract in contracts:
        target_error = route_path_error(root, contract.target)
        if target_error:
            errors.append(
                f"conditional authority {contract.name}: "
                f"{contract.target}: {target_error}"
            )
        else:
            target = root / contract.target
            normalized = " ".join(target.read_text(encoding="utf-8").split())
            measurements[contract.name] = count_file(target)
            errors.extend(
                f"conditional authority {contract.name}: "
                f"{contract.target}: missing target marker: {marker!r}"
                for marker in contract.target_markers
                if marker not in normalized
            )

        for reference, markers in contract.references:
            reference_error = route_path_error(root, reference)
            if reference_error:
                errors.append(
                    f"conditional authority {contract.name}: "
                    f"{reference}: {reference_error}"
                )
                continue
            normalized = " ".join(
                (root / reference).read_text(encoding="utf-8").split()
            )
            errors.extend(
                f"conditional authority {contract.name}: "
                f"{reference}: missing reference marker: {marker!r}"
                for marker in markers
                if marker not in normalized
            )
    return errors, measurements


def budget_findings(
    label: str,
    actual: Counts,
    limit: Counts,
    *,
    enforce: bool,
) -> tuple[list[str], list[str]]:
    exceeded = []
    if actual.bytes > limit.bytes:
        exceeded.append(f"{actual.bytes} bytes > {limit.bytes}")
    if actual.words > limit.words:
        exceeded.append(f"{actual.words} words > {limit.words}")
    if not exceeded:
        soft_limit_exceeded = []
        if actual.bytes >= limit.bytes * SOFT_BUDGET_RATIO:
            soft_limit_exceeded.append(f"{actual.bytes}/{limit.bytes} bytes")
        if actual.words >= limit.words * SOFT_BUDGET_RATIO:
            soft_limit_exceeded.append(f"{actual.words}/{limit.words} words")
        if not soft_limit_exceeded:
            return [], []
        return [], [
            f"{label} context budget at or above "
            f"{SOFT_BUDGET_RATIO:.0%}: {', '.join(soft_limit_exceeded)}"
        ]
    message = f"{label} context budget exceeded: {', '.join(exceeded)}"
    return ([message], []) if enforce else ([], [message])


def measure_skill_route(
    root: Path,
    name: str,
    skill_file: Path,
    baseline: Counts,
) -> tuple[list[str], Counts]:
    errors: list[str] = []
    try:
        reads = parse_reads(skill_file)
    except (OSError, UnicodeError, ValueError) as error:
        return [str(error)], baseline

    duplicate_reads = sorted(
        value for value, count in Counter(reads).items() if count > 1
    )
    if duplicate_reads:
        errors.append(f"{skill_file}: duplicate reads: {duplicate_reads}")

    baseline_duplicates = sorted(set(BASELINE_FILES) & set(reads))
    if baseline_duplicates:
        errors.append(
            f"{skill_file}: redundantly rereads baseline: {baseline_duplicates}"
        )

    missing_reads = sorted(REQUIRED_READS.get(name, set()) - set(reads))
    if missing_reads:
        errors.append(f"{skill_file}: missing mandatory reads: {missing_reads}")

    route = baseline + count_file(skill_file)
    for value in dict.fromkeys(reads):
        reason = route_path_error(root, value)
        if reason:
            errors.append(f"{skill_file}: {value}: {reason}")
            continue
        route += count_file(root / value)
    return errors, route


def audit(
    root: Path,
    *,
    enforce_budget: bool,
    current_date: date | None = None,
) -> tuple[list[str], list[str], dict]:
    errors: list[str] = []
    warnings: list[str] = []
    if enforce_budget:
        errors.extend(baseline_contract_errors(root))
    profile_errors, baseline_files = active_baseline_files(root)
    errors.extend(profile_errors)
    errors.extend(validate_adr_index(root))
    errors.extend(validate_guide_index(root))
    warnings.extend(handoff_warnings(root, current_date=current_date or date.today()))
    conditional_errors, conditional_routes = validate_conditional_authorities(
        root,
        CONDITIONAL_AUTHORITIES,
    )
    errors.extend(conditional_errors)
    baseline = Counts()
    for value in baseline_files:
        path = root / value
        if not path.is_file():
            errors.append(f"baseline file is missing: {value}")
            continue
        baseline += count_file(path)

    budget_errors, budget_warnings = budget_findings(
        "baseline",
        baseline,
        Counts(BASELINE_BYTE_LIMIT, BASELINE_WORD_LIMIT),
        enforce=enforce_budget,
    )
    errors.extend(budget_errors)
    warnings.extend(budget_warnings)

    skill_directory = root / ".skills"
    skill_files = sorted(skill_directory.glob("*.skill.md"))
    actual_skills = {
        path.name.removesuffix(".skill.md"): path for path in skill_files
    }
    for missing_skill in sorted(REQUIRED_READS.keys() - actual_skills.keys()):
        errors.append(f"required skill is missing: {missing_skill}")

    largest_name = ""
    largest = Counts()
    for name, skill_file in actual_skills.items():
        route_errors, route = measure_skill_route(root, name, skill_file, baseline)
        errors.extend(route_errors)

        if route.bytes > largest.bytes:
            largest_name = name
            largest = route

        route_errors, route_warnings = budget_findings(
            f"{name} declared route",
            route,
            Counts(ROUTE_BYTE_LIMIT, ROUTE_WORD_LIMIT),
            enforce=enforce_budget,
        )
        errors.extend(route_errors)
        warnings.extend(route_warnings)

    report = {
        "baseline": baseline,
        "largest_route_name": largest_name,
        "largest_route": largest,
        "skill_count": len(skill_files),
        "budget_mode": "enforced" if enforce_budget else "reported",
        "conditional_routes": conditional_routes,
        "baseline_files": baseline_files,
    }
    return errors, warnings, report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate")
    validate.add_argument("--root", type=Path, default=Path("."))
    validate.add_argument("--enforce-budget", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        errors, warnings, report = audit(
            args.root.resolve(),
            enforce_budget=args.enforce_budget,
        )
    except (OSError, UnicodeError) as error:
        print(f"context budget: ERROR: {error}", file=sys.stderr)
        return 2

    baseline = report["baseline"]
    largest = report["largest_route"]
    print(
        "context budget: "
        f"baseline={baseline.bytes}/{BASELINE_BYTE_LIMIT} bytes, "
        f"{baseline.words}/{BASELINE_WORD_LIMIT} words; "
        f"largest={report['largest_route_name']} "
        f"{largest.bytes}/{ROUTE_BYTE_LIMIT} bytes, "
        f"{largest.words}/{ROUTE_WORD_LIMIT} words; "
        f"skills={report['skill_count']}; mode={report['budget_mode']}"
    )
    for name, counts in report["conditional_routes"].items():
        print(
            f"context budget: conditional={name} "
            f"{counts.bytes} bytes, {counts.words} words"
        )
    for warning in warnings:
        print(f"context budget: WARNING: {warning}")
    for error in errors:
        print(f"context budget: ERROR: {error}", file=sys.stderr)
    if errors:
        return 2
    print("context budget: OK — declared routes preserve required files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
