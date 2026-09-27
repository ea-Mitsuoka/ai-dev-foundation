import tempfile
import unittest
from pathlib import Path

from scripts import makefile_profile


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


if __name__ == "__main__":
    unittest.main()
