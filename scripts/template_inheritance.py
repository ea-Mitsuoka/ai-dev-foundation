#!/usr/bin/env python3
"""Validate, plan, and report local template inheritance defined by foundation ADRs."""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


SCHEMA_VERSION = 1
FLEET_SCHEMA_VERSION = 2
SUPPORTED_MANIFEST_SCHEMA_VERSIONS = {1, 2}
AGENT_PROFILE_SCHEMA_VERSION = 1
MANIFEST_PATH = ".github/inheritance/manifest.json"
AGENT_PROFILE_PATH = ".github/inheritance/agent-profile.json"
TEMPLATE_SYNC_IGNORE_PATH = ".templatesyncignore"
FOUNDATION_BOOTSTRAP_EXPORT_PATH = ".ai/contracts/foundation/inheritance-export.json"
DEFAULT_FLEET_CONFIG_PATH = Path("docs/foundation/inheritance-fleet.json")
MAX_CONTRACT_BYTES = 1_000_000
MAX_OWNERSHIP_ROOTS = 1_000
MAX_AGENT_INPUTS = 32
MAX_FLEET_REPOSITORIES = 32
MAX_AUDITED_INHERITED_FILES = 10_000
HASH_BATCH_SIZE = 256
MAX_FIRST_PARENT_COMMITS = 100_000
MAX_CHANGED_PATHS = 1_000
FLEET_LIFECYCLES = {"active", "paused", "retired"}
IMPACT_PRIORITY = {
    "foundation-only": 0,
    "schedule-only": 1,
    "manual-boundary": 2,
    "child-migration-required": 3,
}
REPOSITORY_TARGET = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
COMMIT_ID = re.compile(r"^[0-9a-f]{40}$")
REQUIRED_PROTECTED_PATHS = {
    ".gitignore",
    ".github/governance/repository.json",
    ".github/inheritance/manifest.json",
    ".github/workflows/template-sync.yml",
    ".templatesyncignore",
}
REQUIRED_TEMPLATE_SYNC_IGNORES = {".github/workflows/"}
BOOTSTRAP_MANUAL_BOUNDARIES = {
    ".ai/project/agent-overlay.md",
    ".github/workflows/template-sync.yml",
    "README.md",
}
README_OWNER_MARKER = re.compile(r"<!--\s*repository-readme-owner:\s*([^\s]+)\s*-->")


class InheritanceError(ValueError):
    pass


def _object(value, fields, label):
    if type(value) is not dict:
        raise InheritanceError(f"{label} must be an object")
    unknown = sorted(set(value) - fields)
    missing = sorted(fields - set(value))
    if unknown or missing:
        details = []
        if unknown:
            details.append(f"unknown fields: {', '.join(unknown)}")
        if missing:
            details.append(f"missing fields: {', '.join(missing)}")
        raise InheritanceError(f"{label} has {'; '.join(details)}")


def _repository(value, label):
    if type(value) is not str or not REPOSITORY_TARGET.fullmatch(value):
        raise InheritanceError(f"{label} must be OWNER/REPOSITORY")
    return value


def _ownership_root(value, label, *, file_only=False):
    if type(value) is not str or not value or value != value.strip() or len(value) > 1_024:
        raise InheritanceError(f"{label} must be a safe repository-relative ownership root")
    is_directory = value.endswith("/")
    body = value[:-1] if is_directory else value
    parts = body.split("/")
    if (
        not body
        or body.startswith("/")
        or (file_only and is_directory)
        or any(part in {"", ".", "..", ".git"} for part in parts)
        or any(char in "*?[]\\" or ord(char) < 32 or ord(char) == 127 for char in value)
    ):
        raise InheritanceError(f"{label} must be a safe repository-relative ownership root")
    return value


def _repository_file_path(value, label):
    if type(value) is not str or not value or len(value) > 4_096:
        raise InheritanceError(f"{label} must be a safe repository-relative file path")
    parts = value.split("/")
    if (
        value.startswith("/")
        or value.endswith("/")
        or any(part in {"", ".", "..", ".git"} for part in parts)
        or any(ord(char) < 32 or ord(char) == 127 for char in value)
    ):
        raise InheritanceError(f"{label} must be a safe repository-relative file path")
    return value


def _branch(value, label):
    try:
        _ownership_root(value, label, file_only=True)
    except InheritanceError as error:
        raise InheritanceError(f"{label} is not a safe branch name") from error
    if (
        len(value) > 255
        or value == "@"
        or value.startswith(("-", "."))
        or value.endswith((".", ".lock"))
        or ".." in value
        or "@{" in value
        or any(part.startswith(".") or part.endswith(".lock") for part in value.split("/"))
        or any(char in " ~^:" for char in value)
    ):
        raise InheritanceError(f"{label} is not a safe branch name")
    return value


def _ownership_roots(value, label):
    if type(value) is not list or not value or len(value) > MAX_OWNERSHIP_ROOTS:
        raise InheritanceError(f"{label} must be a non-empty unique list of ownership roots")
    roots = [_ownership_root(root, f"{label}[{index}]") for index, root in enumerate(value)]
    if len(roots) != len(set(roots)):
        raise InheritanceError(f"{label} must be a non-empty unique list of ownership roots")
    return roots


def _overlaps(left, right):
    return left == right or (left.endswith("/") and right.startswith(left)) or (
        right.endswith("/") and left.startswith(right)
    )


def _reject_overlaps(roots, label):
    for index, left in enumerate(roots):
        for right in roots[index + 1 :]:
            if _overlaps(left, right):
                raise InheritanceError(f"{label} ownership roots overlap: {left}, {right}")


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise InheritanceError(f"contract JSON contains duplicate key: {key}")
        value[key] = item
    return value


