import io
import subprocess
import pytest
from PIL import Image
from farmbot.adb import ADB, ADBError


class FakeCompleted:
    def __init__(self, stdout=b"", returncode=0):
        self.stdout = stdout
        self.returncode = returncode


def _png_bytes(w=4, h=3, color=(10, 20, 30)):
    buf = io.BytesIO()
    Image.new("RGB", (w, h), color).save(buf, format="PNG")
    return buf.getvalue()


def test_device_ready_true_when_state_is_device():
    calls = []
    def runner(cmd, **kw):
        calls.append(cmd)
        return FakeCompleted(stdout=b"device\n")
    adb = ADB("emulator-5554", runner=runner)
    assert adb.device_ready() is True
    assert calls[0] == ["adb", "-s", "emulator-5554", "get-state"]


def test_device_ready_false_when_offline():
    adb = ADB("s", runner=lambda cmd, **kw: FakeCompleted(stdout=b"offline\n"))
    assert adb.device_ready() is False


def test_screencap_returns_image():
    adb = ADB("s", runner=lambda cmd, **kw: FakeCompleted(stdout=_png_bytes(4, 3)))
    img = adb.screencap()
    assert img.size == (4, 3)


def test_tap_issues_input_tap():
    calls = []
    adb = ADB("s", runner=lambda cmd, **kw: calls.append(cmd) or FakeCompleted())
    adb.tap(120, 240)
    assert calls[0] == ["adb", "-s", "s", "shell", "input", "tap", "120", "240"]


def test_swipe_issues_input_swipe():
    calls = []
    adb = ADB("s", runner=lambda cmd, **kw: calls.append(cmd) or FakeCompleted())
    adb.swipe(1, 2, 3, 4, ms=250)
    assert calls[0] == ["adb", "-s", "s", "shell", "input", "swipe", "1", "2", "3", "4", "250"]


def test_adb_passes_timeout_to_runner():
    # A hung adb call must be bounded so control returns to the task loop and the
    # kill-switch is honored; the runner therefore always gets timeout=<value>.
    captured = {}
    def runner(cmd, **kw):
        captured.update(kw)
        return FakeCompleted(stdout=b"device\n")
    adb = ADB("s", runner=runner, timeout=12.5)
    adb.device_ready()
    assert captured.get("timeout") == 12.5


def test_screencap_retries_then_succeeds_after_timeout():
    good = _png_bytes(4, 3)
    seq = [subprocess.TimeoutExpired(cmd="adb", timeout=20.0), FakeCompleted(stdout=good)]
    calls = {"n": 0}
    def runner(cmd, **kw):
        item = seq[calls["n"]]
        calls["n"] += 1
        if isinstance(item, BaseException):
            raise item
        return item
    slept = []
    adb = ADB("s", runner=runner, sleeper=lambda s: slept.append(s))
    img = adb.screencap()
    assert img.size == (4, 3)
    assert calls["n"] == 2          # failed once, retried once
    assert len(slept) == 1          # slept between the two attempts (no real sleep)


def test_screencap_retries_then_succeeds_after_bad_bytes():
    seq = [FakeCompleted(stdout=b"not-a-png"), FakeCompleted(stdout=_png_bytes(2, 2))]
    calls = {"n": 0}
    def runner(cmd, **kw):
        item = seq[calls["n"]]
        calls["n"] += 1
        return item
    adb = ADB("s", runner=runner, sleeper=lambda s: None)
    img = adb.screencap()
    assert img.size == (2, 2)
    assert calls["n"] == 2


def test_screencap_raises_adberror_after_exhausting_retries():
    def runner(cmd, **kw):
        raise subprocess.TimeoutExpired(cmd="adb", timeout=20.0)
    slept = []
    adb = ADB("s", runner=runner, sleeper=lambda s: slept.append(s))
    with pytest.raises(ADBError):
        adb.screencap()
    assert slept                    # retried (and slept) before giving up


def test_screencap_raises_adberror_when_bytes_never_parse():
    adb = ADB("s", runner=lambda cmd, **kw: FakeCompleted(stdout=b"garbage"),
              sleeper=lambda s: None)
    with pytest.raises(ADBError):
        adb.screencap()
