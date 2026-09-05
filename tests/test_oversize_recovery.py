"""The StopFailure net under the image-budget guard.

StopFailure is the only hook event that sees the 30MB 400. It cannot unblock the
session (every API call fails past the cap, /compact included), so all it can do is
alert the human and leave a resumable checkpoint behind.
"""
import importlib.util
import json
import os

import pytest

HOOK = os.path.join(os.path.dirname(__file__), "..", "scripts", "hooks", "oversize_recovery.py")

REAL_400 = ('API Error: 400 [{"error":{"code":400,"message":"The message size '
            '(30040700 bytes) exceeds 30.000MB limit.","status":"FAILED_PRECONDITION"}}]')


def _load():
    spec = importlib.util.spec_from_file_location("oversize_recovery", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def hook():
    return _load()


def _dump(obj):
    return json.dumps(obj, separators=(",", ":"))


def test_recognises_the_real_error(hook):
    assert hook.is_size_cap_400(REAL_400)


def test_ignores_other_failures(hook):
    for other in ("", None, "API Error: 429 quota exceeded",
                  "API Error: 400 invalid model name",
                  "anthropic policy refusal"):
        assert not hook.is_size_cap_400(other)


def _transcript(tmp_path):
    lines = [
        _dump({"type": "user", "message": {"role": "user",
                                           "content": "grind conquest sector 3"}}),
        _dump({"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "text", "text": "Node 7 is the wall; swapping in Wat Tambor."},
            {"type": "tool_use", "name": "TodoWrite", "input": {"todos": [
                {"content": "clear node 7", "status": "in_progress"},
                {"content": "bank the disk", "status": "pending"}]}},
            {"type": "tool_use", "name": "Bash",
             "input": {"command": "python3 scripts/cq_step.py --node 7"}},
        ]}}),
        _dump({"type": "user", "message": {"role": "user", "content": [{
            "type": "tool_result", "tool_use_id": "t1",
            "content": [{"type": "image",
                         "source": {"type": "base64", "data": "Z" * 200_000}}]}]}}),
    ]
    p = tmp_path / "t.jsonl"
    p.write_text("\n".join(lines) + "\n")
    return str(p)


def test_ledger_carries_the_resumable_tail(hook, tmp_path):
    ledger = hook.build_ledger(_transcript(tmp_path))
    assert "grind conquest sector 3" in ledger
    assert "Node 7 is the wall" in ledger
    assert "cq_step.py" in ledger
    assert "clear node 7" in ledger and "in_progress" in ledger


def test_ledger_never_carries_image_payload(hook, tmp_path):
    ledger = hook.build_ledger(_transcript(tmp_path))
    assert "ZZZZZZZZZZ" not in ledger
    assert len(ledger) <= hook.MAX_LEDGER_CHARS


def test_ledger_drops_the_sessions_own_400s(hook, tmp_path):
    """The tail of a dying session is mostly its own error messages."""
    p = tmp_path / "t.jsonl"
    p.write_text("\n".join([
        _dump({"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "text", "text": "Placing the Inquisitorius wall in Trenches."}]}}),
        _dump({"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "text", "text": REAL_400}]}}),
    ]) + "\n")
    ledger = hook.build_ledger(str(p))
    assert "Inquisitorius wall" in ledger
    assert "30040700" not in ledger


def test_ledger_is_none_without_a_transcript(hook):
    assert hook.build_ledger(None) is None
    assert hook.build_ledger("/nonexistent.jsonl") is None


def _run(hook, tmp_path, monkeypatch, last_message, existing=None):
    """Drive main() end to end against a fake cwd, with the alert stubbed out."""
    alerts = []
    monkeypatch.setattr(hook, "notify", lambda note: alerts.append(note))
    (tmp_path / "memory").mkdir(exist_ok=True)
    target = tmp_path / "memory" / "session_state.md"
    if existing is not None:
        target.write_text(existing)
    payload = {"last_assistant_message": last_message, "cwd": str(tmp_path),
               "transcript_path": _transcript(tmp_path), "hook_event_name": "StopFailure"}
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO(_dump(payload)))
    with pytest.raises(SystemExit) as exc:
        hook.main()
    assert exc.value.code == 0
    return alerts, target


def test_writes_the_checkpoint_and_alerts(hook, tmp_path, monkeypatch):
    alerts, target = _run(hook, tmp_path, monkeypatch, REAL_400)
    assert alerts, "the human has to be told; the model cannot be reached"
    assert target.is_file()
    assert "cq_step.py" in target.read_text()


def test_does_nothing_on_an_unrelated_failure(hook, tmp_path, monkeypatch):
    alerts, target = _run(hook, tmp_path, monkeypatch, "API Error: 429 quota exceeded")
    assert not alerts
    assert not target.exists()


def test_preserves_a_handwritten_checkpoint(hook, tmp_path, monkeypatch):
    """A ledger Claude wrote on purpose outranks anything reconstructed after the fact."""
    _, target = _run(hook, tmp_path, monkeypatch, REAL_400,
                     existing="# where I am\nMid-way through the Vol-24 feat map.\n")
    body = target.read_text()
    assert "Vol-24 feat map" in body
    assert "cq_step.py" in body


def test_does_not_stack_its_own_checkpoints(hook, tmp_path, monkeypatch):
    _run(hook, tmp_path, monkeypatch, REAL_400)
    _, target = _run(hook, tmp_path, monkeypatch, REAL_400)
    assert target.read_text().count(hook.BANNER) == 1
