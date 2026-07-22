import json
from datetime import datetime

from reggate_agent import MvpRunResult, format_pr_comment, process_event


def test_format_pr_comment_contains_results():
    result = MvpRunResult(
        dataset_id="tdp-dataset-9999",
        env_url="https://tec.local/env/example",
        smoke_passed=True,
        teardown_at="2026-07-22T19:00:00+00:00",
    )

    comment = format_pr_comment(result)

    assert "RegGate is running" in comment
    assert "`tdp-dataset-9999`" in comment
    assert "https://tec.local/env/example" in comment
    assert "✅ PASS" in comment
    assert "`2026-07-22T19:00:00+00:00`" in comment


def test_process_event_for_pull_request_contains_mvp_results():
    payload = {
        "action": "opened",
        "repository": {"full_name": "0xlve/TDMAgent-T-Mobile"},
        "pull_request": {"number": 12},
    }
    headers = {"X-GitHub-Event": "pull_request"}

    result = process_event(headers=headers, payload=payload)

    assert result["echo"]["event"] == "pull_request"
    assert result["echo"]["pr_number"] == 12
    assert result["mvp"]["dataset_id"].startswith("tdp-dataset-")
    assert result["mvp"]["env_url"].startswith("https://")
    assert isinstance(result["mvp"]["smoke_passed"], bool)
    datetime.fromisoformat(result["mvp"]["teardown_at"])
    assert "RegGate is running..." in result["mvp"]["comment_markdown"]
    assert result["github_comment"]["status"] == "skipped"


def test_process_event_for_non_pr_only_echoes():
    payload = {"action": "ping", "repository": {"full_name": "0xlve/TDMAgent-T-Mobile"}}
    headers = {"X-GitHub-Event": "ping"}

    result = process_event(headers=headers, payload=payload)

    assert result["echo"]["event"] == "ping"
    assert result["message"] == "Ignored non-pull_request event."
    assert "mvp" not in result


def test_webhook_handler_returns_json(client):
    payload = {
        "action": "opened",
        "repository": {"full_name": "0xlve/TDMAgent-T-Mobile"},
        "pull_request": {"number": 101},
    }
    response = client.post("/webhook", data=json.dumps(payload), headers={"X-GitHub-Event": "pull_request"})
    assert response["status"] == 200
    assert response["body"]["echo"]["pr_number"] == 101
    assert "mvp" in response["body"]
