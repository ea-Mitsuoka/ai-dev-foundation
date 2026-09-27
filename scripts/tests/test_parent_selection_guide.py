import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).parents[2]
USAGE_GUIDE = REPOSITORY_ROOT / "docs" / "foundation" / "guides" / "usage.md"
JAPANESE_GUIDE = REPOSITORY_ROOT / "docs" / "foundation" / "guides" / "usage.ja.md"


class ParentSelectionGuideTest(unittest.TestCase):
    def test_english_guide_defines_parent_selection_and_initialization(self):
        content = " ".join(USAGE_GUIDE.read_text(encoding="utf-8").split())

        for contract in (
            "Choose the direct parent template",
            "primary deliverable",
            "terraform-gcp-template",
            "Incidental use of Terraform or Google Cloud",
            "Do not bypass an applicable intermediate template",
            "manifest.json",
            "lock.json",
            "agent-profile.json",
            "TEMPLATE_SYNC_ENABLED",
            "task doctor",
        ):
            with self.subTest(contract=contract):
                self.assertIn(contract, content)

    def test_japanese_guide_matches_the_parent_selection_contract(self):
        content = " ".join(JAPANESE_GUIDE.read_text(encoding="utf-8").split())

        for contract in (
            "直接の親テンプレートを選ぶ",
            "主要な成果物",
            "terraform-gcp-template",
            "TerraformやGoogle Cloudを付随的に使うだけ",
            "適用可能な中間テンプレートを飛ばさない",
            "TEMPLATE_SYNC_ENABLED",
        ):
            with self.subTest(contract=contract):
                self.assertIn(contract, content)


if __name__ == "__main__":
    unittest.main()
