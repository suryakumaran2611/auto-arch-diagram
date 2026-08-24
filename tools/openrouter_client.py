"""OpenRouter client with strict FREE-model enforcement and vision support.

Design goals (nothing hardcoded architecturally):
- Model selection is computed live from OpenRouter's /models catalog:
  only $0-cost models with image+text input qualify; ranking prefers stable
  instruction-tuned general models over previews/safety/utility variants,
  then largest context window.
- Any explicit model override must still pass the free+vision checks or the
  call is refused, guaranteeing a zero-dollar budget.
- API key resolution order: OPENROUTER_API_KEY env -> key file at
  ~/.config/auto-arch-diagram/openrouter_key (chmod 600, outside any repo).
"""
from __future__ import annotations

import base64
import json
import os
import re
from pathlib import Path
from typing import Any

import requests

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
KEY_FILE_PATH = Path.home() / ".config" / "auto-arch-diagram" / "openrouter_key"

# Name fragments that indicate special-purpose models unsuitable for
# architecture-diagram analysis. This is capability filtering, not
# architecture-specific hardcoding.
_EXCLUDED_NAME_FRAGMENTS = (
    "content-safety",
    "guard",
    "moderation",
    "embed",
    "rerank",
    "clip",
    "whisper",
    "tts",
    "transcribe",
)

_TIMEOUT_SECONDS = 45

# Sticky-model state: the last model that successfully answered. Checked ONCE,
# then reused directly for every subsequent call; the ranked list is only
# walked again when the sticky model itself fails. Persisted across processes
# (per-example subprocesses) via a small state file.
_STATE_DIR = Path.home() / ".cache" / "auto-arch-diagram"
_PREFERRED_MODEL_FILE = _STATE_DIR / "preferred_model"


def _load_preferred_model() -> str | None:
    try:
        value = _PREFERRED_MODEL_FILE.read_text(encoding="utf-8").strip()
        return value or None
    except OSError:
        return None


def _save_preferred_model(model_id: str | None) -> None:
    try:
        if model_id is None:
            _PREFERRED_MODEL_FILE.unlink(missing_ok=True)
        else:
            _STATE_DIR.mkdir(parents=True, exist_ok=True)
            _PREFERRED_MODEL_FILE.write_text(model_id + "\n", encoding="utf-8")
    except OSError:
        pass


class OpenRouterError(RuntimeError):
    """Raised for configuration, policy, or API failures."""


def load_api_key() -> str | None:
    key = (os.getenv("OPENROUTER_API_KEY") or "").strip()
    if key:
        return key
    try:
        key = KEY_FILE_PATH.read_text(encoding="utf-8").strip()
        return key or None
    except OSError:
        return None


def fetch_catalog(timeout: int = 30) -> list[dict[str, Any]]:
    resp = requests.get(
        f"{OPENROUTER_BASE_URL}/models", timeout=timeout, headers=_headers(optional=True)
    )
    if resp.status_code != 200:
        raise OpenRouterError(f"Failed to fetch model catalog: HTTP {resp.status_code}")
    return resp.json().get("data", [])


def _headers(optional: bool = False) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    key = load_api_key()
    if key:
        headers["Authorization"] = f"Bearer {key}"
    elif not optional:
        raise OpenRouterError(
            "No OpenRouter API key found. Set OPENROUTER_API_KEY or create "
            f"{KEY_FILE_PATH} (chmod 600)."
        )
    return headers


def _pricing_is_free(model: dict[str, Any]) -> bool:
    pricing = model.get("pricing") or {}
    try:
        prompt = float(pricing.get("prompt") or 1)
        completion = float(pricing.get("completion") or 1)
    except (TypeError, ValueError):
        return False
    # Strict: any non-zero price disqualifies the model.
    return prompt == 0.0 and completion == 0.0


def _supports_vision(model: dict[str, Any]) -> bool:
    arch = model.get("architecture") or {}
    mods = arch.get("input_modalities") or arch.get("input_modality") or []
    if isinstance(mods, str):
        mods = [m.strip() for m in mods.split(",")]
    return "image" in {m.lower() for m in mods}


def _is_suitable(model: dict[str, Any]) -> bool:
    mid = model.get("id", "").lower()
    return not any(frag in mid for frag in _EXCLUDED_NAME_FRAGMENTS)


