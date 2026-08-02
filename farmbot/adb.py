"""adb.py — thin ADB wrappers. The ONLY module (with vision) that touches the device."""
import io
import subprocess
import time
from PIL import Image

# Bounds every blocking adb call so a hung device can't defeat the kill-switch,
# which is only polled between steps (see run.make_kill_switch / tasks.run).
DEFAULT_TIMEOUT = 20.0
# screencap is the one call that can also return unparseable bytes; retry a few times.
SCREENCAP_RETRIES = 2          # → 3 attempts total
SCREENCAP_RETRY_DELAY = 0.5    # seconds between attempts

# Errors that mean "this capture attempt failed, try again": a timed-out adb call,
# or stdout that PIL can't decode (empty/garbage bytes → UnidentifiedImageError(OSError),
# None stdout → TypeError from io.BytesIO(None)).
_RETRYABLE = (subprocess.TimeoutExpired, OSError, ValueError, TypeError)


class ADBError(Exception):
    """An ADB operation failed after exhausting its retries (catchable, not a raw PIL/subprocess error)."""


class ADB:
    def __init__(self, serial, runner=subprocess.run, timeout=DEFAULT_TIMEOUT,
                 screencap_retries=SCREENCAP_RETRIES, sleeper=time.sleep):
        self.serial = serial
        self._run = runner
        self.timeout = timeout
        self._screencap_retries = screencap_retries
        self._sleeper = sleeper

    def _adb(self, *args, capture=False):
        cmd = ["adb", "-s", self.serial, *args]
        return self._run(cmd, capture_output=capture, timeout=self.timeout)

    def device_ready(self):
        out = self._adb("get-state", capture=True)
        return (out.stdout or b"").decode(errors="ignore").strip() == "device"

    def screencap(self):
        last = None
        for attempt in range(self._screencap_retries + 1):
            try:
                out = self._adb("exec-out", "screencap", "-p", capture=True)
                return Image.open(io.BytesIO(out.stdout)).convert("RGB")
            except _RETRYABLE as exc:
                last = exc
                if attempt < self._screencap_retries:
                    self._sleeper(SCREENCAP_RETRY_DELAY)
        raise ADBError(f"screencap failed after {self._screencap_retries + 1} attempts: {last}") from last

    def tap(self, x, y):
        self._adb("shell", "input", "tap", str(int(x)), str(int(y)))

    def swipe(self, x1, y1, x2, y2, ms=300):
        self._adb("shell", "input", "swipe",
                  str(int(x1)), str(int(y1)), str(int(x2)), str(int(y2)), str(int(ms)))
