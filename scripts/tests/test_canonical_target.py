import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).parents[2]
POST_EDIT_HOOK = Path(".claude") / "hooks" / "post-edit-quality.sh"
# Records each call so a test can tell which runner ran; exits with FAKE_RUNNER_STATUS.
FAKE_RUNNER = """#!/bin/sh
echo "$(basename "$0") $*" >> "$FAKE_RUNNER_LOG"
echo "$(basename "$0") $*"
exit "${FAKE_RUNNER_STATUS:-0}"
"""
SYSTEM_PATH = "/usr/bin:/bin"


@unittest.skipUnless(shutil.which("jq"), "the post-edit hook reads its payload with jq")
class PostEditHookTest(unittest.TestCase):
    """The post-edit hook runs canonical targets with go-task only (ADR-0026)."""

    def make_project(self, *, taskfile, runners, status=0):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        root = Path(temporary_directory.name)
        (root / POST_EDIT_HOOK).parent.mkdir(parents=True)
        shutil.copy(REPOSITORY_ROOT / POST_EDIT_HOOK, root / POST_EDIT_HOOK)
        if taskfile:
            (root / "Taskfile.yml").write_text('version: "3"\n', encoding="utf-8")
        fake_bin = root / "fake-bin"
        fake_bin.mkdir()
        for runner in runners:
            (fake_bin / runner).write_text(FAKE_RUNNER, encoding="utf-8")
            (fake_bin / runner).chmod(0o755)
        (fake_bin / "jq").symlink_to(shutil.which("jq"))
        self.runner_log = root / "runner-calls"
        self.environment = {
            "HOME": os.environ.get("HOME", str(root)),
            "PATH": f"{fake_bin}:{SYSTEM_PATH}",
            "FAKE_RUNNER_LOG": str(self.runner_log),
            "FAKE_RUNNER_STATUS": str(status),
        }
        return root

    def runner_calls(self):
        if not self.runner_log.exists():
            return []
        return self.runner_log.read_text(encoding="utf-8").splitlines()

    def run_hook(self, root, file_path):
        return subprocess.run(
            ["bash", str(root / POST_EDIT_HOOK)],
            cwd=root,
            env=self.environment,
            input=json.dumps({"tool_input": {"file_path": file_path}}),
            text=True,
            capture_output=True,
            check=False,
        )

    def test_edit_formats_and_lints_the_file_with_task(self):
        root = self.make_project(taskfile=True, runners=("task", "make"))

        result = self.run_hook(root, "src/app.py")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(
            ["task format FILE=src/app.py", "task lint FILE=src/app.py"],
            self.runner_calls(),
        )

    def test_lint_failure_is_fed_back_to_the_agent(self):
        root = self.make_project(taskfile=True, runners=("task",), status=1)

        result = self.run_hook(root, "src/app.py")

        self.assertEqual(2, result.returncode)
        self.assertIn("Lint failed for src/app.py", result.stderr)

    def test_repository_without_a_taskfile_runs_no_runner(self):
        root = self.make_project(taskfile=False, runners=("task", "make"))

        result = self.run_hook(root, "src/app.py")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual([], self.runner_calls())

    def test_missing_task_keeps_the_hook_non_blocking(self):
        root = self.make_project(taskfile=True, runners=("make",))

        result = self.run_hook(root, "src/app.py")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)
        self.assertEqual([], self.runner_calls())

    def test_documentation_edits_do_not_run_any_target(self):
        root = self.make_project(taskfile=True, runners=("task",))

        result = self.run_hook(root, "docs/guide.md")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual([], self.runner_calls())


class InheritedCallerWiringTest(unittest.TestCase):
    """Inherited automation calls task directly; the make fallback is gone (ADR-0026)."""

    def test_the_runner_dispatcher_is_removed(self):
        self.assertFalse((REPOSITORY_ROOT / "scripts" / "canonical-target.sh").exists())

    def test_pre_commit_hooks_run_task(self):
        config = (REPOSITORY_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")

        self.assertIn("entry: task lint", config)
        self.assertIn("entry: task test-unit", config)
        self.assertNotIn("canonical-target.sh", config)
        self.assertNotIn("entry: make", config)

    def test_release_gates_install_task_and_run_it(self):
        action = (
            REPOSITORY_ROOT / "scripts" / "actions" / "release-gates" / "action.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("uses: ./scripts/actions/setup-task", action)
        self.assertNotIn("hashFiles('Taskfile.yml')", action)
        for target in ("setup", "test", "build"):
            with self.subTest(target=target):
                self.assertIn(f"run: task {target}", action)
        self.assertNotIn("canonical-target.sh", action)
        self.assertNotIn("run: make ", action)


if __name__ == "__main__":
    unittest.main()
