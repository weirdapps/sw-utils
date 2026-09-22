#!/bin/bash
# s.sh — cheap screencap: ~45KB 800px q40 JPEG (measured 2026-09-22), plus native PNG for OCR.
export ANDROID_SERIAL="${ANDROID_SERIAL:-127.0.0.1:5555}"
ADB=/opt/homebrew/bin/adb
n="${1:-s}"
$ADB exec-out screencap -p > "/tmp/${n}.png" || exit 1
sips -Z 800 "/tmp/${n}.png" --out "/tmp/${n}.jpg" -s format jpeg -s formatOptions 40 >/dev/null 2>&1
ls -la "/tmp/${n}.jpg" | awk '{print $5" bytes  /tmp/'"${n}"'.jpg"}'
