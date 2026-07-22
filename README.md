# TDMAgent-T-Mobile
RegGate-Agent

## GitHub App Webhook MVP

This repository now includes an MVP webhook receiver for GitHub PR events.

### Behavior
- Verifies `X-Hub-Signature-256` with `WEBHOOK_SECRET`
- Listens for `pull_request` events with actions `opened` and `synchronize`
- Posts a PR comment: `RegGate is running...` (when `GITHUB_TOKEN` is set)

### Run locally
```bash
pip install -r requirements.txt
export WEBHOOK_SECRET="your-webhook-secret"
export GITHUB_TOKEN="ghp_xxx" # token with permission to comment on PRs
uvicorn reggate_agent.main:app --reload
```

### Test
```bash
pytest -q
```
