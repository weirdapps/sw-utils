# farmbot — SWGOH daily routine bot (PvE only)

⚠️ **PvE only. ToS/ban risk accepted by the owner. Runs on Astra's Mac only.**

Three rails, in order of importance. They are structural, not policy comments:
1. **Never spends crystals.** Every crystal-priced control in the game (the 💎200 energy prompt, the
   💎25 hard-node refresh, the 💎50 shop refresh, crystal-priced shipments) is either a marker that
   is never tapped, or has no template at all so it cannot be found.
2. **Never plays a PvP match.** There is no code path that can. Arena *payouts* are collected from
   the inbox, which needs no battle.
3. **May spend in-game tokens**, and only on an explicit per-item allow-list.

## What it does

One state machine (`tasks.py`), seven entry kinds, all driven from `config.json`:

| kind | what it does | example |
|---|---|---|
| `energy_node` | Multi-Sim a campaign node until the pool is dry | LS Hard 1-D |
| `collect` | tap a free CLAIM until there are none left | inbox, login calendars, quest crates |
| `challenge_sim` | Events → Challenges → MULTI SIM (sims them all in one tap) | daily challenges |
| `battle` | PvE auto-battle: START → squad-select START → AUTO → await VICTORY | Coliseum, guild raid |
| `sequence` | a fixed button order, every tap optional | Galactic War restart→sim→redeem |
| `shop` | buy allow-listed items with tokens | Cantina shipments |
| `conquest` | Galactic Battles → CONQUEST → sector map: free disks, then capped node fights | Conquest 24 Sector 1 |

Every entry starts and ends at the hub and every tap is gated by a template match — it never
blind-taps a coordinate. Entries are idempotent: whatever is already done today has a greyed
control, which fails to match, which is a skip rather than a halt. Running twice in a day is safe.

## Run it

```bash
.venv/bin/python -m farmbot.run --doctor    # preflight: device, config, template coverage
.venv/bin/python -m farmbot.run --dry-run   # print the routine, tap nothing
.venv/bin/python -m farmbot.run --daily     # the full routine, isolating any one bad entry
.venv/bin/python -m farmbot.run --dump      # same engine, but abort on the first halt (debugging)
```

Kill switch: Ctrl-C, or `touch farmbot/STOP` (checked between steps; delete before the next run).
Each run writes `farmbot/reports/<date>.md` — counters, whether the rails held, and the residual
checklist of things that are still yours to do.

## The hub is a 3D panorama, not a menu

The single hardest thing here. Hub game-mode consoles (Campaigns, Events, Raids) are objects in a
3D scene: they move, rescale, and change tap-target as the camera pans, so a console template
matched at one pan taps the wrong place at another. Three findings make it tractable:

- **Overlays are pan-invariant.** The left rail, the energy bar, the home button, `QUESTS`, and the
  `EVENT ACTIVE` badge are HUD, not scene. Prefer them: `events_entry` is deliberately the
  EVENT ACTIVE badge, not the 3D "Events" console, and it opens the same menu.
- **A rail label is not a hit target.** Tapping one falls *through* to whatever console is behind
  it. Templates are cropped on the distinctive label; `tap_offset` moves the tap onto the icon.
- **A submenu round-trip restores the default pan**; the home button alone does not (it is a no-op
  while the hub is already showing). That is what `recenter: true` does. `pan: far_left|far_right`
  then swipes into an end stop, the only other reproducible camera position.

## Capture templates

```bash
.venv/bin/python -m farmbot.devtool shot /tmp/s.png     # look at the screen
.venv/bin/python -m farmbot.devtool crop L T R B NAME   # crop it into templates/
.venv/bin/python -m farmbot.devtool find NAME...        # score templates against the live screen
.venv/bin/python -m farmbot.devtool coverage            # what the config needs vs what exists
```

Rules learned the hard way:
- **Capture unselected.** The engine often arrives with a different node already selected; a
  template cropped in its selected (glowing) state will not match.
- **Exclude anything that changes** — badge counts, timers, prices. A confirm template keeps the
  currency *icon* and drops the digits, which is what makes it currency-specific and price-agnostic.
- **Include the word that makes it safe.** `bronzium_free` contains "FREE", so it cannot match the
  €23.99 and 💎3,200 cards sitting in the same grid.
- Matching is **grayscale**, so it cannot tell an enabled button from a greyed one. Where that
  matters the step is optional, so a wasted tap on a dead button is harmless.

## Status

Live-validated on BlueStacks (Astra, 14.36M GP). 195 device-free tests. `--doctor` reports full
template coverage for the 19-entry routine. Known gaps are listed at the end of
`docs/swgoh-daily-automation-spec.md`; the big ones are the DS chapter-8 navigation and the
Fleet-variant of the depleted-node marker.

Of the 8 daily quests it closes 7. The eighth is the Arena battle, which is PvP — rail 2 means there
is no code path that can play it, so 7/8 is the ceiling by design, not a gap.
