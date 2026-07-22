import hashlib
import hmac
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from reggate_agent import main as reggate_agent_main


def _signature(payload: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def test_webhook_rejects_invalid_signature(monkeypatch):
    monkeypatch.setattr(reggate_agent_main, "WEBHOOK_SECRET", "test-secret")
    client = TestClient(reggate_agent_main.app)

    response = client.post(
        "/webhook",
        content=b'{"action":"opened"}',
        headers={"X-Hub-Signature-256": "sha256=bad", "X-GitHub-Event": "pull_request"},
    )

    assert response.status_code == 401
    assert response.json() == {"error": "Invalid signature"}


def test_webhook_triggers_pull_request_handler(monkeypatch):
    monkeypatch.setattr(reggate_agent_main, "WEBHOOK_SECRET", "test-secret")
    handler = AsyncMock()
    monkeypatch.setattr(reggate_agent_main, "handle_pr_trigger", handler)

    payload = (
        b'{"action":"opened","pull_request":{"number":1,'
        b'"head":{"sha":"abcdef0123456789","ref":"feature"},'
        b'"base":{"repo":{"full_name":"octo/repo"}}}}'
    )
    client = TestClient(reggate_agent_main.app)

    response = client.post(
        "/webhook",
        content=payload,
        headers={
            "X-Hub-Signature-256": _signature(payload, "test-secret"),
            "X-GitHub-Event": "pull_request",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    handler.assert_awaited_once()


def test_webhook_ignores_non_trigger_actions(monkeypatch):
    monkeypatch.setattr(reggate_agent_main, "WEBHOOK_SECRET", "test-secret")
    handler = AsyncMock()
    monkeypatch.setattr(reggate_agent_main, "handle_pr_trigger", handler)

    payload = b'{"action":"closed","pull_request":{"number":1}}'
    client = TestClient(reggate_agent_main.app)

    response = client.post(
        "/webhook",
        content=payload,
        headers={
            "X-Hub-Signature-256": _signature(payload, "test-secret"),
            "X-GitHub-Event": "pull_request",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    handler.assert_not_awaited()
