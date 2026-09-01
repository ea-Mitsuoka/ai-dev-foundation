import tempfile
import unittest
from pathlib import Path

from scripts import readme_ownership


class ReadmeOwnershipTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def write_readme(self, content: str):
        (self.root / "README.md").write_text(content, encoding="utf-8")

    def test_supported_github_origins_resolve_repository(self):
        origins = (
            "https://github.com/acme/child.git",
            "git@github.com:acme/child.git",
            "ssh://git@github.com/acme/child.git",
        )

        for origin in origins:
            with self.subTest(origin=origin):
                self.assertEqual(
                    "acme/child",
                    readme_ownership.repository_from_origin_url(origin),
                )

    def test_origin_with_embedded_credentials_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "credential-free"):
            readme_ownership.repository_from_origin_url(
                "https://token@github.com/acme/child.git"
            )

    def test_matching_marker_passes(self):
        self.write_readme(
            "# Child\n\n<!-- repository-readme-owner: acme/child -->\n"
        )

        errors, warnings = readme_ownership.audit_readme(
            self.root,
            "acme/child",
        )

        self.assertEqual([], errors)
        self.assertEqual([], warnings)

    def test_parent_marker_reports_owner_qualified_archive(self):
        self.write_readme(
            "# Parent\n\n<!-- repository-readme-owner: Parent-Owner/Parent-Repo -->\n"
        )

        errors, warnings = readme_ownership.audit_readme(
            self.root,
            "acme/child",
        )

        self.assertEqual([], warnings)
        self.assertEqual(1, len(errors))
        self.assertIn(
            "docs/inheritance/readmes/parent-owner/parent-repo.md",
            errors[0],
        )

    def test_ownership_mismatch_directs_the_governance_re_audit(self):
        """An identity change is detected here and nowhere else in `make doctor`.

        The account move that produced ADR-0019 left the new repository with no branch
        ruleset, because rulesets and repository settings live on GitHub rather than in
        the history that moved. This marker mismatch is the signal that fires at that
        moment, so it has to name the governance check.
        """
        self.write_readme(
            "# Parent\n\n<!-- repository-readme-owner: former-owner/foundation -->\n"
        )

        errors, warnings = readme_ownership.audit_readme(
            self.root,
            "acme/child",
        )

        self.assertEqual([], warnings)
        self.assertEqual(1, len(errors))
        self.assertIn("scripts/github_governance.py audit --repo acme/child", errors[0])
        self.assertIn("do not travel with the git history", errors[0])

    def test_legacy_missing_marker_can_warn_without_failing(self):
        self.write_readme("# Legacy child\n")

        errors, warnings = readme_ownership.audit_readme(
            self.root,
            "acme/child",
            allow_missing_marker=True,
        )

        self.assertEqual([], errors)
        self.assertEqual(1, len(warnings))

    def test_missing_marker_fails_when_not_allowed(self):
        self.write_readme("# New child\n")

        errors, warnings = readme_ownership.audit_readme(
            self.root,
            "acme/child",
        )

        self.assertEqual([], warnings)
        self.assertEqual(1, len(errors))

    def test_missing_readme_fails(self):
        errors, warnings = readme_ownership.audit_readme(
            self.root,
            "acme/child",
        )

        self.assertEqual(["README.md is missing"], errors)
        self.assertEqual([], warnings)

    def test_multiple_markers_fail(self):
        self.write_readme(
            "<!-- repository-readme-owner: acme/child -->\n"
            "<!-- repository-readme-owner: acme/child -->\n"
        )

        errors, warnings = readme_ownership.audit_readme(
            self.root,
            "acme/child",
        )

        self.assertEqual([], warnings)
        self.assertEqual(1, len(errors))
        self.assertIn("expected exactly one", errors[0])

    def test_malformed_marker_fails_even_for_legacy_mode(self):
        self.write_readme("<!-- repository-readme-owner: invalid -->\n")

        errors, warnings = readme_ownership.audit_readme(
            self.root,
            "acme/child",
            allow_missing_marker=True,
        )

        self.assertEqual([], warnings)
        self.assertEqual(
            ["README.md contains a malformed repository-readme-owner marker"],
            errors,
        )


if __name__ == "__main__":
    unittest.main()
