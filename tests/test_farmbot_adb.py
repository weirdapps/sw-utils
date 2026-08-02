import io
from PIL import Image
from farmbot.adb import ADB


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
