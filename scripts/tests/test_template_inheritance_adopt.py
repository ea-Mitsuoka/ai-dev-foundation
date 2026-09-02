"""adopt-child (ADR-0021, sequenced by ADR-0022): adopt the foundation into an existing repository.

These tests build the parent and the existing repository in temporary directories only,
so they hold at the foundation root and in every template and leaf that inherits them.
"""

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "template_inheritance.py"
SPEC = importlib.util.spec_from_file_location("template_inheritance_adopt", MODULE_PATH)
inheritance = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inheritance)

PARENT = "acme/parent-template"
CHILD = "acme/existing-service"
EXPORT_PATH = ".ai/contracts/foundation/inheritance-export.json"
FOUNDATION_ENTRY = ".ai/contracts/foundation/agent-entry.md"
AUTH = "scripts/template_sync_auth.py"
WORKFLOW = ".github/workflows/template-sync.yml"
ARCHIVE = "docs/inheritance/readmes/acme/parent-template.md"
CHILD_README = f"<!-- repository-readme-owner: {CHILD} -->\n# Existing Service\n"
TRANSPORT_FILES = [WORKFLOW, ".templatesyncignore", AUTH]
METADATA_FILES = [
    ".ai/project/agent-overlay.md",
    ".github/inheritance/agent-profile.json",
    ".github/inheritance/lock.json",
    ".github/inheritance/manifest.json",
    "README.md",
    ARCHIVE,
]


class AdoptChildTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        root = Path(self.temporary_directory.name)
        self.parent = root / "parent"
        self.child = root / "child"
        self.payload = root / "payload"
        for directory in (self.parent, self.child, self.payload):
            directory.mkdir()

        # --- the direct parent publishes an export -----------------------------------
        self.git(self.parent, "init", "-b", "main")
        self.configure(self.parent)
        self.git(self.parent, "remote", "add", "origin", f"https://github.com/{PARENT}.git")
        protected = sorted(
            {
                ".gitignore",
                ".github/governance/repository.json",
                ".github/inheritance/lock.json",
                ".github/inheritance/manifest.json",
                ".github/inheritance/agent-profile.json",
                ".github/workflows/",
                ".templatesyncignore",
                ".ai/project/",
                "README.md",
                "docs/inheritance/readmes/",
            }
        )
        export = {
            "schema_version": 1,
            "repository": PARENT,
            "branch": "main",
            "inherited_paths": [".ai/contracts/foundation/", "docs/foundation/", "scripts/"],
            "protected_paths": protected,
            "agent_inputs": [
                {"layer": "foundation", "repository": PARENT, "path": FOUNDATION_ENTRY}
            ],
        }
        self.write(self.parent, EXPORT_PATH, json.dumps(export))
        self.write(self.parent, FOUNDATION_ENTRY, "foundation contract\n")
        self.write(self.parent, "docs/foundation/guide.md", "foundation guide\n")
        self.write(self.parent, AUTH, "print('auth v1')\n")
        self.write(self.parent, "scripts/shared.py", "print('parent')\n")
        self.write(self.parent, "scripts/other.py", "print('other')\n")
        self.write(self.parent, "README.md", f"<!-- repository-readme-owner: {PARENT} -->\n# Parent\n")
        self.source = self.commit(self.parent, "publish export")
        self.git(self.parent, "update-ref", "refs/remotes/origin/main", self.source)

        # --- an existing repository with its own history ------------------------------
        self.git(self.child, "init", "-b", "main")
        self.configure(self.child)
        self.git(self.child, "remote", "add", "origin", f"https://github.com/{CHILD}.git")
        self.write(self.child, "README.md", CHILD_README)
        self.write(self.child, "src/app.py", "print('app')\n")
        self.write(self.child, "docs/foundation/guide.md", "foundation guide\n")  # identical
        self.write(self.child, "scripts/shared.py", "print('child')\n")  # differs
        self.write(self.child, "scripts/local_tool.py", "print('mine')\n")  # child only
        main = self.commit(self.child, "existing history")
        self.git(self.child, "update-ref", "refs/remotes/origin/main", main)
        self.git(self.child, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
        self.git(self.child, "switch", "-c", "chore/adopt-foundation")

        # --- reviewed project payloads --------------------------------------------------
        self.write(self.payload, "README.md", CHILD_README)
        self.write(self.payload, ".ai/project/agent-overlay.md", f"# Overlay\n\nRepository: {CHILD}\n")
        self.write(
            self.payload, WORKFLOW,
            "name: Template Sync\non: workflow_dispatch\njobs:\n  sync:\n"
            "    if: vars.TEMPLATE_SYNC_ENABLED == 'true'\n    steps:\n"
            "      - uses: acme/template-sync@sha\n        with:\n"
            f"          source_repo_path: \"{PARENT}\"\n"
            f"        env:\n          SOURCE_REPOSITORY: \"{PARENT}\"\n",
        )
        self.write_archive(self.source)

    # -- helpers ---------------------------------------------------------------------------

    def git(self, root, *arguments):
        result = subprocess.run(
            ["git", "-C", str(root), *arguments], capture_output=True, check=False, text=True, timeout=5
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def configure(self, root):
        self.git(root, "config", "user.name", "Test User")
        self.git(root, "config", "user.email", "test@example.invalid")

    def commit(self, root, message):
        self.git(root, "add", "-A")
        self.git(root, "commit", "-q", "-m", message)
        return self.git(root, "rev-parse", "HEAD")

    def write(self, root, relative_path, content):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def write_archive(self, source):
        self.write(
            self.payload, ARCHIVE,
            f"---\nsource-repository: {PARENT}\nsource-commit: {source}\n---\n\n"
            f"<!-- repository-readme-owner: {PARENT} -->\n# Parent\n",
        )

    def plan(self, source=None, **kwargs):
        return inheritance.plan_adopt(self.child, self.parent, source or self.source, CHILD, **kwargs)

    def apply(self, source=None, **overrides):
        arguments = {
            "confirm_repository": CHILD,
            "confirm_source": source or self.source,
            "payload_root": self.payload,
        }
        arguments.update(overrides)
        return inheritance.apply_adopt(self.child, self.parent, source or self.source, CHILD, **arguments)

    def prepare(self, **overrides):
        arguments = {"prepare": True, "protect": ["scripts/local_tool.py"], "accept": ["scripts/shared.py"]}
        arguments.update(overrides)
        return self.apply(**arguments)

    def simulate_sync(self, source=None):
        """What the bot Template Sync PR delivers: every inherited parent file not excluded."""
        source = source or self.source
        # The temp dir may be a symlink on macOS; production passes a resolved root too.
        positive, exceptions = inheritance._read_template_sync_ignore(self.child.resolve())
        listing = self.git(self.parent, "ls-tree", "-r", "--name-only", source)
        for path in listing.splitlines():
            if not inheritance._owned_by(path, [".ai/contracts/foundation/", "docs/foundation/", "scripts/"]):
                continue
            if inheritance._template_sync_excludes(path, positive, exceptions):
                continue
            blob = subprocess.run(
                ["git", "-C", str(self.parent), "show", f"{source}:{path}"],
                capture_output=True, check=True, timeout=5,
            ).stdout  # exact bytes, unlike the stripping git() helper
            target = self.child / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(blob)
        self.commit(self.child, "build: sync with parent")

    def tracked_changes(self):
        return sorted(self.git(self.child, "status", "--porcelain").split("\n"))

    # -- classification and resolution ---------------------------------------------------

    def test_plan_classifies_without_writing(self):
        before = self.tracked_changes()
        result = self.plan()

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["classification"]["identical"], ["docs/foundation/guide.md"])
        self.assertEqual(
            result["classification"]["collision"],
            [
                {"path": "scripts/local_tool.py", "reason": "child_only"},
                {"path": "scripts/shared.py", "reason": "differs"},
            ],
        )
        self.assertEqual(
            result["classification"]["pending"],
            [FOUNDATION_ENTRY, EXPORT_PATH, "scripts/other.py", AUTH],
        )
        self.assertEqual(result["resolution"]["unresolved"], ["scripts/local_tool.py", "scripts/shared.py"])
        self.assertEqual(self.tracked_changes(), before)

    def test_resolved_plan_is_ready_to_prepare_and_reports_what_activation_still_needs(self):
        result = self.plan(protect=["scripts/local_tool.py"], accept=["scripts/shared.py"])

        self.assertEqual(result["status"], "ready_to_prepare")
        self.assertFalse(result["activation"]["prepared"])
        self.assertEqual(result["activation"]["missing_count"], 5)  # 4 pending + the accepted collision
        self.assertEqual(result["activation"]["stray"], [])  # the child-only file is protected

    def test_protecting_a_file_under_an_inherited_root_splits_that_root(self):
        manifest = self.plan(protect=["scripts/local_tool.py", "scripts/shared.py"])["desired"]["manifest"]

        self.assertNotIn("scripts/", manifest["inherited_paths"])
        self.assertIn("scripts/other.py", manifest["inherited_paths"])
        self.assertIn(AUTH, manifest["inherited_paths"])
        self.assertIn("scripts/shared.py", manifest["protected_paths"])
        self.assertIn("scripts/local_tool.py", manifest["protected_paths"])

    def test_accepting_keeps_the_path_inherited(self):
        result = self.plan(protect=["scripts/local_tool.py"], accept=["scripts/shared.py"])

        self.assertIn("scripts/shared.py", result["desired"]["manifest"]["inherited_paths"])
        self.assertNotIn("scripts/shared.py", result["desired"]["template_sync_ignore"])

    def test_resolutions_must_name_collisions_and_be_consistent(self):
        with self.assertRaisesRegex(inheritance.InheritanceError, "not a collision"):
            self.plan(protect=["src/app.py"])  # outside every inherited root
        with self.assertRaisesRegex(inheritance.InheritanceError, "no parent version to accept"):
            self.plan(accept=["scripts/local_tool.py"])
        with self.assertRaisesRegex(inheritance.InheritanceError, "both protected and accepted"):
            self.plan(protect=["scripts/shared.py"], accept=["scripts/shared.py"])

    # -- phase 1: prepare ----------------------------------------------------------------

    def test_prepare_refuses_while_a_collision_is_unresolved(self):
        with self.assertRaisesRegex(inheritance.InheritanceError, "every collision must be resolved"):
            self.apply(prepare=True)
        self.assertFalse((self.child / ".templatesyncignore").exists())

    def test_prepare_writes_only_the_transport_and_is_idempotent(self):
        result = self.prepare()

        self.assertEqual(result["status"], "prepared")
        self.assertEqual(result["changed_paths"], sorted(TRANSPORT_FILES))
        for path in METADATA_FILES[1:4]:
            self.assertFalse((self.child / path).exists(), path)
        self.assertEqual((self.child / AUTH).read_text(), "print('auth v1')\n")
        ignore = (self.child / ".templatesyncignore").read_text()
        self.assertIn("scripts/local_tool.py\n", ignore)
        self.assertNotIn("scripts/shared.py\n", ignore)
        # the accepted collision is untouched until the bot delivers the parent version
        self.assertEqual((self.child / "scripts/shared.py").read_text(), "print('child')\n")

        self.commit(self.child, "chore: prepare adoption")
        self.assertEqual(self.plan()["status"], "prepared")  # protections read back from the ignore file
        rerun = self.apply(prepare=True)
        self.assertEqual(rerun["status"], "already_prepared")
        self.assertEqual(rerun["changed_paths"], [])

    def test_prepare_overwrites_the_transport_dependency_only_when_accepted(self):
        self.write(self.child, AUTH, "print('my own auth')\n")
        self.commit(self.child, "child has its own auth script")

        with self.assertRaisesRegex(inheritance.InheritanceError, "every collision must be resolved"):
            self.prepare()
        result = self.prepare(accept=["scripts/shared.py", AUTH])

        self.assertIn(AUTH, result["changed_paths"])
        self.assertEqual((self.child / AUTH).read_text(), "print('auth v1')\n")

    # -- phase 3: activation -------------------------------------------------------------

    def test_activation_refuses_until_the_tree_has_been_delivered(self):
        self.prepare()
        self.commit(self.child, "chore: prepare adoption")

        with self.assertRaisesRegex(inheritance.InheritanceError, "let Template Sync deliver it first"):
            self.apply()
        self.assertFalse((self.child / ".github/inheritance/lock.json").exists())

    def test_activation_after_the_sync_writes_a_true_lock_and_a_valid_contract(self):
        self.prepare()
        self.commit(self.child, "chore: prepare adoption")
        self.simulate_sync()

        self.assertEqual(self.plan()["status"], "ready_to_adopt")
        result = self.apply()

        self.assertEqual(result["status"], "adopted")
        self.assertEqual(result["changed_paths"], sorted(set(METADATA_FILES) - {"README.md"}))
        self.assertEqual(result["protected_collisions"], ["scripts/local_tool.py"])
        lock = json.loads((self.child / ".github/inheritance/lock.json").read_text())
        self.assertEqual(lock["parent"], {"repository": PARENT, "commit": self.source})
        contract = inheritance.validate_inheritance(self.child)  # full validation, no bypass
        self.assertEqual(contract["parent"]["commit"], self.source)
        self.assertEqual((self.child / "scripts/shared.py").read_text(), "print('parent')\n")
        self.assertEqual((self.child / "scripts/local_tool.py").read_text(), "print('mine')\n")

        self.commit(self.child, "chore(inheritance): adopt the foundation")
        self.assertEqual(self.plan()["status"], "already_adopted")
        rerun = self.apply()
        self.assertEqual((rerun["status"], rerun["changed_paths"]), ("already_adopted", []))

    def test_activation_takes_the_commit_the_sync_actually_delivered(self):
        self.prepare()
        self.commit(self.child, "chore: prepare adoption")
        self.write(self.parent, "scripts/other.py", "print('other v2')\n")
        delivered = self.commit(self.parent, "parent moves on")
        self.git(self.parent, "update-ref", "refs/remotes/origin/main", delivered)
        self.simulate_sync(delivered)
        self.write_archive(delivered)

        with self.assertRaisesRegex(inheritance.InheritanceError, "let Template Sync deliver it first"):
            self.apply()  # the inspected commit no longer matches what arrived
        result = self.apply(source=delivered)

        self.assertEqual(result["status"], "adopted")
        lock = json.loads((self.child / ".github/inheritance/lock.json").read_text())
        self.assertEqual(lock["parent"]["commit"], delivered)

    def test_activation_refuses_a_readme_that_is_not_the_reviewed_payload(self):
        self.prepare()
        self.commit(self.child, "chore: prepare adoption")
        self.simulate_sync()
        self.write(self.child, "README.md", "# Different\n")
        self.commit(self.child, "readme without marker")

        with self.assertRaisesRegex(inheritance.InheritanceError, "differs from both parent and desired"):
            self.apply()

    def test_refuses_wrong_confirmation_and_the_default_branch(self):
        with self.assertRaisesRegex(inheritance.InheritanceError, "confirmation must match"):
            self.apply(confirm_source="0" * 40)
        self.git(self.child, "switch", "main")
        with self.assertRaisesRegex(inheritance.InheritanceError, "default branch"):
            self.plan()

    # -- CLI -----------------------------------------------------------------------------

    def test_cli_plans_prepares_and_activates(self):
        common = [
            "adopt-child", "--root", str(self.child), "--parent-root", str(self.parent),
            "--source-commit", self.source, "--repository", CHILD,
            "--protect", "scripts/local_tool.py", "--accept", "scripts/shared.py",
        ]
        confirm = ["--apply", "--payload-root", str(self.payload),
                   "--confirm-repository", CHILD, "--confirm-source", self.source]
        self.assertEqual(inheritance.main(common), 0)
        self.assertEqual(inheritance.main([*common, "--prepare", *confirm]), 0)
        self.commit(self.child, "chore: prepare adoption")
        self.simulate_sync()
        self.assertEqual(inheritance.main([*common, *confirm]), 0)
        self.assertTrue((self.child / ".github/inheritance/manifest.json").is_file())

    def test_cli_rejects_prepare_or_confirmations_without_apply(self):
        base = ["adopt-child", "--root", str(self.child), "--parent-root", str(self.parent),
                "--source-commit", self.source, "--repository", CHILD]
        self.assertEqual(inheritance.main([*base, "--prepare"]), 2)
        self.assertEqual(inheritance.main([*base, "--confirm-repository", CHILD]), 2)


if __name__ == "__main__":
    unittest.main()
