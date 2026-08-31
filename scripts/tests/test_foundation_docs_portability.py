import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).parents[2]
TEMPLATE_CHECK = REPOSITORY_ROOT / "scripts" / "template-check.sh"
AI_GUIDE = (
    REPOSITORY_ROOT
    / "docs"
    / "foundation"
    / "guides"
    / "ai-instruction-files.ja.md"
)
PROJECT_DOCUMENTATION_GUIDE = (
    REPOSITORY_ROOT
    / "docs"
    / "foundation"
    / "guides"
    / "project-documentation.md"
)


class FoundationDocsPortabilityTest(unittest.TestCase):
    def test_root_check_does_not_classify_legacy_children_by_manifest_absence(self):
        script = TEMPLATE_CHECK.read_text(encoding="utf-8")

        self.assertNotIn('if [ ! -f .github/inheritance/manifest.json ]; then', script)
        self.assertIn("ea-Mitsuoka/ai-dev-foundation", script)

    def test_child_doctor_validates_the_local_inheritance_contract(self):
        script = TEMPLATE_CHECK.read_text(encoding="utf-8")

        self.assertIn('if [ -f ".github/inheritance/manifest.json" ]; then', script)
        self.assertIn(
            "python3 scripts/template_inheritance.py validate --root .",
            script,
        )

    def test_child_doctor_rejects_unresolved_makefile_profiles(self):
        script = TEMPLATE_CHECK.read_text(encoding="utf-8")

        self.assertIn("python3 scripts/makefile_profile.py", script)
        self.assertIn("--allow-template-placeholders", script)
        self.assertIn("repository-readme-owner: ea-Mitsuoka/ai-dev-foundation", script)

    def test_optional_example_module_is_not_a_required_local_link(self):
        guide = AI_GUIDE.read_text(encoding="utf-8")

        self.assertNotIn(
            "[src/modules/catalog/MODULE.md](../../../src/modules/catalog/MODULE.md)",
            guide,
        )
        self.assertIn("`src/modules/catalog/MODULE.md`", guide)

    def test_doc_014_links_to_its_current_authority(self):
        guide = PROJECT_DOCUMENTATION_GUIDE.read_text(encoding="utf-8")

        self.assertIn(
            "[DOC-014](../../../.ai/project-document-maintenance.md"
            "#doc-014-root-readme-ownership)",
            guide,
        )
        self.assertNotIn(
            "[DOC-014](../../../.ai/documentation.md"
            "#doc-014-root-readme-ownership)",
            guide,
        )


if __name__ == "__main__":
    unittest.main()
