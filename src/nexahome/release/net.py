"""The only module that talks to the network. Only `nexahome update` uses it, and only when it is run.

HTTPS only (plain HTTP is allowed to the local machine, for a mirror or a test), a time and size limit on every
request, no credentials, and no data about the user: the request carries the tool name and version only.
urllib is imported inside the functions that need it, so importing this module costs nothing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nexahome import __version__

if TYPE_CHECKING:
    from http.client import HTTPMessage, HTTPResponse
    from pathlib import Path
    from typing import IO, Protocol

    class Fetcher(Protocol):
        def __call__(self, url: str, *, timeout: float, max_bytes: int) -> bytes: ...

    class Downloader(Protocol):
        def __call__(self, url: str, destination: Path, *, timeout: float, max_bytes: int) -> str: ...


LOOPBACK = ("127.0.0.1", "localhost", "::1")


class NetworkError(Exception):
    """A request that was refused or failed; the message is for the user."""


def check_url(url: str) -> None:
    from urllib.parse import urlsplit

    parts = urlsplit(url)
    if parts.scheme == "https" and parts.hostname:
        return
    if parts.scheme == "http" and parts.hostname in LOOPBACK:
        return
    raise NetworkError(f"refusing {url.split('?')[0]!r}: only https addresses are used")


def _open(url: str, timeout: float) -> HTTPResponse:
    """Open an address. Every redirect is checked too; the caller closes the response."""
    import urllib.error
    import urllib.request

    class CheckedRedirects(urllib.request.HTTPRedirectHandler):
        def redirect_request(
            self, req: urllib.request.Request, fp: IO[bytes], code: int, msg: str, headers: HTTPMessage, newurl: str
        ) -> urllib.request.Request | None:
            check_url(newurl)  # a redirect may not leave https
            return super().redirect_request(req, fp, code, msg, headers, newurl)

    check_url(url)
    request = urllib.request.Request(url, headers={"User-Agent": f"nexahome/{__version__}"})
    try:
        response: HTTPResponse = urllib.request.build_opener(CheckedRedirects).open(request, timeout=timeout)
    except NetworkError:
        raise
    except urllib.error.HTTPError as error:
        error.close()  # it holds the response body open
        raise NetworkError(f"the server answered HTTP {error.code}") from error
    except (urllib.error.URLError, OSError, ValueError) as error:
        raise NetworkError(str(getattr(error, "reason", error))) from error
    return response


def http_get(url: str, *, timeout: float, max_bytes: int) -> bytes:
    """A small answer (a feed, a checksum list) held in memory, up to max_bytes."""
    from http.client import HTTPException

    with _open(url, timeout) as response:
        try:
            data: bytes = response.read(max_bytes + 1)
        except (OSError, HTTPException) as error:  # HTTPException: the body ended early
            raise NetworkError(str(error) or type(error).__name__) from error
    if len(data) > max_bytes:
        raise NetworkError(f"the answer is larger than the {max_bytes} byte limit")
    return data


def http_download(url: str, destination: Path, *, timeout: float, max_bytes: int) -> str:
    """A large file streamed to disk in 64 KiB pieces and hashed on the way, so memory stays at one piece however
    big the file is. Returns the SHA-256 as hex; the file is removed when the download fails."""
    import hashlib
    from http.client import HTTPException

    digest = hashlib.sha256()
    written = 0
    try:
        with _open(url, timeout) as response, destination.open("wb") as out:
            while piece := response.read(65536):
                written += len(piece)
                if written > max_bytes:
                    raise NetworkError(f"the download is larger than the {max_bytes} byte limit")
                digest.update(piece)
                out.write(piece)
    except (OSError, HTTPException) as error:
        destination.unlink(missing_ok=True)
        raise NetworkError(str(error) or type(error).__name__) from error
    except NetworkError:
        destination.unlink(missing_ok=True)
        raise
    return digest.hexdigest()
