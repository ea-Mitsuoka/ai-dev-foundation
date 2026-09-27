import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).parents[2]
DISPATCHER = Path("scripts") / "canonical-target.sh"
POST_EDIT_HOOK = Path(".claude") / "hooks" / "post-edit-quality.sh"
# Records each call so a test can tell which runner ran; exits with FAKE_RUNNER_STATUS.
FAKE_RUNNER = """#!/bin/sh
echo "$(basename "$0") $*" >> "$FAKE_RUNNER_LOG"
echo "$(basename "$0") $*"
exit "${FAKE_RUNNER_STATUS:-0}"
"""
SYSTEM_PATH = "/usr/bin:/bin"


class CanonicalTargetTestCase(unittest.TestCase):
    def make_project(self, *, taskfile, runners, status=0):
        """Build a repository root holding the real dispatcher and hook, with fake runners."""
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        root = Path(temporary_directory.name)
        for relative in (DISPATCHER, POST_EDIT_HOOK):
            (root / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(REPOSITORY_ROOT / relative, root / relative)
        if taskfile:
            (root / "Taskfile.yml").write_text('version: "3"\n', encoding="utf-8")
        fake_bin = root / "fake-bin"
        fake_bin.mkdir()
        for runner in runners:
            (fake_bin / runner).write_text(FAKE_RUNNER, encoding="utf-8")
            (fake_bin / runner).chmod(0o755)
        jq = shutil.which("jq")
        if jq:
            (fake_bin / "jq").symlink_to(jq)
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


class CanonicalTargetDispatcherTest(CanonicalTargetTestCase):
    def dispatch(self, root, *arguments):
        (root / "src").mkdir(exist_ok=True)
        return subprocess.run(
            ["bash", str(root / DISPATCHER), *arguments],
            cwd=root / "src",
            env=self.environment,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_repository_with_a_root_taskfile_runs_task(self):
        root = self.make_project(taskfile=True, runners=("task", "make"))

        result = self.dispatch(root, "format", "FILE=src/app.py")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(["task format FILE=src/app.py"], self.runner_calls())

    def test_repository_without_a_taskfile_runs_make(self):
        root = self.make_project(taskfile=False, runners=("task", "make"))

        result = self.dispatch(root, "format", "FILE=src/app.py")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(
            ["make --no-print-directory format FILE=src/app.py"], self.runner_calls()
        )

    def test_runner_failure_status_is_returned_unchanged(self):
        root = self.make_project(taskfile=True, runners=("task",), status=3)

        result = self.dispatch(root, "lint")

        self.assertEqual(3, result.returncode)

    def test_missing_runner_exits_127_without_running_the_other_runner(self):
        root = self.make_project(taskfile=True, runners=("make",))

        result = self.dispatch(root, "lint")

        self.assertEqual(127, result.returncode)
        self.assertIn("canonical-target: task is not installed", result.stderr)
        self.assertEqual([], self.runner_calls())

    def test_missing_target_is_a_usage_error(self):
        root = self.make_project(taskfile=True, runners=("task",))

        result = self.dispatch(root)

        self.assertEqual(2, result.returncode)
        self.assertIn("usage: canonical-target.sh <target> [VAR=value ...]", result.stderr)
        self.assertEqual([], self.runner_calls())


@unittest.skipUnless(shutil.which("jq"), "the post-edit hook reads its payload with jq")
class PostEditHookRunnerTest(CanonicalTargetTestCase):
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

    def test_lint_failure_through_task_is_fed_back_to_the_agent(self):
        root = self.make_project(taskfile=True, runners=("task", "make"), status=1)

        result = self.run_hook(root, "src/app.py")

        self.assertEqual(2, result.returncode)
        self.assertIn("Lint failed for src/app.py", result.stderr)
        self.assertEqual(
            ["task format FILE=src/app.py", "task lint FILE=src/app.py"],
            self.runner_calls(),
        )

    def test_repository_without_a_taskfile_keeps_using_make(self):
        root = self.make_project(taskfile=False, runners=("task", "make"))

        result = self.run_hook(root, "src/app.py")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(
            [
                "make --no-print-directory format FILE=src/app.py",
                "make --no-print-directory lint FILE=src/app.py",
            ],
            self.runner_calls(),
        )

    def test_missing_runner_keeps_the_hook_non_blocking(self):
        root = self.make_project(taskfile=True, runners=())

        result = self.run_hook(root, "src/app.py")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)

    def test_documentation_edits_do_not_run_any_target(self):
        root = self.make_project(taskfile=True, runners=("task",))

        result = self.run_hook(root, "docs/guide.md")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual([], self.runner_calls())


class InheritedCallerWiringTest(unittest.TestCase):
    def test_pre_commit_hooks_run_targets_through_the_dispatcher(self):
        config = (REPOSITORY_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")

        self.assertIn("entry: bash scripts/canonical-target.sh lint", config)
        self.assertIn("entry: bash scripts/canonical-target.sh test-unit", config)
        self.assertNotIn("entry: make", config)

    def test_release_gates_install_task_only_for_taskfile_repositories(self):
        action = (
            REPOSITORY_ROOT / "scripts" / "actions" / "release-gates" / "action.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("if: hashFiles('Taskfile.yml') != ''", action)
        self.assertIn("uses: ./scripts/actions/setup-task", action)
        for target in ("setup", "test", "build"):
            with self.subTest(target=target):
                self.assertIn(f"run: bash scripts/canonical-target.sh {target}", action)
        self.assertNotIn("run: make ", action)


if __name__ == "__main__":
    unittest.main()
