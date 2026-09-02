"""adopt-child (ADR-0021): adopt the foundation into an existing repository.

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
ARCHIVE = "docs/inheritance/readmes/acme/parent-template.md"
CHILD_README = f"<!-- repository-readme-owner: {CHILD} -->\n# Existing Service\n"


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
            self.payload, ".github/workflows/template-sync.yml",
            "name: Template Sync\non: workflow_dispatch\njobs:\n  sync:\n"
            "    if: vars.TEMPLATE_SYNC_ENABLED == 'true'\n    steps:\n"
            "      - uses: acme/template-sync@sha\n        with:\n"
            f"          source_repo_path: \"{PARENT}\"\n"
            f"        env:\n          SOURCE_REPOSITORY: \"{PARENT}\"\n",
        )
        self.write(
            self.payload, ARCHIVE,
            f"---\nsource-repository: {PARENT}\nsource-commit: {self.source}\n---\n\n"
            f"<!-- repository-readme-owner: {PARENT} -->\n# Parent\n",
        )

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

    def plan(self, **kwargs):
        return inheritance.plan_adopt(self.child, self.parent, self.source, CHILD, **kwargs)

    def apply(self, **overrides):
        arguments = {
            "confirm_repository": CHILD,
            "confirm_source": self.source,
            "payload_root": self.payload,
            "protect": ["scripts/local_tool.py"],
            "accept": ["scripts/shared.py"],
        }
        arguments.update(overrides)
        return inheritance.apply_adopt(self.child, self.parent, self.source, CHILD, **arguments)

    # -- classification ------------------------------------------------------------------

    def test_plan_classifies_identical_colliding_and_pending_paths_without_writing(self):
        before = self.git(self.child, "status", "--porcelain")
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
            [FOUNDATION_ENTRY, EXPORT_PATH, "scripts/other.py"],
        )
        self.assertEqual(result["resolution"]["unresolved"], ["scripts/local_tool.py", "scripts/shared.py"])
        self.assertEqual(self.git(self.child, "status", "--porcelain"), before)

    def test_plan_is_ready_once_every_collision_has_a_resolution(self):
        result = self.plan(protect=["scripts/local_tool.py"], accept=["scripts/shared.py"])

        self.assertEqual(result["status"], "ready_to_adopt")
        self.assertEqual(result["resolution"]["unresolved"], [])

    def test_protecting_a_file_under_an_inherited_root_splits_that_root(self):
        result = self.plan(protect=["scripts/local_tool.py", "scripts/shared.py"])
        manifest = result["desired"]["manifest"]

        self.assertNotIn("scripts/", manifest["inherited_paths"])
        self.assertIn("scripts/other.py", manifest["inherited_paths"])
        self.assertNotIn("scripts/shared.py", manifest["inherited_paths"])
        self.assertIn("scripts/shared.py", manifest["protected_paths"])
        self.assertIn("scripts/local_tool.py", manifest["protected_paths"])
        self.assertIn("scripts/shared.py", result["desired"]["template_sync_ignore"])
        self.assertIn("scripts/local_tool.py", result["desired"]["template_sync_ignore"])

    def test_accepting_the_parent_keeps_the_path_inherited(self):
        # local_tool.py is protected under scripts/, so the root necessarily splits; the
        # accepted shared.py must land on the inherited side of that split, not the protected.
        result = self.plan(protect=["scripts/local_tool.py"], accept=["scripts/shared.py"])
        manifest = result["desired"]["manifest"]

        self.assertIn("scripts/shared.py", manifest["inherited_paths"])
        self.assertNotIn("scripts/shared.py", manifest["protected_paths"])
        self.assertNotIn("scripts/shared.py", result["desired"]["template_sync_ignore"])

    def test_a_root_without_protected_collisions_stays_whole(self):
        # Remove the child-only file so scripts/ has only an accepted collision.
        (self.child / "scripts/local_tool.py").unlink()
        self.commit(self.child, "drop local tool")

        result = self.plan(accept=["scripts/shared.py"])

        self.assertEqual(result["status"], "ready_to_adopt")
        self.assertIn("scripts/", result["desired"]["manifest"]["inherited_paths"])

    def test_resolutions_must_name_collisions_and_be_consistent(self):
        with self.assertRaisesRegex(inheritance.InheritanceError, "not a collision"):
            self.plan(protect=["docs/foundation/guide.md"])
        with self.assertRaisesRegex(inheritance.InheritanceError, "no parent version to accept"):
            self.plan(accept=["scripts/local_tool.py"])
        with self.assertRaisesRegex(inheritance.InheritanceError, "both protected and accepted"):
            self.plan(protect=["scripts/shared.py"], accept=["scripts/shared.py"])

    # -- apply ---------------------------------------------------------------------------

    def test_apply_refuses_while_a_collision_is_unresolved(self):
        with self.assertRaisesRegex(inheritance.InheritanceError, "every collision must be resolved"):
            self.apply(protect=[], accept=[])
        self.assertFalse((self.child / ".github/inheritance/manifest.json").exists())

    def test_apply_writes_metadata_and_payloads_but_never_an_inherited_path(self):
        result = self.apply()

        self.assertEqual(result["status"], "adopted")
        self.assertEqual(
            result["changed_paths"],
            sorted(
                [
                    ".ai/project/agent-overlay.md",
                    ".github/inheritance/agent-profile.json",
                    ".github/inheritance/lock.json",
                    ".github/inheritance/manifest.json",
                    ".github/workflows/template-sync.yml",
                    ".templatesyncignore",
                    ARCHIVE,
                ]
            ),
        )
        self.assertEqual(result["pending_inherited_paths"], 3)
        # inherited content is untouched: the collision still differs and nothing pending arrived
        self.assertEqual((self.child / "scripts/shared.py").read_text(), "print('child')\n")
        self.assertFalse((self.child / FOUNDATION_ENTRY).exists())
        lock = json.loads((self.child / ".github/inheritance/lock.json").read_text())
        self.assertEqual(lock["parent"], {"repository": PARENT, "commit": self.source})

    def test_apply_validates_structurally_and_the_full_contract_holds_after_the_first_sync(self):
        self.apply()

        inheritance.validate_inheritance(self.child, require_agent_inputs=False)
        with self.assertRaisesRegex(inheritance.InheritanceError, "agent profile.inputs\\[0\\].path"):
            inheritance.validate_inheritance(self.child)

        # the first Template Sync delivers the inherited tree
        for path in (FOUNDATION_ENTRY, EXPORT_PATH, "scripts/other.py", "scripts/shared.py"):
            self.write(self.child, path, (self.parent / path).read_text(encoding="utf-8"))
        contract = inheritance.validate_inheritance(self.child)
        self.assertEqual(contract["parent"]["commit"], self.source)

    def test_rerun_after_apply_is_idempotent_and_needs_no_flags(self):
        self.apply()
        self.commit(self.child, "adopt boundary")

        self.assertEqual(self.plan()["status"], "already_adopted")
        result = self.apply(protect=[], accept=[])
        self.assertEqual(result["status"], "already_adopted")
        self.assertEqual(result["changed_paths"], [])
        self.assertEqual(result["protected_collisions"], ["scripts/local_tool.py"])

    def test_apply_refuses_to_overwrite_a_readme_that_is_not_the_reviewed_payload(self):
        self.write(self.child, "README.md", "# Different\n")
        self.commit(self.child, "readme without marker")

        with self.assertRaisesRegex(inheritance.InheritanceError, "differs from both parent and desired"):
            self.apply()

    def test_apply_refuses_wrong_confirmation_and_the_default_branch(self):
        with self.assertRaisesRegex(inheritance.InheritanceError, "confirmation must match"):
            self.apply(confirm_source="0" * 40)
        self.git(self.child, "switch", "main")
        with self.assertRaisesRegex(inheritance.InheritanceError, "default branch"):
            self.plan()

    # -- CLI -----------------------------------------------------------------------------

    def test_cli_plans_and_applies(self):
        common = [
            "adopt-child", "--root", str(self.child), "--parent-root", str(self.parent),
            "--source-commit", self.source, "--repository", CHILD,
            "--protect", "scripts/local_tool.py", "--accept", "scripts/shared.py",
        ]
        self.assertEqual(inheritance.main(common), 0)
        self.assertEqual(
            inheritance.main([*common, "--apply", "--payload-root", str(self.payload),
                              "--confirm-repository", CHILD, "--confirm-source", self.source]),
            0,
        )
        self.assertTrue((self.child / ".github/inheritance/manifest.json").is_file())

    def test_cli_rejects_confirmations_without_apply(self):
        self.assertEqual(
            inheritance.main([
                "adopt-child", "--root", str(self.child), "--parent-root", str(self.parent),
                "--source-commit", self.source, "--repository", CHILD, "--confirm-repository", CHILD,
            ]),
            2,
        )


if __name__ == "__main__":
    unittest.main()