def _read_json(root, relative_path):
    candidate = root / relative_path
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as error:
        raise InheritanceError(f"{relative_path} must be a file inside the repository root") from error
    if resolved != candidate:
        raise InheritanceError(f"{relative_path} must not use a symlink")
    if not resolved.is_relative_to(root):
        raise InheritanceError(f"{relative_path} must be a file inside the repository root")
    if not resolved.is_file():
        raise InheritanceError(f"{relative_path} must be a file inside the repository root")
    try:
        if resolved.stat().st_size > MAX_CONTRACT_BYTES:
            raise InheritanceError(f"{relative_path} exceeds {MAX_CONTRACT_BYTES} bytes")
        return json.loads(resolved.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise InheritanceError(f"{relative_path} must contain valid UTF-8 JSON") from error


def _read_template_sync_ignore(root):
    candidate = root / TEMPLATE_SYNC_IGNORE_PATH
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as error:
        raise InheritanceError(
            f"{TEMPLATE_SYNC_IGNORE_PATH} must be a file inside the repository root"
        ) from error
    if resolved != candidate or not resolved.is_relative_to(root) or not resolved.is_file():
        raise InheritanceError(
            f"{TEMPLATE_SYNC_IGNORE_PATH} must be a non-symlink file inside the repository root"
        )
    try:
        if resolved.stat().st_size > MAX_CONTRACT_BYTES:
            raise InheritanceError(f"{TEMPLATE_SYNC_IGNORE_PATH} exceeds {MAX_CONTRACT_BYTES} bytes")
        lines = resolved.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        raise InheritanceError(f"{TEMPLATE_SYNC_IGNORE_PATH} must contain valid UTF-8 text") from error

    positive = []
    exceptions = []
    for line_number, line in enumerate(lines, start=1):
        entry = line.strip()
        if not entry or entry.startswith("#"):
            continue
        destination = exceptions if entry.startswith(":!") else positive
        root_entry = entry[2:] if destination is exceptions else entry
        if root_entry.endswith("/**"):
            root_entry = root_entry[:-2]
        try:
            destination.append(
                _ownership_root(root_entry, f"{TEMPLATE_SYNC_IGNORE_PATH}:{line_number}")
            )
        except InheritanceError as error:
            raise InheritanceError(
                f"{TEMPLATE_SYNC_IGNORE_PATH}:{line_number} must be a literal path, "
                "directory, directory/**, or :! exception"
            ) from error
    return positive, exceptions


def _covers(outer, inner):
    return outer == inner or (outer.endswith("/") and inner.startswith(outer))


def _owned_by(path, roots):
    return any(root == path or (root.endswith("/") and path.startswith(root)) for root in roots)


def _require_regular_file(root, relative_path, label):
    candidate = root / relative_path
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as error:
        raise InheritanceError(f"{label} must be a file inside the repository root") from error
    if (
        resolved != candidate
        or not resolved.is_relative_to(root)
        or not resolved.is_file()
    ):
        raise InheritanceError(f"{label} must be a non-symlink file inside the repository root")


def _agent_profile_inputs(root, inputs):
    if type(inputs) is not list or not 2 <= len(inputs) <= MAX_AGENT_INPUTS:
        raise InheritanceError(
            f"agent profile.inputs must contain 2 to {MAX_AGENT_INPUTS} ordered inputs"
        )

    validated = []
    for index, item in enumerate(inputs):
        label = f"agent profile.inputs[{index}]"
        _object(item, {"layer", "repository", "path"}, label)
        layer = item["layer"]
        if layer not in {"foundation", "template", "project"}:
            raise InheritanceError(f"{label}.layer must be foundation, template, or project")
        repository = _repository(item["repository"], f"{label}.repository")
        path = _ownership_root(item["path"], f"{label}.path", file_only=True)
        _require_regular_file(root, path, f"{label}.path")
        validated.append({"layer": layer, "repository": repository, "path": path})
    return validated


def _validate_agent_input_order(inputs, parent_repository):
    layers = [item["layer"] for item in inputs]
    if (
        layers[0] != "foundation"
        or layers[-1] != "project"
        or layers.count("foundation") != 1
        or layers.count("project") != 1
        or any(layer != "template" for layer in layers[1:-1])
    ):
        raise InheritanceError(
            "agent profile inputs must use foundation, template..., project order"
        )
    if len({item["repository"].casefold() for item in inputs}) != len(inputs):
        raise InheritanceError("agent profile input repositories must be unique")
    if len({item["path"] for item in inputs}) != len(inputs):
        raise InheritanceError("agent profile input paths must be unique")

    templates = inputs[1:-1]
    foundation_repository = inputs[0]["repository"]
    if parent_repository.casefold() == foundation_repository.casefold():
        if templates:
            raise InheritanceError(
                "agent profile template order must be empty when foundation is the direct parent"
            )
    elif not templates or templates[-1]["repository"].casefold() != parent_repository.casefold():
        raise InheritanceError("agent profile final template input must match the direct parent")


def _validate_agent_input_ownership(inputs, inherited, protected):
    foundation = inputs[0]
    project = inputs[-1]

    if not foundation["path"].startswith(".ai/contracts/foundation/"):
        raise InheritanceError(
            "foundation agent profile input must use .ai/contracts/foundation/"
        )
    if not project["path"].startswith(".ai/project/"):
        raise InheritanceError("project agent profile input must use .ai/project/")

    for item in inputs[:-1]:
        if not _owned_by(item["path"], inherited):
            raise InheritanceError(f"agent profile {item['layer']} input must be inherited")
        if item["layer"] == "template":
            owner, repository = item["repository"].casefold().split("/", 1)
            expected_root = f".ai/contracts/templates/{owner}/{repository}/"
            if not item["path"].startswith(expected_root):
                raise InheritanceError(
                    f"template agent profile input must use owner-qualified root {expected_root}"
                )
    if not _owned_by(project["path"], protected):
        raise InheritanceError("agent profile project input must be protected")


def _validate_agent_profile(root, parent_repository, inherited, protected):
    if not _owned_by(AGENT_PROFILE_PATH, protected):
        raise InheritanceError(f"manifest.protected_paths must protect {AGENT_PROFILE_PATH}")
    profile = _read_json(root, AGENT_PROFILE_PATH)
    _object(
        profile,
        {"schema_version", "authority_policy", "inputs"},
        "agent profile",
    )
    if (
        type(profile["schema_version"]) is not int
        or profile["schema_version"] != AGENT_PROFILE_SCHEMA_VERSION
    ):
        raise InheritanceError(
            f"agent profile.schema_version must be {AGENT_PROFILE_SCHEMA_VERSION}"
        )
    if profile["authority_policy"] != "strengthen-only":
        raise InheritanceError("agent profile.authority_policy must be strengthen-only")
    inputs = _agent_profile_inputs(root, profile["inputs"])
    _validate_agent_input_order(inputs, parent_repository)
    _validate_agent_input_ownership(inputs, inherited, protected)

    return {
        "profile_file": AGENT_PROFILE_PATH,
        "authority_policy": "strengthen-only",
        "inputs": inputs,
    }


def _validate_template_sync_ignore(root, protected):
    positive, exceptions = _read_template_sync_ignore(root)
    required = sorted(set(protected) | REQUIRED_TEMPLATE_SYNC_IGNORES)
    missing = sorted(
        path for path in required if not any(_covers(entry, path) for entry in positive)
    )
    if missing:
        raise InheritanceError(f"template sync ignore is missing protected paths: {missing}")
    unsafe_exceptions = sorted(
        exception
        for exception in exceptions
        if any(_overlaps(exception, protected_root) for protected_root in required)
    )
    if unsafe_exceptions:
        raise InheritanceError(
            f"template sync exception re-includes protected paths: {unsafe_exceptions}"
        )
    return {
        "ignore_file": TEMPLATE_SYNC_IGNORE_PATH,
        "required": required,
    }


def validate_inheritance(root):
    """Validate manifest, lock, and exclusive path ownership without external I/O."""
    try:
        repository_root = Path(root).resolve(strict=True)
    except OSError as error:
        raise InheritanceError("repository root must exist") from error
    if not repository_root.is_dir():
        raise InheritanceError("repository root must be a directory")

    manifest = _read_json(repository_root, MANIFEST_PATH)
    _object(manifest, {"schema_version", "parent", "lock_file", "inherited_paths", "protected_paths"}, "manifest")
    manifest_version = manifest["schema_version"]
    if (
        type(manifest_version) is not int
        or manifest_version not in SUPPORTED_MANIFEST_SCHEMA_VERSIONS
    ):
        supported = ", ".join(str(version) for version in sorted(SUPPORTED_MANIFEST_SCHEMA_VERSIONS))
        raise InheritanceError(f"manifest.schema_version must be one of: {supported}")
    _object(manifest["parent"], {"repository", "branch"}, "manifest.parent")
    parent_repository = _repository(manifest["parent"]["repository"], "manifest.parent.repository")
    parent_branch = _branch(manifest["parent"]["branch"], "manifest.parent.branch")
    lock_file = _ownership_root(manifest["lock_file"], "manifest.lock_file", file_only=True)
    inherited = _ownership_roots(manifest["inherited_paths"], "manifest.inherited_paths")
    protected = _ownership_roots(manifest["protected_paths"], "manifest.protected_paths")

    _reject_overlaps(inherited, "manifest.inherited_paths")
    _reject_overlaps(protected, "manifest.protected_paths")
    for inherited_root in inherited:
        for protected_root in protected:
            if _overlaps(inherited_root, protected_root):
                raise InheritanceError(
                    "inherited and protected ownership roots overlap: "
                    f"{inherited_root}, {protected_root}"
                )

    required = REQUIRED_PROTECTED_PATHS | {lock_file}
    if manifest_version == 2:
        required.add(AGENT_PROFILE_PATH)
    missing = sorted(path for path in required if not any(_overlaps(root, path) for root in protected))
    if missing:
        raise InheritanceError(f"manifest is missing required protected paths: {missing}")

    template_sync = _validate_template_sync_ignore(repository_root, protected)

    lock = _read_json(repository_root, lock_file)
    _object(lock, {"schema_version", "parent"}, "lock")
    if type(lock["schema_version"]) is not int or lock["schema_version"] != SCHEMA_VERSION:
        raise InheritanceError(f"lock.schema_version must be {SCHEMA_VERSION}")
    _object(lock["parent"], {"repository", "commit"}, "lock.parent")
    locked_repository = _repository(lock["parent"]["repository"], "lock.parent.repository")
    commit = lock["parent"]["commit"]
    if locked_repository != parent_repository:
        raise InheritanceError("lock.parent.repository must match manifest.parent.repository")
    if type(commit) is not str or not COMMIT_ID.fullmatch(commit) or commit == "0" * 40:
        raise InheritanceError("lock.parent.commit must be a full non-zero lowercase commit ID")

    result = {
        "schema_version": manifest_version,
        "parent": {"repository": parent_repository, "branch": parent_branch, "commit": commit},
        "lock_file": lock_file,
        "ownership": {"inherited": sorted(inherited), "protected": sorted(protected)},
        "template_sync": template_sync,
    }
    if manifest_version == 2:
        result["agent_contract"] = _validate_agent_profile(
            repository_root,
            parent_repository,
            inherited,
            protected,
        )
    return result


def _git(root, arguments, operation):
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *arguments],
            capture_output=True,
            check=False,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise InheritanceError(f"parent Git {operation} could not run") from error
    if result.returncode != 0:
        raise InheritanceError(f"parent Git {operation} failed; refresh the local parent checkout")
    return result.stdout


def _git_blob(root, object_id, path):
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "cat-file", "blob", object_id],
            capture_output=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise InheritanceError(f"parent Git blob read could not run: {path}") from error
    if result.returncode != 0 or len(result.stdout) > MAX_CONTRACT_BYTES:
        raise InheritanceError(f"parent workflow blob is unavailable or too large: {path}")
    return result.stdout


def _github_repository(remote_url):
    for prefix in ("https://github.com/", "git@github.com:", "ssh://git@github.com/"):
        if remote_url.startswith(prefix):
            repository = remote_url[len(prefix) :]
            if repository.endswith(".git"):
                repository = repository[:-4]
            if REPOSITORY_TARGET.fullmatch(repository):
                return repository
    raise InheritanceError("parent origin must be a credential-free GitHub repository URL")


def _parent_root(parent_root):
    try:
        root = Path(parent_root).resolve(strict=True)
    except OSError as error:
        raise InheritanceError("parent root must exist") from error
    if not root.is_dir():
        raise InheritanceError("parent root must be a directory")
    top_level = Path(_git(root, ["rev-parse", "--show-toplevel"], "root discovery").strip()).resolve()
    if top_level != root:
        raise InheritanceError("parent root must be the Git worktree top level")
    return root


def _next_parent_commit(parent_root, contract):
    remote = _git(parent_root, ["remote", "get-url", "origin"], "origin discovery").strip()
    if _github_repository(remote).casefold() != contract["parent"]["repository"].casefold():
        raise InheritanceError("parent origin does not match manifest.parent.repository")
    branch = contract["parent"]["branch"]
    target = _git(
        parent_root,
        ["rev-parse", "--verify", f"refs/remotes/origin/{branch}^{{commit}}"],
        "remote branch resolution",
    ).strip()
    if not COMMIT_ID.fullmatch(target):
        raise InheritanceError("parent remote branch did not resolve to a full commit ID")
    history = _git(
        parent_root,
        ["rev-list", "--first-parent", f"--max-count={MAX_FIRST_PARENT_COMMITS + 1}", target],
        "first-parent history read",
    ).splitlines()
    locked = contract["parent"]["commit"]
    if locked not in history:
        suffix = " within the supported history window" if len(history) > MAX_FIRST_PARENT_COMMITS else ""
        raise InheritanceError(f"locked commit is not on the remote branch first-parent history{suffix}")
    index = history.index(locked)
    return target, None if index == 0 else history[index - 1]


def _changed_paths(parent_root, locked, candidate):
    output = _git(
        parent_root,
        ["diff-tree", "--no-commit-id", "--name-only", "-r", "-z", "--no-renames", locked, candidate],
        "candidate diff read",
    )
    paths = sorted(path for path in output.split("\0") if path)
    if len(paths) > MAX_CHANGED_PATHS:
        raise InheritanceError(f"candidate commit changes more than {MAX_CHANGED_PATHS} paths")
    for index, path in enumerate(paths):
        _repository_file_path(path, f"parent changed path[{index}]")
    return paths


def _path_owner(path, ownership):
    for owner in ("inherited", "protected"):
        if any(root == path or (root.endswith("/") and path.startswith(root)) for root in ownership[owner]):
            return owner
    return "unowned"


def _parent_entry(parent_root, candidate, path):
    output = _git(parent_root, ["ls-tree", "-z", candidate, "--", path], "candidate tree read")
    if not output:
        return None
    try:
        metadata, actual_path = output.rstrip("\0").split("\t", 1)
        mode, object_type, object_id = metadata.split(" ")
    except ValueError as error:
        raise InheritanceError(f"parent path has an invalid tree entry: {path}") from error
    if actual_path != path or object_type != "blob" or mode not in {"100644", "100755"}:
        raise InheritanceError(f"parent path must be a regular file: {path}")
    return object_id, mode == "100755"


