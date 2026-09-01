import tempfile
import unittest
from pathlib import Path

from scripts.pr_size_policy import (
    DECOMPOSITION_CHECKPOINT_LINES,
    decomposition_checkpoints,
    evaluate_size,
    summarize_lockfiles,
)


class PullRequestSizePolicyTests(unittest.TestCase):
    def test_excludes_lockfile_churn_from_hard_limit(self) -> None:
        lockfile_stats = summarize_lockfiles(
            [
                {"filename": "package.json", "additions": 15, "deletions": 58},
                {"filename": "pnpm-lock.yaml", "additions": 300, "deletions": 700},
            ]
        )

        result = evaluate_size(315, 758, 2, lockfile_stats)

        self.assertEqual(result.changed_lines, 73)
        self.assertEqual(result.changed_files, 1)
        self.assertEqual(result.level, "ok")

    def test_recognizes_nested_lockfiles_across_paginated_responses(self) -> None:
        payload = [
            [{"filename": "infra/.terraform.lock.hcl", "additions": 8, "deletions": 3}],
            [{"filename": "services/api/poetry.lock", "additions": 10, "deletions": 5}],
        ]

        self.assertEqual(summarize_lockfiles(payload), (18, 8, 2))

    def test_does_not_exclude_similarly_named_source_files(self) -> None:
        payload = [
            {"filename": "docs/pnpm-lock.yaml.md", "additions": 1000, "deletions": 0},
            {"filename": "src/package-lock.json.ts", "additions": 1000, "deletions": 0},
        ]

        self.assertEqual(summarize_lockfiles(payload), (0, 0, 0))

    def test_rejects_malformed_file_statistics(self) -> None:
        with self.assertRaises(ValueError):
            summarize_lockfiles(
                [{"filename": "pnpm-lock.yaml", "additions": "300", "deletions": 0}]
            )

    def test_rejects_exclusions_larger_than_aggregate_statistics(self) -> None:
        with self.assertRaises(ValueError):
            evaluate_size(10, 10, 1, (11, 0, 1))

    def test_preserves_soft_and_hard_limits(self) -> None:
        self.assertEqual(evaluate_size(401, 0, 1, (0, 0, 0)).level, "soft")
        self.assertEqual(evaluate_size(801, 0, 1, (0, 0, 0)).level, "hard")

    def test_reports_changed_source_beyond_the_decomposition_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            grown = root / "scripts/template_inheritance.py"
            small = root / "scripts/pr_size_policy.py"
            grown.parent.mkdir(parents=True)
            grown.write_text("value = 1\n" * 1_200, encoding="utf-8")
            small.write_text("value = 1\n" * 100, encoding="utf-8")

            checkpoints = decomposition_checkpoints(
                [
                    {"filename": "scripts/template_inheritance.py"},
                    {"filename": "scripts/pr_size_policy.py"},
                ],
                root,
            )

        self.assertEqual([("scripts/template_inheritance.py", 1_200)], checkpoints)

    def test_counts_only_non_blank_lines_against_the_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            padded = root / "app.py"
            padded.write_text("value = 1\n\n" * DECOMPOSITION_CHECKPOINT_LINES, encoding="utf-8")

            at_threshold = decomposition_checkpoints([{"filename": "app.py"}], root)

            padded.write_text(
                "value = 1\n\n" * (DECOMPOSITION_CHECKPOINT_LINES + 1),
                encoding="utf-8",
            )
            beyond_threshold = decomposition_checkpoints([{"filename": "app.py"}], root)

        self.assertEqual([], at_threshold)
        self.assertEqual(
            [("app.py", DECOMPOSITION_CHECKPOINT_LINES + 1)],
            beyond_threshold,
        )

    def test_exempts_generated_declarative_and_fixture_content(self) -> None:
        exempt = (
            "openapi.yaml",
            "package-lock.json",
            "db/migrations/0001_create_users.py",
            "tests/fixtures/large_payload.py",
            "src/generated/client.ts",
            "src/schema.gen.ts",
            "proto/service_pb2.py",
            "vendor/library/core.go",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for filename in exempt:
                target = root / filename
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("value = 1\n" * 2_000, encoding="utf-8")

            checkpoints = decomposition_checkpoints(
                [{"filename": filename} for filename in exempt],
                root,
            )

        self.assertEqual([], checkpoints)

    def test_ignores_removed_and_absent_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            removed = root / "legacy.py"
            removed.write_text("value = 1\n" * 2_000, encoding="utf-8")

            checkpoints = decomposition_checkpoints(
                [
                    {"filename": "legacy.py", "status": "removed"},
                    {"filename": "renamed_away.py"},
                ],
                root,
            )

        self.assertEqual([], checkpoints)

    def test_refuses_absolute_and_traversing_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            outside = root / "outside.py"
            outside.write_text("value = 1\n" * 2_000, encoding="utf-8")
            inside = root / "package"
            inside.mkdir()

            checkpoints = decomposition_checkpoints(
                [
                    {"filename": "package/../outside.py"},
                    {"filename": str(outside)},
                ],
                inside,
            )

        self.assertEqual([], checkpoints)

    def test_rejects_file_entries_without_a_filename(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            with self.assertRaises(ValueError):
                decomposition_checkpoints(
                    [{"additions": 1}],
                    Path(temporary_directory),
                )


if __name__ == "__main__":
    unittest.main()
