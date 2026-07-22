import json
import threading
from http.client import HTTPConnection
from http.server import HTTPServer

import pytest

from webhook_server import WebhookHandler


class _TestClient:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    def post(self, path: str, data: str, headers: dict | None = None) -> dict:
        conn = HTTPConnection(self.host, self.port, timeout=5)
        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)
        conn.request("POST", path, body=data, headers=request_headers)
        response = conn.getresponse()
        body = response.read().decode("utf-8")
        conn.close()
        return {"status": response.status, "body": json.loads(body)}


@pytest.fixture
def client():
    server = HTTPServer(("127.0.0.1", 0), WebhookHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield _TestClient("127.0.0.1", server.server_port)
    server.shutdown()
    thread.join(timeout=5)
