"""URL helpers for safe logging and source handling.

Credentials embedded in Git URLs (``https://user:token@host/org/repo.git``) must
never reach job logs or uploaded artifacts. These helpers strip userinfo, query
strings and fragments while keeping the URL useful for debugging.
"""

from __future__ import annotations

import os
import re
from typing import Iterable

_URL_WITH_SCHEME_RE = re.compile(
    r"^(?P<scheme>[A-Za-z][A-Za-z0-9+.-]*://)(?P<authority>[^/?#]*)(?P<tail>.*)$",
    re.DOTALL,
)

_INLINE_URL_RE = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*://[^\s'\"<>]+")

# Environment variables that hold credentials in GitHub Actions and GitLab CI.
_SECRET_ENV_VARS = (
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "GOOGLE_AI_KEY",
    "OPENROUTER_API_KEY",
    "OPENAI_API_KEY",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "AUTO_ARCH_GITLAB_TOKEN",
    "AUTO_ARCH_PUSH_TOKEN",
    "AUTO_ARCH_DEPLOY_TOKEN",
    "CI_JOB_TOKEN",
)

_SECRET_PATTERNS = (
    # ?key=..., &api_key=..., ?access_token=...
    re.compile(r"(?i)([?&](?:key|api[_-]?key|access[_-]?token|token)=)[^&\s'\"<>]+"),
    # Authorization: Bearer <token> / Basic <credentials>
    re.compile(r"(?i)(authorization:\s*(?:bearer|basic)\s+)[^\s'\",<>]+"),
    # x-goog-api-key: <token>
    re.compile(r"(?i)(x-goog-api-key:\s*)[^\s'\",<>]+"),
)

_MIN_SECRET_LENGTH = 6


def redact_secrets(text: str, secrets: Iterable[str] = ()) -> str:
    """Remove API keys and tokens from free-form text before logging it.

    Covers literal secret values (explicit ``secrets`` and well-known CI
    environment variables), ``?key=``/``?token=`` query parameters, Authorization
    headers and ``x-goog-api-key`` headers.

    >>> redact_secrets("https://api.example.com/v1?key=abc123")
    'https://api.example.com/v1?key=***'
    """
    if not text:
        return ""

    candidates = list(secrets)
    candidates.extend(os.environ.get(name, "") for name in _SECRET_ENV_VARS)

    redacted = text
    for value in candidates:
        value = (value or "").strip()
        if len(value) >= _MIN_SECRET_LENGTH and value in redacted:
            redacted = redacted.replace(value, "***")

    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub(lambda match: match.group(1) + "***", redacted)

    return redacted


def redact_url(url: str) -> str:
    """Return ``url`` without credentials, query string or fragment.

    >>> redact_url("https://user:token@gitlab.example.com/group/repo.git")
    'https://***@gitlab.example.com/group/repo.git'
    >>> redact_url("https://gitlab.example.com/group/repo.git?private_token=abc")
    'https://gitlab.example.com/group/repo.git'
    """
    if not url:
        return ""

    match = _URL_WITH_SCHEME_RE.match(url)
    if not match:
        return url.split("?", 1)[0].split("#", 1)[0]

    authority = match.group("authority")
    if "@" in authority:
        authority = "***@" + authority.rsplit("@", 1)[1]

    tail = match.group("tail").split("?", 1)[0].split("#", 1)[0]
    return f"{match.group('scheme')}{authority}{tail}"


def redact_text(text: str) -> str:
    """Redact every URL embedded in a free-form message (for example git stderr)."""
    if not text:
        return ""
    return _INLINE_URL_RE.sub(lambda match: redact_url(match.group(0)), text)


def split_git_source(source: str) -> tuple[str, str]:
    """Split ``<repository>[//<subfolder>]`` without breaking ``scheme://``.

    >>> split_git_source("https://host/org/repo.git//terraform")
    ('https://host/org/repo.git', 'terraform')
    >>> split_git_source("git@host:org/repo.git//modules/vpc")
    ('git@host:org/repo.git', 'modules/vpc')
    """
    scheme, separator, rest = source.partition("://")
    if separator:
        repository, marker, subfolder = rest.partition("//")
        if marker:
            return f"{scheme}://{repository}", subfolder.strip("/")
        return source, ""

    if source.startswith("git@"):
        repository, marker, subfolder = source.partition("//")
        if marker:
            return repository, subfolder.strip("/")

    return source, ""
