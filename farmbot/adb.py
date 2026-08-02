"""adb.py — thin ADB wrappers. The ONLY module (with vision) that touches the device."""
import io
import subprocess
from PIL import Image


class ADB:
    def __init__(self, serial, runner=subprocess.run):
        self.serial = serial
        self._run = runner

    def _adb(self, *args, capture=False):
        cmd = ["adb", "-s", self.serial, *args]
        return self._run(cmd, capture_output=capture)

    def device_ready(self):
        out = self._adb("get-state", capture=True)
        return (out.stdout or b"").decode(errors="ignore").strip() == "device"

    def screencap(self):
        out = self._adb("exec-out", "screencap", "-p", capture=True)
        return Image.open(io.BytesIO(out.stdout)).convert("RGB")

    def tap(self, x, y):
        self._adb("shell", "input", "tap", str(int(x)), str(int(y)))

    def swipe(self, x1, y1, x2, y2, ms=300):
        self._adb("shell", "input", "swipe",
                  str(int(x1)), str(int(y1)), str(int(x2)), str(int(y2)), str(int(ms)))
