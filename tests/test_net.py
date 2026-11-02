import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from nexahome import net


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 (the name http.server expects)
        if self.path == "/ok":
            body = b"hello"
        elif self.path == "/big":
            body = b"x" * 5000
        elif self.path == "/hop":
            self.send_response(302)
            self.send_header("Location", "/ok")
            self.end_headers()
            return
        elif self.path == "/away":
            self.send_response(302)
            self.send_header("Location", "http://example.invalid/elsewhere")
            self.end_headers()
            return
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        self.server_header = self.headers.get("User-Agent", "")
        Handler.last_agent = self.server_header

    def log_message(self, format: str, *args: object) -> None:
        pass

    last_agent = ""


@pytest.fixture
def server() -> Iterator[str]:
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()
    httpd.server_close()
    thread.join(5)


def test_a_local_http_server_is_allowed_and_the_agent_names_only_the_tool(server: str) -> None:
    assert net.http_get(f"{server}/ok", timeout=5, max_bytes=100) == b"hello"
    assert Handler.last_agent.startswith("nexahome/") and len(Handler.last_agent) < 30


def test_an_answer_over_the_limit_is_refused(server: str) -> None:
    with pytest.raises(net.NetworkError, match="larger than"):
        net.http_get(f"{server}/big", timeout=5, max_bytes=1000)


def test_a_missing_page_and_a_dead_address_are_network_errors(server: str) -> None:
    with pytest.raises(net.NetworkError, match="HTTP 404"):
        net.http_get(f"{server}/nope", timeout=5, max_bytes=100)
    with pytest.raises(net.NetworkError):
        net.http_get("http://127.0.0.1:9/", timeout=2, max_bytes=100)


def test_a_redirect_may_not_leave_https(server: str) -> None:
    with pytest.raises(net.NetworkError, match="only https"):
        net.http_get(f"{server}/away", timeout=5, max_bytes=100)


@pytest.mark.parametrize("url", ["http://example.com/x", "ftp://example.com/x", "file:///etc/passwd", "example.com", "https://"])
def test_only_https_or_the_local_machine_is_used(url: str) -> None:
    with pytest.raises(net.NetworkError):
        net.check_url(url)


@pytest.mark.parametrize("url", ["https://example.com/x?token=1", "http://localhost:8000/x", "http://127.0.0.1/x"])
def test_allowed_addresses(url: str) -> None:
    net.check_url(url)


def test_a_redirect_that_stays_allowed_is_followed(server: str) -> None:
    assert net.http_get(f"{server}/hop", timeout=5, max_bytes=100) == b"hello"
