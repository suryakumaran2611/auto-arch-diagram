"""Unit tests for the AI enhancement stack.

Covers the OpenRouter client (free-model enforcement, fallbacks, JSON
critique parsing), the vision feedback loop (render suggestion mapping,
plateau/early-stop), contextual label overrides, and the standalone
guide render + stitch helpers.
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import openrouter_client as orc
import diagram_feedback as feedback
import generate_arch_diagram as gen


@pytest.fixture(autouse=True)
def _isolated_sticky_model_state(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Every test gets isolated sticky-model state; never touch the real cache."""
    monkeypatch.setattr(orc, "_PREFERRED_MODEL_FILE", tmp_path / "preferred_model")


# --------------------------------------------------------------------- key
def test_load_api_key_prefers_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "  env-key  ")
    assert orc.load_api_key() == "env-key"


def test_load_api_key_falls_back_to_keyfile(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    keyfile = tmp_path / "openrouter_key"
    keyfile.write_text("file-key\n", encoding="utf-8")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr(orc, "KEY_FILE_PATH", keyfile)
    assert orc.load_api_key() == "file-key"


def test_load_api_key_missing_returns_none(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr(orc, "KEY_FILE_PATH", tmp_path / "absent")
    assert orc.load_api_key() is None


# ------------------------------------------------------- catalog filtering
def _model(mid: str, *, free: bool = True, vision: bool = True, ctx: int = 8000) -> dict:
    return {
        "id": mid,
        "context_length": ctx,
        "pricing": {
            "prompt": "0" if free else "0.001",
            "completion": "0" if free else "0.002",
        },
        "architecture": {
            "input_modalities": ["image", "text"] if vision else ["text"],
        },
    }


def test_ranked_models_filters_paid_and_non_vision() -> None:
    catalog = [
        _model("paid/vendor-model", free=False),
        _model("free/text-only", vision=False),
        _model("mod-guard/free", vision=True),
        _model("acme/free-vision"),
    ]
    ranked = orc.ranked_free_vision_models(catalog=catalog)
    ids = [m["id"] for m in ranked]
    assert "paid/vendor-model" not in ids
    assert "free/text-only" not in ids
    assert "mod-guard/free" not in ids  # moderation/guard filtering
    assert ids == ["acme/free-vision"]


def test_ranked_models_penalizes_previews_and_router() -> None:
    catalog = [
        _model("vendor/model-preview", ctx=100000),
        _model("openrouter/free", ctx=200000),
        _model("meta-llama/llama-3.2-11b-vision:free", ctx=8000),
        _model("google/gemma-3-27b-it:free", ctx=128000),
    ]
    ids = [m["id"] for m in orc.ranked_free_vision_models(catalog=catalog)]
    assert ids[0].startswith(("meta-llama/", "google/"))
    assert "openrouter/free" not in ids[:2]
    assert "vendor/model-preview" not in ids[:2]


def test_ranked_models_override_must_be_free_and_vision() -> None:
    catalog = [
        _model("acme/free-vision"),
        _model("paid/vendor-model", free=False),
    ]
    picked = orc.ranked_free_vision_models(catalog=catalog, override_model="acme/free-vision")
    assert [m["id"] for m in picked] == ["acme/free-vision"]
    with pytest.raises(orc.OpenRouterError):
        orc.ranked_free_vision_models(catalog=catalog, override_model="paid/vendor-model")
    with pytest.raises(orc.OpenRouterError):
        orc.ranked_free_vision_models(catalog=catalog, override_model="does/not-exist")


def test_no_eligible_models_raises() -> None:
    with pytest.raises(orc.OpenRouterError):
        orc.ranked_free_vision_models(catalog=[_model("text/only", vision=False)])


# ------------------------------------------------------- completion calls
class _Resp(SimpleNamespace):
    def json(self) -> dict:
        return self._json  # type: ignore[attr-defined]


def test_fallback_walks_models_on_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_post(url, headers=None, json=None, timeout=None):  # noqa: A002
        model = json["model"]
        calls.append(model)
        if model == "m1":
            return _Resp(status_code=429, text="rate limited", _json={})
        return _Resp(
            status_code=200,
            _json={"choices": [{"message": {"content": "ok"}}]},
        )

    monkeypatch.setattr(orc.requests, "post", fake_post)
    content, answered = orc.chat_completion_with_fallback(
        [{"role": "user", "content": "hi"}], ["m1", "m2"]
    )
    assert content == "ok"
    assert answered == "m2"
    assert calls == ["m1", "m2"]


def test_fallback_walks_entire_ranked_list(monkeypatch: pytest.MonkeyPatch) -> None:
    """An exhausted candidate must never block later ranked models."""
    exhausted = {f"m{i}" for i in range(1, 6)}

    def fake_post(url, headers=None, json=None, timeout=None):  # noqa: A002
        model = json["model"]
        if model in exhausted:
            return _Resp(status_code=429, text="rate limited", _json={})
        return _Resp(
            status_code=200,
            _json={"choices": [{"message": {"content": f"from-{model}"}}]},
        )

    monkeypatch.setattr(orc.requests, "post", fake_post)
    ranked = [f"m{i}" for i in range(1, 8)]  # m1..m5 dead, m6 answers
    content, answered = orc.chat_completion_with_fallback(
        [{"role": "user", "content": "hi"}], ranked
    )
    assert answered == "m6"
    assert content == "from-m6"
    # Explicit cap still honored.
    with pytest.raises(orc.OpenRouterError):
        orc.chat_completion_with_fallback([{"role": "user", "content": "hi"}], ranked, max_models=2)


def test_sticky_model_reused_and_persisted(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """After discovery the working model is called directly on every later call."""
    state_file = tmp_path / "preferred_model"
    monkeypatch.setattr(orc, "_PREFERRED_MODEL_FILE", state_file)

    calls: list[str] = []

    def fake_post(url, headers=None, json=None, timeout=None):  # noqa: A002
        model = json["model"]
        calls.append(model)
        if model == "dead1":
            return _Resp(status_code=429, text="rate limited", _json={})
        return _Resp(
            status_code=200,
            _json={"choices": [{"message": {"content": f"from-{model}"}}]},
        )

    monkeypatch.setattr(orc.requests, "post", fake_post)

    # First call walks past dead1 and sticks to good2.
    _, answered = orc.chat_completion_with_fallback(
        [{"role": "user", "content": "hi"}], ["dead1", "good2"]
    )
    assert answered == "good2"
    assert calls == ["dead1", "good2"]
    assert state_file.read_text().strip() == "good2"

    # Second call goes straight to the sticky model - no re-probing.
    _, answered = orc.chat_completion_with_fallback(
        [{"role": "user", "content": "hi"}], ["dead1", "good2"]
    )
    assert answered == "good2"
    assert calls == ["dead1", "good2", "good2"]


def test_sticky_model_cleared_on_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """When the sticky model dies it is forgotten so a new one can stick."""
    state_file = tmp_path / "preferred_model"
    state_file.write_text("was-good\n", encoding="utf-8")
    monkeypatch.setattr(orc, "_PREFERRED_MODEL_FILE", state_file)

    def fake_post(url, headers=None, json=None, timeout=None):  # noqa: A002
        model = json["model"]
        if model in {"was-good", "also-dead"}:
            return _Resp(status_code=429, text="rate limited", _json={})
        return _Resp(
            status_code=200,
            _json={"choices": [{"message": {"content": f"from-{model}"}}]},
        )

    monkeypatch.setattr(orc.requests, "post", fake_post)
    _, answered = orc.chat_completion_with_fallback(
        [{"role": "user", "content": "hi"}], ["was-good", "also-dead", "new-good"]
    )
    assert answered == "new-good"
    assert state_file.read_text().strip() == "new-good"


def test_fallback_does_not_retry_client_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(url, headers=None, json=None, timeout=None):  # noqa: A002
        return _Resp(status_code=400, text="bad request", _json={})

    monkeypatch.setattr(orc.requests, "post", fake_post)
    with pytest.raises(orc.OpenRouterError):
        orc.chat_completion_with_fallback([{"role": "user", "content": "hi"}], ["m1", "m2"])


def test_critique_diagram_parses_json_from_prose(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    png = tmp_path / "d.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 16)
    raw = 'Sure! {"score": 8, "hints": [{"tag": "s3", "text": "assets_bucket stores site"}]} hope that helps'
    monkeypatch.setattr(
        orc, "chat_completion_with_fallback", lambda *a, **k: (raw, "test-model")
    )
    critique, model = orc.critique_diagram(png, "flowchart LR", "AWS:", "test-model")
    assert critique["score"] == 8
    assert model == "test-model"


def test_critique_diagram_rejects_non_json(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    png = tmp_path / "d.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 16)
    monkeypatch.setattr(
        orc, "chat_completion_with_fallback", lambda *a, **k: ("no json here", "m")
    )
    with pytest.raises(orc.OpenRouterError):
        orc.critique_diagram(png, "flowchart LR", "AWS:", "m")


# --------------------------------------------------------- feedback loop
def test_apply_suggestion_mappings() -> None:
    render = gen.RenderConfig()
    spaced = feedback.apply_suggestion(render, "increase_spacing", {"multiplier": 1.5})
    assert spaced.min_nodesep == pytest.approx(render.min_nodesep * 1.5)
    assert spaced.min_ranksep == pytest.approx(render.min_ranksep * 1.5)

    splined = feedback.apply_suggestion(render, "change_splines", None)
    assert splined.edge_routing == "polyline"

    fonts = feedback.apply_suggestion(render, "enlarge_fonts", None)
    assert fonts.node_fontsize == render.node_fontsize + 1

    quiet = feedback.apply_suggestion(render, "reduce_edge_noise", None)
    assert quiet.concentrate is True

    untouched = feedback.apply_suggestion(render, "unknown_action", None)
    assert untouched is render


def test_flip_direction() -> None:
    assert feedback.flip_direction("LR") == "TB"
    assert feedback.flip_direction("tb") == "LR"


def test_run_feedback_loop_without_key_is_noop(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr(orc, "load_api_key", lambda: None)
    render = gen.RenderConfig()
    out = feedback.run_feedback_loop({}, set(), direction="LR", render=render, title="t")
    assert out[0] is render
    assert out[1] == "LR"
    assert out[2] == {}
    assert out[3] == []


def test_run_feedback_loop_stops_on_target_score(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(orc, "load_api_key", lambda: "k")
    monkeypatch.setattr(
        orc,
        "ranked_free_vision_models",
        lambda override_model=None: [{"id": "test/vision:free"}],
    )

    rendered: list[str] = []

    def fake_render(resources, edges, *, out_path, title, direction, render):
        rendered.append(str(out_path))
        return None

    critiques = iter(
        [
            ({"score": 9, "hints": [], "labels": {}}, "test/vision:free"),
        ]
    )
    monkeypatch.setattr(gen, "_render_icon_diagram_from_terraform", fake_render)
    monkeypatch.setattr(orc, "critique_diagram", lambda *a, **k: next(critiques))

    render = gen.RenderConfig()
    best_render, best_dir, critique, history = feedback.run_feedback_loop(
        {"aws_s3_bucket.a": {}},
        set(),
        direction="LR",
        render=render,
        title="t",
    )
    assert len(history) == 1  # target score reached on first iteration
    assert critique["score"] == 9
    assert best_render is render
    assert best_dir == "LR"
    assert len(rendered) == 1


def test_run_feedback_loop_applies_suggestions_then_plateaus(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(orc, "load_api_key", lambda: "k")
    monkeypatch.setattr(
        orc,
        "ranked_free_vision_models",
        lambda override_model=None: [{"id": "test/vision:free"}],
    )
    monkeypatch.setattr(gen, "_render_icon_diagram_from_terraform", lambda *a, **k: None)

    # Constant mediocre scores: stagnation counter must stop after two
    # non-improving iterations (not immediately after the second render).
    critiques = iter(
        (
            {"score": 5, "suggestions": [{"action": "increase_spacing", "params": {}}]},
            {"score": 5, "suggestions": [{"action": "change_splines", "params": {}}]},
            {"score": 5, "suggestions": []},
            {"score": 5, "suggestions": []},
        )
    )

    def fake_critique(*args, **kwargs):
        return next(critiques), "test/vision:free"

    monkeypatch.setattr(orc, "critique_diagram", fake_critique)

    _, _, _, history = feedback.run_feedback_loop(
        {"aws_s3_bucket.a": {}}, set(), direction="LR", render=gen.RenderConfig(), title="t"
    )
    assert [h["score"] for h in history] == [5, 5, 5]


def test_format_insights_markdown_sections() -> None:
    md = feedback.format_insights_markdown(
        {
            "score": 8,
            "insights_md": "Static website served from S3.",
            "hints": [{"tag": "s3", "text": "assets_bucket stores static files"}],
            "labels": {"assets_bucket": "Static Assets"},
            "issues": [{"type": "layout", "detail": "dense region"}],
        },
        [{"iteration": 0, "score": 7, "model": "m"}, {"iteration": 1, "score": 8, "model": "m"}],
        "test/model",
    )
    assert "AI Architecture Insights" in md
    assert "`[S3]` assets_bucket stores static files" in md
    assert "iter0: 7/10" in md
    assert feedback.format_insights_markdown({}, [], "") == ""


# ------------------------------------------------------ label overrides
def test_sanitize_label_rules() -> None:
    assert gen._sanitize_label("  Primary   Database (Multi-AZ)!  ") == "Primary Database (Multi-AZ)"
    assert gen._sanitize_label("<script>alert(1)</script>") == "scriptalert(1)/script"
    assert gen._sanitize_label("!!!") is None
    assert gen._sanitize_label(123) is None
    assert len(gen._sanitize_label("x" * 100)) <= 32


def test_extract_label_overrides_matches_ids_and_names() -> None:
    resources = {
        "aws_s3_bucket.assets_bucket": {},
        "aws_db_instance.postgres_db": {},
        "aws_instance.web": {},
    }
    overrides = gen._extract_label_overrides(
        {
            "labels": {
                "aws_s3_bucket.assets_bucket": "Versioned Static Assets",
                "postgres_db": "Primary Database",
                "unknown_resource": "Ignored",
                "aws_instance.web": "!!!",
            }
        },
        resources,
    )
    assert overrides == {
        "aws_s3_bucket.assets_bucket": "Versioned Static Assets",
        "aws_db_instance.postgres_db": "Primary Database",
    }


def test_label_override_changes_node_label(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gen, "_CURRENT_LABEL_OVERRIDES", {"web": "Frontend Web Tier"})
    assert "Frontend Web Tier" in gen._tf_node_label("aws_instance.web")
    monkeypatch.setattr(gen, "_CURRENT_LABEL_OVERRIDES", {})
    assert "web" in gen._tf_node_label("aws_instance.web")


def test_build_ai_annotations_hints_and_legacy_fallback() -> None:
    hints = gen._build_ai_annotations(
        {"hints": [{"tag": "s3", "text": "assets_bucket serves site"}, "bad"]}
    )
    assert hints == ("[S3] assets_bucket serves site",)
    legacy = gen._build_ai_annotations(
        {
            "insights_md": "## Overview\nServes a static site.\n",
            "strengths": ["clear grouping"],
            "issues": [{"type": "layout", "detail": "crowded"}],
        }
    )
    assert any("static site" in h for h in legacy)
    assert legacy[-2] == "+ clear grouping"
    assert legacy[-1].startswith("! [layout]")


def test_wrap_hint_respects_width() -> None:
    wrapped = gen._wrap_hint(" ".join(["word"] * 30), width=20)
    assert all(len(line) <= 20 for line in wrapped.splitlines())


# ------------------------------------------------ guide render + stitch
def test_render_guide_png_creates_image(tmp_path: Path) -> None:
    out = tmp_path / "guide.png"
    ok = gen._render_guide_png(
        gen.RenderConfig(),
        ("[S3] assets_bucket serves static content", "[KMS] kms_key encrypts bucket"),
        out,
    )
    if ok:  # graphviz available in CI/dev environments
        from PIL import Image

        with Image.open(out) as im:
            assert im.width > 0 and im.height > 0


def test_stitch_guide_below_raster(tmp_path: Path) -> None:
    pytest.importorskip("PIL")
    from PIL import Image

    diagram = tmp_path / "diagram.png"
    Image.new("RGBA", (400, 300), (0, 0, 0, 0)).save(diagram)
    guide = tmp_path / "guide.png"
    Image.new("RGB", (500, 120), "#EEEEEE").save(guide)

    assert gen._stitch_guide_below(diagram, guide) is True
    with Image.open(diagram) as stitched:
        assert stitched.mode == "RGB"
        assert stitched.width == 400
        # Transparent regions were flattened onto white, not black.
        assert stitched.getpixel((10, 10)) == (255, 255, 255)

        # The guide strip must stay a footnote: at most ~8% of page area.
        pixels = stitched.load()
        xs = [
            x
            for x in range(stitched.width)
            if pixels[x, stitched.height - 10] == (238, 238, 238)
        ]
        ys = [
            y
            for y in range(stitched.height)
            if pixels[stitched.width // 2, y] == (238, 238, 238)
        ]
        assert xs and ys, "expected a visible guide strip"
        guide_fraction = (len(xs) * len(ys)) / (stitched.width * stitched.height)
        assert guide_fraction <= 0.09


def test_append_guide_to_svg_extends_canvas(tmp_path: Path) -> None:
    pytest.importorskip("PIL")
    import xml.etree.ElementTree as ET

    from PIL import Image

    svg = tmp_path / "diagram.svg"
    svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'xmlns:xlink="http://www.w3.org/1999/xlink" width="600pt" height="400pt" '
        'viewBox="0 0 600 400"><g id="graph0"></g></svg>',
        encoding="utf-8",
    )
    guide = tmp_path / "guide.png"
    Image.new("RGB", (300, 150), "#DDDDDD").save(guide)

    assert gen._append_guide_to_svg(svg, guide) is True
    text = svg.read_text(encoding="utf-8")
    assert "data:image/png;base64," in text

    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    root = ET.fromstring(text)
    total_h = float(root.get("height").removesuffix("pt"))
    images = root.findall("{http://www.w3.org/2000/svg}image")
    assert len(images) == 1
    img = images[0]
    img_w = float(img.get("width"))
    img_h = float(img.get("height"))

    # Embedded guide stays a footnote: at most ~8% of the final page area.
    assert (img_w * img_h) / (600 * total_h) <= 0.085
    # Centered horizontally within the original canvas.
    assert abs(float(img.get("x")) + img_w / 2 - 300) < 1.5
    # Canvas grew only modestly.
    assert total_h < 400 * 1.4


def test_stitch_guide_below_missing_files_is_noop(tmp_path: Path) -> None:
    assert gen._stitch_guide_below(tmp_path / "nope.png", tmp_path / "guide.png") is False


# --------------------------------------------------------------- palette
def test_official_provider_palette_constants() -> None:
    assert gen.PROVIDER_ACCENT_COLORS["AWS"] == "#FF9900"
    assert gen.PROVIDER_ACCENT_COLORS["AZURE"] == "#0078D4"
    assert gen.PROVIDER_ACCENT_COLORS["GCP"] == "#4285F4"
    assert gen.PROVIDER_ACCENT_COLORS["OCI"] == "#C74634"
    assert gen.PROVIDER_ACCENT_COLORS["IBM"] == "#0F62FE"
    assert gen._provider_accent("aws") == "#FF9900"
    assert gen._provider_tint("gcp") == "#EDF2FE"
    assert gen._provider_accent("unknown") is None


def test_render_config_defaults_to_white_canvas() -> None:
    assert gen.RenderConfig().background == "white"


def test_drawio_exporter_mirrors_palette(tmp_path: Path) -> None:
    from tools.drawio_exporter import export_drawio

    out = tmp_path / "arch.drawio"
    export_drawio(
        {"aws_s3_bucket.assets": {}, "azurerm_storage_account.sa": {}},
        {("aws_s3_bucket.assets", "azurerm_storage_account.sa")},
        out,
        title="Palette",
        render=gen.RenderConfig(),
    )
    text = out.read_text(encoding="utf-8")
    assert "#FF9900" in text  # AWS accent
    assert "#0078D4" in text  # Azure accent


def test_drawio_exporter_proper_diagram_structure(tmp_path: Path) -> None:
    """Nodes use pretty labels, valid PNG URIs, official AWS shapes; no
    floating utility-provider groups (jgraph AWS-diagram conventions)."""
    import xml.etree.ElementTree as ET

    from tools.drawio_exporter import export_drawio

    resources = {
        "aws_vpc.main": {},
        "aws_instance.web": {},
        "random_password.db_master_password": {"Type": "random_password"},
    }
    edges: set[tuple[str, str]] = set()
    out = tmp_path / "arch.drawio"
    export_drawio(resources, edges, out, title="Structure", render=gen.RenderConfig())

    root = ET.fromstring(out.read_text(encoding="utf-8"))
    vertices = [c for c in root.findall(".//mxCell") if c.get("vertex") == "1"]
    assert vertices

    # No raw terraform ids as node labels.
    assert not [c for c in vertices if c.get("value", "").startswith("aws_")]

    # Every embedded icon is a properly-formed base64 data URI.
    for cell in vertices:
        style = cell.get("style", "")
        if "image=data:image/png," in style:
            assert "image=data:image/png;base64," in style

    # Known AWS resource uses the official mxgraph.aws4 shape library.
    styles = {c.get("value", ""): c.get("style", "") for c in vertices}
    assert any("resIcon=mxgraph.aws4.ec2" in s for s in styles.values())

    # Utility providers fold into a single bucket - no "{X} Cloud" noise.
    values = set(styles)
    assert "Other Resources" in values
    assert not any(v.endswith("RANDOM Cloud") for v in values)

    # White page background like reference diagrams.
    model = root.find(".//mxGraphModel")
    assert model is not None
    assert (model.get("background") or "").lower() == "#ffffff"