def _child_entry(child_root, parent_root, path):
    current = child_root
    for part in path.split("/"):
        current /= part
        if current.is_symlink():
            raise InheritanceError(f"inherited child path must not use a symlink: {path}")
        if not current.exists():
            return None
    if not current.is_file():
        raise InheritanceError(f"inherited child path must be a regular file: {path}")
    object_id = _git(parent_root, ["hash-object", "--no-filters", "--", str(current)], "child hash").strip()
    return object_id, bool(current.stat().st_mode & 0o111)


def _parent_inherited_entries(parent_root, revision, ownership_roots):
    output = _git(
        parent_root,
        ["ls-tree", "-r", "-z", revision, "--", *ownership_roots],
        "inherited tree read",
    )
    entries = {}
    for index, raw_entry in enumerate(entry for entry in output.split("\0") if entry):
        try:
            metadata, path = raw_entry.split("\t", 1)
            mode, object_type, object_id = metadata.split(" ")
        except ValueError as error:
            raise InheritanceError("parent inherited tree has an invalid entry") from error
        _repository_file_path(path, f"parent inherited path[{index}]")
        if (
            not _owned_by(path, ownership_roots)
            or object_type != "blob"
            or mode not in {"100644", "100755"}
        ):
            raise InheritanceError(f"parent inherited path must be a regular file: {path}")
        if path in entries:
            raise InheritanceError(f"parent inherited tree contains a duplicate path: {path}")
        entries[path] = (object_id, mode == "100755")
        if len(entries) > MAX_AUDITED_INHERITED_FILES:
            raise InheritanceError(
                f"inherited audit exceeds {MAX_AUDITED_INHERITED_FILES} files"
            )
    return entries


def _child_inherited_entries(child_root, parent_root, ownership_roots):
    output = _git(
        child_root,
        [
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            *ownership_roots,
        ],
        "child inherited paths read",
    )
    files = []
    for index, path in enumerate(path for path in output.split("\0") if path):
        _repository_file_path(path, f"inherited child path[{index}]")
        if not _owned_by(path, ownership_roots):
            raise InheritanceError(f"child inherited path is outside ownership: {path}")
        current = child_root
        missing = False
        for part in path.split("/"):
            current /= part
            if current.is_symlink():
                raise InheritanceError(
                    f"inherited child path must not use a symlink: {path}"
                )
            if not current.exists():
                missing = True
                break
        if missing:
            continue
        if not current.is_file():
            raise InheritanceError(f"inherited child path must be a regular file: {path}")
        files.append((path, current, bool(current.stat().st_mode & 0o111)))
        if len(files) > MAX_AUDITED_INHERITED_FILES:
            raise InheritanceError(
                f"inherited audit exceeds {MAX_AUDITED_INHERITED_FILES} files"
            )

    entries = {}
    for start in range(0, len(files), HASH_BATCH_SIZE):
        batch = files[start : start + HASH_BATCH_SIZE]
        hashes = _git(
            parent_root,
            ["hash-object", "--no-filters", "--", *(str(item[1]) for item in batch)],
            "child hash batch",
        ).splitlines()
        if len(hashes) != len(batch):
            raise InheritanceError("child inherited file hashing returned an invalid result")
        for (path, _current, executable), object_id in zip(batch, hashes, strict=True):
            entries[path] = (object_id, executable)
    return entries


def plan_inheritance(root, parent_root):
    """Plan one first-parent commit without modifying either worktree."""
    contract = validate_inheritance(root)
    child_root = Path(root).resolve(strict=True)
    parent_root = _parent_root(parent_root)
    target, candidate = _next_parent_commit(parent_root, contract)
    changes = {name: [] for name in ("add", "modify", "candidate_delete", "already_current")}
    skipped = {name: [] for name in ("protected", "unowned")}
    if candidate:
        for path in _changed_paths(parent_root, contract["parent"]["commit"], candidate):
            owner = _path_owner(path, contract["ownership"])
            if owner != "inherited":
                skipped[owner].append(path)
                continue
            parent_entry = _parent_entry(parent_root, candidate, path)
            child_entry = _child_entry(child_root, parent_root, path)
            if parent_entry is None:
                operation = "candidate_delete" if child_entry else "already_current"
            elif child_entry is None:
                operation = "add"
            else:
                operation = "already_current" if child_entry == parent_entry else "modify"
            changes[operation].append(path)
    counts = {name: len(paths) for name, paths in {**changes, **skipped}.items()}
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "changes" if candidate else "up_to_date",
        "parent": {
            "repository": contract["parent"]["repository"],
            "branch": contract["parent"]["branch"],
            "locked_commit": contract["parent"]["commit"],
            "target_commit": target,
            "candidate_commit": candidate,
        },
        "changes": changes,
        "skipped": skipped,
        "summary": {**counts, "total": sum(counts.values())},
    }


def _bootstrap_export_path(parent_repository, parent_root, source_commit):
    owner, repository = parent_repository.casefold().split("/", 1)
    candidates = [
        f".ai/contracts/templates/{owner}/{repository}/inheritance-export.json",
        FOUNDATION_BOOTSTRAP_EXPORT_PATH,
    ]
    for path in candidates:
        entry = _parent_entry(parent_root, source_commit, path)
        if entry:
            try:
                export = json.loads(
                    _git_blob(parent_root, entry[0], path).decode("utf-8"),
                    object_pairs_hook=_unique_object,
                )
            except (UnicodeError, json.JSONDecodeError) as error:
                raise InheritanceError(
                    f"parent inheritance export must contain valid UTF-8 JSON: {path}"
                ) from error
            if (
                type(export) is dict
                and type(export.get("repository")) is str
                and export["repository"].casefold() == parent_repository.casefold()
            ):
                return path, export
    raise InheritanceError("direct parent does not publish a matching inheritance export")


def _validate_bootstrap_export(export_path, export, parent_repository):
    _object(
        export,
        {
            "schema_version",
            "repository",
            "branch",
            "inherited_paths",
            "protected_paths",
            "agent_inputs",
        },
        "inheritance export",
    )
    if type(export["schema_version"]) is not int or export["schema_version"] != 1:
        raise InheritanceError("inheritance export.schema_version must be 1")
    repository = _repository(export["repository"], "inheritance export.repository")
    if repository.casefold() != parent_repository.casefold():
        raise InheritanceError("inheritance export repository does not match parent origin")
    branch = _branch(export["branch"], "inheritance export.branch")
    inherited = _ownership_roots(
        export["inherited_paths"], "inheritance export.inherited_paths"
    )
    protected = _ownership_roots(
        export["protected_paths"], "inheritance export.protected_paths"
    )
    _reject_overlaps(inherited + protected, "inheritance export")
    missing = sorted(
        path
        for path in REQUIRED_PROTECTED_PATHS
        | BOOTSTRAP_MANUAL_BOUNDARIES
        | {"docs/inheritance/readmes/"}
        if not _owned_by(path, protected)
    )
    if missing:
        raise InheritanceError(f"inheritance export is missing protected paths: {missing}")
    if not _owned_by(export_path, inherited):
        raise InheritanceError("inheritance export must inherit its own export file")
    return {
        "path": export_path,
        "repository": repository,
        "branch": branch,
        "inherited_paths": inherited,
        "protected_paths": protected,
        "agent_inputs": export["agent_inputs"],
    }


def _bootstrap_export(parent_root, parent_repository, source_commit):
    export_path, export = _bootstrap_export_path(
        parent_repository, parent_root, source_commit
    )
    return _validate_bootstrap_export(export_path, export, parent_repository)


def _bootstrap_parent(parent_root, source_commit):
    parent_root = _parent_root(parent_root)
    remote = _git(parent_root, ["remote", "get-url", "origin"], "origin discovery").strip()
    parent_repository = _github_repository(remote)
    if type(source_commit) is not str or not COMMIT_ID.fullmatch(source_commit):
        raise InheritanceError("source commit must be a full lowercase commit ID")
    resolved = _git(
        parent_root,
        ["rev-parse", "--verify", f"{source_commit}^{{commit}}"],
        "source commit resolution",
    ).strip()
    if resolved != source_commit:
        raise InheritanceError("source commit did not resolve exactly")
    export = _bootstrap_export(parent_root, parent_repository, source_commit)
    target = _git(
        parent_root,
        ["rev-parse", "--verify", f"refs/remotes/origin/{export['branch']}^{{commit}}"],
        "remote branch resolution",
    ).strip()
    history = _git(
        parent_root,
        ["rev-list", "--first-parent", f"--max-count={MAX_FIRST_PARENT_COMMITS + 1}", target],
        "source first-parent history read",
    ).splitlines()
    if source_commit not in history:
        raise InheritanceError("source commit is not on the parent branch first-parent history")
    return parent_root, parent_repository, export


def _bootstrap_desired(child_root, repository, parent_repository, source_commit, export):
    inputs = [
        *export["agent_inputs"],
        {
            "layer": "project",
            "repository": repository,
            "path": ".ai/project/agent-overlay.md",
        },
    ]
    inputs = _agent_profile_inputs(child_root, inputs)
    _validate_agent_input_order(inputs, parent_repository)
    _validate_agent_input_ownership(
        inputs, export["inherited_paths"], export["protected_paths"]
    )
    ignore = {"docs/**"}
    ignore.update(
        f"{path}**" if path.endswith("/") else path
        for path in export["protected_paths"]
    )
    if _owned_by("docs/foundation/", export["inherited_paths"]):
        ignore.update(
            {"docs/**", ":!docs/foundation/", ":!docs/foundation/**"}
        )
    return {
        "manifest": {
            "schema_version": 2,
            "parent": {"repository": parent_repository, "branch": export["branch"]},
            "lock_file": ".github/inheritance/lock.json",
            "inherited_paths": export["inherited_paths"],
            "protected_paths": export["protected_paths"],
        },
        "lock": {
            "schema_version": 1,
            "parent": {"repository": parent_repository, "commit": source_commit},
        },
        "agent_profile": {
            "schema_version": 1,
            "authority_policy": "strengthen-only",
            "inputs": inputs,
        },
        "template_sync_ignore": sorted(ignore),
    }


def plan_bootstrap(root, parent_root, source_commit, repository):
    """Plan direct-child metadata from an explicit parent export without writing."""
    child_root, child_repository, branch = _child_finalization_worktree(root)
    repository = _repository(repository, "child repository")
    if child_repository.casefold() != repository.casefold():
        raise InheritanceError("child origin does not match requested repository")
    for path in BOOTSTRAP_MANUAL_BOUNDARIES:
        _require_regular_file(child_root, path, f"bootstrap manual boundary {path}")
    parent_root, parent_repository, export = _bootstrap_parent(
        parent_root, source_commit
    )
    parent_entries = _parent_inherited_entries(
        parent_root, source_commit, export["inherited_paths"]
    )
    child_entries = _child_inherited_entries(
        child_root, parent_root, export["inherited_paths"]
    )
    if child_entries != parent_entries:
        raise InheritanceError("child inherited template copy does not match exact parent commit")
    desired = _bootstrap_desired(
        child_root, repository, parent_repository, source_commit, export
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "ready_to_bootstrap",
        "repository": repository,
        "branch": branch,
        "parent": {
            "repository": parent_repository,
            "commit": source_commit,
            "export": export["path"],
        },
        "desired": desired,
        "manual_boundaries": sorted(BOOTSTRAP_MANUAL_BOUNDARIES),
    }


