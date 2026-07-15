"""Conservatively audit external links published by the GitHub profile.

Permanent client failures such as HTTP 404 and 410 fail the audit. Bot blocks,
authentication gates, rate limits, timeouts and server failures are reported as
warnings so a scheduled check does not become a flaky per-push quality gate.
"""

from __future__ import annotations

import argparse
import os
import re
import socket
import ssl
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FILES = (
    ROOT / "README.md",
    ROOT / "README_EXPANDED.md",
    ROOT / "PROFILE_ES.md",
    ROOT / "PROFILE_HE.md",
    ROOT / "profile.json",
)
URL_PATTERN = re.compile(r"https?://[^\s<>\"')\]]+")
TRANSIENT_OR_RESTRICTED_STATUSES = {
    401,
    403,
    405,
    408,
    425,
    429,
    500,
    501,
    502,
    503,
    504,
    999,
}
PERMANENT_MISSING_STATUSES = {404, 410}
Opener = Callable[..., object]


@dataclass(frozen=True)
class LinkResult:
    """One URL audit result."""

    url: str
    state: str
    detail: str
    status: int | None = None


def build_parser() -> argparse.ArgumentParser:
    """Create the external-link audit CLI parser."""
    parser = argparse.ArgumentParser(
        prog="check_external_links",
        description="Audit public profile links while tolerating transient network failures.",
    )
    parser.add_argument(
        "--file",
        action="append",
        dest="files",
        type=Path,
        help="Source file to scan; repeat to override the default public profile files.",
    )
    parser.add_argument(
        "--url",
        action="append",
        default=[],
        help="Additional HTTPS URL to check.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=12.0,
        help="Timeout in seconds for each HTTP attempt.",
    )
    return parser


def extract_urls(paths: Iterable[Path]) -> list[str]:
    """Return sorted, de-duplicated HTTP(S) URLs from public profile sources."""
    urls: set[str] = set()
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(f"Link source not found: {path}")
        content = path.read_text(encoding="utf-8")
        for match in URL_PATTERN.finditer(content):
            urls.add(match.group(0).rstrip(".,;:"))
    return sorted(urls, key=str.casefold)


def classify_status(url: str, status: int) -> str:
    """Classify an HTTP status as ok, warning or failure."""
    if 200 <= status < 400:
        return "ok"
    if status in TRANSIENT_OR_RESTRICTED_STATUSES or status >= 500:
        return "warning"
    if status in PERMANENT_MISSING_STATUSES:
        return "failure"

    # LinkedIn frequently blocks automated clients with non-standard 4xx
    # responses. Keep those visible without asserting that the profile is gone.
    hostname = (urlsplit(url).hostname or "").casefold()
    if hostname == "linkedin.com" or hostname.endswith(".linkedin.com"):
        return "warning"
    if 400 <= status < 500:
        return "failure"
    return "warning"


def _request_status(url: str, method: str, timeout: float, opener: Opener) -> int:
    """Return the HTTP status, including statuses raised as ``HTTPError``."""
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/json;q=0.8,*/*;q=0.5",
        "Connection": "close",
        "User-Agent": "LiriothTeltanion-profile-link-audit/1.0",
    }
    if method == "GET":
        headers["Range"] = "bytes=0-0"
    request = Request(url, headers=headers, method=method)
    try:
        response = opener(request, timeout=timeout)
        with response:
            status = response.getcode()
            return int(status if status is not None else 200)
    except HTTPError as error:
        return int(error.code)


def check_url(url: str, timeout: float = 12.0, opener: Opener | None = None) -> LinkResult:
    """Check one URL with HEAD and a lightweight GET fallback."""
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return LinkResult(url, "failure", "not an absolute HTTP(S) URL")
    if timeout <= 0:
        return LinkResult(url, "failure", "timeout must be greater than zero")

    active_opener = opener or urlopen
    attempts: list[str] = []
    final_status: int | None = None
    for method in ("HEAD", "GET"):
        try:
            status = _request_status(url, method, timeout, active_opener)
            attempts.append(f"{method} HTTP {status}")
            final_status = status
            state = classify_status(url, status)
            if state == "ok":
                return LinkResult(url, state, "; ".join(attempts), status)
            if method == "GET":
                return LinkResult(url, state, "; ".join(attempts), status)
        except (TimeoutError, socket.timeout, ssl.SSLError, URLError, OSError) as error:
            attempts.append(f"{method} {type(error).__name__}: {error}")

    detail = "; ".join(attempts) or "no HTTP attempt completed"
    if final_status is not None:
        return LinkResult(url, classify_status(url, final_status), detail, final_status)
    return LinkResult(url, "warning", detail)


def audit_urls(urls: Sequence[str], timeout: float = 12.0) -> list[LinkResult]:
    """Audit URLs in stable order."""
    return [check_url(url, timeout) for url in sorted(set(urls), key=str.casefold)]


def _annotation(state: str, message: str) -> None:
    """Print a readable line and a GitHub annotation when running in Actions."""
    label = {"ok": "OK", "warning": "WARN", "failure": "FAIL"}[state]
    print(f"[{label}] {message}")
    if os.environ.get("GITHUB_ACTIONS") == "true" and state != "ok":
        command = "warning" if state == "warning" else "error"
        escaped = message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print(f"::{command} title=External link audit::{escaped}")


def main() -> int:
    """Run the public-profile external-link audit."""
    args = build_parser().parse_args()
    if args.timeout <= 0:
        print("External link audit failed: --timeout must be greater than zero.")
        return 2

    paths = tuple(args.files) if args.files else DEFAULT_FILES
    try:
        urls = set(extract_urls(paths))
    except (OSError, UnicodeError) as error:
        print(f"External link audit failed: {error}")
        return 2
    urls.update(args.url)
    if not urls:
        print("External link audit failed: no HTTP(S) URLs were found.")
        return 2

    results = audit_urls(sorted(urls), args.timeout)
    for result in results:
        _annotation(result.state, f"{result.url} — {result.detail}")

    failures = sum(result.state == "failure" for result in results)
    warnings = sum(result.state == "warning" for result in results)
    print(
        f"External link audit complete: {len(results)} checked, "
        f"{failures} permanent failure(s), {warnings} warning(s)."
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
