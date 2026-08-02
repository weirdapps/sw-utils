import os
import sys

# Make scripts/ importable as flat modules (matches how the scripts run themselves).
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
# Make the repo root importable so `from farmbot.X import Y` resolves.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