def _bootstrap_payload_root(payload_root, child_root):
    if payload_root is None:
        raise InheritanceError("bootstrap --apply requires --payload-root")
    candidate = Path(payload_root)
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as error:
        raise InheritanceError("bootstrap payload root must exist") from error
    if (
        candidate.is_symlink()
        or not resolved.is_dir()
        or resolved == child_root
        or resolved.is_relative_to(child_root)
    ):
        raise InheritanceError("bootstrap payload root must be an external non-symlink directory")
    return resolved


def _bootstrap_payload_file(payload_root, path):
    _repository_file_path(path, "bootstrap payload path")
    candidate = payload_root / path
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as error:
        raise InheritanceError(f"bootstrap payload must provide {path}") from error
    if resolved != candidate or not resolved.is_relative_to(payload_root) or not resolved.is_file():
        raise InheritanceError(f"bootstrap payload must provide a non-symlink file: {path}")
    try:
        if resolved.stat().st_size > MAX_CONTRACT_BYTES:
            raise InheritanceError(f"bootstrap payload exceeds {MAX_CONTRACT_BYTES} bytes: {path}")
        return resolved.read_bytes()
    except OSError as error:
        raise InheritanceError(f"bootstrap payload could not be read: {path}") from error


def _bootstrap_text(payload, path):
    try:
        return payload.decode("utf-8")
    except UnicodeError as error:
        raise InheritanceError(f"bootstrap payload must be UTF-8: {path}") from error


def _validate_sync_workflow_payload(payload, parent_repository):
    workflow_path = ".github/workflows/template-sync.yml"
    workflow = _bootstrap_text(payload, workflow_path)
    quoted_parent = re.escape(parent_repository)
    required = (
        r"(?m)^\s*source_repo_path:\s*[\"']" + quoted_parent + r"[\"']\s*$",
        r"(?m)^\s*SOURCE_REPOSITORY:\s*[\"']" + quoted_parent + r"[\"']\s*$",
        r"vars\.TEMPLATE_SYNC_ENABLED\s*==\s*[\"']true[\"']",
    )
    if re.search(r"(?<!\$)\{\{", workflow) or any(
        not re.search(pattern, workflow) for pattern in required
    ):
        raise InheritanceError("bootstrap Template Sync workflow has invalid direct-parent settings")


def _validate_bootstrap_manual_payloads(payloads, repository, parent_repository, source_commit):
    readme = _bootstrap_text(payloads["README.md"], "README.md")
    if README_OWNER_MARKER.findall(readme) != [repository]:
        raise InheritanceError("bootstrap README must contain exactly the child ownership marker")
    overlay_path = ".ai/project/agent-overlay.md"
    overlay = _bootstrap_text(payloads[overlay_path], overlay_path)
    if repository not in overlay or "{{" in overlay:
        raise InheritanceError("bootstrap project overlay must identify the child without placeholders")
    workflow_path = ".github/workflows/template-sync.yml"
    _validate_sync_workflow_payload(payloads[workflow_path], parent_repository)
    owner, parent = parent_repository.casefold().split("/", 1)
    archive_path = f"docs/inheritance/readmes/{owner}/{parent}.md"
    archive = _bootstrap_text(payloads[archive_path], archive_path)
    expected_frontmatter = (
        f"---\nsource-repository: {parent_repository}\n"
        f"source-commit: {source_commit}\n---\n"
    )
    if not archive.startswith(expected_frontmatter) or README_OWNER_MARKER.findall(archive) != [parent_repository]:
        raise InheritanceError("bootstrap README archive has invalid source provenance")


def _bootstrap_payloads(plan, child_root, payload_root):
    parent_repository = plan["parent"]["repository"]
    owner, parent = parent_repository.casefold().split("/", 1)
    archive_path = f"docs/inheritance/readmes/{owner}/{parent}.md"
    paths = [*sorted(BOOTSTRAP_MANUAL_BOUNDARIES), archive_path]
    payload_root = _bootstrap_payload_root(payload_root, child_root)
    payloads = {path: _bootstrap_payload_file(payload_root, path) for path in paths}
    _validate_bootstrap_manual_payloads(
        payloads, plan["repository"], parent_repository, plan["parent"]["commit"]
    )
    desired = plan["desired"]
    payloads.update(
        {
            MANIFEST_PATH: (json.dumps(desired["manifest"], indent=2) + "\n").encode(),
            ".github/inheritance/lock.json": (
                json.dumps(desired["lock"], indent=2) + "\n"
            ).encode(),
            AGENT_PROFILE_PATH: (
                json.dumps(desired["agent_profile"], indent=2) + "\n"
            ).encode(),
            TEMPLATE_SYNC_IGNORE_PATH: (
                "# Generated from the exact direct-parent inheritance export.\n"
                + "\n".join(desired["template_sync_ignore"])
                + "\n"
            ).encode(),
        }
    )
    return payloads


def _bootstrap_path_change(child_root, parent_root, source_commit, path, desired):
    child_entry = _child_entry(child_root, parent_root, path)
    if child_entry is not None:
        try:
            if (child_root / path).read_bytes() == desired:
                return child_entry[1]
        except OSError as error:
            raise InheritanceError(f"bootstrap target could not be read: {path}") from error
    parent_entry = _parent_entry(parent_root, source_commit, path)
    if child_entry is None:
        if parent_entry is None:
            return True
    elif parent_entry is not None and child_entry == parent_entry:
        return True
    raise InheritanceError(f"bootstrap target differs from both parent and desired content: {path}")


def _write_bootstrap_payload(child_root, path, payload):
    destination = child_root / path
    temporary = destination.with_name(f".{destination.name}.bootstrap-tmp")
    if temporary.exists() or temporary.is_symlink():
        raise InheritanceError(f"bootstrap temporary path already exists: {path}")
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_bytes(payload)
        temporary.chmod(0o644)
        temporary.replace(destination)
    except OSError as error:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise InheritanceError(f"bootstrap write failed: {path}") from error


def apply_bootstrap(
    root, parent_root, source_commit, repository, *,
    confirm_repository, confirm_source, payload_root,
):
    """Write a confirmed child bootstrap payload and converge safely on retries."""
    if confirm_repository != repository or confirm_source != source_commit:
        raise InheritanceError("repository and source confirmation must match exactly")
    plan = plan_bootstrap(root, parent_root, source_commit, repository)
    child_root = Path(root).resolve(strict=True)
    parent_root = _parent_root(parent_root)
    payloads = _bootstrap_payloads(plan, child_root, payload_root)
    changed = [
        path for path, payload in sorted(payloads.items())
        if _bootstrap_path_change(child_root, parent_root, source_commit, path, payload)
    ]
    for path in changed:
        _write_bootstrap_payload(child_root, path, payloads[path])
    validate_inheritance(child_root)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "bootstrapped" if changed else "already_bootstrapped",
        "repository": repository,
        "parent": plan["parent"],
        "changed_paths": changed,
    }


ADOPT_TRANSPORT_DEPENDENCY = "scripts/template_sync_auth.py"
ADOPT_WORKFLOW_PATH = ".github/workflows/template-sync.yml"
ADOPT_REPORT_LIMIT = 50


def _adopt_recorded_protections(child_root, export):
    """Protections decided by an earlier phase live in the ignore file and the manifest."""
    recorded = set()
    if (child_root / MANIFEST_PATH).is_file():
        manifest = _read_json(child_root, MANIFEST_PATH)
        if type(manifest) is not dict or type(manifest.get("protected_paths")) is not list:
            raise InheritanceError("existing manifest.protected_paths must be a list")
        recorded.update(
            path
            for path in _ownership_roots(manifest["protected_paths"], "existing manifest.protected_paths")
            if not _owned_by(path, export["protected_paths"])
        )
    if (child_root / TEMPLATE_SYNC_IGNORE_PATH).is_file():
        positive, _exceptions = _read_template_sync_ignore(child_root)
        recorded.update(
            entry
            for entry in positive
            if not entry.endswith("/")
            and _owned_by(entry, export["inherited_paths"])
            and not _owned_by(entry, export["protected_paths"])
        )
    return recorded


def _adopt_ownership(export, parent_entries, protections):
    """Move each protected collision out of the inherited roots (ADR-0021).

    A protected file under an inherited directory root splits that root into the parent's
    remaining files at the source commit, because ownership roots may not overlap.
    """
    inherited = list(export["inherited_paths"])
    protected = list(export["protected_paths"])
    for path in sorted(protections):
        if _owned_by(path, protected):
            continue
        roots = [root for root in inherited if _owned_by(path, [root])]
        if not roots:
            raise InheritanceError(f"protected path is not under an inherited root: {path}")
        root = roots[0]
        inherited.remove(root)
        if root != path:
            inherited.extend(
                entry for entry in parent_entries if _owned_by(entry, [root]) and entry != path
            )
        protected.append(path)
    return sorted(set(inherited)), sorted(set(protected))


def _adopt_agent_inputs(inputs):
    """Shape-check agent inputs whose files may not have arrived yet (ADR-0022 phase 1)."""
    if type(inputs) is not list or not 2 <= len(inputs) <= MAX_AGENT_INPUTS:
        raise InheritanceError(
            f"agent profile.inputs must contain 2 to {MAX_AGENT_INPUTS} ordered inputs"
        )
    validated = []
    for index, item in enumerate(inputs):
        label = f"agent profile.inputs[{index}]"
        _object(item, {"layer", "repository", "path"}, label)
        if item["layer"] not in {"foundation", "template", "project"}:
            raise InheritanceError(f"{label}.layer must be foundation, template, or project")
        validated.append(
            {
                "layer": item["layer"],
                "repository": _repository(item["repository"], f"{label}.repository"),
                "path": _ownership_root(item["path"], f"{label}.path", file_only=True),
            }
        )
    return validated


