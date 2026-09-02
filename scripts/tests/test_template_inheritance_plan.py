import contextlib
import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "template_inheritance.py"
REPOSITORY_ROOT = MODULE_PATH.parent.parent
SPEC = importlib.util.spec_from_file_location("template_inheritance_plan", MODULE_PATH)
inheritance = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inheritance)

PARENT_REPOSITORY = "acme/parent-template"
PROTECTED_PATHS = [
    ".gitignore",
    ".github/governance/repository.json",
    ".github/inheritance/lock.json",
    ".github/inheritance/manifest.json",
    ".github/workflows/template-sync.yml",
    ".templatesyncignore",
]


class TemplateInheritancePlanTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        temporary_root = Path(self.temporary_directory.name)
        self.parent = temporary_root / "parent"
        self.child = temporary_root / "child"
        self.parent.mkdir()
        self.child.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Test User")
        self.git("config", "user.email", "test@example.invalid")
        self.git("remote", "add", "origin", f"https://github.com/{PARENT_REPOSITORY}.git")

        for path, content in {
            "inherited/modify.txt": "old\n",
            "inherited/delete.txt": "old\n",
            "inherited/current.txt": "old\n",
            ".github/workflows/shared.yml": "old\n",
            ".gitignore": "parent-old\n",
            ".github/workflows/template-sync.yml": "parent-old\n",
        }.items():
            self.write(self.parent, path, content)
        self.locked_commit = self.commit("base")

        for path, content in {
            "inherited/modify.txt": "future\n",
            "inherited/delete.txt": "old\n",
            "inherited/current.txt": "new\n",
            ".github/workflows/shared.yml": "old\n",
            ".gitignore": "child-local\n",
            ".github/workflows/template-sync.yml": "parent-new\n",
        }.items():
            self.write(self.child, path, content)
        self.write_contract(self.locked_commit)

        for path, content in {
            "inherited/add.txt": "new\n",
            "inherited/modify.txt": "new\n",
            "inherited/current.txt": "new\n",
            ".github/workflows/shared.yml": "new\n",
            ".gitignore": "parent-new\n",
            ".github/workflows/template-sync.yml": "parent-new\n",
            "unowned.txt": "new\n",
        }.items():
            self.write(self.parent, path, content)
        (self.parent / "inherited/delete.txt").unlink()
        self.candidate_commit = self.commit("candidate")
        self.write(self.parent, "inherited/modify.txt", "future\n")
        self.write(self.parent, "inherited/later.txt", "later\n")
        self.target_commit = self.commit("later")
        self.git("update-ref", "refs/remotes/origin/main", self.target_commit)

    def git(self, *arguments):
        result = subprocess.run(
            ["git", "-C", str(self.parent), *arguments],
            capture_output=True,
            check=False,
            text=True,
            timeout=5,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-m", message)
        return self.git("rev-parse", "HEAD")

    def write(self, root, relative_path, content):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def write_contract(self, commit):
        manifest = {
            "schema_version": 1,
            "parent": {"repository": PARENT_REPOSITORY, "branch": "main"},
            "lock_file": ".github/inheritance/lock.json",
            "inherited_paths": ["inherited/", ".github/workflows/shared.yml"],
            "protected_paths": PROTECTED_PATHS,
        }
        lock = {"schema_version": 1, "parent": {"repository": PARENT_REPOSITORY, "commit": commit}}
        self.write(self.child, ".github/inheritance/manifest.json", json.dumps(manifest))
        self.write(self.child, ".github/inheritance/lock.json", json.dumps(lock))
        self.write(
            self.child,
            ".templatesyncignore",
            "\n".join(PROTECTED_PATHS + [".github/workflows/**"]) + "\n",
        )

    def synchronize_child_to_target(self):
        for path, content in {
            "inherited/add.txt": "new\n",
            "inherited/modify.txt": "future\n",
            "inherited/current.txt": "new\n",
            "inherited/later.txt": "later\n",
            ".github/workflows/shared.yml": "new\n",
        }.items():
            self.write(self.child, path, content)
        (self.child / "inherited/delete.txt").unlink()
        self.write_contract(self.target_commit)
        for arguments in (
            ("init", "-b", "main"),
            ("config", "user.name", "Test User"),
            ("config", "user.email", "test@example.invalid"),
            ("add", "-A"),
            ("commit", "-m", "synchronized child"),
        ):
            result = subprocess.run(
                ["git", "-C", str(self.child), *arguments],
                capture_output=True,
                check=False,
                text=True,
                timeout=5,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def write_fleet_config(
        self,
        *,
        repository="acme/child-template",
        directory="child",
        parent_repository=PARENT_REPOSITORY,
        parent_directory="parent",
        lifecycle="active",
        reason="maintained",
        repositories=None,
    ):
        config_path = Path(self.temporary_directory.name) / "fleet.json"
        entry = {
            "repository": repository,
            "directory": directory,
            "parent_repository": parent_repository,
            "parent_directory": parent_directory,
            "lifecycle": lifecycle,
            "reason": reason,
        }
        config_path.write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "repositories": repositories or [entry],
                }
            ),
            encoding="utf-8",
        )
        return config_path

    def snapshot_child(self):
        return {
            str(path.relative_to(self.child)): path.read_bytes()
            for path in self.child.rglob("*")
            if path.is_file()
        }

    def test_plan_selects_only_next_first_parent_commit_and_is_read_only(self):
        before = self.snapshot_child()
        result = inheritance.plan_inheritance(self.child, self.parent)

        self.assertEqual(result["status"], "changes")
        self.assertEqual(result["parent"]["candidate_commit"], self.candidate_commit)
        self.assertEqual(result["parent"]["target_commit"], self.target_commit)
        self.assertEqual(result["changes"]["add"], ["inherited/add.txt"])
        self.assertEqual(
            result["changes"]["modify"],
            [".github/workflows/shared.yml", "inherited/modify.txt"],
        )
        self.assertEqual(result["changes"]["candidate_delete"], ["inherited/delete.txt"])
        self.assertEqual(result["changes"]["already_current"], ["inherited/current.txt"])
        self.assertEqual(
            result["skipped"]["protected"],
            [".github/workflows/template-sync.yml", ".gitignore"],
        )
        self.assertEqual(result["skipped"]["unowned"], ["unowned.txt"])
        self.assertNotIn("inherited/later.txt", json.dumps(result))
        self.assertEqual(self.snapshot_child(), before)

    def test_plan_reports_up_to_date_at_remote_branch_head(self):
        self.write_contract(self.target_commit)

        result = inheritance.plan_inheritance(self.child, self.parent)

        self.assertEqual(result["status"], "up_to_date")
        self.assertIsNone(result["parent"]["candidate_commit"])
        self.assertEqual(result["summary"]["total"], 0)

    def test_parent_origin_must_match_manifest(self):
        self.git("remote", "set-url", "origin", "https://github.com/acme/other.git")

        with self.assertRaisesRegex(inheritance.InheritanceError, "origin"):
            inheritance.plan_inheritance(self.child, self.parent)

    def test_lock_must_be_on_first_parent_history(self):
        self.git("switch", "-c", "side", self.locked_commit)
        self.write(self.parent, "side.txt", "side\n")
        side_commit = self.commit("side")
        self.git("switch", "main")
        self.git("merge", "--no-ff", "side", "-m", "merge side")
        self.git("update-ref", "refs/remotes/origin/main", self.git("rev-parse", "HEAD"))
        self.write_contract(side_commit)

        with self.assertRaisesRegex(inheritance.InheritanceError, "first-parent"):
            inheritance.plan_inheritance(self.child, self.parent)

    def test_inherited_child_symlink_is_rejected(self):
        outside = Path(self.temporary_directory.name) / "outside.txt"
        outside.write_text("outside\n", encoding="utf-8")
        (self.child / "inherited/modify.txt").unlink()
        (self.child / "inherited/modify.txt").symlink_to(outside)

        with self.assertRaisesRegex(inheritance.InheritanceError, "symlink"):
            inheritance.plan_inheritance(self.child, self.parent)

    def test_plan_cli_prints_the_same_candidate(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = inheritance.main(
                ["plan", "--root", str(self.child), "--parent-root", str(self.parent)]
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(json.loads(stdout.getvalue())["parent"]["candidate_commit"], self.candidate_commit)

    def test_plan_accepts_literal_glob_characters_in_a_git_path(self):
        self.write(self.parent, "inherited/[literal].txt", "literal\n")
        literal_commit = self.commit("literal path")
        self.git("update-ref", "refs/remotes/origin/main", literal_commit)
        self.write_contract(self.target_commit)

        result = inheritance.plan_inheritance(self.child, self.parent)

        self.assertEqual(result["changes"]["add"], ["inherited/[literal].txt"])

    def test_fleet_report_classifies_propagation_boundaries(self):
        result = inheritance.fleet_report(
            [("acme/child-template", self.child, self.parent)]
        )

        repository = result["repositories"][0]
        self.assertEqual(repository["repository"], "acme/child-template")
        self.assertEqual(repository["repository_source"], "explicit-argument")
        self.assertEqual(
            repository["synchronized"],
            ["inherited/current.txt", "inherited/modify.txt"],
        )
        self.assertEqual(repository["pending_sync"], ["inherited/add.txt"])
        self.assertEqual(
            repository["pending_manual_port"],
            [
                {
                    "path": ".github/workflows/shared.yml",
                    "reason": "workflow-security-boundary",
                }
            ],
        )
        self.assertEqual(
            repository["manually_ported"],
            [".github/workflows/template-sync.yml"],
        )
        self.assertEqual(
            repository["protected_review"],
            [{"path": ".gitignore", "reason": "repository-owned-boundary"}],
        )
        self.assertEqual(
            repository["ownership_review"],
            [{"path": "unowned.txt", "reason": "ownership-decision-required"}],
        )
        self.assertEqual(
            repository["deletion_review"],
            [{"path": "inherited/delete.txt", "reason": "deletion-review-required"}],
        )
        self.assertEqual(result["summary"]["repositories"], 1)
        self.assertEqual(result["summary"]["pending_manual_port"], 1)
        self.assertEqual(result["status"], "attention")

    def test_fleet_report_aggregates_multiple_explicit_children(self):
        second_child = Path(self.temporary_directory.name) / "second-child"
        second_child.mkdir()
        for path, content in self.snapshot_child().items():
            self.write(second_child, path, content.decode("utf-8"))

        result = inheritance.fleet_report(
            [
                ("acme/child-two", second_child, self.parent),
                ("acme/child-one", self.child, self.parent),
            ]
        )

        self.assertEqual(
            [item["repository"] for item in result["repositories"]],
            ["acme/child-one", "acme/child-two"],
        )
        self.assertEqual(result["summary"]["repositories"], 2)
        self.assertEqual(result["summary"]["manually_ported"], 2)
        self.assertEqual(result["summary"]["pending_manual_port"], 2)
        self.assertEqual(result["summary"]["protected_review"], 2)

    def test_fleet_report_recognizes_an_exact_ignored_inherited_manual_port(self):
        self.write(self.child, ".github/workflows/shared.yml", "new\n")

        result = inheritance.fleet_report(
            [("acme/child-template", self.child, self.parent)]
        )

        repository = result["repositories"][0]
        self.assertEqual(repository["pending_manual_port"], [])
        self.assertIn(".github/workflows/shared.yml", repository["manually_ported"])

    def test_fleet_report_ignores_transient_unowned_path_absent_from_target_and_child(self):
        (self.parent / "unowned.txt").unlink()
        target_without_transient_path = self.commit("remove transient unowned path")
        self.git(
            "update-ref", "refs/remotes/origin/main", target_without_transient_path
        )

        result = inheritance.fleet_report(
            [("acme/child-template", self.child, self.parent)]
        )

        repository = result["repositories"][0]
        self.assertEqual(
            repository["parent"]["candidate_commit"], self.candidate_commit
        )
        self.assertEqual(
            repository["parent"]["target_commit"], target_without_transient_path
        )
        self.assertEqual(repository["ownership_review"], [])

    def test_fleet_report_audits_all_inherited_files_when_lock_matches_head(self):
        self.synchronize_child_to_target()
        self.write(self.child, "inherited/modify.txt", "child drift\n")
        (self.child / "inherited/add.txt").unlink()
        (self.child / "inherited/current.txt").chmod(0o755)
        self.write(self.child, "inherited/stale.txt", "removed upstream\n")

        result = inheritance.fleet_report(
            [("acme/child-template", self.child, self.parent)]
        )

        repository = result["repositories"][0]
        self.assertEqual(result["status"], "attention")
        self.assertEqual(repository["parent"]["locked_commit"], self.target_commit)
        self.assertEqual(repository["parent"]["target_commit"], self.target_commit)
        self.assertIsNone(repository["parent"]["candidate_commit"])
        self.assertEqual(repository["audited_inherited_files"], 6)
        self.assertEqual(
            repository["pending_sync"],
            ["inherited/add.txt", "inherited/current.txt", "inherited/modify.txt"],
        )
        self.assertEqual(
            repository["deletion_review"],
            [{"path": "inherited/stale.txt", "reason": "deletion-review-required"}],
        )
        self.assertEqual(result["summary"]["audited_inherited_files"], 6)

    def test_fleet_report_proves_complete_steady_state(self):
        self.synchronize_child_to_target()
        self.write(self.child, ".gitignore", "child-local\n*.pyc\n")
        self.write(self.child, "inherited/generated.pyc", "ignored build artifact\n")

        result = inheritance.fleet_report(
            [("acme/child-template", self.child, self.parent)]
        )

        repository = result["repositories"][0]
        self.assertEqual(result["status"], "ready")
        self.assertEqual(repository["audited_inherited_files"], 5)
        self.assertEqual(
            repository["synchronized"],
            [
                "inherited/add.txt",
                "inherited/current.txt",
                "inherited/later.txt",
                "inherited/modify.txt",
            ],
        )
        self.assertEqual(
            repository["manually_ported"], [".github/workflows/shared.yml"]
        )

    def test_fleet_audit_loads_fixed_worktree_relationships(self):
        self.synchronize_child_to_target()
        config_path = self.write_fleet_config()

        result = inheritance.fleet_audit(
            config_path, Path(self.temporary_directory.name)
        )

        self.assertEqual(result["status"], "ready")
        self.assertEqual(
            result["repositories"][0]["repository_source"], "fixed-fleet-config"
        )

    def test_fleet_audit_reports_paused_and_retired_without_worktrees(self):
        self.synchronize_child_to_target()
        active = {
            "repository": "acme/child-template",
            "directory": "child",
            "parent_repository": PARENT_REPOSITORY,
            "parent_directory": "parent",
            "lifecycle": "active",
            "reason": "maintained",
        }
        paused = {
            "repository": "acme/paused",
            "directory": "missing-paused",
            "parent_repository": PARENT_REPOSITORY,
            "parent_directory": "parent",
            "lifecycle": "paused",
            "reason": "owner access is unavailable",
        }
        retired = {
            "repository": "acme/retired",
            "directory": "missing-retired",
            "parent_repository": PARENT_REPOSITORY,
            "parent_directory": "parent",
            "lifecycle": "retired",
            "reason": "replaced by acme/child-template",
        }
        config_path = self.write_fleet_config(repositories=[active, paused, retired])

        result = inheritance.fleet_audit(
            config_path, Path(self.temporary_directory.name)
        )

        self.assertEqual(result["status"], "attention")
        self.assertEqual(
            [(item["repository"], item["lifecycle"]) for item in result["repositories"]],
            [
                ("acme/child-template", "active"),
                ("acme/paused", "paused"),
                ("acme/retired", "retired"),
            ],
        )
        self.assertEqual(result["summary"]["active"], 1)
        self.assertEqual(result["summary"]["paused"], 1)
        self.assertEqual(result["summary"]["retired"], 1)

    def test_fleet_audit_rejects_parent_mismatch_and_missing_worktree(self):
        mismatch = self.write_fleet_config(parent_repository="acme/other-parent")
        with self.assertRaisesRegex(inheritance.InheritanceError, "parent"):
            inheritance.fleet_audit(mismatch, Path(self.temporary_directory.name))

        missing = self.write_fleet_config(directory="missing-child")
        with self.assertRaisesRegex(inheritance.InheritanceError, "must exist"):
            inheritance.fleet_audit(missing, Path(self.temporary_directory.name))

    def test_fleet_audit_rejects_duplicate_repository_and_directory(self):
        entry = {
            "repository": "acme/child-template",
            "directory": "child",
            "parent_repository": PARENT_REPOSITORY,
            "parent_directory": "parent",
            "lifecycle": "active",
            "reason": "maintained",
        }
        config_path = self.write_fleet_config(repositories=[entry, dict(entry)])

        with self.assertRaisesRegex(inheritance.InheritanceError, "duplicate child"):
            inheritance.fleet_audit(config_path, Path(self.temporary_directory.name))

    def test_propagation_impact_classifies_each_active_child_boundary(self):
        paused = {
            "repository": "acme/paused",
            "directory": "missing-paused",
            "parent_repository": PARENT_REPOSITORY,
            "parent_directory": "parent",
            "lifecycle": "paused",
            "reason": "owner access is unavailable",
        }
        active = {
            "repository": "acme/child-template",
            "directory": "child",
            "parent_repository": PARENT_REPOSITORY,
            "parent_directory": "parent",
            "lifecycle": "active",
            "reason": "maintained",
        }
        config_path = self.write_fleet_config(repositories=[paused, active])

        result = inheritance.propagation_impact(
            config_path,
            Path(self.temporary_directory.name),
            PARENT_REPOSITORY,
            self.locked_commit,
            self.candidate_commit,
        )

        self.assertEqual(result["status"], "child-migration-required")
        self.assertEqual(result["parent_repository"], PARENT_REPOSITORY)
        self.assertEqual(result["base_commit"], self.locked_commit)
        self.assertEqual(result["head_commit"], self.candidate_commit)
        self.assertEqual(result["children"], ["acme/child-template"])
        impacts = {item["path"]: item["impact"] for item in result["changes"]}
        self.assertEqual(impacts["inherited/add.txt"], "schedule-only")
        self.assertEqual(impacts["inherited/delete.txt"], "schedule-only")
        self.assertEqual(
            impacts[".github/workflows/shared.yml"], "manual-boundary"
        )
        self.assertEqual(
            impacts[".github/workflows/template-sync.yml"], "manual-boundary"
        )
        self.assertEqual(impacts[".gitignore"], "foundation-only")
        self.assertEqual(impacts["unowned.txt"], "child-migration-required")

    def test_propagation_impact_rejects_reverse_history(self):
        config_path = self.write_fleet_config()

        with self.assertRaisesRegex(inheritance.InheritanceError, "ancestry"):
            inheritance.propagation_impact(
                config_path,
                Path(self.temporary_directory.name),
                PARENT_REPOSITORY,
                self.candidate_commit,
                self.locked_commit,
            )

    def test_propagation_impact_cli_prints_deterministic_json(self):
        config_path = self.write_fleet_config()
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = inheritance.main(
                [
                    "propagation-impact",
                    "--config",
                    str(config_path),
                    "--workspace-root",
                    self.temporary_directory.name,
                    "--parent-repository",
                    PARENT_REPOSITORY,
                    "--base-commit",
                    self.locked_commit,
                    "--head-commit",
                    self.candidate_commit,
                ]
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            json.loads(stdout.getvalue())["status"], "child-migration-required"
        )

    def test_canonical_fleet_config_uses_the_common_foundation_docs_root(self):
        expected = Path("docs/foundation/inheritance-fleet.json")

        self.assertEqual(inheritance.DEFAULT_FLEET_CONFIG_PATH, expected)
        self.assertTrue((REPOSITORY_ROOT / expected).is_file())

    def test_canonical_foundation_publishes_a_valid_bootstrap_export(self):
        path = ".ai/contracts/foundation/inheritance-export.json"
        export = inheritance._validate_bootstrap_export(
            path,
            inheritance._read_json(REPOSITORY_ROOT, path),
            "ea-Mitsuoka/ai-dev-foundation",
        )

        self.assertEqual(
            export["path"],
            ".ai/contracts/foundation/inheritance-export.json",
        )
        self.assertIn("docs/foundation/", export["inherited_paths"])

    def test_canonical_fleet_contains_every_active_relationship_once(self):
        config = json.loads(
            (REPOSITORY_ROOT / inheritance.DEFAULT_FLEET_CONFIG_PATH).read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(config["schema_version"], 2)
        self.assertEqual(
            {
                (
                    item["repository"],
                    item["directory"],
                    item["parent_repository"],
                    item["parent_directory"],
                    item["lifecycle"],
                )
                for item in config["repositories"]
            },
            {
                (
                    "ea-Mitsuoka/terraform-gcp-template",
                    "terraform-gcp-template",
                    "ea-Mitsuoka/ai-dev-foundation",
                    "ai-dev-foundation",
                    "active",
                ),
                (
                    "ea-Mitsuoka/nextjs-saas-template",
                    "nextjs-saas-template",
                    "ea-Mitsuoka/ai-dev-foundation",
                    "ai-dev-foundation",
                    "active",
                ),
                (
                    "ea-Mitsuoka/secure-ga4-bq-template",
                    "secure-ga4-bq-template",
                    "ea-Mitsuoka/terraform-gcp-template",
                    "terraform-gcp-template",
                    "active",
                ),
                (
                    "ea-Mitsuoka/secure-ai-controls",
                    "secure-ai-controls",
                    "ea-Mitsuoka/terraform-gcp-template",
                    "terraform-gcp-template",
                    "active",
                ),
            },
        )
        self.assertTrue(all(item["reason"] for item in config["repositories"]))
        self.assertEqual(len(config["repositories"]), 4)

    def test_fleet_report_rejects_duplicate_children_and_pair_limit(self):
        with self.assertRaisesRegex(inheritance.InheritanceError, "duplicate child"):
            inheritance.fleet_report(
                [
                    ("acme/child", self.child, self.parent),
                    ("acme/child", self.child, self.parent),
                ]
            )

        too_many = [
            (f"acme/child-{index}", self.child / str(index), self.parent)
            for index in range(inheritance.MAX_FLEET_REPOSITORIES + 1)
        ]
        with self.assertRaisesRegex(inheritance.InheritanceError, "fleet repositories"):
            inheritance.fleet_report(too_many)

    def test_fleet_report_rejects_a_protected_child_symlink(self):
        outside = Path(self.temporary_directory.name) / "outside-ignore"
        outside.write_text("outside\n", encoding="utf-8")
        (self.child / ".gitignore").unlink()
        (self.child / ".gitignore").symlink_to(outside)

        with self.assertRaisesRegex(inheritance.InheritanceError, "symlink"):
            inheritance.fleet_report(
                [("acme/child-template", self.child, self.parent)]
            )

    def test_fleet_report_preserves_parent_identity_validation(self):
        self.git("remote", "set-url", "origin", "https://github.com/acme/other.git")

        with self.assertRaisesRegex(inheritance.InheritanceError, "origin"):
            inheritance.fleet_report(
                [("acme/child-template", self.child, self.parent)]
            )

    def test_fleet_report_cli_prints_deterministic_json(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = inheritance.main(
                [
                    "fleet-report",
                    "--repository",
                    "acme/child-template",
                    str(self.child),
                    str(self.parent),
                ]
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            json.loads(stdout.getvalue())["repositories"][0]["repository"],
            "acme/child-template",
        )


class TemplateInheritanceFinalizeTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        temporary_root = Path(self.temporary_directory.name)
        self.parent = temporary_root / "parent"
        self.child = temporary_root / "child"
        self.parent.mkdir()
        self.child.mkdir()

        self.git(self.parent, "init", "-b", "main")
        self.configure_git(self.parent)
        self.git(
            self.parent,
            "remote",
            "add",
            "origin",
            f"https://github.com/{PARENT_REPOSITORY}.git",
        )
        self.write(self.parent, "inherited/ordinary.txt", "old\n")
        self.write(self.parent, ".github/workflows/shared.yml", "old\n")
        self.locked_commit = self.commit(self.parent, "base")

        self.write(self.parent, "inherited/ordinary.txt", "new\n")
        self.write(self.parent, ".github/workflows/shared.yml", "new\n")
        self.source_commit = self.commit(self.parent, "source")
        self.git(
            self.parent,
            "update-ref",
            "refs/remotes/origin/main",
            self.source_commit,
        )

        self.write(self.child, "inherited/ordinary.txt", "new\n")
        self.write(self.child, ".github/workflows/shared.yml", "old\n")
        self.write_contract(self.locked_commit)
        self.git(self.child, "init", "-b", "main")
        self.configure_git(self.child)
        self.git(
            self.child,
            "remote",
            "add",
            "origin",
            "https://github.com/acme/child-template.git",
        )
        child_main = self.commit(self.child, "template sync result")
        self.git(self.child, "update-ref", "refs/remotes/origin/main", child_main)
        self.git(
            self.child,
            "symbolic-ref",
            "refs/remotes/origin/HEAD",
            "refs/remotes/origin/main",
        )
        self.git(self.child, "switch", "-c", "chore/template_sync_source")

    def git(self, root, *arguments):
        result = subprocess.run(
            ["git", "-C", str(root), *arguments],
            capture_output=True,
            check=False,
            text=True,
            timeout=5,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def configure_git(self, root):
        self.git(root, "config", "user.name", "Test User")
        self.git(root, "config", "user.email", "test@example.invalid")

    def commit(self, root, message):
        self.git(root, "add", "-A")
        self.git(root, "commit", "-m", message)
        return self.git(root, "rev-parse", "HEAD")

    def write(self, root, relative_path, content):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def write_contract(self, commit):
        manifest = {
            "schema_version": 1,
            "parent": {"repository": PARENT_REPOSITORY, "branch": "main"},
            "lock_file": ".github/inheritance/lock.json",
            "inherited_paths": ["inherited/", ".github/workflows/shared.yml"],
            "protected_paths": PROTECTED_PATHS,
        }
        lock = {
            "schema_version": 1,
            "parent": {"repository": PARENT_REPOSITORY, "commit": commit},
        }
        self.write(
            self.child,
            ".github/inheritance/manifest.json",
            json.dumps(manifest),
        )
        self.write(
            self.child,
            ".github/inheritance/lock.json",
            json.dumps(lock),
        )
        self.write(
            self.child,
            ".templatesyncignore",
            "\n".join(PROTECTED_PATHS + [".github/workflows/**"]) + "\n",
        )

    def test_finalization_plan_reports_exact_source_manual_port_read_only(self):
        plan = inheritance.plan_finalization(
            self.child,
            self.parent,
            self.source_commit,
        )

        self.assertEqual(plan["status"], "ready_to_finalize")
        self.assertEqual(plan["pending_sync"], [])
        self.assertEqual(
            plan["pending_manual_port"],
            [
                {
                    "path": ".github/workflows/shared.yml",
                    "reason": "workflow-security-boundary",
                }
            ],
        )
        self.assertEqual(self.git(self.child, "status", "--porcelain"), "")

    def test_finalization_plan_blocks_pending_template_sync_content(self):
        self.write(self.child, "inherited/ordinary.txt", "old\n")
        self.commit(self.child, "stale ordinary content")

        plan = inheritance.plan_finalization(
            self.child,
            self.parent,
            self.source_commit,
        )

        self.assertEqual(plan["status"], "blocked")
        self.assertEqual(plan["pending_sync"], ["inherited/ordinary.txt"])

    def test_finalization_plan_ignores_unchanged_repository_owned_protected_path(self):
        self.write(self.parent, ".gitignore", "parent-only\n")
        protected_source = self.commit(self.parent, "protected change")
        self.git(
            self.parent,
            "update-ref",
            "refs/remotes/origin/main",
            protected_source,
        )

        protected = inheritance.plan_finalization(
            self.child,
            self.parent,
            protected_source,
        )
        self.assertEqual(protected["protected_review"], [])
        self.assertEqual(protected["status"], "ready_to_finalize")

    def test_finalization_plan_blocks_protected_path_changed_on_sync_branch(self):
        self.write(self.child, ".gitignore", "transport overwrite\n")
        self.commit(self.child, "modify protected child path")

        protected = inheritance.plan_finalization(
            self.child,
            self.parent,
            self.source_commit,
        )

        self.assertEqual(protected["protected_review"], [".gitignore"])
        self.assertEqual(protected["status"], "blocked")

    def test_finalization_plan_blocks_unowned_path_changed_on_sync_branch(self):
        self.write(self.child, "unexpected.txt", "transport injection\n")
        self.commit(self.child, "add unowned child path")

        review = inheritance.plan_finalization(
            self.child,
            self.parent,
            self.source_commit,
        )

        self.assertEqual(review["ownership_review"], ["unexpected.txt"])
        self.assertEqual(review["status"], "blocked")

    def test_finalization_plan_reports_inherited_deletion(self):
        self.write(self.parent, ".gitignore", "parent-only\n")
        self.commit(self.parent, "protected change")

        (self.parent / ".gitignore").unlink()
        (self.parent / "inherited/ordinary.txt").unlink()
        deletion_source = self.commit(self.parent, "delete inherited file")
        self.git(
            self.parent,
            "update-ref",
            "refs/remotes/origin/main",
            deletion_source,
        )

        deletion = inheritance.plan_finalization(
            self.child,
            self.parent,
            deletion_source,
        )
        self.assertEqual(deletion["deletion_review"], ["inherited/ordinary.txt"])

    def test_finalization_plan_accepts_recorded_checkpoint_before_current_head(self):
        self.write(self.parent, "inherited/later.txt", "later\n")
        later_commit = self.commit(self.parent, "later")
        self.git(
            self.parent,
            "update-ref",
            "refs/remotes/origin/main",
            later_commit,
        )

        plan = inheritance.plan_finalization(
            self.child,
            self.parent,
            self.source_commit,
        )

        self.assertEqual(plan["parent"]["source_commit"], self.source_commit)
        self.assertNotIn("inherited/later.txt", json.dumps(plan))

    def test_finalization_plan_requires_accepted_source_and_non_default_branch(self):
        with self.assertRaisesRegex(inheritance.InheritanceError, "source commit"):
            inheritance.plan_finalization(
                self.child,
                self.parent,
                "b" * 40,
            )

        self.git(self.child, "switch", "main")
        with self.assertRaisesRegex(inheritance.InheritanceError, "default branch"):
            inheritance.plan_finalization(
                self.child,
                self.parent,
                self.source_commit,
            )

    def apply(self, *, source=None, repository="acme/child-template"):
        source = source or self.source_commit
        return inheritance.apply_finalization(
            self.child,
            self.parent,
            source,
            confirm_repository=repository,
            confirm_source=source,
        )

    def test_finalization_apply_ports_workflow_updates_lock_and_is_idempotent(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = inheritance.main(
                [
                    "finalize-sync",
                    "--root",
                    str(self.child),
                    "--parent-root",
                    str(self.parent),
                    "--source-commit",
                    self.source_commit,
                    "--apply",
                    "--confirm-repository",
                    "acme/child-template",
                    "--confirm-source",
                    self.source_commit,
                ]
            )

        result = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(result["status"], "finalized")
        self.assertEqual(
            result["changes"]["manual_ported"],
            [".github/workflows/shared.yml"],
        )
        self.assertTrue(result["changes"]["lock_updated"])
        self.assertEqual(
            (self.child / ".github/workflows/shared.yml").read_text(encoding="utf-8"),
            "new\n",
        )
        self.assertEqual(
            json.loads(
                (self.child / ".github/inheritance/lock.json").read_text(
                    encoding="utf-8"
                )
            )["parent"]["commit"],
            self.source_commit,
        )

        self.commit(self.child, "finalize")
        repeated = self.apply()
        self.assertEqual(repeated["status"], "already_finalized")
        self.assertEqual(self.git(self.child, "status", "--porcelain"), "")

    def test_finalization_apply_refuses_pending_sync_before_writing(self):
        self.write(self.child, "inherited/ordinary.txt", "old\n")
        self.commit(self.child, "stale ordinary content")

        with self.assertRaisesRegex(inheritance.InheritanceError, "pending sync"):
            self.apply()

        self.assertEqual(
            (self.child / ".github/workflows/shared.yml").read_text(encoding="utf-8"),
            "old\n",
        )
        self.assertEqual(
            json.loads(
                (self.child / ".github/inheritance/lock.json").read_text(
                    encoding="utf-8"
                )
            )["parent"]["commit"],
            self.locked_commit,
        )

    def test_finalization_apply_refuses_protected_branch_change(self):
        self.write(self.child, ".gitignore", "transport overwrite\n")
        self.commit(self.child, "modify protected child path")

        with self.assertRaisesRegex(inheritance.InheritanceError, "protected review"):
            self.apply()

    def test_finalization_apply_refuses_deletion(self):
        (self.parent / "inherited/ordinary.txt").unlink()
        deletion_source = self.commit(self.parent, "delete inherited file")
        self.git(
            self.parent,
            "update-ref",
            "refs/remotes/origin/main",
            deletion_source,
        )
        with self.assertRaisesRegex(inheritance.InheritanceError, "deletion review"):
            self.apply(source=deletion_source)

    def test_finalization_apply_requires_exact_confirmation(self):
        with self.assertRaisesRegex(inheritance.InheritanceError, "confirmation"):
            self.apply(repository="acme/other")


class TemplateInheritanceBootstrapTest(unittest.TestCase):
    git = TemplateInheritanceFinalizeTest.git
    configure_git = TemplateInheritanceFinalizeTest.configure_git
    commit = TemplateInheritanceFinalizeTest.commit
    write = TemplateInheritanceFinalizeTest.write
    write_contract = TemplateInheritanceFinalizeTest.write_contract

    def setUp(self):
        TemplateInheritanceFinalizeTest.setUp(self)
        self.write(
            self.parent, ".ai/contracts/foundation/agent-entry.md", "foundation\n"
        )
        protected = sorted(
            (set(PROTECTED_PATHS) - {".github/workflows/template-sync.yml"})
            | {
                ".ai/project/",
                ".github/inheritance/agent-profile.json",
                ".github/workflows/",
                "README.md",
                "docs/inheritance/readmes/",
            }
        )
        export = {
            "schema_version": 1,
            "repository": PARENT_REPOSITORY,
            "branch": "main",
            "inherited_paths": [
                ".ai/contracts/foundation/",
                "docs/foundation/",
                "inherited/",
            ],
            "protected_paths": protected,
            "agent_inputs": [
                {
                    "layer": "foundation",
                    "repository": PARENT_REPOSITORY,
                    "path": ".ai/contracts/foundation/agent-entry.md",
                }
            ],
        }
        export_path = ".ai/contracts/foundation/inheritance-export.json"
        self.write(self.parent, export_path, json.dumps(export))
        self.write(self.parent, "docs/foundation/guide.md", "foundation guide\n")
        self.write(self.parent, ".ai/project/agent-overlay.md", "parent project\n")
        self.write(self.parent, ".github/workflows/template-sync.yml", "name: parent sync\n")
        self.write(
            self.parent,
            "README.md",
            f"<!-- repository-readme-owner: {PARENT_REPOSITORY} -->\n# Parent\n",
        )
        for path in (
            ".github/inheritance/manifest.json",
            ".github/inheritance/lock.json",
            ".templatesyncignore",
        ):
            self.write(
                self.parent, path, (self.child / path).read_text(encoding="utf-8")
            )
        self.bootstrap_source = self.commit(self.parent, "export child contract")
        self.git(
            self.parent,
            "update-ref",
            "refs/remotes/origin/main",
            self.bootstrap_source,
        )
        for path in (
            ".ai/contracts/foundation/agent-entry.md",
            "docs/foundation/guide.md",
            export_path,
        ):
            self.write(
                self.child, path, (self.parent / path).read_text(encoding="utf-8")
            )
        for path in (".ai/project/agent-overlay.md", ".github/workflows/template-sync.yml", "README.md"):
            self.write(self.child, path, (self.parent / path).read_text(encoding="utf-8"))
        self.commit(self.child, "copy bootstrap inputs")
        self.payload = Path(self.temporary_directory.name) / "payload"
        self.payload.mkdir()
        self.write(
            self.payload, "README.md",
            "<!-- repository-readme-owner: acme/child-template -->\n# Child Template\n",
        )
        self.write(
            self.payload, ".ai/project/agent-overlay.md",
            "# Project Agent Overlay\n\nRepository: acme/child-template\n",
        )
        self.write(
            self.payload, ".github/workflows/template-sync.yml",
            "name: Template Sync\non: workflow_dispatch\njobs:\n  sync:\n"
            "    if: vars.TEMPLATE_SYNC_ENABLED == 'true'\n    steps:\n"
            f"      - uses: acme/template-sync@sha\n        with:\n"
            f"          source_repo_path: \"{PARENT_REPOSITORY}\"\n"
            f"        env:\n          SOURCE_REPOSITORY: \"{PARENT_REPOSITORY}\"\n",
        )
        archive = "docs/inheritance/readmes/acme/parent-template.md"
        self.write(
            self.payload, archive,
            f"---\nsource-repository: {PARENT_REPOSITORY}\nsource-commit: {self.bootstrap_source}\n---\n\n"
            f"<!-- repository-readme-owner: {PARENT_REPOSITORY} -->\n# Parent\n",
        )

    def plan_bootstrap(self):
        return inheritance.plan_bootstrap(
            self.child,
            self.parent,
            self.bootstrap_source,
            "acme/child-template",
        )

    def apply_bootstrap(self, **overrides):
        arguments = {
            "confirm_repository": "acme/child-template",
            "confirm_source": self.bootstrap_source,
            "payload_root": self.payload,
        }
        arguments.update(overrides)
        return inheritance.apply_bootstrap(
            self.child, self.parent, self.bootstrap_source,
            "acme/child-template", **arguments,
        )

    def test_bootstrap_plan_builds_direct_parent_metadata_without_writes(self):
        self.write(self.parent, ".ai/contracts/foundation/inheritance-export.json", "{}")
        result = self.plan_bootstrap()

        self.assertEqual(result["status"], "ready_to_bootstrap")
        self.assertEqual(result["parent"]["repository"], PARENT_REPOSITORY)
        self.assertEqual(
            result["desired"]["agent_profile"]["inputs"][-1]["repository"],
            "acme/child-template",
        )
        self.assertEqual(
            result["manual_boundaries"],
            [
                ".ai/project/agent-overlay.md",
                ".github/workflows/template-sync.yml",
                "README.md",
            ],
        )
        self.assertIn("docs/**", result["desired"]["template_sync_ignore"])
        self.assertIn(":!docs/foundation/", result["desired"]["template_sync_ignore"])
        self.assertIn(
            ":!docs/foundation/**", result["desired"]["template_sync_ignore"]
        )
        self.assertEqual(self.git(self.child, "status", "--porcelain=v1"), "")

    def test_bootstrap_plan_rejects_inherited_drift(self):
        self.write(self.child, "inherited/ordinary.txt", "drift\n")
        self.commit(self.child, "drift")

        with self.assertRaisesRegex(inheritance.InheritanceError, "template copy"):
            self.plan_bootstrap()

    def test_bootstrap_plan_rejects_non_first_parent_source(self):
        self.git(self.parent, "switch", "-c", "side", self.bootstrap_source)
        self.write(self.parent, "side.txt", "side\n")
        side_commit = self.commit(self.parent, "side")
        self.git(self.parent, "switch", "main")
        self.write(self.parent, "main.txt", "main\n")
        self.commit(self.parent, "main")
        self.git(self.parent, "merge", "--no-ff", "side", "-m", "merge side")
        self.git(
            self.parent, "update-ref", "refs/remotes/origin/main",
            self.git(self.parent, "rev-parse", "HEAD"),
        )

        with self.assertRaisesRegex(inheritance.InheritanceError, "first-parent"):
            inheritance.plan_bootstrap(
                self.child, self.parent, side_commit, "acme/child-template"
            )

    def test_bootstrap_cli_prints_deterministic_json(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = inheritance.main(
                [
                    "bootstrap-child",
                    "--root", str(self.child),
                    "--parent-root", str(self.parent),
                    "--source-commit", self.bootstrap_source,
                    "--repository", "acme/child-template",
                ]
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            json.loads(stdout.getvalue())["status"], "ready_to_bootstrap"
        )

    def test_bootstrap_apply_writes_valid_metadata_and_is_idempotent(self):
        result = self.apply_bootstrap()

        self.assertEqual(result["status"], "bootstrapped")
        self.assertEqual(
            inheritance.validate_inheritance(self.child)["schema_version"], 2
        )
        self.commit(self.child, "bootstrap child")
        repeated = self.apply_bootstrap()
        self.assertEqual(repeated["status"], "already_bootstrapped")
        self.assertEqual(self.git(self.child, "status", "--porcelain=v1"), "")

    def test_bootstrap_apply_accepts_github_actions_expressions(self):
        workflow_path = ".github/workflows/template-sync.yml"
        workflow = (self.payload / workflow_path).read_text(encoding="utf-8")
        workflow = workflow.replace(
            "        env:\n",
            "        env:\n          GH_TOKEN: ${{ github.token }}\n",
        )
        self.write(self.payload, workflow_path, workflow)

        result = self.apply_bootstrap()

        self.assertEqual(result["status"], "bootstrapped")

    def test_bootstrap_apply_rejects_unresolved_workflow_placeholders(self):
        workflow_path = ".github/workflows/template-sync.yml"
        workflow = (self.payload / workflow_path).read_text(encoding="utf-8")
        workflow = workflow.replace(
            "        env:\n",
            "        env:\n          CHILD_REPOSITORY: {{ repository }}\n",
        )
        self.write(self.payload, workflow_path, workflow)

        with self.assertRaisesRegex(
            inheritance.InheritanceError, "invalid direct-parent settings"
        ):
            self.apply_bootstrap()

    def test_bootstrap_apply_normalizes_desired_file_mode(self):
        self.apply_bootstrap()
        readme = self.child / "README.md"
        readme.chmod(0o755)
        self.commit(self.child, "make desired README executable")

        result = self.apply_bootstrap()

        self.assertIn("README.md", result["changed_paths"])
        self.assertEqual(readme.stat().st_mode & 0o111, 0)

    def test_bootstrap_apply_refuses_wrong_confirmation_and_existing_archive(self):
        with self.assertRaisesRegex(inheritance.InheritanceError, "confirmation"):
            self.apply_bootstrap(confirm_repository="acme/other")
        with self.assertRaisesRegex(inheritance.InheritanceError, "payload-root"):
            self.apply_bootstrap(payload_root=None)
        self.write(
            self.child, "docs/inheritance/readmes/acme/parent-template.md", "different\n"
        )
        self.commit(self.child, "conflicting archive")
        with self.assertRaisesRegex(inheritance.InheritanceError, "differs"):
            self.apply_bootstrap()
