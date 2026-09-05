"""The PreToolUse image-budget guard.

Regression cover for the 2026-09-05 session death: 224 images / 29.9MB of base64
against a 30MB request cap. The guard existed and was never wired; when it was
read, it also disarmed itself.
"""
import importlib.util
import json
import os

import pytest

HOOK = os.path.join(os.path.dirname(__file__), "..", "scripts", "hooks", "shrink_read_images.py")


def _load():
    spec = importlib.util.spec_from_file_location("shrink_read_images", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def hook():
    return _load()


def _dump(obj):
    # Claude Code writes compact JSON; the old substring matcher was sensitive to
    # exactly this, so the fixtures have to reproduce it.
    return json.dumps(obj, separators=(",", ":"))


def _image_line(nbytes, kind="user"):
    """A transcript line carrying one base64 image of roughly nbytes."""
    return _dump({
        "type": kind,
        "message": {"role": "user", "content": [{
            "type": "tool_result",
            "tool_use_id": "toolu_x",
            "content": [{"type": "image", "source": {"type": "base64",
                                                     "media_type": "image/png",
                                                     "data": "A" * nbytes}}],
        }]},
    })


def _write(tmp_path, lines):
    p = tmp_path / "transcript.jsonl"
    p.write_text("\n".join(lines) + "\n")
    return str(p)


def test_counts_base64_image_payload(hook, tmp_path):
    t = _write(tmp_path, [_image_line(3000), _image_line(5000)])
    assert hook.banked_image_bytes(t) == 8000


def test_real_compact_boundary_resets_the_tally(hook, tmp_path):
    boundary = _dump({"type": "system", "subtype": "compact_boundary"})
    t = _write(tmp_path, [_image_line(9000), boundary, _image_line(2500)])
    assert hook.banked_image_bytes(t) == 2500


def test_prose_mentioning_the_marker_does_not_disarm_the_guard(hook, tmp_path):
    """Reading this hook's own source must not zero the tally.

    The old implementation substring-matched '"compact_boundary"' against the raw
    line, so any transcript entry quoting the marker - a Read of the hook, a grep
    of it, this very test - silently reset the budget to zero and let the session
    run straight into the 400.
    """
    quoting = _dump({
        "type": "user",
        "message": {"role": "user", "content": [{
            "type": "tool_result",
            "tool_use_id": "toolu_y",
            "content": 'COMPACT_MARKERS = (\'"isCompactSummary":true\', \'"compact_boundary"\', \'"type":"summary"\')',
        }]},
    })
    t = _write(tmp_path, [_image_line(9000), quoting, _image_line(2500)])
    assert hook.banked_image_bytes(t) == 11500


def test_microcompact_does_not_reset(hook, tmp_path):
    """Microcompact clears tool results selectively, so a full reset under-counts.

    Over-counting costs one refused Read; under-counting costs the whole session.
    """
    boundary = _dump({"type": "system", "subtype": "microcompact_boundary"})
    t = _write(tmp_path, [_image_line(9000), boundary, _image_line(2500)])
    assert hook.banked_image_bytes(t) == 11500


def test_missing_transcript_is_zero_not_a_crash(hook):
    assert hook.banked_image_bytes(None) == 0
    assert hook.banked_image_bytes("/nonexistent/transcript.jsonl") == 0


def test_decide_allows_a_fresh_session(hook):
    assert hook.decide(0) is None


def test_decide_warns_before_it_refuses(hook):
    verdict = hook.decide(hook.WARN_BYTES + 1)
    assert verdict is not None
    kind, _ = verdict
    assert kind == "warn"


def test_decide_refuses_over_budget(hook):
    kind, message = hook.decide(hook.BUDGET_BYTES + 1)
    assert kind == "deny"
    assert "/clear" in message


def test_budget_leaves_headroom_under_the_api_cap(hook):
    """20MB banked plus a turn's own payload has to stay under 30MB."""
    assert hook.BUDGET_BYTES < 30_000_000
    assert 30_000_000 - hook.BUDGET_BYTES >= 5_000_000
    assert hook.WARN_BYTES < hook.BUDGET_BYTES


def test_screenshot_tools_are_budget_checked(hook):
    """5 of the 224 killing images came from chrome-devtools, not Read."""
    assert any("take_screenshot" in t for t in hook.IMAGE_TOOLS)
    assert any("browser_take_screenshot" in t for t in hook.IMAGE_TOOLS)
    assert "Read" in hook.IMAGE_TOOLS
