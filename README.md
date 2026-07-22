# TDMAgent-T-Mobile

Minimal RegGate MVP implementation for pull request gating signals.

## Features

- Webhook receiver (`POST /webhook`) that echoes PR event metadata
- GitHub client for posting PR comments (`RegGate is running...`)
- TDP integration stub that returns a hardcoded dataset ID
- TEC integration stub that returns a basic environment URL
- AFT integration stub that returns smoke pass/fail
- PR markdown formatter for human-readable results
- Simple teardown scheduling with a delayed UTC timestamp

## Run locally

```bash
python webhook_server.py
```

Then send a webhook payload to `http://localhost:8080/webhook`.

To enable GitHub comment posting, set:

```bash
export GITHUB_TOKEN=<token>
```

## Test

```bash
pytest -q
```
