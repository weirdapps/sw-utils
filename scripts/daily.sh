#!/usr/bin/env bash
# One-command SWGOH daily driver: fresh board from live comlink + daily brief.
#
#   ./scripts/daily.sh
#
# Opens the comlink SSH tunnel to the VPS if it isn't already up, recomputes the
# grounded board from the live roster (auto file-fallback if comlink is down),
# renders the daily brief, and opens the HTML.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# 1) comlink tunnel (Mac:3999 -> vps:3000) if not already listening
if ! nc -z localhost 3999 2>/dev/null; then
  echo "· opening comlink tunnel (Mac:3999 -> vps:3000)…"
  ssh -fN -L 3999:127.0.0.1:3000 vps 2>/dev/null || echo "  tunnel failed — falling back to saved roster file"
  sleep 2
fi

# 2) fresh board via live comlink (venv has comlink-python; falls back to file)
echo "· computing board…"
COMLINK_URL=http://localhost:3999 .venv/bin/python scripts/compute_teams.py

# 3) daily brief (stdlib only)
echo "· rendering brief…"
python3 scripts/daily_brief.py

# 4) open the HTML brief
BRIEF="output/brief_$(TZ=Europe/Athens date +%Y-%m-%d).html"
[ -f "$BRIEF" ] && { echo "· opening $BRIEF"; open "$BRIEF"; }
