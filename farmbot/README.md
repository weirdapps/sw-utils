# farmbot — SWGOH energy-dump macro (Track B MVP)

⚠️ **PvE only. ToS/ban risk accepted by the owner. Runs on Astra's Mac only.**
Never spends crystals; never touches PvP (Arena/GAC/TW).

## One-time setup (manual)
1. Install **BlueStacks Air** (Apple Silicon). Install SWGOH; **log in as Astra**.
2. Enable ADB: BlueStacks → Settings → Advanced → Android Debug Bridge. Note the serial.
3. Install platform-tools so `adb` is on PATH; confirm `adb devices` lists the emulator.
4. `.venv/bin/pip install -r farmbot/requirements.txt`
5. `cp farmbot/config.example.json farmbot/config.json`; set `device_serial` and your 3★ `nodes`.

## Capture templates (supervised, one-time per game build)
For each screen the flow needs — `home`, `campaign_<name>`, `node_<id>`, `sim_button`,
`sim_max`, `sim_confirm`, `rewards`, `back`, `energy_out` — navigate the emulator to that
screen, then:
```
.venv/bin/python -m farmbot.run --capture
```
Enter the template name and the crop box. Templates land in `farmbot/templates/`.

## Run
- Dry run (prints the node plan, taps nothing): `.venv/bin/python -m farmbot.run --dry-run`
- Live dump: `.venv/bin/python -m farmbot.run --dump`
- **Kill-switch:** Ctrl-C, or `touch farmbot/STOP` (delete it before the next run).
- On any unknown screen the run halts and saves `farmbot/halts/<ts>_<state>.png`.

## Safety model
Every tap is gated by a template match (never blind-taps). Hard `max_actions` cap.
Energy-out on a node is detected and skipped (never refreshes with crystals).