def _adopt_desired(repository, parent_repository, source_commit, export, ownership):
    inherited, protected = ownership
    inputs = _adopt_agent_inputs(
        [
            *export["agent_inputs"],
            {"layer": "project", "repository": repository, "path": ".ai/project/agent-overlay.md"},
        ]
    )
    _validate_agent_input_order(inputs, parent_repository)
    _validate_agent_input_ownership(inputs, inherited, protected)
    ignore = {"docs/**"}
    ignore.update(f"{path}**" if path.endswith("/") else path for path in protected)
    if _owned_by("docs/foundation/", inherited):
        ignore.update({":!docs/foundation/", ":!docs/foundation/**"})
    return {
        "manifest": {
            "schema_version": 2,
            "parent": {"repository": parent_repository, "branch": export["branch"]},
            "lock_file": ".github/inheritance/lock.json",
            "inherited_paths": inherited,
            "protected_paths": protected,
        },
        "lock": {
            "schema_version": 1,
            "parent": {"repository": parent_repository, "commit": source_commit},
        },
        "agent_profile": {
            "schema_version": 1,
            "authority_policy": "strengthen-only",
            "inputs": inputs,
        },
        "template_sync_ignore": sorted(ignore),
    }


def _adopt_ignore_payload(desired):
    return (
        "# Generated from the exact direct-parent inheritance export (adopt-child).\n"
        + "\n".join(desired["template_sync_ignore"])
        + "\n"
    ).encode()


def _adopt_metadata_payloads(desired):
    return {
        MANIFEST_PATH: (json.dumps(desired["manifest"], indent=2) + "\n").encode(),
        ".github/inheritance/lock.json": (json.dumps(desired["lock"], indent=2) + "\n").encode(),
        AGENT_PROFILE_PATH: (json.dumps(desired["agent_profile"], indent=2) + "\n").encode(),
        TEMPLATE_SYNC_IGNORE_PATH: _adopt_ignore_payload(desired),
    }


def _adopt_matches(child_root, path, payload):
    try:
        return (child_root / path).read_bytes() == payload
    except OSError:
        return False


def plan_adopt(root, parent_root, source_commit, repository, *, protect=(), accept=()):
    """Classify an existing repository against its direct parent without writing.

    Adoption is phased (ADR-0022): ``--prepare`` writes only the transport, Template Sync
    delivers the tree, and ``--apply`` writes the metadata once the tree matches.
    """
    child_root, child_repository, branch = _child_finalization_worktree(root)
    repository = _repository(repository, "child repository")
    if child_repository.casefold() != repository.casefold():
        raise InheritanceError("child origin does not match requested repository")
    parent_root, parent_repository, export = _bootstrap_parent(parent_root, source_commit)
    if not _owned_by(ADOPT_TRANSPORT_DEPENDENCY, export["inherited_paths"]):
        raise InheritanceError(
            f"direct parent does not export the transport dependency {ADOPT_TRANSPORT_DEPENDENCY}"
        )
    parent_entries = _parent_inherited_entries(parent_root, source_commit, export["inherited_paths"])
    child_entries = _child_inherited_entries(child_root, parent_root, export["inherited_paths"])

    identical, collisions, pending = [], {}, []
    for path in sorted(set(parent_entries) | set(child_entries)):
        parent_entry = parent_entries.get(path)
        child_entry = child_entries.get(path)
        if child_entry is None:
            pending.append(path)
        elif parent_entry is None:
            collisions[path] = "child_only"
        elif child_entry == parent_entry:
            identical.append(path)
        else:
            collisions[path] = "differs"

    protect = {_repository_file_path(path, "protect path") for path in protect}
    accept = {_repository_file_path(path, "accept path") for path in accept}
    known = set(collisions) | set(identical)
    for path in sorted(protect | accept):
        if path not in known:
            raise InheritanceError(f"resolution names a path that is not a collision: {path}")
    protect |= _adopt_recorded_protections(child_root, export)
    if protect & accept:
        raise InheritanceError(
            f"a collision cannot be both protected and accepted: {sorted(protect & accept)}"
        )
    for path in sorted(accept):
        if collisions.get(path) == "child_only":
            raise InheritanceError(f"a child-only path has no parent version to accept: {path}")

    ownership = _adopt_ownership(export, parent_entries, protect)
    desired = _adopt_desired(repository, parent_repository, source_commit, export, ownership)
    prepared = (
        _adopt_matches(child_root, TEMPLATE_SYNC_IGNORE_PATH, _adopt_ignore_payload(desired))
        and (child_root / ADOPT_WORKFLOW_PATH).is_file()
        and child_entries.get(ADOPT_TRANSPORT_DEPENDENCY) == parent_entries.get(ADOPT_TRANSPORT_DEPENDENCY)
    )
    # Once the transport is prepared, an unprotected `differs` collision is what the sync
    # will overwrite: it was accepted when the ignore file was written without it.
    unresolved = sorted(
        path for path, reason in collisions.items()
        if path not in protect and path not in accept and not (prepared and reason == "differs")
    )
    effective_inherited = ownership[0]
    missing = sorted(
        path for path, entry in parent_entries.items()
        if _owned_by(path, effective_inherited) and child_entries.get(path) != entry
    )
    stray = sorted(
        path for path in child_entries
        if _owned_by(path, effective_inherited) and path not in parent_entries
    )
    activated = all(
        _adopt_matches(child_root, path, payload)
        for path, payload in _adopt_metadata_payloads(desired).items()
    )
    if unresolved:
        status = "blocked"
    elif activated:
        status = "already_adopted"
    elif not missing and not stray:
        status = "ready_to_adopt"
    elif prepared:
        status = "prepared"
    else:
        status = "ready_to_prepare"
    owner, parent = parent_repository.casefold().split("/", 1)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "repository": repository,
        "branch": branch,
        "parent": {
            "repository": parent_repository,
            "commit": source_commit,
            "export": export["path"],
        },
        "classification": {
            "identical": identical,
            "collision": [
                {"path": path, "reason": reason} for path, reason in sorted(collisions.items())
            ],
            "pending": pending,
        },
        "resolution": {
            "protect": sorted(protect),
            "accept": sorted(accept),
            "unresolved": unresolved,
        },
        "activation": {
            "prepared": prepared,
            "missing": missing[:ADOPT_REPORT_LIMIT],
            "missing_count": len(missing),
            "stray": stray[:ADOPT_REPORT_LIMIT],
        },
        "desired": desired,
        "payloads": {
            "prepare": [ADOPT_WORKFLOW_PATH],
            "apply": [
                *sorted(BOOTSTRAP_MANUAL_BOUNDARIES),
                f"docs/inheritance/readmes/{owner}/{parent}.md",
            ],
        },
    }


def _adopt_prepare_payloads(plan, child_root, parent_root, payload_root):
    source_commit = plan["parent"]["commit"]
    payload_root = _bootstrap_payload_root(payload_root, child_root)
    workflow = _bootstrap_payload_file(payload_root, ADOPT_WORKFLOW_PATH)
    _validate_sync_workflow_payload(workflow, plan["parent"]["repository"])
    entry = _parent_entry(parent_root, source_commit, ADOPT_TRANSPORT_DEPENDENCY)
    if entry is None:
        raise InheritanceError(f"parent does not provide {ADOPT_TRANSPORT_DEPENDENCY}")
    dependency = _git_blob(parent_root, entry[0], ADOPT_TRANSPORT_DEPENDENCY)
    return {
        TEMPLATE_SYNC_IGNORE_PATH: _adopt_ignore_payload(plan["desired"]),
        ADOPT_WORKFLOW_PATH: workflow,
        ADOPT_TRANSPORT_DEPENDENCY: dependency,
    }


def _adopt_prepare_change(child_root, parent_root, source_commit, path, payload):
    # The ignore file is generated, and the transport dependency is the parent's exact blob:
    # a differing child copy is a collision that plan_adopt already required to be accepted.
    if path in {TEMPLATE_SYNC_IGNORE_PATH, ADOPT_TRANSPORT_DEPENDENCY}:
        return not _adopt_matches(child_root, path, payload)
    return _bootstrap_path_change(child_root, parent_root, source_commit, path, payload)


def apply_adopt(
    root, parent_root, source_commit, repository, *,
    confirm_repository, confirm_source, payload_root, prepare=False, protect=(), accept=(),
):
    """Phase 1 (``prepare``) writes the transport; phase 3 writes the metadata (ADR-0022)."""
    if confirm_repository != repository or confirm_source != source_commit:
        raise InheritanceError("repository and source confirmation must match exactly")
    plan = plan_adopt(root, parent_root, source_commit, repository, protect=protect, accept=accept)
    if plan["status"] == "blocked":
        raise InheritanceError(
            "every collision must be resolved with --protect or --accept: "
            f"{plan['resolution']['unresolved']}"
        )
    child_root = Path(root).resolve(strict=True)
    parent_root = _parent_root(parent_root)

    if prepare:
        payloads = _adopt_prepare_payloads(plan, child_root, parent_root, payload_root)
        changed = [
            path for path, payload in sorted(payloads.items())
            if _adopt_prepare_change(child_root, parent_root, source_commit, path, payload)
        ]
        for path in changed:
            _write_bootstrap_payload(child_root, path, payloads[path])
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "prepared" if changed else "already_prepared",
            "repository": repository,
            "parent": plan["parent"],
            "changed_paths": changed,
            "protected_collisions": plan["resolution"]["protect"],
            "accepted_collisions": plan["resolution"]["accept"],
            "pending_inherited_paths": len(plan["classification"]["pending"]),
        }

    activation = plan["activation"]
    if activation["missing_count"] or activation["stray"]:
        raise InheritanceError(
            "inherited tree does not match the source commit; let Template Sync deliver it "
            f"first (missing={activation['missing_count']}, stray={len(activation['stray'])}, "
            f"first={activation['missing'][:5] or activation['stray'][:5]})"
        )
    payloads = _bootstrap_payloads(plan, child_root, payload_root)
    payloads.update(_adopt_metadata_payloads(plan["desired"]))
    changed = [
        path for path, payload in sorted(payloads.items())
        if _bootstrap_path_change(child_root, parent_root, source_commit, path, payload)
    ]
    for path in changed:
        _write_bootstrap_payload(child_root, path, payloads[path])
    validate_inheritance(child_root)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "adopted" if changed else "already_adopted",
        "repository": repository,
        "parent": plan["parent"],
        "changed_paths": changed,
        "protected_collisions": plan["resolution"]["protect"],
        "accepted_collisions": plan["resolution"]["accept"],
    }


def _manual_boundary_reason(path):
    if path.startswith(".github/workflows/"):
        return "workflow-security-boundary"
    if path == AGENT_PROFILE_PATH or path.startswith(".ai/project/"):
        return "agent-project-boundary"
    if path.startswith(".github/inheritance/") or path == TEMPLATE_SYNC_IGNORE_PATH:
        return "inheritance-ownership-boundary"
    return "repository-owned-boundary"


