import hashlib
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from nexahome.release import net


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 (the name http.server expects)
        Handler.last_agent = self.headers.get("User-Agent", "")  # before any byte is sent, so the test cannot race it
        if self.path == "/ok":
            body = b"hello"
        elif self.path == "/big":
            body = b"x" * 5000
        elif self.path == "/huge":  # 20 MiB, sent piece by piece
            self.send_response(200)
            self.send_header("Content-Length", str(20 * 1024 * 1024))
            self.end_headers()
            piece = b"y" * 65536
            for _ in range(20 * 16):
                self.wfile.write(piece)
            return
        elif self.path == "/cut":  # a chunked body that ends before its last chunk
            self.send_response(200)
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            self.wfile.write(b"5\r\nhello\r\n")
            self.wfile.flush()
            self.close_connection = True
            return
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

    def log_message(self, format: str, *args: object) -> None:
        pass

    last_agent = ""


@pytest.fixture
def server() -> Iterator[str]:
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
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


def test_a_download_is_streamed_to_a_file_and_hashed(server: str, tmp_path: Path) -> None:
    target = tmp_path / "big.bin"
    digest = net.http_download(f"{server}/big", target, timeout=5, max_bytes=10_000)
    assert target.read_bytes() == b"x" * 5000 and digest == hashlib.sha256(b"x" * 5000).hexdigest()


def test_a_download_over_the_limit_leaves_no_file(server: str, tmp_path: Path) -> None:
    target = tmp_path / "big.bin"
    with pytest.raises(net.NetworkError, match="larger than"):
        net.http_download(f"{server}/big", target, timeout=5, max_bytes=1000)
    assert not target.exists()


def test_a_failed_download_leaves_no_file(server: str, tmp_path: Path) -> None:
    target = tmp_path / "gone.bin"
    with pytest.raises(net.NetworkError, match="HTTP 404"):
        net.http_download(f"{server}/nope", target, timeout=5, max_bytes=1000)
    assert not target.exists()


def test_a_download_into_a_missing_folder_is_a_network_error_not_a_crash(server: str, tmp_path: Path) -> None:
    with pytest.raises(net.NetworkError):
        net.http_download(f"{server}/ok", tmp_path / "no" / "such" / "dir" / "f", timeout=5, max_bytes=1000)


def test_a_body_that_ends_early_is_a_network_error_not_a_crash(server: str, tmp_path: Path) -> None:
    with pytest.raises(net.NetworkError):
        net.http_get(f"{server}/cut", timeout=5, max_bytes=100)
    target = tmp_path / "cut.bin"
    with pytest.raises(net.NetworkError):
        net.http_download(f"{server}/cut", target, timeout=5, max_bytes=100)
    assert not target.exists()


def test_a_big_download_does_not_load_the_file_into_memory(server: str, tmp_path: Path) -> None:
    import tracemalloc

    target = tmp_path / "huge.bin"
    tracemalloc.start()
    try:
        net.http_download(f"{server}/huge", target, timeout=30, max_bytes=30 * 1024 * 1024)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert target.stat().st_size == 20 * 1024 * 1024
    assert peak < 2 * 1024 * 1024  # a 20 MiB file, under 2 MiB of Python memory: it is streamed
