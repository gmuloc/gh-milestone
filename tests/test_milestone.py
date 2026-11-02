import contextlib
import io
import json
import runpy
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE = runpy.run_path(str(Path(__file__).resolve().parents[1] / "gh-milestone"))
run = MODULE["run"]
Error = MODULE["Error"]


def milestone(number=7, title="Release 7", state="open"):
    return {
        "number": number,
        "title": title,
        "state": state,
        "open_issues": 2,
        "closed_issues": 1,
        "due_on": None,
        "html_url": f"https://example.test/team/project/milestone/{number}",
    }


def issue(number, pr=False):
    item = {
        "number": number,
        "title": f"Item {number}",
        "state": "open",
        "html_url": f"https://example.test/{number}",
    }
    if pr:
        item["pull_request"] = {"merged_at": None}
    return item


class MilestoneTests(unittest.TestCase):
    def invoke(self, arguments, handler):
        calls = []

        def fake_gh(command, **kwargs):
            self.assertEqual(command[0], "gh")
            self.assertNotIn("shell", kwargs)
            calls.append(command)
            if command[1:3] == ["repo", "view"]:
                response = {
                    "nameWithOwner": "team/project",
                    "url": "https://example.test/team/project",
                }
            else:
                self.assertEqual(
                    command[1:6],
                    ["api", "--hostname", "example.test", "--method", "GET"],
                )
                parameters = dict(value.split("=", 1) for value in command[8::2])
                response = handler(command[6], parameters)
            return subprocess.CompletedProcess(command, 0, json.dumps(response), "")

        output = io.StringIO()
        with (
            patch("subprocess.run", side_effect=fake_gh),
            contextlib.redirect_stdout(output),
        ):
            self.assertEqual(run(arguments), 0)
        return output.getvalue(), calls

    def test_default_lists_open_milestones(self):
        def handler(path, query):
            self.assertEqual(path, "repos/team/project/milestones")
            self.assertEqual(query["state"], "open")
            return [milestone()]

        output, _ = self.invoke([], handler)
        self.assertIn("Release 7", output)

    def test_exact_title_resolution_includes_closed_milestones_and_quotes(self):
        title = 'Release "7" / candidate'

        def handler(path, query):
            if path.endswith("milestones"):
                self.assertEqual(query["state"], "all")
                return [milestone(title=title, state="closed")]
            self.assertEqual(query["milestone"], "7")
            self.assertEqual(query["state"], "open")
            return [issue(2), issue(3, pr=True)]

        output, _ = self.invoke(["issues", title, "--json"], handler)
        self.assertEqual([item["number"] for item in json.loads(output)], [2])

    def test_pr_filter_before_limit_and_pagination(self):
        def handler(path, query):
            if path.endswith("milestones/7"):
                return milestone()
            if query["page"] == "1":
                return [issue(number) for number in range(100)]
            return [issue(101, pr=True), issue(102), issue(103, pr=True)]

        output, calls = self.invoke(["prs", "7", "--limit", "1", "--json"], handler)
        self.assertEqual([item["number"] for item in json.loads(output)], [101])
        self.assertEqual(len(calls), 4)

    def test_milestone_title_pagination(self):
        def handler(path, query):
            if query["page"] == "1":
                return [milestone(number, f"Other {number}") for number in range(100)]
            return [milestone(title="Target")]

        output, _ = self.invoke(["view", "Target", "--json"], handler)
        self.assertEqual(json.loads(output)["title"], "Target")

    def test_repo_option_before_and_after_command(self):
        for arguments in (
            ["-R", "example.test/team/project", "list"],
            ["list", "-R", "example.test/team/project"],
        ):
            with self.subTest(arguments=arguments):
                _, calls = self.invoke(arguments, lambda *_: [])
                self.assertEqual(
                    calls[0][1:4], ["repo", "view", "example.test/team/project"]
                )

    def test_unknown_title_has_actionable_error(self):
        with self.assertRaisesRegex(Error, "was not found in team/project"):
            self.invoke(["view", "Missing"], lambda *_: [])

    def test_gh_errors_preserved(self):
        completed = subprocess.CompletedProcess(
            ["gh"], 1, "", "authentication required"
        )
        with (
            patch("subprocess.run", return_value=completed),
            self.assertRaisesRegex(Error, "authentication required"),
        ):
            run(["list"])

    def test_json_all_state_and_limit(self):
        def handler(path, query):
            self.assertEqual(query["state"], "all")
            return [milestone(1), milestone(2)]

        output, _ = self.invoke(
            ["list", "--state", "all", "--limit", "1", "--json"], handler
        )
        self.assertEqual([item["number"] for item in json.loads(output)], [1])

    def test_view_human_counts_include_prs(self):
        output, _ = self.invoke(["view", "7"], lambda *_: milestone())
        self.assertIn("includes PRs", output)

    def test_view_json_without_items_is_unchanged(self):
        output, calls = self.invoke(["view", "7", "--json"], lambda *_: milestone())
        self.assertEqual(json.loads(output), milestone())
        self.assertEqual(len(calls), 2)

    def test_view_items_includes_all_states_and_all_pages(self):
        closed_issue = issue(101)
        closed_issue["state"] = "closed"
        merged_pr = issue(102, pr=True)
        merged_pr["state"] = "closed"
        merged_pr["pull_request"]["merged_at"] = "2026-11-02T10:00:00Z"

        def handler(path, query):
            if path.endswith("milestones/7"):
                return milestone()
            self.assertEqual(query["milestone"], "7")
            self.assertEqual(query["state"], "all")
            if query["page"] == "1":
                return [issue(number, pr=number % 2 == 0) for number in range(100)]
            return [closed_issue, merged_pr]

        output, _ = self.invoke(["view", "7", "--items", "--json"], handler)
        result = json.loads(output)
        self.assertEqual(result["milestone"], milestone())
        self.assertEqual(len(result["items"]), 102)
        self.assertEqual(result["items"][-2:], [closed_issue, merged_pr])

    def test_view_items_human_output_distinguishes_types_and_merged_prs(self):
        merged = issue(3, pr=True)
        merged["state"] = "closed"
        merged["pull_request"]["merged_at"] = "2026-11-02T10:00:00Z"

        def handler(path, query):
            return milestone() if path.endswith("milestones/7") else [issue(2), merged]

        output, _ = self.invoke(["view", "7", "--items"], handler)
        self.assertIn("Release 7", output)
        self.assertIn("TYPE", output)
        self.assertIn("ISSUE", output)
        self.assertIn("PR", output)
        self.assertIn("merged", output)
        self.assertIn("https://example.test/3", output)

    def test_view_items_state_and_limit(self):
        def handler(path, query):
            if path.endswith("milestones/7"):
                return milestone()
            self.assertEqual(query["state"], "open")
            return [issue(1), issue(2, pr=True)]

        output, _ = self.invoke(
            ["view", "7", "--items", "--state", "open", "--limit", "1", "--json"],
            handler,
        )
        self.assertEqual([item["number"] for item in json.loads(output)["items"]], [1])

    def test_view_items_empty_milestone(self):
        output, _ = self.invoke(
            ["view", "7", "--items"],
            lambda path, _: milestone() if path.endswith("milestones/7") else [],
        )
        self.assertIn("No issues or PRs found.", output)

    def test_view_item_filters_require_items_before_calling_github(self):
        for option in (["--state", "open"], ["--limit", "1"]):
            with (
                self.subTest(option=option),
                patch("subprocess.run") as gh,
                contextlib.redirect_stderr(io.StringIO()) as errors,
                self.assertRaises(SystemExit) as exited,
            ):
                run(["view", "7", *option])
            self.assertEqual(exited.exception.code, 2)
            self.assertIn("require --items", errors.getvalue())
            gh.assert_not_called()


if __name__ == "__main__":
    unittest.main()