def _manual_transport_reason(path):
    if path.startswith(".github/workflows/"):
        return "workflow-security-boundary"
    return "legacy-transport-exclusion"


def _template_sync_excludes(path, excluded, exceptions):
    return _owned_by(path, excluded) and not _owned_by(path, exceptions)


def _child_finalization_worktree(root):
    child_root = Path(root).resolve(strict=True)
    top_level = Path(
        _git(child_root, ["rev-parse", "--show-toplevel"], "child root discovery").strip()
    ).resolve()
    if top_level != child_root:
        raise InheritanceError("child root must be the Git worktree top level")
    if _git(child_root, ["status", "--porcelain=v1"], "child status read"):
        raise InheritanceError("child worktree must be clean before finalization")
    branch = _git(
        child_root, ["symbolic-ref", "--quiet", "--short", "HEAD"], "child branch read"
    ).strip()
    default_ref = _child_default_ref(child_root)
    if branch == default_ref.removeprefix("origin/"):
        raise InheritanceError("finalization must not run on the default branch")
    remote = _git(child_root, ["remote", "get-url", "origin"], "child origin read").strip()
    return child_root, _github_repository(remote), branch


def _child_default_ref(child_root):
    return _git(
        child_root,
        ["symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"],
        "child default branch read",
    ).strip()


def _finalization_context(root, parent_root, source_commit):
    contract = validate_inheritance(root)
    child_root, child_repository, branch = _child_finalization_worktree(root)
    parent_root = _parent_root(parent_root)
    if type(source_commit) is not str or not COMMIT_ID.fullmatch(source_commit):
        raise InheritanceError("source commit must be a full lowercase commit ID")
    target, _candidate = _next_parent_commit(parent_root, contract)
    accepted_range = _git(
        parent_root,
        [
            "rev-list",
            "--first-parent",
            f"{contract['parent']['commit']}..{target}",
        ],
        "accepted source range read",
    ).splitlines()
    if source_commit != contract["parent"]["commit"] and source_commit not in accepted_range:
        raise InheritanceError("source commit must be in the accepted first-parent range")
    return child_root, parent_root, contract, child_repository, branch


def _finalization_review(child_root, parent_root, contract, source_commit):
    inherited = contract["ownership"]["inherited"]
    excluded, exceptions = _read_template_sync_ignore(child_root)
    parent_entries = _parent_inherited_entries(parent_root, source_commit, inherited)
    child_entries = _child_inherited_entries(child_root, parent_root, inherited)
    review = {
        name: []
        for name in (
            "synchronized",
            "pending_sync",
            "pending_manual_port",
            "manually_ported",
            "protected_review",
            "ownership_review",
            "deletion_review",
        )
    }
    for path in sorted(set(parent_entries) | set(child_entries)):
        parent_entry = parent_entries.get(path)
        child_entry = child_entries.get(path)
        is_manual = _template_sync_excludes(path, excluded, exceptions)
        if parent_entry is None:
            review["deletion_review"].append(path)
        elif child_entry == parent_entry:
            review["manually_ported" if is_manual else "synchronized"].append(path)
        elif is_manual:
            review["pending_manual_port"].append(
                {"path": path, "reason": _manual_transport_reason(path)}
            )
        else:
            review["pending_sync"].append(path)

    if source_commit != contract["parent"]["commit"]:
        for path in _changed_paths(
            parent_root, contract["parent"]["commit"], source_commit
        ):
            owner = _path_owner(path, contract["ownership"])
            if owner in {"inherited", "protected"}:
                continue
            parent_entry = _parent_entry(parent_root, source_commit, path)
            child_entry = _child_entry(child_root, parent_root, path)
            if parent_entry is not None or child_entry is not None:
                review["ownership_review"].append(path)

    default_ref = _child_default_ref(child_root)
    for path in _changed_paths(child_root, default_ref, "HEAD"):
        owner = _path_owner(path, contract["ownership"])
        if owner == "protected" and path != contract["lock_file"]:
            review["protected_review"].append(path)
        elif owner == "unowned":
            review["ownership_review"].append(path)
    for name in review:
        unique = (
            {item["path"]: item for item in review[name]}.values()
            if name == "pending_manual_port"
            else set(review[name])
        )
        review[name] = sorted(
            unique,
            key=(lambda item: item["path"]) if name == "pending_manual_port" else None,
        )
    return review


def _finalization_report(contract, child_repository, branch, source_commit, review):
    has_unsupported_manual_port = any(
        item["reason"] != "workflow-security-boundary"
        for item in review["pending_manual_port"]
    )
    is_blocked = has_unsupported_manual_port or any(
        review[name]
        for name in (
            "pending_sync",
            "protected_review",
            "ownership_review",
            "deletion_review",
        )
    )
    has_work = bool(review["pending_manual_port"]) or (
        contract["parent"]["commit"] != source_commit
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "status": (
            "blocked"
            if is_blocked
            else "ready_to_finalize" if has_work else "already_finalized"
        ),
        "repository": child_repository,
        "branch": branch,
        "parent": {
            "repository": contract["parent"]["repository"],
            "locked_commit": contract["parent"]["commit"],
            "source_commit": source_commit,
        },
        **review,
    }


def plan_finalization(root, parent_root, source_commit):
    """Report exact-source finalization work without modifying either worktree."""
    child_root, parent_root, contract, repository, branch = _finalization_context(
        root, parent_root, source_commit
    )
    review = _finalization_review(child_root, parent_root, contract, source_commit)
    return _finalization_report(contract, repository, branch, source_commit, review)


def _raise_finalization_blocker(review):
    for category, message in (
        ("pending_sync", "pending sync content must be accepted first"),
        ("protected_review", "protected review is required"),
        ("ownership_review", "ownership review is required"),
        ("deletion_review", "deletion review is required"),
    ):
        if review[category]:
            raise InheritanceError(f"{message}: {review[category]}")
    unsupported = [
        item
        for item in review["pending_manual_port"]
        if item["reason"] != "workflow-security-boundary"
    ]
    if unsupported:
        raise InheritanceError(f"unsupported manual port is required: {unsupported}")


def _manual_port_payload(parent_root, source_commit, path):
    entry = _parent_entry(parent_root, source_commit, path)
    if entry is None:
        raise InheritanceError(f"manual-port source file is missing: {path}")
    return path, _git_blob(parent_root, entry[0], path), entry[1]


def _write_manual_port(child_root, payload):
    path, content, is_executable = payload
    destination = child_root / path
    parent = destination.parent
    if (
        parent.is_symlink()
        or not parent.is_dir()
        or destination.is_symlink()
        or (destination.exists() and not destination.is_file())
    ):
        raise InheritanceError(f"manual-port destination is unsafe: {path}")
    destination.write_bytes(content)
    destination.chmod(0o755 if is_executable else 0o644)


def _write_lock_commit(child_root, contract, source_commit):
    lock_path = child_root / contract["lock_file"]
    temporary = lock_path.with_name(f".{lock_path.name}.finalize.tmp")
    if temporary.exists() or temporary.is_symlink():
        raise InheritanceError("temporary lock path must be absent before finalization")
    lock = _read_json(child_root, contract["lock_file"])
    lock["parent"]["commit"] = source_commit
    try:
        temporary.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
        temporary.replace(lock_path)
    except OSError as error:
        try:
            temporary.unlink(missing_ok=True)
        except OSError as cleanup_error:
            raise InheritanceError(
                "inheritance lock update and temporary cleanup failed"
            ) from cleanup_error
        raise InheritanceError("inheritance lock update failed before acceptance") from error


def apply_finalization(
    root,
    parent_root,
    source_commit,
    *,
    confirm_repository,
    confirm_source,
):
    """Materialize supported manual ports and atomically advance the accepted lock."""
    child_root, parent_root, contract, repository, branch = _finalization_context(
        root, parent_root, source_commit
    )
    if confirm_repository != repository or confirm_source != source_commit:
        raise InheritanceError("repository and source confirmation must match exactly")
    review = _finalization_review(child_root, parent_root, contract, source_commit)
    _raise_finalization_blocker(review)
    manual_paths = [item["path"] for item in review["pending_manual_port"]]
    payloads = [
        _manual_port_payload(parent_root, source_commit, path)
        for path in manual_paths
    ]
    for payload in payloads:
        _write_manual_port(child_root, payload)

    completed = _finalization_review(child_root, parent_root, contract, source_commit)
    _raise_finalization_blocker(completed)
    if completed["pending_manual_port"]:
        raise InheritanceError("manual-port finalization did not converge")
    lock_updated = contract["parent"]["commit"] != source_commit
    if lock_updated:
        _write_lock_commit(child_root, contract, source_commit)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "finalized" if manual_paths or lock_updated else "already_finalized",
        "repository": repository,
        "branch": branch,
        "parent": {
            "repository": contract["parent"]["repository"],
            "source_commit": source_commit,
        },
        "changes": {"manual_ported": manual_paths, "lock_updated": lock_updated},
        "review": completed,
    }


