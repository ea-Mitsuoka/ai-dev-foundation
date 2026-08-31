import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).parents[2]


class LocalWorkflowActionsTest(unittest.TestCase):
    CASES = {
        "ai-review": {
            "workflow": ".github/workflows/ai-review.yml",
            "action": "scripts/actions/ai-review/action.yml",
            "implementation": "anthropics/claude-code-action@",
            "pinned_action": (
                "anthropics/claude-code-action@"
                "fa7e2f0a29a126f0b81cdcf360561b36e44cf608"
            ),
        },
        "container": {
            "workflow": ".github/workflows/container.yml",
            "action": "scripts/actions/container-scan/action.yml",
            "implementation": "docker build",
            "pinned_action": (
                "aquasecurity/trivy-action@"
                "ed142fd0673e97e23eac54620cfb913e5ce36c25"
            ),
        },
        "dast": {
            "workflow": ".github/workflows/dast.yml",
            "action": "scripts/actions/dast-baseline/action.yml",
            "implementation": "zaproxy/action-baseline@",
            "pinned_action": (
                "zaproxy/action-baseline@"
                "de8ad967d3548d44ef623df22cf95c3b0baf8b25"
            ),
        },
        "labels": {
            "workflow": ".github/workflows/labels-sync.yml",
            "action": "scripts/actions/labels-sync/action.yml",
            "implementation": "crazy-max/ghaction-github-labeler@",
            "pinned_action": (
                "crazy-max/ghaction-github-labeler@"
                "548a7c3603594ec17c819e1239f281a3b801ab4d"
            ),
        },
    }

    def test_protected_callers_keep_boundaries_and_delegate_implementation(self):
        for name, case in self.CASES.items():
            with self.subTest(name=name):
                workflow = (REPOSITORY_ROOT / case["workflow"]).read_text(
                    encoding="utf-8"
                )
                local_action = (
                    f"uses: ./{case['action'].removesuffix('/action.yml')}"
                )
                self.assertIn("permissions:", workflow)
                self.assertNotIn("uses: ea-Mitsuoka/ai-dev-foundation/", workflow)
                if local_action in workflow:
                    self.assertIn("actions/checkout@", workflow)
                    self.assertNotIn(case["implementation"], workflow)
                else:
                    self.assertIn(case["pinned_action"], workflow)

    def test_synchronized_local_actions_hold_pinned_implementations(self):
        for name, case in self.CASES.items():
            with self.subTest(name=name):
                action_path = REPOSITORY_ROOT / case["action"]
                self.assertTrue(action_path.is_file())
                action = action_path.read_text(encoding="utf-8")
                self.assertIn("using: composite", action)
                self.assertIn(case["pinned_action"], action)

    def test_container_caller_runs_when_local_implementation_changes(self):
        workflow = (
            REPOSITORY_ROOT / ".github" / "workflows" / "container.yml"
        ).read_text(encoding="utf-8")

        if "uses: ./scripts/actions/container-scan" in workflow:
            self.assertIn('"scripts/actions/container-scan/**"', workflow)
        else:
            self.assertIn("docker build", workflow)

    def test_ai_review_caller_keeps_opt_in_permissions_and_secret_boundary(self):
        workflow = (
            REPOSITORY_ROOT / ".github" / "workflows" / "ai-review.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("vars.ENABLE_AI_REVIEW == 'true'", workflow)
        self.assertIn("pull-requests: write", workflow)
        if "uses: ./scripts/actions/ai-review" in workflow:
            self.assertIn(
                "anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}", workflow
            )
            self.assertIn(
                "pull-request-number: ${{ github.event.pull_request.number }}",
                workflow,
            )
        else:
            self.assertIn(
                "anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}", workflow
            )
            self.assertIn("github.event.pull_request.number", workflow)

    def test_scorecard_caller_keeps_security_permissions_and_verified_steps(self):
        workflow = (
            REPOSITORY_ROOT / ".github" / "workflows" / "scorecard.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("security-events: write", workflow)
        self.assertIn("id-token: write", workflow)
        self.assertIn("persist-credentials: false", workflow)
        action_uses = [
            line.strip().removeprefix("- uses: ").split(maxsplit=1)[0]
            for line in workflow.splitlines()
            if line.strip().startswith("- uses: ")
        ]
        self.assertEqual(
            [
                "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803",
                "ossf/scorecard-action@"
                "4eaacf0543bb3f2c246792bd56e8cdeffafb205a",
                "github/codeql-action/upload-sarif@"
                "5595ccaf912efad79be6eef63a5619ff05969be3",
            ],
            action_uses,
        )
        self.assertFalse(
            (
                REPOSITORY_ROOT
                / "scripts"
                / "actions"
                / "scorecard"
                / "action.yml"
            ).exists()
        )

    def test_release_callers_keep_boundaries_and_delegate_implementations(self):
        workflow = (
            REPOSITORY_ROOT / ".github" / "workflows" / "release.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("contents: write", workflow)
        self.assertIn("pull-requests: write", workflow)
        self.assertIn("id-token: write", workflow)
        self.assertIn("attestations: write", workflow)
        self.assertIn("if: needs.release-please.outputs.release_created == 'true'", workflow)
        self.assertIn("ref: ${{ needs.release-please.outputs.tag_name }}", workflow)
        if "uses: ./scripts/actions/release-please" in workflow:
            self.assertIn("uses: ./scripts/actions/release-gates", workflow)
            self.assertNotIn("googleapis/release-please-action@", workflow)
            self.assertNotIn("aquasecurity/trivy-action@", workflow)
        else:
            self.assertIn(
                "googleapis/release-please-action@"
                "45996ed1f6d02564a971a2fa1b5860e934307cf7",
                workflow,
            )
            self.assertIn(
                "aquasecurity/trivy-action@"
                "ed142fd0673e97e23eac54620cfb913e5ce36c25",
                workflow,
            )

    def test_release_actions_preserve_outputs_and_pinned_gates(self):
        release_please = (
            REPOSITORY_ROOT
            / "scripts"
            / "actions"
            / "release-please"
            / "action.yml"
        ).read_text(encoding="utf-8")
        release_gates = (
            REPOSITORY_ROOT / "scripts" / "actions" / "release-gates" / "action.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("release_created:", release_please)
        self.assertIn("tag_name:", release_please)
        self.assertIn(
            "googleapis/release-please-action@"
            "45996ed1f6d02564a971a2fa1b5860e934307cf7",
            release_please,
        )
        self.assertIn(
            "aquasecurity/trivy-action@"
            "ed142fd0673e97e23eac54620cfb913e5ce36c25",
            release_gates,
        )
        self.assertIn("actions/attest-build-provenance@", release_gates)

    def test_main_push_release_attaches_sbom_to_release_please_tag(self):
        workflow = (
            REPOSITORY_ROOT / ".github" / "workflows" / "release.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("name: Attach generated SBOM to GitHub Release", workflow)
        self.assertIn(
            "RELEASE_TAG: ${{ needs.release-please.outputs.tag_name }}", workflow
        )
        self.assertIn("SBOM_PATH: sbom.spdx.json", workflow)
        self.assertIn('test -n "$RELEASE_TAG"', workflow)
        self.assertIn('test -s "$SBOM_PATH"', workflow)
        self.assertIn(
            'gh release upload "$RELEASE_TAG" "$SBOM_ASSET" --clobber', workflow
        )
        self.assertNotIn("RELEASE_TAG: ${{ github.ref_name }}", workflow)


if __name__ == "__main__":
    unittest.main()