def ranked_free_vision_models(
    catalog: list[dict[str, Any]] | None = None,
    override_model: str | None = None,
) -> list[dict[str, Any]]:
    """Rank all currently-available FREE vision models, best first.

    Ranking: penalize preview/beta/experimental builds and auto-routers,
    then prefer the largest context window.
    """
    catalog = catalog if catalog is not None else fetch_catalog()

    eligible = [
        m
        for m in catalog
        if _pricing_is_free(m) and _supports_vision(m) and _is_suitable(m)
    ]
    if not eligible:
        raise OpenRouterError(
            "No free vision-capable models are currently available on OpenRouter."
        )

    def penalty(model_id: str) -> int:
        score = 0
        mid = model_id.lower()
        if ":free" not in mid and "/" in mid:
            score += 5  # unmarked zero-cost promos rotate away more often
        for frag in ("preview", "beta", "experimental", "alpha"):
            if frag in mid:
                score += 10
        if mid == "openrouter/free":
            score += 20  # meta-router: keep as last resort
        if "gemma" in mid or "llama" in mid or "qwen" in mid or "nemotron" in mid:
            score -= 2  # established open-vision families
        return score

    def rank(model: dict[str, Any]) -> tuple[int, int]:
        pid = str(model.get("id", ""))
        ctx = model.get("context_length") or 0
        return (penalty(pid), -int(ctx))

    eligible.sort(key=rank)

    if override_model:
        wanted = override_model.strip()
        match = next((m for m in eligible if m.get("id") == wanted), None)
        if match is None:
            raise OpenRouterError(
                f"Requested model {wanted!r} refused (not free, not vision-capable, "
                "or unavailable). Budget is $0: only verified free vision models "
                "may be used."
            )
        return [match]

    return eligible


def select_free_vision_model(
    catalog: list[dict[str, Any]] | None = None,
    override_model: str | None = None,
) -> dict[str, Any]:
    """Pick the best currently-available FREE vision model."""
    return ranked_free_vision_models(catalog, override_model)[0]


def chat_completion(
    messages: list[dict[str, Any]],
    model: str,
    *,
    temperature: float = 0.2,
    max_tokens: int = 2000,
    timeout: int = _TIMEOUT_SECONDS,
) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    try:
        resp = requests.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers=_headers(),
            json=payload,
            timeout=(5, timeout),
        )
    except Exception as req_err:
        raise OpenRouterError(f"OpenRouter request failed: {req_err}") from req_err

    if resp.status_code != 200:
        raise OpenRouterError(f"OpenRouter request failed: HTTP {resp.status_code}: {resp.text[:300]}")
    choice = (resp.json().get("choices") or [{}])[0]
    content = (choice.get("message") or {}).get("content") or ""
    if not content.strip():
        raise OpenRouterError(
            "Model returned empty content "
            f"(finish_reason={choice.get('finish_reason')}); "
            "try a higher max_tokens budget"
        )
    return content


# Statuses worth walking the ranked list for: rate limits, outages, and
# models that are unavailable to this key/harness (403/404). Auth failures
# (401/402) stay fatal - they indicate a configuration problem, not a model.
_FALLBACK_STATUS = {403, 404, 429, 500, 502, 503, 504}


def chat_completion_with_fallback(
    messages: list[dict[str, Any]],
    models: list[str],
    *,
    temperature: float = 0.2,
    max_tokens: int = 2000,
    timeout: int = 45,
    max_models: int | None = None,
) -> tuple[str, str]:
    """Try ranked free models in order; fall through on rate limits/outages.

    Walks the ENTIRE ranked list by default - an exhausted candidate never
    blocks later (possibly healthier) models. Pass `max_models` to cap.
    Returns (content, model_that_answered).
    """
    last_error: Exception | None = None
    candidates = models if max_models is None else list(models[:max_models])
    # Sticky model first: skip re-probing dead candidates on every call.
    preferred = _load_preferred_model()
    if preferred and preferred in candidates:
        candidates.remove(preferred)
        candidates.insert(0, preferred)
    for model_id in candidates:
        try:
            content = chat_completion(
                messages,
                model_id,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
            )
            _save_preferred_model(model_id)  # remember for all subsequent calls
            return content, model_id
        except Exception as exc:
            if model_id == preferred:
                _save_preferred_model(None)
            print(f"[ai-enhance] {model_id} failed ({exc}); trying next free model")
            last_error = exc
            continue
    raise OpenRouterError(
        f"All candidate free models failed: {last_error}"
    ) if last_error else OpenRouterError("No candidate models provided.")


def _image_data_url(png_path: Path) -> str:
    data = png_path.read_bytes()
    return "data:image/png;base64," + base64.b64encode(data).decode("ascii")