def _fleet_repository(repository, child_root, parent_root):
    child_root = Path(child_root).resolve(strict=True)
    parent_root = _parent_root(parent_root)
    plan = plan_inheritance(child_root, parent_root)
    candidate = plan["parent"]["candidate_commit"]
    target = plan["parent"]["target_commit"]
    excluded, exceptions = _read_template_sync_ignore(child_root)
    synchronized = []
    pending_sync = []
    pending_manual_port = []
    manually_ported = []
    protected_review = []
    ownership_review = []
    deletion_review = [
        {"path": path, "reason": "deletion-review-required"}
        for path in plan["changes"]["candidate_delete"]
    ]
    audited_inherited_files = sum(len(paths) for paths in plan["changes"].values())

    if candidate:
        for path in plan["changes"]["already_current"]:
            destination = (
                manually_ported
                if _template_sync_excludes(path, excluded, exceptions)
                else synchronized
            )
            destination.append(path)
        for path in plan["changes"]["add"] + plan["changes"]["modify"]:
            child_entry = _child_entry(child_root, parent_root, path)
            target_entry = _parent_entry(parent_root, target, path)
            is_manual = _template_sync_excludes(path, excluded, exceptions)
            if child_entry == target_entry:
                destination = manually_ported if is_manual else synchronized
                destination.append(path)
            elif is_manual:
                pending_manual_port.append(
                    {"path": path, "reason": _manual_transport_reason(path)}
                )
            else:
                pending_sync.append(path)
        for path in plan["skipped"]["protected"]:
            child_entry = _child_entry(child_root, parent_root, path)
            accepted_entries = {
                _parent_entry(parent_root, revision, path)
                for revision in {candidate, target}
            }
            if child_entry in accepted_entries:
                manually_ported.append(path)
            else:
                protected_review.append(
                    {"path": path, "reason": _manual_boundary_reason(path)}
                )
        for path in plan["skipped"]["unowned"]:
            child_entry = _child_entry(child_root, parent_root, path)
            target_entry = _parent_entry(parent_root, target, path)
            if child_entry is None and target_entry is None:
                continue
            ownership_review.append(
                {"path": path, "reason": "ownership-decision-required"}
            )
    else:
        ownership_roots = validate_inheritance(child_root)["ownership"]["inherited"]
        parent_entries = _parent_inherited_entries(parent_root, target, ownership_roots)
        child_entries = _child_inherited_entries(child_root, parent_root, ownership_roots)
        audited_paths = sorted(set(parent_entries) | set(child_entries))
        if len(audited_paths) > MAX_AUDITED_INHERITED_FILES:
            raise InheritanceError(
                f"inherited audit exceeds {MAX_AUDITED_INHERITED_FILES} files"
            )
        audited_inherited_files = len(audited_paths)
        for path in audited_paths:
            parent_entry = parent_entries.get(path)
            child_entry = child_entries.get(path)
            is_manual = _template_sync_excludes(path, excluded, exceptions)
            if parent_entry is None:
                deletion_review.append(
                    {"path": path, "reason": "deletion-review-required"}
                )
            elif child_entry == parent_entry:
                destination = manually_ported if is_manual else synchronized
                destination.append(path)
            elif is_manual:
                pending_manual_port.append(
                    {"path": path, "reason": _manual_transport_reason(path)}
                )
            else:
                pending_sync.append(path)

    return {
        "repository": repository,
        "repository_source": "explicit-argument",
        "parent": plan["parent"],
        "audited_inherited_files": audited_inherited_files,
        "synchronized": sorted(synchronized),
        "pending_sync": sorted(pending_sync),
        "pending_manual_port": sorted(
            pending_manual_port, key=lambda item: item["path"]
        ),
        "manually_ported": sorted(manually_ported),
        "protected_review": protected_review,
        "ownership_review": ownership_review,
        "deletion_review": sorted(deletion_review, key=lambda item: item["path"]),
    }


def _validated_fleet_entries(repositories):
    if type(repositories) is not list or not 1 <= len(repositories) <= MAX_FLEET_REPOSITORIES:
        raise InheritanceError(
            f"fleet repositories must contain 1 to {MAX_FLEET_REPOSITORIES} entries"
        )

    entries = []
    seen_repositories = set()
    seen_roots = set()
    for index, entry in enumerate(repositories):
        if type(entry) not in {list, tuple} or len(entry) != 3:
            raise InheritanceError(
                f"fleet repositories[{index}] must contain repository, child root, parent root"
            )
        repository = _repository(entry[0], f"fleet repositories[{index}].repository")
        try:
            child_root = Path(entry[1]).resolve(strict=True)
        except OSError as error:
            raise InheritanceError(
                f"fleet repositories[{index}].child root must exist"
            ) from error
        repository_key = repository.casefold()
        if repository_key in seen_repositories or child_root in seen_roots:
            raise InheritanceError("fleet repositories contain a duplicate child")
        seen_repositories.add(repository_key)
        seen_roots.add(child_root)
        entries.append((repository, child_root, entry[2]))
    return sorted(entries, key=lambda item: item[0].casefold())


def _fleet_summary(reports):
    categories = (
        "synchronized",
        "pending_sync",
        "pending_manual_port",
        "manually_ported",
        "protected_review",
        "ownership_review",
        "deletion_review",
    )
    summary = {
        category: sum(len(report[category]) for report in reports)
        for category in categories
    }
    summary["audited_inherited_files"] = sum(
        report["audited_inherited_files"] for report in reports
    )
    summary["repositories"] = len(reports)
    return summary


def fleet_report(repositories):
    """Report bounded local propagation state without modifying any worktree."""
    reports = [
        _fleet_repository(repository, child_root, parent_root)
        for repository, child_root, parent_root in _validated_fleet_entries(repositories)
    ]
    summary = _fleet_summary(reports)
    needs_attention = any(
        summary[category]
        for category in (
            "pending_sync",
            "pending_manual_port",
            "protected_review",
            "ownership_review",
            "deletion_review",
        )
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "attention" if needs_attention else "ready",
        "repositories": reports,
        "summary": summary,
    }


def _fleet_directory(value, label):
    return _ownership_root(value, label, file_only=True)


def _fleet_worktree(workspace_root, directory, label):
    candidate = workspace_root / directory
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as error:
        raise InheritanceError(f"{label} must exist under the fleet workspace root") from error
    if resolved != candidate or not resolved.is_relative_to(workspace_root) or not resolved.is_dir():
        raise InheritanceError(
            f"{label} must be a non-symlink directory under the fleet workspace root"
        )
    return resolved


