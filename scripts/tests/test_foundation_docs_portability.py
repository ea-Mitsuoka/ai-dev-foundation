import json
import re
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


INHERITANCE_EXPORT = REPOSITORY_ROOT / ".ai" / "contracts" / "foundation" / "inheritance-export.json"
OPTIONAL_REPOSITORY_OWNED_ROOTS = ("profiles/", "src/", "tests/")
RELATIVE_LINK = re.compile(r"\]\((?!https?://|mailto:|#)([^)#\s]+)")


def inherited_markdown_documents():
    export = json.loads(INHERITANCE_EXPORT.read_text(encoding="utf-8"))
    for declared in export["inherited_paths"]:
        path = REPOSITORY_ROOT / declared
        if path.is_dir():
            yield from sorted(path.rglob("*.md"))
        elif path.suffix == ".md":
            yield path


class FoundationDocsPortabilityTest(unittest.TestCase):
    def test_inherited_documents_do_not_link_into_optional_repository_owned_paths(self):
        # ADR-0024: a descendant may delete profiles/, src/, and tests/; an inherited
        # document that links into them breaks that descendant's offline link check.
        offenders = []
        for document in inherited_markdown_documents():
            for match in RELATIVE_LINK.finditer(document.read_text(encoding="utf-8")):
                target = (document.parent / match.group(1)).resolve()
                try:
                    relative = target.relative_to(REPOSITORY_ROOT.resolve()).as_posix()
                except ValueError:
                    continue
                if relative.startswith(OPTIONAL_REPOSITORY_OWNED_ROOTS):
                    offenders.append(f"{document.relative_to(REPOSITORY_ROOT)} -> {relative}")
        self.assertEqual(offenders, [])

    def test_agent_entry_routes_to_the_inherited_make_target_contract(self):
        entry = (REPOSITORY_ROOT / ".ai" / "contracts" / "foundation" / "agent-entry.md").read_text(
            encoding="utf-8"
        )
        contract = REPOSITORY_ROOT / ".ai" / "contracts" / "foundation" / "make-targets.md"

        self.assertTrue(contract.is_file())
        self.assertIn(".ai/contracts/foundation/make-targets.md", entry)
        self.assertNotIn("profiles/README.md", entry)

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
