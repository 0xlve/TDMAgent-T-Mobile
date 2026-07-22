import hashlib
import hmac
import json
import os
from typing import Any

import httpx
from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse

app = FastAPI()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")


@app.post("/webhook")
async def github_webhook(request: Request, x_hub_signature_256: str = Header(default="")) -> JSONResponse:
    payload = await request.body()

    if not is_valid_signature(payload, x_hub_signature_256, WEBHOOK_SECRET):
        return JSONResponse({"error": "Invalid signature"}, status_code=401)

    event = json.loads(payload.decode("utf-8"))
    event_type = request.headers.get("X-GitHub-Event")

    if event_type == "pull_request" and event.get("action") in {"opened", "synchronize"}:
        await handle_pr_trigger(event["pull_request"])

    return JSONResponse({"status": "ok"}, status_code=200)


def is_valid_signature(payload: bytes, signature: str, secret: str) -> bool:
    if not secret:
        return False

    expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature or "")


async def handle_pr_trigger(pr: dict[str, Any]) -> None:
    repo_full_name = pr["base"]["repo"]["full_name"]
    pr_number = pr["number"]
    sha = pr["head"]["sha"]

    await post_pr_comment(
        repo_full_name,
        pr_number,
        f"RegGate is running for `{sha[:7]}`. This is the webhook MVP plumbing check.",
    )


async def post_pr_comment(repo_full_name: str, pr_number: int, body: str) -> None:
    if not GITHUB_TOKEN:
        return

    owner, repo = repo_full_name.split("/", 1)
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": "token " + GITHUB_TOKEN,
        "Accept": "application/vnd.github+json",
    }

    async with httpx.AsyncClient(timeout=15) as client:
        await client.post(url, headers=headers, json={"body": body})
