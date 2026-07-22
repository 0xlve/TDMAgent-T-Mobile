# RegGate MVP Tutorial

This tutorial shows how to run the MVP locally and send a pull request webhook event.

## Prerequisites

- Python 3.10+ (3.12 works)
- `pip`

## 1) Install dependencies

```bash
python -m pip install -r requirements.txt
```

## 2) (Optional) Set GitHub token

Set this only if you want the service to post a comment to a real GitHub PR.

```bash
export GITHUB_TOKEN=<your_github_token>
```

If `GITHUB_TOKEN` is not set, the service still works and returns `github_comment.status: skipped`.

## 3) Start the webhook server

```bash
python webhook_server.py
```

Server endpoint:

- `POST http://localhost:8080/webhook`

## 4) Send a sample pull_request event

In a second terminal:

```bash
curl -X POST "http://localhost:8080/webhook" \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: pull_request" \
  -d '{
    "action": "opened",
    "repository": { "full_name": "0xlve/TDMAgent-T-Mobile" },
    "pull_request": { "number": 12 }
  }'
```

## 5) Check the response

You should receive JSON with:

- `echo` (event metadata)
- `mvp.dataset_id` (hardcoded TDP ID)
- `mvp.env_url` (hardcoded TEC URL)
- `mvp.smoke_passed` (AFT smoke status)
- `mvp.teardown_at` (scheduled teardown time in UTC)
- `mvp.comment_markdown` (formatted PR comment body)

## 6) Run tests

```bash
pytest -q
```

## Notes

- Non-PR events are ignored and return `Ignored non-pull_request event.`
- This is an MVP: TDP, TEC, and AFT are currently stubbed with fixed/demo outputs.
