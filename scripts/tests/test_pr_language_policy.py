import json
import tempfile
import unittest
from pathlib import Path

from scripts.pr_language_policy import (
    EXCEPTION_LABEL,
    MIN_JAPANESE_CHARACTERS,
    PolicyError,
    classify_repository,
    evaluate,
    main,
    measure,
    prose,
)

REPOSITORY_ROOT = Path(__file__).parents[2]
# ADR-0011 marker that only the canonical foundation root carries in its README.
FOUNDATION_README_OWNER = "<!-- repository-readme-owner: ea-Mitsuoka/ai-dev-foundation -->"
FOUNDATION = "acme/ai-foundation"
TEMPLATE = "acme/stack-template"
LEAF = "acme/product"

# Japanese script only — no punctuation, spaces, or Latin letters — so every character
# counts and a prefix slice removes exactly one counted character per position.
JAPANESE_60 = (
    "この変更は認証境界を整理し設定の読込順序を明示して失敗時の挙動を記録する"
    "利用先リポジトリの本文は日本語で書き見出しは英語のまま残す"
    "テストも同じ変更で追加する"
)
assert measure(JAPANESE_60).japanese == len(JAPANESE_60) >= MIN_JAPANESE_CHARACTERS


def profile(repository, *, template=None):
    inputs = [
        {"layer": "foundation", "repository": FOUNDATION, "path": ".ai/contracts/foundation/agent-entry.md"}
    ]
    if template:
        inputs.append(
            {"layer": "template", "repository": template, "path": f".ai/contracts/templates/acme/{template.split('/')[1]}/agent-overlay.md"}
        )
    inputs.append({"layer": "project", "repository": repository, "path": ".ai/project/agent-overlay.md"})
    return {"schema_version": 1, "authority_policy": "strengthen-only", "inputs": inputs}


class RepositoryFixture:
    def __init__(self, root: Path):
        self.root = root

    def write(self, relative_path: str, content: str) -> Path:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def profile(self, repository, **kwargs):
        self.write(".github/inheritance/agent-profile.json", json.dumps(profile(repository, **kwargs)))

    def foundation_export(self, repository):
        self.write(
            ".ai/contracts/foundation/inheritance-export.json",
            json.dumps({"schema_version": 1, "repository": repository}),
        )


class ClassificationTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.fixture = RepositoryFixture(Path(self.temporary_directory.name))

    def test_the_foundation_root_is_the_repository_that_publishes_the_foundation_export(self):
        self.fixture.profile(FOUNDATION)
        self.fixture.foundation_export(FOUNDATION)

        self.assertEqual("root", classify_repository(self.fixture.root))

    def test_a_template_publishes_its_own_owner_qualified_contract_root(self):
        self.fixture.profile(TEMPLATE)
        self.fixture.foundation_export(FOUNDATION)
        self.fixture.write(".ai/contracts/templates/acme/stack-template/agent-overlay.md", "# overlay\n")

        self.assertEqual("template", classify_repository(self.fixture.root))

    def test_a_repository_that_only_consumes_contracts_is_a_leaf(self):
        self.fixture.profile(LEAF, template=TEMPLATE)
        self.fixture.foundation_export(FOUNDATION)
        self.fixture.write(".ai/contracts/templates/acme/stack-template/agent-overlay.md", "# overlay\n")

        self.assertEqual("leaf", classify_repository(self.fixture.root))

    def test_owner_case_in_the_profile_does_not_change_the_answer(self):
        self.fixture.profile("Acme/stack-template")
        self.fixture.write(".ai/contracts/templates/acme/stack-template/agent-overlay.md", "# overlay\n")

        self.assertEqual("template", classify_repository(self.fixture.root))

    def test_a_missing_or_ambiguous_project_layer_is_an_error_not_a_leaf(self):
        self.fixture.write(".github/inheritance/agent-profile.json", json.dumps({"inputs": []}))

        with self.assertRaises(PolicyError):
            classify_repository(self.fixture.root)

    def test_this_repository_classifies_from_its_own_contract(self):
        # This test is inherited: at the canonical foundation root the answer is "root";
        # in every descendant it must still classify (never raise) as template or leaf.
        scope = classify_repository(REPOSITORY_ROOT)

        if FOUNDATION_README_OWNER in (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8"):
            self.assertEqual("root", scope)
        else:
            self.assertIn(scope, {"template", "leaf"})


class ProseTest(unittest.TestCase):
    def test_removes_everything_that_carries_no_authored_language(self):
        body = (
            "## What & why\n"
            "<!-- 2-5 sentences in English -->\n"
            "説明。\n"
            "```bash\nmake test  # English inside code\n```\n"
            "`inline English` と https://example.com/english/path\n"
            "| Package | Purpose |\n|---|---|\n| left-pad | padding |\n"
            "- [x] Local (inside one module)\n"
            "Refs: #12\n"
        )

        text = prose(body)

        for removed in ("What & why", "sentences in English", "make test", "inline English", "example.com", "left-pad"):
            self.assertNotIn(removed, text)
        self.assertIn("説明", text)
        self.assertIn("Local (inside one module)", text)  # checklist text stays, marker goes
        self.assertIn("Refs", text)

    def test_measures_japanese_script_and_latin_letters_only(self):
        result = measure("テスト test 123 ！？ カナ 漢字")

        self.assertEqual(result.japanese, 7)
        self.assertEqual(result.latin, 4)
        self.assertAlmostEqual(result.share, 7 / 11)


class EvaluationTest(unittest.TestCase):
    def test_root_and_template_repositories_pass_with_an_english_body(self):
        for scope in ("root", "template"):
            with self.subTest(scope=scope):
                verdict = evaluate(scope, "Purely English body.", "someone", frozenset())
                self.assertEqual(verdict.level, "pass")

    def test_a_leaf_passes_a_japanese_body(self):
        verdict = evaluate("leaf", f"## What & why\n\n{JAPANESE_60}\n", "someone", frozenset())

        self.assertEqual(verdict.level, "pass")

    def test_a_leaf_fails_an_english_body(self):
        verdict = evaluate("leaf", "This body explains everything, in English only.", "someone", frozenset())

        self.assertEqual(verdict.level, "fail")

    def test_one_japanese_character_is_not_enough(self):
        verdict = evaluate("leaf", "Mostly English with a token 字 at the end.", "someone", frozenset())

        self.assertEqual(verdict.level, "fail")

    def test_enough_characters_but_a_minority_share_fails(self):
        english = " ".join(["This sentence pads the body with English prose."] * 12)

        verdict = evaluate("leaf", f"{english}\n{JAPANESE_60}\n", "someone", frozenset())

        self.assertEqual(verdict.level, "fail")

    def test_one_character_short_of_the_minimum_fails(self):
        body = JAPANESE_60[: MIN_JAPANESE_CHARACTERS - 1]
        self.assertEqual(measure(body).japanese, MIN_JAPANESE_CHARACTERS - 1)

        self.assertEqual(evaluate("leaf", body, "someone", frozenset()).level, "fail")

    def test_trusted_bots_are_exempt_by_exact_login(self):
        for login in ("github-actions[bot]", "dependabot[bot]", "renovate[bot]"):
            with self.subTest(login=login):
                self.assertEqual(evaluate("leaf", "English.", login, frozenset()).level, "exempt")
        self.assertEqual(evaluate("leaf", "English.", "github-actions", frozenset()).level, "fail")

    def test_the_reviewer_label_downgrades_a_failure_to_a_warning(self):
        verdict = evaluate("leaf", "English with an approved reason.", "someone", frozenset({EXCEPTION_LABEL}))

        self.assertEqual(verdict.level, "warn")
        self.assertIn(EXCEPTION_LABEL, verdict.reason)

    def test_the_label_does_not_change_a_passing_body(self):
        verdict = evaluate("leaf", JAPANESE_60, "someone", frozenset({EXCEPTION_LABEL}))

        self.assertEqual(verdict.level, "pass")


class CommandLineTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.fixture = RepositoryFixture(Path(self.temporary_directory.name))
        self.fixture.profile(LEAF, template=TEMPLATE)
        self.fixture.foundation_export(FOUNDATION)

    def run_policy(self, body, author="someone", labels=None):
        body_file = self.fixture.write("pr-body.md", body)
        argv = ["--root", str(self.fixture.root), "--body-file", str(body_file), "--author", author]
        if labels is not None:
            labels_file = self.fixture.write("pr-labels.json", json.dumps(labels))
            argv += ["--labels-json", str(labels_file)]
        return main(argv)

    def test_exit_codes_follow_the_verdict(self):
        self.assertEqual(0, self.run_policy(JAPANESE_60))
        self.assertEqual(1, self.run_policy("English only."))
        self.assertEqual(0, self.run_policy("English only.", author="renovate[bot]"))

    def test_labels_accept_plain_names_and_github_label_objects(self):
        self.assertEqual(0, self.run_policy("English only.", labels=[EXCEPTION_LABEL]))
        self.assertEqual(0, self.run_policy("English only.", labels=[{"name": EXCEPTION_LABEL, "color": "ededed"}]))
        self.assertEqual(1, self.run_policy("English only.", labels=["type:docs"]))

    def test_unreadable_inputs_are_reported_as_invalid_not_as_a_language_failure(self):
        labels_file = self.fixture.write("pr-labels.json", "{not json")
        body_file = self.fixture.write("pr-body.md", "English only.")

        code = main(["--root", str(self.fixture.root), "--body-file", str(body_file), "--author", "x", "--labels-json", str(labels_file)])

        self.assertEqual(2, code)


if __name__ == "__main__":
    unittest.main()
