import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
PUBLIC_ONLY = "if: github.event.repository.visibility == 'public'"
WORKFLOWS = ROOT / ".github" / "workflows"
REPOSITORY_READ = ("read", "write")
ALL_SCOPES = ("read-all", "write-all")


def _reads_the_repository(job: dict) -> bool:
    """True when the job checks out the repository or runs an in-repository action."""
    for step in job.get("steps") or []:
        uses = str(step.get("uses", ""))
        if "actions/checkout" in uses or uses.startswith("./"):
            return True
    return False


def _grants_contents_read(effective) -> bool:
    if effective in ALL_SCOPES:
        return True
    return isinstance(effective, dict) and effective.get("contents") in REPOSITORY_READ


class PrivateRepositoryWorkflowTest(unittest.TestCase):
    def test_jobs_that_read_the_repository_keep_contents_permission(self) -> None:
        """A job-level `permissions:` block replaces the workflow-level defaults
        outright, so a job that lists only its extra scopes silently drops
        `contents`. Cloning a public repository still succeeds without it, which
        hides the mistake until the same workflow runs in a private descendant and
        checkout fails with `Repository not found`."""
        for path in sorted(WORKFLOWS.glob("*.yml")):
            workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
            workflow_scopes = workflow.get("permissions")
            for name, job in (workflow.get("jobs") or {}).items():
                if not _reads_the_repository(job):
                    continue
                job_scopes = job.get("permissions")
                effective = job_scopes if job_scopes is not None else workflow_scopes
                with self.subTest(workflow=path.name, job=name):
                    self.assertTrue(
                        _grants_contents_read(effective),
                        f"{path.name}:{name} checks out the repository but its "
                        f"effective permissions are {effective!r}",
                    )

    def test_code_scanning_jobs_are_public_only(self) -> None:
        for path, job in (
            (".github/workflows/codeql.yml", "analyze"),
            (".github/workflows/scorecard.yml", "analysis"),
        ):
            with self.subTest(path=path):
                workflow = (ROOT / path).read_text(encoding="utf-8")
                job_body = workflow.split(f"  {job}:\n", maxsplit=1)[1]

                self.assertIn(f"    {PUBLIC_ONLY}\n", job_body)

    def test_only_the_plan_limited_release_step_is_public_only(self) -> None:
        workflow = (ROOT / ".github/workflows/release.yml").read_text(
            encoding="utf-8"
        )
        release_gates = (
            ROOT / "scripts/actions/release-gates/action.yml"
        ).read_text(encoding="utf-8")

        self.assertNotIn(PUBLIC_ONLY, workflow)
        self.assertIn(
            "if: github.event.repository.visibility == 'public' && "
            "hashFiles('dist/**') != ''",
            release_gates,
        )

    def test_portable_security_scans_remain_enabled_for_private_repositories(self) -> None:
        workflow = (ROOT / ".github/workflows/security.yml").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("repository.visibility", workflow)


if __name__ == "__main__":
    unittest.main()
