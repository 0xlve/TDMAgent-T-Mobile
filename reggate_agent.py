"""Minimal RegGate MVP workflow primitives."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from urllib import error, request


@dataclass(frozen=True)
class MvpRunResult:
    dataset_id: str
    env_url: str
    smoke_passed: bool
    teardown_at: str


class GitHubClient:
    """Minimal GitHub API client for posting PR comments."""

    def __init__(self, token: str, api_url: str = "https://api.github.com") -> None:
        self.token = token
        self.api_url = api_url.rstrip("/")

    def post_issue_comment(self, owner: str, repo: str, issue_number: int, body: str) -> Dict[str, Any]:
        url = f"{self.api_url}/repos/{owner}/{repo}/issues/{issue_number}/comments"
        data = json.dumps({"body": body}).encode("utf-8")
        req = request.Request(url=url, data=data, method="POST")
        req.add_header("Authorization", "Bearer " + self.token)
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("Content-Type", "application/json")
        try:
            with request.urlopen(req) as resp:  # nosec B310 - trusted GitHub API endpoint
                response_body = resp.read().decode("utf-8")
                return {"status": resp.status, "body": json.loads(response_body) if response_body else {}}
        except error.HTTPError as exc:
            return {"status": exc.code, "error": exc.reason}
        except error.URLError as exc:
            return {"status": "network_error", "error": str(exc.reason)}


def is_pull_request_event(headers: Dict[str, str], payload: Dict[str, Any]) -> bool:
    return headers.get("X-GitHub-Event", "").lower() == "pull_request" and bool(payload.get("pull_request"))


def build_event_echo(headers: Dict[str, str], payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "event": headers.get("X-GitHub-Event", ""),
        "action": payload.get("action"),
        "repository": payload.get("repository", {}).get("full_name"),
        "pr_number": payload.get("pull_request", {}).get("number"),
    }


def request_tdp_dataset() -> str:
    return "tdp-dataset-0001"


def create_tec_environment() -> str:
    return "https://tec.local/env/basic-0001"


def run_aft_smoke_suite() -> bool:
    return True


def schedule_teardown(hours_from_now: int = 2) -> str:
    scheduled = datetime.now(tz=timezone.utc) + timedelta(hours=hours_from_now)
    return scheduled.isoformat()


def run_mvp_flow() -> MvpRunResult:
    return MvpRunResult(
        dataset_id=request_tdp_dataset(),
        env_url=create_tec_environment(),
        smoke_passed=run_aft_smoke_suite(),
        teardown_at=schedule_teardown(),
    )


def format_pr_comment(result: MvpRunResult) -> str:
    smoke = "✅ PASS" if result.smoke_passed else "❌ FAIL"
    return "\n".join(
        [
            "## RegGate is running...",
            "",
            "| Check | Result |",
            "| --- | --- |",
            f"| TDP dataset | `{result.dataset_id}` |",
            f"| TEC environment | {result.env_url} |",
            f"| AFT smoke | {smoke} |",
            f"| Planned teardown (UTC) | `{result.teardown_at}` |",
        ]
    )


def process_event(
    headers: Dict[str, str],
    payload: Dict[str, Any],
    github_client: Optional[GitHubClient] = None,
) -> Dict[str, Any]:
    response: Dict[str, Any] = {"echo": build_event_echo(headers, payload)}
    if not is_pull_request_event(headers, payload):
        response["message"] = "Ignored non-pull_request event."
        return response

    result = run_mvp_flow()
    comment = format_pr_comment(result)
    response["mvp"] = {
        "dataset_id": result.dataset_id,
        "env_url": result.env_url,
        "smoke_passed": result.smoke_passed,
        "teardown_at": result.teardown_at,
        "comment_markdown": comment,
    }

    repository = payload.get("repository", {}).get("full_name", "")
    pr_number = payload.get("pull_request", {}).get("number")

    if github_client and repository and isinstance(pr_number, int):
        try:
            owner, repo = repository.split("/", 1)
        except ValueError:
            response["github_comment"] = {"status": "skipped", "reason": "Invalid repository full_name."}
        else:
            response["github_comment"] = github_client.post_issue_comment(owner, repo, pr_number, comment)
    else:
        response["github_comment"] = {"status": "skipped", "reason": "Missing GitHub client or PR metadata."}
    return response


def load_github_client_from_env() -> Optional[GitHubClient]:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return None
    return GitHubClient(token=token)
