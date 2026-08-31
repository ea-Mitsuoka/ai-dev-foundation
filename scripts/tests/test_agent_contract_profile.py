import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "template_inheritance.py"
SPEC = importlib.util.spec_from_file_location("agent_contract_profile", MODULE_PATH)
inheritance = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inheritance)

FOUNDATION = "acme/ai-foundation"
PARENT = "acme/stack-template"
PROJECT = "acme/product"
COMMIT = "a" * 40
PROFILE_PATH = ".github/inheritance/agent-profile.json"
FOUNDATION_ENTRY_PATH = ".ai/contracts/foundation/agent-entry.md"
REPOSITORY_ROOT = Path(__file__).parents[2]
FOUNDATION_README_OWNER = (
    "<!-- repository-readme-owner: ea-Mitsuoka/ai-dev-foundation -->"
)
FOUNDATION_ROOT_INPUTS = [
    {
        "layer": "foundation",
        "repository": "ea-Mitsuoka/ai-dev-foundation",
        "path": FOUNDATION_ENTRY_PATH,
    },
    {
        "layer": "project",
        "repository": "ea-Mitsuoka/ai-dev-foundation",
        "path": ".ai/project/agent-overlay.md",
    },
]
REQUIRED_PROTECTED = [
    ".gitignore",
    ".github/governance/repository.json",
    ".github/inheritance/lock.json",
    ".github/inheritance/manifest.json",
    PROFILE_PATH,
    ".github/workflows/template-sync.yml",
    ".templatesyncignore",
    ".ai/project/",
]


def is_canonical_foundation_root(root):
    """Identify the canonical root without using its descendant-owned profile."""
    readme = root / "README.md"
    return readme.is_file() and FOUNDATION_README_OWNER in readme.read_text(
        encoding="utf-8"
    )


def profile_input(layer, repository, path):
    return {"layer": layer, "repository": repository, "path": path}


class AgentContractProfileTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name) / "child"
        self.root.mkdir()

    def write(self, relative_path, content):
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def write_contract(self, *, parent, inputs, inherited=None, protected=None):
        manifest = {
            "schema_version": 2,
            "parent": {"repository": parent, "branch": "main"},
            "lock_file": ".github/inheritance/lock.json",
            "inherited_paths": inherited or [
                ".ai/contracts/foundation/",
                ".ai/contracts/templates/",
            ],
            "protected_paths": protected or REQUIRED_PROTECTED,
        }
        lock = {
            "schema_version": 1,
            "parent": {"repository": parent, "commit": COMMIT},
        }
        profile = {
            "schema_version": 1,
            "authority_policy": "strengthen-only",
            "inputs": inputs,
        }
        self.write(".github/inheritance/manifest.json", json.dumps(manifest))
        self.write(".github/inheritance/lock.json", json.dumps(lock))
        self.write(PROFILE_PATH, json.dumps(profile))
        self.write(
            ".templatesyncignore",
            "\n".join(manifest["protected_paths"] + [".github/workflows/**"]) + "\n",
        )
        for item in inputs:
            self.write(item["path"], f"{item['layer']} contract\n")

    def test_direct_child_reports_foundation_then_project(self):
        inputs = [
            profile_input(
                "foundation", FOUNDATION, ".ai/contracts/foundation/agent-entry.md"
            ),
            profile_input("project", PROJECT, ".ai/project/agent-overlay.md"),
        ]
        self.write_contract(parent=FOUNDATION, inputs=inputs)

        result = inheritance.validate_inheritance(self.root)

        self.assertEqual(result["agent_contract"]["inputs"], inputs)
        self.assertEqual(result["agent_contract"]["authority_policy"], "strengthen-only")

    def test_descendant_root_is_not_canonical_foundation(self):
        inputs = [
            profile_input(
                "foundation", FOUNDATION, ".ai/contracts/foundation/agent-entry.md"
            ),
            profile_input("project", PROJECT, ".ai/project/agent-overlay.md"),
        ]
        self.write_contract(parent=FOUNDATION, inputs=inputs)
        self.write("README.md", "<!-- repository-readme-owner: acme/product -->\n")
        self.write("CLAUDE.md", "# Compatibility entry\n\nProject-specific entry.\n")

        self.assertFalse(is_canonical_foundation_root(self.root))

    def test_multi_level_child_preserves_parent_to_child_template_order(self):
        inputs = [
            profile_input(
                "foundation", FOUNDATION, ".ai/contracts/foundation/agent-entry.md"
            ),
            profile_input(
                "template",
                "acme/platform-template",
                ".ai/contracts/templates/acme/platform-template/agent-overlay.md",
            ),
            profile_input(
                "template",
                PARENT,
                ".ai/contracts/templates/acme/stack-template/agent-overlay.md",
            ),
            profile_input("project", PROJECT, ".ai/project/agent-overlay.md"),
        ]
        self.write_contract(parent=PARENT, inputs=inputs)

        result = inheritance.validate_inheritance(self.root)

        self.assertEqual(
            [item["repository"] for item in result["agent_contract"]["inputs"]],
            [FOUNDATION, "acme/platform-template", PARENT, PROJECT],
        )

    def test_profile_rejects_unsafe_authority_order_or_policy(self):
        valid_inputs = [
            profile_input(
                "foundation", FOUNDATION, ".ai/contracts/foundation/agent-entry.md"
            ),
            profile_input("project", PROJECT, ".ai/project/agent-overlay.md"),
        ]
        cases = (
            list(reversed(valid_inputs)),
            valid_inputs
            + [
                profile_input(
                    "template",
                    PARENT,
                    ".ai/contracts/templates/acme/stack-template/agent-overlay.md",
                )
            ],
        )
        for inputs in cases:
            with self.subTest(inputs=inputs):
                self.write_contract(parent=FOUNDATION, inputs=inputs)
                with self.assertRaisesRegex(inheritance.InheritanceError, "order"):
                    inheritance.validate_inheritance(self.root)

        self.write_contract(parent=FOUNDATION, inputs=valid_inputs)
        profile = json.loads((self.root / PROFILE_PATH).read_text(encoding="utf-8"))
        profile["authority_policy"] = "last-wins"
        self.write(PROFILE_PATH, json.dumps(profile))
        with self.assertRaisesRegex(inheritance.InheritanceError, "strengthen-only"):
            inheritance.validate_inheritance(self.root)

    def test_profile_rejects_missing_or_misowned_references(self):
        inputs = [
            profile_input(
                "foundation", FOUNDATION, ".ai/contracts/foundation/agent-entry.md"
            ),
            profile_input("project", PROJECT, ".ai/project/agent-overlay.md"),
        ]
        self.write_contract(parent=FOUNDATION, inputs=inputs)
        (self.root / inputs[0]["path"]).unlink()
        with self.assertRaisesRegex(inheritance.InheritanceError, "must be a file"):
            inheritance.validate_inheritance(self.root)

        self.write_contract(
            parent=FOUNDATION,
            inputs=inputs,
            inherited=["scripts/"],
        )
        with self.assertRaisesRegex(inheritance.InheritanceError, "must be inherited"):
            inheritance.validate_inheritance(self.root)

    def test_template_overlay_is_owner_qualified_and_ends_at_direct_parent(self):
        inputs = [
            profile_input(
                "foundation", FOUNDATION, ".ai/contracts/foundation/agent-entry.md"
            ),
            profile_input(
                "template",
                "acme/other-template",
                ".ai/contracts/templates/acme/other-template/agent-overlay.md",
            ),
            profile_input("project", PROJECT, ".ai/project/agent-overlay.md"),
        ]
        self.write_contract(parent=PARENT, inputs=inputs)
        with self.assertRaisesRegex(inheritance.InheritanceError, "direct parent"):
            inheritance.validate_inheritance(self.root)

        inputs[1]["repository"] = PARENT
        inputs[1]["path"] = ".ai/contracts/templates/wrong/path/agent-overlay.md"
        self.write_contract(parent=PARENT, inputs=inputs)
        with self.assertRaisesRegex(inheritance.InheritanceError, "owner-qualified"):
            inheritance.validate_inheritance(self.root)


