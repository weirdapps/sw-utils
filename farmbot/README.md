# farmbot — SWGOH energy-dump macro (Track B MVP)

⚠️ **PvE only. ToS/ban risk accepted by the owner. Runs on Astra's Mac only.**
Never spends crystals; never touches PvP (Arena/GAC/TW).

## One-time setup (manual)
1. Install **BlueStacks Air** (Apple Silicon). Install SWGOH; **log in as Astra**.
2. Enable ADB: BlueStacks → Settings → Advanced → Android Debug Bridge. Note the serial.
3. Install platform-tools so `adb` is on PATH; confirm `adb devices` lists the emulator.
4. `.venv/bin/pip install -r farmbot/requirements.txt`
5. `cp farmbot/config.example.json farmbot/config.json`; set `device_serial` and your 3★ `nodes`.

## Real energy-dump flow (validated live)
Each node is an independent journey that starts and ends at the hub:
```
HOME (verify) -> tap Campaigns -> Campaigns menu (verify) -> tap <campaign> PLAY
  -> [optional: tap chapter tab] -> tap node icon -> tap MULTI SIM
  -> SIM dialog (auto-filled to max energy) -> tap green SIM -> rewards -> tap home button
```
Multi Sim pre-fills the quantity to the max the current energy allows, so there is no
"set max" step. Energy-out = the confirm is unavailable while an `energy_out` marker shows;
that node is skipped (never refreshed with crystals) and the run recovers to the hub.

## Capture templates (supervised, one-time per game build)
Reusable (shared across all energy types): `home`, `campaigns_entry`, `campaigns_menu`,
`multi_sim`, `sim_confirm`, `rewards`, `dialog_close`, `home_button`, `energy_out`.
Per node: `campaign_<name>` (e.g. `campaign_cantina`, `campaign_light`, `campaign_dark`,
`campaign_fleet`), `node_<campaign>_<id>` (campaign-scoped, e.g. `node_cantina_1-A`,
`node_light_1-D` — so Cantina 1-A and Fleet 1-A don't collide), `chapter_tab_<n>` if the node
sets a `chapter`, and `hard_tab` if it sets `"difficulty": "hard"` (LS/DS/Fleet Hard nodes). Navigate the emulator to each screen, then:
```
.venv/bin/python -m farmbot.run --capture
```
Enter the template name and the crop box. Templates land in `farmbot/templates/`.

Config `nodes` entries: `{ "campaign": <name>, "node": <id>, ["chapter": <n>], "sim": "max" }`.

## Run
- Dry run (prints the node plan, taps nothing): `.venv/bin/python -m farmbot.run --dry-run`
- Live dump: `.venv/bin/python -m farmbot.run --dump`
- **Kill-switch:** Ctrl-C, or `touch farmbot/STOP` (delete it before the next run).
- On any unknown screen the run halts and saves `farmbot/halts/<ts>_<state>.png`.

## Safety model
Every tap is gated by a template match (never blind-taps). Hard `max_actions` cap.
When energy is too low to sim, MULTI SIM opens a **"Purchase Energy" crystal prompt** — the
macro detects this (`energy_out` = its CANCEL button), taps **CANCEL** (never PURCHASE), and
recovers to the hub. It never spends crystals. Verified live: an energy-out run left the crystal
balance unchanged.

## Status
Live-validated on BlueStacks Air (Astra, 2026-08-02): full navigation + a real Multi-Sim (11
battles), the energy-out→CANCEL path (crystals unchanged), and halt-on-unknown all confirmed on
device. Templates captured for the Cantina 1-A flow; other campaigns/nodes need their
`campaign_<name>` / `node_<id>` / `chapter_tab_<n>` templates captured the same way.
