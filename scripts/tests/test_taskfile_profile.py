import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts import taskfile_profile


REPOSITORY_ROOT = Path(__file__).parents[2]
FOUNDATION_README_MARKER = (
    "<!-- repository-readme-owner: ea-Mitsuoka/ai-dev-foundation -->"
)


class TaskfileProfileTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)

    def write_taskfile(self, tasks):
        (self.root / "Taskfile.yml").write_text(
            'version: "3"\n\ntasks:\n' + tasks, encoding="utf-8"
        )

    def test_downstream_rejects_required_template_placeholders(self):
        self.write_taskfile(
            "  setup:\n    cmds:\n"
            "      - 'echo \"[template] setup: not wired yet\"'\n"
            "  test:\n    cmds:\n"
            "      - 'echo \"[template] test: not wired yet\"'\n"
        )

        with self.assertRaisesRegex(taskfile_profile.TaskfileProfileError, "setup, test"):
            taskfile_profile.validate_taskfile(self.root)

    def test_foundation_may_retain_template_placeholders(self):
        self.write_taskfile(
            "  build:\n    cmds:\n"
            "      - 'echo \"[template] build: not wired yet\"'\n"
        )

        unresolved = taskfile_profile.validate_taskfile(
            self.root, allow_template_placeholders=True
        )

        self.assertEqual(["build"], unresolved)

    def test_explicit_not_applicable_task_is_valid(self):
        self.write_taskfile(
            "  build:\n    cmds:\n"
            "      - 'echo \"[project] build: not applicable — no artifact\"'\n"
        )

        self.assertEqual([], taskfile_profile.validate_taskfile(self.root))

    def test_documented_placeholder_text_is_not_an_implementation(self):
        self.write_taskfile(
            "  # Replace [template] test: not wired yet during setup\n"
            "  test:\n    cmds:\n"
            "      - 'echo \"[project] test: not applicable — no test surface\"'\n"
        )

        self.assertEqual([], taskfile_profile.validate_taskfile(self.root))

    def test_placeholders_in_block_and_cmd_forms_are_detected(self):
        self.write_taskfile(
            "  lint:\n    cmds:\n      - |\n"
            "        echo \"[template] lint: not wired yet\"\n"
            "  coverage:\n    cmds:\n"
            "      - cmd: echo \"[template] coverage: not wired yet\"\n"
        )

        unresolved = taskfile_profile.validate_taskfile(
            self.root, allow_template_placeholders=True
        )

        self.assertEqual(["lint", "coverage"], unresolved)

    def test_missing_taskfile_fails_closed(self):
        with self.assertRaisesRegex(
            taskfile_profile.TaskfileProfileError, "Taskfile.yml cannot be read"
        ):
            taskfile_profile.validate_taskfile(self.root)

    def test_command_line_reports_placeholders_as_failure(self):
        self.write_taskfile(
            "  setup:\n    cmds:\n"
            "      - 'echo \"[template] setup: not wired yet\"'\n"
        )

        result = subprocess.run(
            ["python3", str(REPOSITORY_ROOT / "scripts" / "taskfile_profile.py"),
             "--root", str(self.root)],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(1, result.returncode)
        self.assertIn("taskfile profile: ERROR:", result.stderr)
        self.assertIn("setup", result.stderr)


class TaskTargetContractTest(unittest.TestCase):
    """The inherited contract carries the ADR-0026 rules every Taskfile must follow."""

    def setUp(self):
        self.contract = " ".join(
            (REPOSITORY_ROOT / ".ai" / "contracts" / "foundation" / "task-targets.md")
            .read_text(encoding="utf-8")
            .split()
        )

    def test_every_canonical_target_keeps_a_binding_row(self):
        for target in (
            "setup", "format", "lint", "test", "test-unit", "test-integration",
            "coverage", "build", "run", "security-scan", "sbom", "clean", "doctor",
        ):
            with self.subTest(target=target):
                self.assertIn(f"| `{target}` |", self.contract)

    def test_task_specific_rules_are_stated(self):
        for rule in (
            "`task format FILE=<path>`",
            "`desc:`",
            "`task --list`",
            'no `"*"` task',
            "`deps:` in parallel",
            "`includes:` references files in the repository",
            "`mvdan.cc/sh`",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, self.contract)

    def test_repositories_that_have_not_migrated_keep_make(self):
        self.assertIn("without a root `Taskfile.yml`", self.contract)
        self.assertIn("`scripts/canonical-target.sh`", self.contract)
        self.assertIn("`scripts/taskfile_profile.py`", self.contract)


class TaskfileOwnershipExportTest(unittest.TestCase):
    """A descendant bootstrapped or adopted from the export owns its root Taskfile."""

    def test_export_protects_the_root_taskfile(self):
        export = json.loads(
            (REPOSITORY_ROOT / ".ai" / "contracts" / "foundation" / "inheritance-export.json")
            .read_text(encoding="utf-8")
        )

        self.assertIn("Taskfile.yml", export["protected_paths"])
        self.assertNotIn("Taskfile.yml", export["inherited_paths"])


class DoctorProfileSelectionTest(unittest.TestCase):
    """template-check.sh picks the profile validator by the runner the repository uses."""

    def run_doctor(self, *, taskfile, foundation_readme=False):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        root = Path(temporary_directory.name)
        (root / "scripts").mkdir()
        shutil.copy(REPOSITORY_ROOT / "scripts" / "template-check.sh", root / "scripts")
        if taskfile:
            (root / "Taskfile.yml").write_text('version: "3"\n', encoding="utf-8")
        if foundation_readme:
            (root / "README.md").write_text(
                FOUNDATION_README_MARKER + "\n", encoding="utf-8"
            )
        fake_bin = root / "fake-bin"
        fake_bin.mkdir()
        python_log = root / "python-calls"
        (fake_bin / "python3").write_text(
            f'#!/bin/sh\necho "$*" >> "{python_log}"\n', encoding="utf-8"
        )
        (fake_bin / "python3").chmod(0o755)
        environment = os.environ.copy()
        environment["PATH"] = f"{fake_bin}:{environment['PATH']}"
        subprocess.run(
            ["bash", str(root / "scripts" / "template-check.sh")],
            cwd=root,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        return python_log.read_text(encoding="utf-8").splitlines()

    def profile_calls(self, calls):
        return [call for call in calls if "_profile.py" in call]

    def test_repository_with_a_root_taskfile_is_validated_by_taskfile_profile(self):
        calls = self.run_doctor(taskfile=True)

        self.assertEqual(
            ["scripts/taskfile_profile.py --root ."], self.profile_calls(calls)
        )

    def test_repository_without_a_taskfile_keeps_the_makefile_profile(self):
        calls = self.run_doctor(taskfile=False)

        self.assertEqual(
            ["scripts/makefile_profile.py --root ."], self.profile_calls(calls)
        )

    def test_foundation_template_may_keep_placeholders_in_either_profile(self):
        calls = self.run_doctor(taskfile=True, foundation_readme=True)

        self.assertEqual(
            ["scripts/taskfile_profile.py --root . --allow-template-placeholders"],
            self.profile_calls(calls),
        )


if __name__ == "__main__":
    unittest.main()