_CRITIQUE_PROMPT = """You are a principal cloud enterprise architect reviewing an auto-generated \
architecture diagram rendered from Infrastructure-as-Code.

The image shows the rendered diagram. The Mermaid source and the parsed resource \
inventory are provided for cross-checking.

Produce comprehensive architectural contributions:
1) A quality score for the DIAGRAM layout (readability, grouping, edge routing).
2) An executive Title and Subtitle summarizing the platform capability.
3) Context hints explaining operational semantics, storage, encryption, and data retention.
4) Contextual display labels and operational Tooltips for key resources.
5) Flow step labels describing data/control flow paths between components.
6) Markdown insights on architecture design, scalability, and security posture.

Respond with STRICT JSON only (no markdown fence, no prose):
{
  "score": <integer 0-10 diagram quality>,
  "title": "<executive title, max 6 words, e.g. 'Enterprise MLOps & Data Platform'>",
  "subtitle": "<operational summary, max 12 words, e.g. 'Multi-region automated training and inference pipeline'>",
  "hints": [{"tag": "s3|secrets|kms|iam|compute|network|data|general", "text": "<max 15 words>"}],
  "labels": {"<resource-name-part>": "<contextual display label, max 5 words>"},
  "tooltips": {"<resource-name-part>": "<purpose, scaling, security details, max 20 words>"},
  "flow_labels": {"<source_resource -> target_resource>": "<numbered action, e.g. '1. Ingest Events'>"},
  "insights_md": "<markdown summary (<=150 words): architecture summary, dataflow stages, security & scaling>",
  "suggestions": [{"action": "increase_spacing|change_splines|enlarge_fonts|reduce_edge_noise",
                   "params": {"multiplier": 1.25}}]
}
Label, Tooltip & Layout rules (strict):
- Architecture Flow: Professional cloud architectures follow Left-to-Right (LR) horizontal progression (Ingress -> Compute -> Storage). Preserve LR direction for optimal widescreen reading.
- Ground every label and tooltip in concrete evidence from the inventory.
- Max 5 words for labels, Title Case, no raw terraform prefixes (aws_, azurerm_, etc.).
- Flow labels should be numbered sequentially ('1. Ingress Request', '2. Transform Payload', etc.).
- Propose up to 12 labels and up to 8 flow labels.
Score honestly; reserve 9-10 for diagrams you would publish unchanged."""

_json_block_re = re.compile(r"\{.*\}", re.DOTALL)


def _extract_first_json_object(text: str) -> str | None:
    """Extract the first balanced {...} object, ignoring braces inside strings."""
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escaped = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def _parse_critique_json(raw: str) -> dict[str, Any]:
    """Parse a model's critique, tolerating common LLM JSON mistakes."""
    candidate = _extract_first_json_object(raw) or (
        _json_block_re.search(raw).group(0) if _json_block_re.search(raw) else None
    )
    if not candidate:
        raise OpenRouterError(
            f"Model response did not contain a JSON object: {raw[:300]!r}"
        )
    # Ordered repair ladder: least to most aggressive.
    no_trailing = re.sub(r",\s*([}\]])", r"\1", candidate)
    straight_quotes = re.sub(r"[\u201c\u201d]", '"', no_trailing)
    # Missing commas between items separated by a line break.
    joined = re.sub(r"([\]}])[ \t]*\r?\n[ \t]*(?=[{\"\[])",
                    r"\1,\n", straight_quotes)
    candidates: list[str] = []
    for variant in (candidate, no_trailing, straight_quotes, joined):
        if variant not in candidates:
            candidates.append(variant)
    last_error: Exception | None = None
    for variant in candidates:
        for strict_flag in (True, False):
            try:
                parsed = json.loads(variant, strict=strict_flag)
            except json.JSONDecodeError as exc:
                last_error = exc
                continue
            return parsed if isinstance(parsed, dict) else {}
    raise OpenRouterError(
        f"Model returned invalid JSON: {last_error}; head={candidate[:300]!r}"
    )


def critique_diagram(
    png_path: Path,
    mermaid_text: str,
    resource_summary: str,
    model: str | list[str],
) -> tuple[dict[str, Any], str]:
    """Send the rendered diagram for vision-based critique + validation.

    `model` may be a single id or a ranked list for rate-limit fallback.
    Returns (critique_json, model_that_answered).
    """
    models = [model] if isinstance(model, str) else list(model)
    user_content = [
        {"type": "text", "text": _CRITIQUE_PROMPT},
        {
            "type": "image_url",
            "image_url": {"url": _image_data_url(png_path)},
        },
        {
            "type": "text",
            "text": f"Mermaid source:\n```mermaid\n{mermaid_text}```\n\n"
                    f"Parsed resources ({resource_summary})",
        },
    ]
    last_error: OpenRouterError | None = None
    for _ in range(2):  # one clean retry: model JSON/length behavior is non-deterministic
        raw, answered_by = chat_completion_with_fallback(
            [{"role": "user", "content": user_content}], models, max_tokens=6000
        )
        try:
            return _parse_critique_json(raw), answered_by
        except OpenRouterError as exc:
            last_error = exc
    assert last_error is not None  # noqa: S101 - loop always runs once
    raise last_error
