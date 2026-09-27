import os
import re
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).parents[2]
ACTION_DIRECTORY = REPOSITORY_ROOT / "scripts" / "actions" / "setup-task"
INSTALLER = ACTION_DIRECTORY / "install.sh"
FOUNDATION_README_MARKER = (
    "<!-- repository-readme-owner: ea-Mitsuoka/ai-dev-foundation -->"
)
# The single go-task pin (ADR-0026). A version update changes this literal together with
# the version and checksums in install.sh.
PINNED_RELEASE_URL = "https://github.com/go-task/task/releases/download/v3.53.1"
FAKE_UNAME = """#!/bin/sh
case "$1" in
  -s) echo "$FAKE_UNAME_S" ;;
  -m) echo "$FAKE_UNAME_M" ;;
esac
"""
FAKE_CURL = """#!/bin/sh
printf '%s\\n' "$@" > "$FAKE_CURL_LOG"
output=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --output) output="$2"; shift 2 ;;
    *) shift ;;
  esac
done
printf 'not a go-task release archive' > "$output"
"""


def write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


class SetupTaskInstallerTest(unittest.TestCase):
    def run_installer(self, system: str, machine: str):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        root = Path(temporary_directory.name)
        fake_bin = root / "fake-bin"
        fake_bin.mkdir()
        write_executable(fake_bin / "uname", FAKE_UNAME)
        write_executable(fake_bin / "curl", FAKE_CURL)
        curl_log = root / "curl-arguments"
        install_directory = root / "bin"
        environment = os.environ.copy()
        environment.update(
            {
                "PATH": f"{fake_bin}:{environment['PATH']}",
                "FAKE_UNAME_S": system,
                "FAKE_UNAME_M": machine,
                "FAKE_CURL_LOG": str(curl_log),
            }
        )
        result = subprocess.run(
            ["bash", str(INSTALLER), str(install_directory)],
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        curl_arguments = (
            curl_log.read_text(encoding="utf-8").splitlines()
            if curl_log.exists()
            else None
        )
        return result, curl_arguments, install_directory

    def test_archive_with_a_different_checksum_is_rejected_and_not_installed(self):
        result, _, install_directory = self.run_installer("Linux", "x86_64")

        self.assertNotEqual(0, result.returncode)
        self.assertIn("SHA-256 mismatch for task_linux_amd64.tar.gz", result.stderr)
        self.assertFalse((install_directory / "task").exists())

    def test_download_requests_the_pinned_release_asset_for_the_platform(self):
        cases = {
            ("Linux", "x86_64"): "task_linux_amd64.tar.gz",
            ("Linux", "aarch64"): "task_linux_arm64.tar.gz",
            ("Darwin", "arm64"): "task_darwin_arm64.tar.gz",
            ("Darwin", "x86_64"): "task_darwin_amd64.tar.gz",
        }
        for (system, machine), asset in cases.items():
            with self.subTest(system=system, machine=machine):
                _, curl_arguments, _ = self.run_installer(system, machine)

                self.assertIsNotNone(curl_arguments)
                self.assertIn(f"{PINNED_RELEASE_URL}/{asset}", curl_arguments)
                self.assertIn("--fail", curl_arguments)
                self.assertIn("=https", curl_arguments)

    def test_unsupported_platform_is_rejected_before_any_download(self):
        result, curl_arguments, install_directory = self.run_installer("SunOS", "sun4v")

        self.assertNotEqual(0, result.returncode)
        self.assertIn("unsupported platform SunOS-sun4v", result.stderr)
        self.assertIsNone(curl_arguments)
        self.assertFalse((install_directory / "task").exists())

    def test_missing_install_directory_argument_is_a_usage_error(self):
        result = subprocess.run(
            ["bash", str(INSTALLER)],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("usage: install.sh <install-directory>", result.stderr)

    def test_every_supported_platform_pins_a_sha256_digest(self):
        installer = INSTALLER.read_text(encoding="utf-8")
        pins = dict(re.findall(r"asset=(task_\w+\.tar\.gz); sha256=(\w+)", installer))

        self.assertEqual(
            {
                "task_darwin_amd64.tar.gz",
                "task_darwin_arm64.tar.gz",
                "task_linux_amd64.tar.gz",
                "task_linux_arm64.tar.gz",
            },
            set(pins),
        )
        for asset, digest in pins.items():
            with self.subTest(asset=asset):
                self.assertRegex(digest, r"^[0-9a-f]{64}$")


class SetupTaskActionTest(unittest.TestCase):
    def test_action_runs_the_pinned_installer_without_third_party_actions(self):
        action = (ACTION_DIRECTORY / "action.yml").read_text(encoding="utf-8")

        self.assertIn("using: composite", action)
        self.assertIn('bash "${GITHUB_ACTION_PATH}/install.sh"', action)
        self.assertIn('>> "${GITHUB_PATH}"', action)
        self.assertNotIn("uses:", action)

    def test_foundation_ci_exercises_the_action(self):
        readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
        if FOUNDATION_README_MARKER not in readme:
            self.skipTest("descendant workflows are protected repository-owned files")
        workflow = (REPOSITORY_ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("uses: ./scripts/actions/setup-task", workflow)
        self.assertIn("task --version", workflow)


if __name__ == "__main__":
    unittest.main()
