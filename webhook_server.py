"""Simple HTTP webhook receiver for RegGate MVP."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from reggate_agent import load_github_client_from_env, process_event


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802 - stdlib method name
        if self.path != "/webhook":
            self._send_json(404, {"error": "Not found"})
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length) if content_length else b"{}"
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON payload"})
            return

        headers = {"X-GitHub-Event": self.headers.get("X-GitHub-Event", "")}
        result = process_event(headers=headers, payload=payload, github_client=load_github_client_from_env())
        self._send_json(200, result)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return

    def _send_json(self, status_code: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_server(host: str = "0.0.0.0", port: int = 8080) -> None:
    server = HTTPServer((host, port), WebhookHandler)
    print(f"RegGate webhook server listening on http://{host}:{port}/webhook")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
