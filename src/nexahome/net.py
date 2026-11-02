"""The only module that talks to the network. Only `nexahome update` uses it, and only when it is run.

HTTPS only (plain HTTP is allowed to the local machine, for a mirror or a test), a time and size limit on every
request, no credentials, and no data about the user: the request carries the tool name and version only.
"""

import urllib.error
import urllib.parse
import urllib.request
from email.message import Message
from typing import IO, Protocol

from nexahome import __version__

LOOPBACK = ("127.0.0.1", "localhost", "::1")


class NetworkError(Exception):
    """A request that was refused or failed; the message is for the user."""


class Fetcher(Protocol):
    def __call__(self, url: str, *, timeout: float, max_bytes: int) -> bytes: ...


def check_url(url: str) -> None:
    parts = urllib.parse.urlsplit(url)
    if parts.scheme == "https" and parts.hostname:
        return
    if parts.scheme == "http" and parts.hostname in LOOPBACK:
        return
    raise NetworkError(f"refusing {url.split('?')[0]!r}: only https addresses are used")


class _CheckedRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self, req: urllib.request.Request, fp: IO[bytes], code: int, msg: str, headers: Message, newurl: str
    ) -> urllib.request.Request | None:
        check_url(newurl)  # a redirect may not leave https
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def http_get(url: str, *, timeout: float, max_bytes: int) -> bytes:
    check_url(url)
    request = urllib.request.Request(url, headers={"User-Agent": f"nexahome/{__version__}"})
    try:
        with urllib.request.build_opener(_CheckedRedirects).open(request, timeout=timeout) as response:
            data: bytes = response.read(max_bytes + 1)
    except NetworkError:
        raise
    except urllib.error.HTTPError as error:
        error.close()  # it holds the response body open
        raise NetworkError(f"the server answered HTTP {error.code}") from error
    except (urllib.error.URLError, OSError, ValueError) as error:
        raise NetworkError(str(getattr(error, "reason", error))) from error
    if len(data) > max_bytes:
        raise NetworkError(f"the answer is larger than the {max_bytes} byte limit")
    return data
