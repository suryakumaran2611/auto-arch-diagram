"""Security-focused tests for URL redaction and remote-source handling.

Credentials embedded in Git URLs must never reach job logs, uploaded artifacts or
Python tracebacks. These tests pin the behaviour of ``tools/url_utils.py`` and the
error path of ``_handle_git_source``.
"""

from __future__ import annotations

import subprocess

import pytest

from tools import generate_arch_diagram as generator
from tools.url_utils import redact_text, redact_url, split_git_source


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (
            "https://user:token@gitlab.example.com/group/repo.git",
            "https://***@gitlab.example.com/group/repo.git",
        ),
        (
            "https://glpat-abc123@gitlab.example.com/group/repo.git//terraform",
            "https://***@gitlab.example.com/group/repo.git//terraform",
        ),
        (
            "https://gitlab.example.com/group/repo.git?private_token=abc",
            "https://gitlab.example.com/group/repo.git",
        ),
        (
            "https://gitlab.example.com/group/repo.git#fragment",
            "https://gitlab.example.com/group/repo.git",
        ),
        ("https://gitlab.example.com/group/repo.git", "https://gitlab.example.com/group/repo.git"),
        ("git@gitlab.example.com:group/repo.git", "git@gitlab.example.com:group/repo.git"),
        ("/local/path/to/infra", "/local/path/to/infra"),
        ("", ""),
    ],
)
def test_redact_url_removes_credentials_and_queries(url: str, expected: str):
    assert redact_url(url) == expected


def test_redact_text_removes_embedded_credentials():
    message = (
        "fatal: unable to access "
        "'https://deploy-token:glpat-secret@gitlab.example.com/group/repo.git/': "
        "The requested URL returned error: 403"
    )
    redacted = redact_text(message)

    assert "glpat-secret" not in redacted
    assert "deploy-token" not in redacted
    assert "https://***@gitlab.example.com/group/repo.git/" in redacted


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            "https://gitlab.example.com/platform/landing-zone.git",
            ("https://gitlab.example.com/platform/landing-zone.git", ""),
        ),
        (
            "https://gitlab.example.com/platform/landing-zone.git//terraform",
            ("https://gitlab.example.com/platform/landing-zone.git", "terraform"),
        ),
        (
            "https://user:token@gitlab.example.com/platform/landing-zone.git//envs/prod",
            ("https://user:token@gitlab.example.com/platform/landing-zone.git", "envs/prod"),
        ),
        (
            "git@gitlab.example.com:platform/landing-zone.git//modules/vpc",
            ("git@gitlab.example.com:platform/landing-zone.git", "modules/vpc"),
        ),
        ("/local/infra", ("/local/infra", "")),
    ],
)
def test_split_git_source_preserves_the_scheme(source: str, expected: tuple[str, str]):
    assert split_git_source(source) == expected


def test_git_clone_failure_does_not_leak_credentials(monkeypatch: pytest.MonkeyPatch):
    source = "https://deploy-token:glpat-secret@gitlab.example.com/group/repo.git//terraform"

    def fake_run(*args, **kwargs):
        raise subprocess.CalledProcessError(
            128,
            ["git", "clone", "--depth", "1", source, "/tmp/clone"],
            stderr=(
                "fatal: unable to access "
                "'https://deploy-token:glpat-secret@gitlab.example.com/group/repo.git/': "
                "The requested URL returned error: 403"
            ),
        )

    monkeypatch.setattr(generator.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError) as excinfo:
        generator._handle_git_source(source)

    message = str(excinfo.value)
    assert "glpat-secret" not in message
    assert "deploy-token" not in message
    assert "https://***@gitlab.example.com/group/repo.git" in message


def test_source_subfolder_cannot_escape_the_clone(monkeypatch: pytest.MonkeyPatch, tmp_path):
    source = "https://gitlab.example.com/group/repo.git//../../etc"

    def fake_run(*args, **kwargs):
        # Pretend the clone succeeded; the returned temp dir is what matters.
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr(generator.subprocess, "run", fake_run)
    monkeypatch.setattr(generator.tempfile, "TemporaryDirectory", lambda: _FakeTempDir(tmp_path))

    with pytest.raises(RuntimeError, match="escapes the cloned repository"):
        generator._handle_git_source(source)


class _FakeTempDir:
    def __init__(self, path):
        self.name = str(path)

    def cleanup(self):
        return None