def _read_fleet_config(config_path):
    candidate = Path(config_path)
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    if candidate.is_symlink():
        raise InheritanceError("fleet config must be a non-symlink file")
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as error:
        raise InheritanceError("fleet config must be a file") from error
    if not resolved.is_file():
        raise InheritanceError("fleet config must be a non-symlink file")
    try:
        if resolved.stat().st_size > MAX_CONTRACT_BYTES:
            raise InheritanceError(f"fleet config exceeds {MAX_CONTRACT_BYTES} bytes")
        config = json.loads(
            resolved.read_text(encoding="utf-8"), object_pairs_hook=_unique_object
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise InheritanceError("fleet config must contain valid UTF-8 JSON") from error

    _object(
        config,
        {"schema_version", "repositories"},
        "fleet config",
    )
    if (
        type(config["schema_version"]) is not int
        or config["schema_version"] != FLEET_SCHEMA_VERSION
    ):
        raise InheritanceError(
            f"fleet config.schema_version must be {FLEET_SCHEMA_VERSION}"
        )

    repositories = config["repositories"]
    if type(repositories) is not list or not 1 <= len(repositories) <= MAX_FLEET_REPOSITORIES:
        raise InheritanceError(
            f"fleet config.repositories must contain 1 to {MAX_FLEET_REPOSITORIES} entries"
        )
    validated = []
    repository_keys = set()
    directories = set()
    for index, entry in enumerate(repositories):
        label = f"fleet config.repositories[{index}]"
        _object(
            entry,
            {
                "repository",
                "directory",
                "parent_repository",
                "parent_directory",
                "lifecycle",
                "reason",
            },
            label,
        )
        repository = _repository(entry["repository"], f"{label}.repository")
        parent_repository = _repository(
            entry["parent_repository"], f"{label}.parent_repository"
        )
        directory = _fleet_directory(entry["directory"], f"{label}.directory")
        parent_directory = _fleet_directory(
            entry["parent_directory"], f"{label}.parent_directory"
        )
        lifecycle = entry["lifecycle"]
        if type(lifecycle) is not str or lifecycle not in FLEET_LIFECYCLES:
            raise InheritanceError(
                f"{label}.lifecycle must be active, paused, or retired"
            )
        reason = entry["reason"]
        if (
            type(reason) is not str
            or not reason.strip()
            or reason != reason.strip()
            or len(reason) > 512
        ):
            raise InheritanceError(f"{label}.reason must be a concise non-empty string")
        repository_key = repository.casefold()
        if repository_key == parent_repository.casefold() or directory == parent_directory:
            raise InheritanceError("fleet config child and parent must be distinct")
        if repository_key in repository_keys or directory in directories:
            raise InheritanceError("fleet config contains a duplicate child")
        repository_keys.add(repository_key)
        directories.add(directory)
        validated.append(
            {
                "repository": repository,
                "directory": directory,
                "parent_repository": parent_repository,
                "parent_directory": parent_directory,
                "lifecycle": lifecycle,
                "reason": reason,
            }
        )
    lifecycle_by_repository = {
        item["repository"].casefold(): item["lifecycle"] for item in validated
    }
    for item in validated:
        parent_lifecycle = lifecycle_by_repository.get(
            item["parent_repository"].casefold()
        )
        if item["lifecycle"] == "active" and parent_lifecycle in {"paused", "retired"}:
            raise InheritanceError(
                "fleet config active repository cannot inherit from a paused or retired parent"
            )
    return sorted(validated, key=lambda item: item["repository"].casefold())


def _fleet_workspace_root(workspace_root):
    try:
        workspace_root = Path(workspace_root).resolve(strict=True)
    except OSError as error:
        raise InheritanceError("fleet workspace root must exist") from error
    if not workspace_root.is_dir():
        raise InheritanceError("fleet workspace root must be a directory")
    return workspace_root


def fleet_audit(config_path, workspace_root):
    """Audit active relationships and report every fixed fleet lifecycle."""
    workspace_root = _fleet_workspace_root(workspace_root)

    repositories = []
    entries = _read_fleet_config(config_path)
    for index, entry in enumerate(entries):
        if entry["lifecycle"] != "active":
            continue
        child_root = _fleet_worktree(
            workspace_root, entry["directory"], f"fleet repository[{index}].directory"
        )
        parent_root = _fleet_worktree(
            workspace_root,
            entry["parent_directory"],
            f"fleet repository[{index}].parent_directory",
        )
        contract = validate_inheritance(child_root)
        if contract["parent"]["repository"].casefold() != entry[
            "parent_repository"
        ].casefold():
            raise InheritanceError(
                f"fleet repository parent does not match child manifest: {entry['repository']}"
            )
        repositories.append((entry["repository"], child_root, parent_root))

    report = fleet_report(repositories) if repositories else {
        "schema_version": SCHEMA_VERSION,
        "status": "ready",
        "repositories": [],
        "summary": _fleet_summary([]),
    }
    entry_by_repository = {
        entry["repository"].casefold(): entry for entry in entries
    }
    for repository in report["repositories"]:
        entry = entry_by_repository[repository["repository"].casefold()]
        repository["repository_source"] = "fixed-fleet-config"
        repository["lifecycle"] = "active"
        repository["reason"] = entry["reason"]
    report["repositories"].extend(
        {
            "repository": entry["repository"],
            "repository_source": "fixed-fleet-config",
            "lifecycle": entry["lifecycle"],
            "reason": entry["reason"],
        }
        for entry in entries
        if entry["lifecycle"] != "active"
    )
    report["repositories"].sort(key=lambda item: item["repository"].casefold())
    for lifecycle in sorted(FLEET_LIFECYCLES):
        report["summary"][lifecycle] = sum(
            item["lifecycle"] == lifecycle for item in report["repositories"]
        )
    report["summary"]["repositories"] = len(report["repositories"])
    report["schema_version"] = FLEET_SCHEMA_VERSION
    if report["summary"]["paused"]:
        report["status"] = "attention"
    return report


def _impact_for_path(path, contract, excluded, exceptions):
    owner = _path_owner(path, contract["ownership"])
    if owner == "inherited":
        if _template_sync_excludes(path, excluded, exceptions):
            return "manual-boundary", _manual_transport_reason(path)
        return "schedule-only", "template-sync-owned"
    if owner == "unowned":
        return "child-migration-required", "ownership-decision-required"
    reason = _manual_boundary_reason(path)
    if reason == "workflow-security-boundary":
        return "manual-boundary", reason
    if reason in {"agent-project-boundary", "inheritance-ownership-boundary"}:
        return "child-migration-required", reason
    return "foundation-only", reason


def _propagation_context(config_path, workspace_root, parent_repository):
    parent_repository = _repository(parent_repository, "parent repository")
    workspace_root = _fleet_workspace_root(workspace_root)
    entries = [
        entry
        for entry in _read_fleet_config(config_path)
        if entry["lifecycle"] == "active"
        and entry["parent_repository"].casefold() == parent_repository.casefold()
    ]
    if not entries:
        raise InheritanceError("parent repository has no active direct child in fleet config")
    parent_directories = {entry["parent_directory"] for entry in entries}
    if len(parent_directories) != 1:
        raise InheritanceError("active direct children disagree on the parent worktree")
    parent_root = _fleet_worktree(
        workspace_root, parent_directories.pop(), "propagation parent directory"
    )
    parent_root = _parent_root(parent_root)
    remote = _git(parent_root, ["remote", "get-url", "origin"], "origin discovery").strip()
    if _github_repository(remote).casefold() != parent_repository.casefold():
        raise InheritanceError("parent origin does not match requested repository")
    return workspace_root, parent_repository, parent_root, entries


def _propagation_paths(parent_root, base_commit, head_commit):
    for revision, label in ((base_commit, "base"), (head_commit, "head")):
        if type(revision) is not str or not COMMIT_ID.fullmatch(revision):
            raise InheritanceError(f"{label} commit must be a full lowercase commit ID")
        resolved = _git(
            parent_root,
            ["rev-parse", "--verify", f"{revision}^{{commit}}"],
            f"{label} commit resolution",
        ).strip()
        if resolved != revision:
            raise InheritanceError(f"{label} commit did not resolve exactly")
    _git(
        parent_root,
        ["merge-base", "--is-ancestor", base_commit, head_commit],
        "commit ancestry validation",
    )
    return _changed_paths(parent_root, base_commit, head_commit)


def _propagation_changes(entries, workspace_root, parent_repository, changed_paths):
    changes = []
    for index, entry in enumerate(entries):
        child_root = _fleet_worktree(
            workspace_root,
            entry["directory"],
            f"propagation child[{index}].directory",
        )
        contract = validate_inheritance(child_root)
        if contract["parent"]["repository"].casefold() != parent_repository.casefold():
            raise InheritanceError(
                f"fleet repository parent does not match child manifest: {entry['repository']}"
            )
        excluded, exceptions = _read_template_sync_ignore(child_root)
        for path in changed_paths:
            impact, reason = _impact_for_path(path, contract, excluded, exceptions)
            changes.append(
                {
                    "repository": entry["repository"],
                    "path": path,
                    "impact": impact,
                    "reason": reason,
                }
            )
    changes.sort(key=lambda item: (item["repository"].casefold(), item["path"]))
    return changes


def propagation_impact(
    config_path,
    workspace_root,
    parent_repository,
    base_commit,
    head_commit,
):
    """Classify a parent diff against every active direct-child ownership contract."""
    workspace_root, parent_repository, parent_root, entries = _propagation_context(
        config_path, workspace_root, parent_repository
    )
    changed_paths = _propagation_paths(parent_root, base_commit, head_commit)
    changes = _propagation_changes(
        entries, workspace_root, parent_repository, changed_paths
    )
    status = max(
        (item["impact"] for item in changes),
        key=lambda impact: IMPACT_PRIORITY[impact],
        default="foundation-only",
    )
    return {
        "schema_version": FLEET_SCHEMA_VERSION,
        "status": status,
        "parent_repository": parent_repository,
        "base_commit": base_commit,
        "head_commit": head_commit,
        "children": sorted(entry["repository"] for entry in entries),
        "changes": changes,
        "summary": {
            impact: sum(item["impact"] == impact for item in changes)
            for impact in IMPACT_PRIORITY
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="validate contract")
    validate.add_argument("--root", type=Path, default=Path("."), help="child repository root")
    plan = commands.add_parser("plan", help="plan the next parent commit")
    plan.add_argument("--root", type=Path, default=Path("."), help="child repository root")
    plan.add_argument("--parent-root", type=Path, required=True, help="local parent Git worktree")
    bootstrap = commands.add_parser(
        "bootstrap-child", help="plan metadata for a direct child repository"
    )
    bootstrap.add_argument("--root", type=Path, default=Path("."), help="child repository root")
    bootstrap.add_argument("--parent-root", type=Path, required=True, help="parent worktree")
    bootstrap.add_argument("--source-commit", required=True)
    bootstrap.add_argument("--repository", required=True, help="child OWNER/REPOSITORY")
    bootstrap.add_argument("--apply", action="store_true", help="write confirmed payload")
    bootstrap.add_argument("--payload-root", type=Path)
    bootstrap.add_argument("--confirm-repository")
    bootstrap.add_argument("--confirm-source")
    adopt = commands.add_parser(
        "adopt-child",
        help="plan, prepare, or activate adoption of an existing repository (ADR-0021/0022)",
    )
    adopt.add_argument("--root", type=Path, default=Path("."), help="existing repository root")
    adopt.add_argument("--parent-root", type=Path, required=True, help="direct-parent worktree")
    adopt.add_argument("--source-commit", required=True)
    adopt.add_argument("--repository", required=True, help="child OWNER/REPOSITORY")
    adopt.add_argument(
        "--protect", action="append", default=[], metavar="PATH",
        help="keep the child copy of a colliding path and stop inheriting it",
    )
    adopt.add_argument(
        "--accept", action="append", default=[], metavar="PATH",
        help="let the first Template Sync overwrite the child copy of a colliding path",
    )
    adopt.add_argument(
        "--prepare", action="store_true",
        help="with --apply: write only the transport (phase 1) instead of the metadata (phase 3)",
    )
    adopt.add_argument("--apply", action="store_true", help="write confirmed payload")
    adopt.add_argument("--payload-root", type=Path)
    adopt.add_argument("--confirm-repository")
    adopt.add_argument("--confirm-source")
    finalize = commands.add_parser(
        "finalize-sync",
        help="plan or apply exact-source manual ports on an existing sync branch",
    )
    finalize.add_argument("--root", type=Path, default=Path("."), help="child repository root")
    finalize.add_argument(
        "--parent-root", type=Path, required=True, help="local parent Git worktree"
    )
    finalize.add_argument("--source-commit", required=True, help="exact Template Sync source")
    finalize.add_argument("--apply", action="store_true", help="write manual ports and lock")
    finalize.add_argument("--confirm-repository", help="exact child OWNER/REPOSITORY")
    finalize.add_argument("--confirm-source", help="repeat the exact source commit")
    fleet = commands.add_parser("fleet-report", help="report local propagation boundaries")
    fleet.add_argument(
        "--repository",
        action="append",
        nargs=3,
        required=True,
        metavar=("REPOSITORY", "CHILD_ROOT", "PARENT_ROOT"),
        help="explicit child repository and local child/parent worktrees",
    )
    audit = commands.add_parser("fleet-audit", help="audit the fixed local fleet")
    audit.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_FLEET_CONFIG_PATH,
        help="machine-readable fleet configuration",
    )
    audit.add_argument(
        "--workspace-root",
        type=Path,
        default=Path(".."),
        help="directory containing every configured Git worktree",
    )
    impact = commands.add_parser(
        "propagation-impact",
        help="classify a parent diff against active direct-child ownership",
    )
    impact.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_FLEET_CONFIG_PATH,
        help="machine-readable fleet configuration",
    )
    impact.add_argument(
        "--workspace-root",
        type=Path,
        default=Path(".."),
        help="directory containing configured Git worktrees",
    )
    impact.add_argument("--parent-repository", required=True)
    impact.add_argument("--base-commit", required=True)
    impact.add_argument("--head-commit", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            report = validate_inheritance(args.root)
        elif args.command == "plan":
            report = plan_inheritance(args.root, args.parent_root)
        elif args.command == "bootstrap-child":
            if args.apply:
                report = apply_bootstrap(
                    args.root, args.parent_root, args.source_commit, args.repository,
                    confirm_repository=args.confirm_repository,
                    confirm_source=args.confirm_source,
                    payload_root=args.payload_root,
                )
            else:
                if args.payload_root or args.confirm_repository or args.confirm_source:
                    raise InheritanceError("bootstrap payload and confirmations require --apply")
                report = plan_bootstrap(
                    args.root, args.parent_root, args.source_commit, args.repository
                )
        elif args.command == "adopt-child":
            if args.apply:
                report = apply_adopt(
                    args.root, args.parent_root, args.source_commit, args.repository,
                    confirm_repository=args.confirm_repository,
                    confirm_source=args.confirm_source,
                    payload_root=args.payload_root,
                    prepare=args.prepare, protect=args.protect, accept=args.accept,
                )
            else:
                if args.prepare or args.payload_root or args.confirm_repository or args.confirm_source:
                    raise InheritanceError("adopt payload, --prepare, and confirmations require --apply")
                report = plan_adopt(
                    args.root, args.parent_root, args.source_commit, args.repository,
                    protect=args.protect, accept=args.accept,
                )
        elif args.command == "finalize-sync":
            if args.apply:
                report = apply_finalization(
                    args.root,
                    args.parent_root,
                    args.source_commit,
                    confirm_repository=args.confirm_repository,
                    confirm_source=args.confirm_source,
                )
            else:
                if args.confirm_repository or args.confirm_source:
                    raise InheritanceError(
                        "confirmation arguments are accepted only with --apply"
                    )
                report = plan_finalization(
                    args.root, args.parent_root, args.source_commit
                )
        elif args.command == "fleet-report":
            report = fleet_report(args.repository)
        elif args.command == "fleet-audit":
            report = fleet_audit(args.config, args.workspace_root)
        else:
            report = propagation_impact(
                args.config,
                args.workspace_root,
                args.parent_repository,
                args.base_commit,
                args.head_commit,
            )
    except InheritanceError as error:
        print(f"inheritance error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
