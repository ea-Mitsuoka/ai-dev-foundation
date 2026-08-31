import tempfile
import unittest
from pathlib import Path

from scripts import makefile_profile


REPOSITORY_ROOT = Path(__file__).parents[2]
FOUNDATION_README_MARKER = (
    "<!-- repository-readme-owner: ea-Mitsuoka/ai-dev-foundation -->"
)


class MakefileProfileTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)

    def write_makefile(self, content):
        (self.root / "Makefile").write_text(content, encoding="utf-8")

    def test_downstream_rejects_required_template_placeholders(self):
        self.write_makefile(
            'setup:\n\t@echo "[template] setup: not wired yet"\n'
            'test:\n\t@echo "[template] test: not wired yet"\n'
        )

        with self.assertRaisesRegex(
            makefile_profile.MakefileProfileError,
            "setup, test",
        ):
            makefile_profile.validate_makefile(self.root)

    def test_foundation_may_retain_template_placeholders(self):
        self.write_makefile(
            'build:\n\t@echo "[template] build: not wired yet"\n'
        )

        unresolved = makefile_profile.validate_makefile(
            self.root,
            allow_template_placeholders=True,
        )

        self.assertEqual(unresolved, ["build"])

    def test_explicit_not_applicable_target_is_valid(self):
        self.write_makefile(
            'build:\n\t@echo "[project] build: not applicable — no artifact"\n'
        )

        unresolved = makefile_profile.validate_makefile(self.root)

        self.assertEqual(unresolved, [])

    def test_documented_placeholder_text_is_not_an_implementation(self):
        self.write_makefile(
            "# Replace [template] test: not wired yet during setup\n"
            'test:\n\t@echo "[project] test: not applicable — no test surface"\n'
        )

        unresolved = makefile_profile.validate_makefile(self.root)

        self.assertEqual(unresolved, [])

    def test_missing_makefile_fails_closed(self):
        with self.assertRaisesRegex(
            makefile_profile.MakefileProfileError,
            "Makefile cannot be read",
        ):
            makefile_profile.validate_makefile(self.root)


class FoundationMakeTargetsTest(unittest.TestCase):
    def setUp(self):
        readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
        if FOUNDATION_README_MARKER not in readme:
            self.skipTest("Foundation-owned root Make targets are not inherited")
        self.makefile = (REPOSITORY_ROOT / "Makefile").read_text(encoding="utf-8")

    def test_foundation_test_targets_execute_regression_suites(self):
        self.assertIn("test: test-unit", self.makefile)
        self.assertIn("bash .claude/hooks/tests/guard-bash.test.sh", self.makefile)
        self.assertIn(
            "python3 -m unittest discover -s scripts/tests -p 'test_*.py'",
            self.makefile,
        )
        self.assertNotIn("[template] test: not wired yet", self.makefile)
        self.assertNotIn("[template] test-unit: not wired yet", self.makefile)

    def test_foundation_coverage_target_emits_a_local_report(self):
        self.assertIn("coverage: ## Test with coverage report", self.makefile)
        self.assertIn("python3 -m trace --count --missing --summary", self.makefile)
        self.assertIn("--coverdir coverage", self.makefile)
        self.assertNotIn("[template] coverage: not wired yet", self.makefile)


if __name__ == "__main__":
    unittest.main()
