"""Transport contracts for normal verified HTTPS and visible source failures."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from geode.pipeline import register_daily as daily

URL = "https://www.sos.state.co.us/CCR/RegisterHome.do?pyear=2026"


class FakeCurl:
    """Write controlled HTTP responses at curl's requested output locations."""

    def __init__(self, responses: list[tuple[int, dict[str, str], bytes, int]]) -> None:
        self.responses = iter(responses)
        self.calls: list[list[str]] = []
        self.paths: list[Path] = []

    def __call__(self, command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        """Supply a response without running any shell or network operation."""

        assert kwargs == {
            "capture_output": True, "text": True, "timeout": 35, "check": False,
        }
        self.calls.append(command)
        status, headers, body, returncode = next(self.responses)
        head = Path(command[command.index("--dump-header") + 1])
        output = Path(command[command.index("--output") + 1])
        self.paths.extend([head, output])
        head.write_text(
            "HTTP/1.1 200 Connection established\r\n\r\n"
            f"HTTP/2 {status}\r\n"
            + "".join(f"{key}: {value}\r\n" for key, value in headers.items())
            + "\r\n"
        )
        output.write_bytes(body)
        return subprocess.CompletedProcess(command, returncode, str(status), "test transport error")


def test_success_uses_bounded_verified_https_without_cookies_or_redirects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The ordinary client identity and transport restrictions remain explicit."""

    fake = FakeCurl([(200, {"Content-Type": "text/html; charset=UTF-8"}, b"<html>ok</html>", 0)])
    monkeypatch.setattr(daily.subprocess, "run", fake)
    client = daily.OfficialSourceClient(delay=0)
    result = client(URL)
    client.close()
    assert result == daily.FetchResult(URL, b"<html>ok</html>", "text/html; charset=UTF-8")
    command = fake.calls[0]
    assert command[:2] == ["curl", "--disable"]  # Ignore user .curlrc settings.
    assert command[command.index("--proto") + 1] == "=https"
    assert command[command.index("--max-time") + 1] == "30"
    assert command[command.index("--max-filesize") + 1] == str(daily.MAX_SOURCE_BYTES)
    assert command[command.index("--user-agent") + 1] == (
        "ProjectGeode/0.1 (Colorado Register research pilot)"
    )
    assert not {"--insecure", "-k", "--location", "-L", "--cookie", "-b"}.intersection(command)
    assert all(not path.exists() for path in fake.paths)


@pytest.mark.parametrize("location", [
    "https://external.example/CCR/private", "http://www.sos.state.co.us/CCR/index",
    "https://www.sos.state.co.us/private",
])
def test_redirect_is_validated_before_another_request(
    monkeypatch: pytest.MonkeyPatch, location: str,
) -> None:
    """Untrusted redirects cannot cause requests outside the official CCR scope."""

    fake = FakeCurl([(302, {"Location": location}, b"", 0)])
    monkeypatch.setattr(daily.subprocess, "run", fake)
    with pytest.raises(ValueError, match="Unapproved source URL"):
        daily.OfficialSourceClient(delay=0)(URL)
    assert len(fake.calls) == 1


def test_permitted_redirect_and_retry_use_the_verified_destination(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A temporary source outage retries only the approved destination."""

    fake = FakeCurl([
        (302, {"Location": "/CCR/RegisterHome.do"}, b"", 0),
        (503, {}, b"Unavailable", 0),
        (429, {}, b"Slow down", 0),
        (200, {"Content-Type": "text/html"}, b"<html>ok</html>", 0),
    ])
    sleeps: list[float] = []
    monkeypatch.setattr(daily.subprocess, "run", fake)
    monkeypatch.setattr(daily.time, "sleep", sleeps.append)
    result = daily.OfficialSourceClient(delay=1)(URL)
    assert result.url == "https://www.sos.state.co.us/CCR/RegisterHome.do"
    assert [call[-1] for call in fake.calls] == [URL, result.url, result.url, result.url]
    assert sleeps == [1, 1, 2, 1, 4, 1]


@pytest.mark.parametrize("status,body,message", [
    (403, b"<html>Challenge</html>", "HTTP 403"),
    (200, b"<html><title>Just a moment</title></html>", "access challenge"),
    (200, b"<html><script>window._cf_chl_opt={}</script></html>", "access challenge"),
    (200, b"", "empty response"),
])
def test_source_denial_or_challenge_never_triggers_a_transport_workaround(
    monkeypatch: pytest.MonkeyPatch, status: int, body: bytes, message: str,
) -> None:
    """Denied or challenged requests fail without alternate identities or cookies."""

    fake = FakeCurl([(status, {"Content-Type": "text/html"}, body, 0)])
    monkeypatch.setattr(daily.subprocess, "run", fake)
    with pytest.raises(ValueError, match=message):
        daily.OfficialSourceClient(delay=0)(URL)
    assert len(fake.calls) == 1
    assert all(not path.exists() for path in fake.paths)


def test_retry_and_redirect_caps(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sources cannot keep the scheduled job in an unbounded retry or redirect loop."""

    monkeypatch.setattr(daily.time, "sleep", lambda _delay: None)
    errors = FakeCurl([(503, {}, b"Unavailable", 0)] * 3)
    monkeypatch.setattr(daily.subprocess, "run", errors)
    with pytest.raises(ValueError, match="HTTP 503"):
        daily.OfficialSourceClient(delay=0)(URL)
    assert len(errors.calls) == 3
    redirects = FakeCurl([(302, {"Location": URL}, b"", 0)] * 4)
    monkeypatch.setattr(daily.subprocess, "run", redirects)
    with pytest.raises(ValueError, match="Too many redirects"):
        daily.OfficialSourceClient(delay=0)(URL)
    assert len(redirects.calls) == 4


def test_background_source_script_is_not_a_challenge_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The real SOS page includes passive Cloudflare JS alongside complete content."""

    body = (
        b"<html><h1>Colorado Register</h1><p>Publication content</p>"
        b"<script src='/cdn-cgi/challenge-platform/scripts/jsd/main.js'></script></html>"
    )
    fake = FakeCurl([(200, {"Content-Type": "text/html"}, body, 0)])
    monkeypatch.setattr(daily.subprocess, "run", fake)
    assert daily.OfficialSourceClient(delay=0)(URL).content == body


@pytest.mark.parametrize("returncode,message", [(63, "size limit"), (60, "transport failed")])
def test_curl_size_and_tls_errors_are_fatal(
    monkeypatch: pytest.MonkeyPatch, returncode: int, message: str,
) -> None:
    """Source size and TLS errors cannot publish partial downloads."""

    fake = FakeCurl([(200, {}, b"partial", returncode)])
    monkeypatch.setattr(daily.subprocess, "run", fake)
    with pytest.raises(ValueError, match=message):
        daily.OfficialSourceClient(delay=0)(URL)
    assert len(fake.calls) == 1


def test_postdownload_size_check_remains_defensive(monkeypatch: pytest.MonkeyPatch) -> None:
    """An older or unusual curl must not admit an oversized saved response."""

    monkeypatch.setattr(daily, "MAX_SOURCE_BYTES", 5)
    fake = FakeCurl([(200, {"Content-Type": "text/html"}, b"too large", 0)])
    monkeypatch.setattr(daily.subprocess, "run", fake)
    with pytest.raises(ValueError, match="size limit"):
        daily.OfficialSourceClient(delay=0)(URL)


@pytest.mark.parametrize("failure,message", [
    (FileNotFoundError(), "requires curl"),
    (subprocess.TimeoutExpired("curl", 35), "timed out"),
])
def test_missing_runtime_or_hung_process_fails_visibly(
    monkeypatch: pytest.MonkeyPatch, failure: Exception, message: str,
) -> None:
    """Transport execution failures become actionable refresh errors."""

    def fail(*_args: Any, **_kwargs: Any) -> None:
        raise failure

    monkeypatch.setattr(daily.subprocess, "run", fail)
    with pytest.raises(ValueError, match=message):
        daily.OfficialSourceClient(delay=0)(URL)
