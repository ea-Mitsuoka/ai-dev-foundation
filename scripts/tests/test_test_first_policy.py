import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).parents[2]


def normalized(relative_path: str) -> str:
    return " ".join((REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8").split())


class TestFirstPolicyTest(unittest.TestCase):
    """ADR-0023: test-first slices, independent expected values, seams, glossary capture."""

    def test_testing_policy_states_tst_004_with_applicability_conditions(self):
        testing = normalized(".ai/testing.md")

        self.assertIn("## TST-004: Test-first slices", testing)
        for contract in (
            "one failing test for one behavior",
            "red → green, one slice at a time",
            "Applies when all three hold",
            "independent of the implementation",
            "Not required for documentation, mechanical configuration, generated code",
            "Name the seams the tests will observe at the MNT-001 design checkpoint",
            "ask the human only when a new public API shape",
            "restructuring existing code is a separate `refactor` change (COD-021, MNT-003)",
        ):
            with self.subTest(contract=contract):
                self.assertIn(contract, testing)

    def test_testing_policy_rejects_tautological_expected_values(self):
        testing = normalized(".ai/testing.md")

        self.assertIn("**Independent expected values**", testing)
        self.assertIn("tautological", testing)
        self.assertIn("does not satisfy GR-021", testing)

    def test_routes_reference_the_new_rules_where_they_apply(self):
        expected_references = {
            ".skills/feature.skill.md": ("TST-004", "TST-010", "COD-021"),
            ".skills/test.skill.md": ("tautological", "TST-010"),
            ".ai/review-checklist.md": ("TST-004", "tautological test (TST-010)"),
            "docs/foundation/guides/ai-instruction-files.ja.md": (
                "TST-004",
                "TST-010",
                "確定した用語はその場で `docs/glossary.md` へ",
            ),
        }

        for relative_path, markers in expected_references.items():
            content = normalized(relative_path)
            with self.subTest(path=relative_path):
                for marker in markers:
                    self.assertIn(marker, content)

    def test_interview_skills_capture_confirmed_terms_in_the_glossary(self):
        requirements = normalized(".skills/requirements.skill.md")
        architecture = normalized(".skills/architecture.skill.md")

        for contract in (
            "record it in `docs/glossary.md` at that moment",
            "challenge wording that conflicts with an existing entry",
            "Write only confirmed meanings; proposals stay in the conversation",
        ):
            with self.subTest(contract=contract):
                self.assertIn(contract, requirements)
        self.assertIn("record it in the glossary at that moment", architecture)
        self.assertIn("challenge wording that conflicts with an existing entry", architecture)

    def test_adr_routing_outside_gr_022_never_waives_gr_022(self):
        architecture = normalized(".skills/architecture.skill.md")

        self.assertIn("Outside GR-022 scope: ADR or decision log?", architecture)
        self.assertIn(
            "hard to reverse, surprising without context, and the result of a real trade-off",
            architecture,
        )
        self.assertIn("This routing never waives GR-022", architecture)

    def test_foundation_glossary_defines_seam_and_tautological_test(self):
        glossary = normalized("docs/foundation/glossary.md")

        self.assertIn("| Seam |", glossary)
        self.assertIn("| Tautological test |", glossary)

    def test_no_implement_skill_or_context_document_is_introduced(self):
        skills = {path.name for path in (REPOSITORY_ROOT / ".skills").glob("*.skill.md")}

        self.assertNotIn("implement.skill.md", skills)
        self.assertNotIn("tdd.skill.md", skills)
        self.assertFalse((REPOSITORY_ROOT / "CONTEXT.md").exists())


if __name__ == "__main__":
    unittest.main()
