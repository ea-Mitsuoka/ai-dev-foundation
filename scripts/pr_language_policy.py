#!/usr/bin/env python3
"""Require Japanese pull-request bodies in leaf repositories (ADR-0020).

A repository is a *template* when it publishes a contract root for others to inherit:
``.ai/contracts/foundation/`` (the fleet root) or
``.ai/contracts/templates/<owner>/<its own name>/``. A repository that only consumes
contract roots is a *leaf*, and only there does this policy judge the body. Both facts
are read from the tree, so CI and a local run give the same answer.

The judgement measures prose, not presence: HTML comments, code, URLs, table rows,
checklist markers, and headings are removed first, then the remainder must carry at
least ``MIN_JAPANESE_CHARACTERS`` of Japanese script and Japanese must make up at least
``MIN_JAPANESE_SHARE`` of all letters. Trusted automation is exempt by exact login, and a
reviewer may exempt one pull request with ``EXCEPTION_LABEL``.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

PROFILE_PATH = Path(".github/inheritance/agent-profile.json")
FOUNDATION_EXPORT_PATH = Path(".ai/contracts/foundation/inheritance-export.json")
TEMPLATE_CONTRACT_ROOT = Path(".ai/contracts/templates")

MIN_JAPANESE_CHARACTERS = 60
MIN_JAPANESE_SHARE = 0.30
TRUSTED_BOTS = frozenset({"github-actions[bot]", "dependabot[bot]", "renovate[bot]"})
EXCEPTION_LABEL = "review:language-exception"

# Hiragana, katakana, CJK unified ideographs, iteration marks, and the prolonged sound
# mark. Half-width katakana and punctuation are deliberately not counted.
JAPANESE = re.compile(r"[぀-ゟ゠-ヿ一-鿿々〆ー]")
LATIN = re.compile(r"[A-Za-z]")

HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
FENCED_CODE = re.compile(r"^(`{3,}|~{3,}).*?^\1[ \t]*$", re.DOTALL | re.MULTILINE)
INLINE_CODE = re.compile(r"`[^`\n]*`")
URL = re.compile(r"https?://\S+")
CHECKLIST_MARKER = re.compile(r"^\s*[-*]\s+\[[ xX]\]\s*", re.MULTILINE)
STRUCTURAL_LINE = re.compile(r"^\s*(\||#).*$", re.MULTILINE)


@dataclass(frozen=True)
class Measurement:
    japanese: int
    latin: int

    @property
    def share(self) -> float:
        letters = self.japanese + self.latin
        return self.japanese / letters if letters else 0.0


@dataclass(frozen=True)
class Verdict:
    level: str  # exempt | pass | warn | fail
    reason: str


class PolicyError(ValueError):
    """The repository or the inputs cannot be interpreted."""


def _project_repository(root: Path) -> str:
    try:
        profile = json.loads((root / PROFILE_PATH).read_text(encoding="utf-8"))
        inputs = profile["inputs"]
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise PolicyError(f"cannot read {PROFILE_PATH}: {error}") from error
    projects = [entry for entry in inputs if entry.get("layer") == "project"]
    if len(projects) != 1 or not isinstance(projects[0].get("repository"), str):
        raise PolicyError(f"{PROFILE_PATH} must declare exactly one project layer")
    repository = projects[0]["repository"]
    if repository.count("/") != 1:
        raise PolicyError(f"project repository is not OWNER/NAME: {repository!r}")
    return repository


def classify_repository(root: Path) -> str:
    """Return ``root``, ``template``, or ``leaf`` for the repository at ``root``."""
    repository = _project_repository(root)
    export_path = root / FOUNDATION_EXPORT_PATH
    if export_path.is_file():
        try:
            export = json.loads(export_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise PolicyError(f"cannot read {FOUNDATION_EXPORT_PATH}: {error}") from error
        if export.get("repository") == repository:
            return "root"
    owner, name = repository.split("/")
    if (root / TEMPLATE_CONTRACT_ROOT / owner.lower() / name).is_dir():
        return "template"
    return "leaf"


def prose(body: str) -> str:
    """Strip the parts of a pull-request body that carry no authored language."""
    text = HTML_COMMENT.sub(" ", body)
    text = FENCED_CODE.sub(" ", text)
    text = INLINE_CODE.sub(" ", text)
    text = URL.sub(" ", text)
    text = STRUCTURAL_LINE.sub(" ", text)
    return CHECKLIST_MARKER.sub("", text)


def measure(text: str) -> Measurement:
    return Measurement(len(JAPANESE.findall(text)), len(LATIN.findall(text)))


def evaluate(scope: str, body: str, author: str, labels: frozenset[str]) -> Verdict:
    if scope != "leaf":
        return Verdict("pass", f"{scope} repository: ADR-0005 keeps PR text English")
    if author in TRUSTED_BOTS:
        return Verdict("exempt", f"{author} is trusted automation")
    result = measure(prose(body))
    detail = (
        f"{result.japanese} Japanese characters (minimum {MIN_JAPANESE_CHARACTERS}), "
        f"{result.share:.0%} of letters (minimum {MIN_JAPANESE_SHARE:.0%})"
    )
    if result.japanese >= MIN_JAPANESE_CHARACTERS and result.share >= MIN_JAPANESE_SHARE:
        return Verdict("pass", detail)
    if EXCEPTION_LABEL in labels:
        return Verdict("warn", f"{EXCEPTION_LABEL} applied by a reviewer; {detail}")
    return Verdict("fail", detail)


def _label_names(payload: object) -> frozenset[str]:
    if not isinstance(payload, list):
        raise PolicyError("labels JSON must be a list")
    names = set()
    for entry in payload:
        name = entry.get("name") if isinstance(entry, dict) else entry
        if not isinstance(name, str):
            raise PolicyError(f"label entry without a name: {entry!r}")
        names.add(name)
    return frozenset(names)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--body-file", required=True, type=Path)
    parser.add_argument("--author", required=True)
    parser.add_argument("--labels-json", type=Path)
    args = parser.parse_args(argv)
    try:
        scope = classify_repository(args.root)
        body = args.body_file.read_text(encoding="utf-8")
        labels = frozenset()
        if args.labels_json is not None:
            labels = _label_names(json.loads(args.labels_json.read_text(encoding="utf-8")))
    except (OSError, ValueError) as error:
        print(f"::error::Invalid PR-language policy input: {error}")
        return 2

    verdict = evaluate(scope, body, args.author, labels)
    print(f"PR body language ({scope} repository): {verdict.level} — {verdict.reason}")
    if verdict.level == "fail":
        print(
            "::error::A leaf repository requires a Japanese pull-request body (ADR-0020): "
            f"{verdict.reason}. Rewrite the body in Japanese, or ask a reviewer to apply "
            f"the {EXCEPTION_LABEL} label and state the reason in the body."
        )
        return 1
    if verdict.level == "warn":
        print(f"::warning::PR body is not Japanese; {verdict.reason} (ADR-0020).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