class FoundationAgentEntryTest(unittest.TestCase):
    def test_entry_is_identity_free_and_routes_required_foundation_context(self):
        root = Path(__file__).parents[2]
        entry_path = root / FOUNDATION_ENTRY_PATH

        self.assertTrue(entry_path.is_file(), f"missing {FOUNDATION_ENTRY_PATH}")
        content = entry_path.read_text(encoding="utf-8")
        normalized_content = " ".join(content.split())
        for project_identity in (
            "{{PROJECT_NAME}}",
            "{{STACK}}",
            "ea-Mitsuoka",
            "ai-dev-foundation",
        ):
            self.assertNotIn(project_identity, content)
        for required_reference in (
            ".ai/guardrails.md",
            ".ai/README.md",
            ".ai/workflow.md",
            ".ai/review-checklist.md",
            "docs/development-handoff.md",
            "profiles/README.md",
            ".claude/README.md",
            "AGENTS.md",
            "Conventional Commits",
            "SemVer",
            "WF-090",
            "authentication",
            "payments",
            "data deletion",
            "production configuration",
            "spending money",
            "make setup",
            "make format",
            "make lint",
            "make test",
            "make test-unit",
            "make test-integration",
            "make coverage",
            "make build",
            "make run",
            "make security-scan",
            "make sbom",
            "make clean",
            "make doctor",
            "foundation",
            "template",
            "project",
            "strengthen-only",
        ):
            with self.subTest(required_reference=required_reference):
                self.assertIn(required_reference, normalized_content)


@unittest.skipUnless(
    is_canonical_foundation_root(REPOSITORY_ROOT),
    "canonical ai-dev-foundation root assertions",
)
class FoundationRootAgentAdapterTest(unittest.TestCase):
    def test_profile_orders_foundation_then_project(self):
        profile_path = REPOSITORY_ROOT / PROFILE_PATH
        self.assertTrue(profile_path.is_file(), f"missing {PROFILE_PATH}")
        profile = json.loads(profile_path.read_text(encoding="utf-8"))

        self.assertEqual(profile["schema_version"], 1)
        self.assertEqual(profile["authority_policy"], "strengthen-only")
        self.assertEqual(profile["inputs"], FOUNDATION_ROOT_INPUTS)
        for item in profile["inputs"]:
            with self.subTest(path=item["path"]):
                self.assertTrue((REPOSITORY_ROOT / item["path"]).is_file())

    def test_adapters_are_small_identity_free_and_bounded(self):
        adapters = {
            "CLAUDE.md": 50,
            "AGENTS.md": 30,
        }
        for path, maximum_lines in adapters.items():
            with self.subTest(path=path):
                content = (REPOSITORY_ROOT / path).read_text(encoding="utf-8")
                self.assertLessEqual(len(content.splitlines()), maximum_lines)
                for identity in (
                    "{{PROJECT_NAME}}",
                    "{{STACK}}",
                    "ea-Mitsuoka",
                    "ai-dev-foundation",
                    "Terraform on GCP",
                ):
                    self.assertNotIn(identity, content)

        claude = (REPOSITORY_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn(PROFILE_PATH, claude)
        self.assertIn("strengthen-only", claude)
        self.assertIn("listed order", claude)
        self.assertIn("must not recursively", claude)
        agents = (REPOSITORY_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("CLAUDE.md", agents)

    def test_project_overlay_contains_facts_not_reusable_workflow(self):
        overlay = REPOSITORY_ROOT / FOUNDATION_ROOT_INPUTS[-1]["path"]
        self.assertTrue(overlay.is_file())
        content = overlay.read_text(encoding="utf-8")
        self.assertIn("ea-Mitsuoka/ai-dev-foundation", content)
        self.assertIn("stack-agnostic", content)
        for reusable_rule in (".ai/workflow.md", "make ", "Stop and ask"):
            self.assertNotIn(reusable_rule, content)

    def test_profile_and_project_overlay_are_template_sync_protected(self):
        ignore_entries = set(
            (REPOSITORY_ROOT / ".templatesyncignore")
            .read_text(encoding="utf-8")
            .splitlines()
        )
        self.assertIn(PROFILE_PATH, ignore_entries)
        self.assertIn(".ai/project/**", ignore_entries)


if __name__ == "__main__":
    unittest.main()
