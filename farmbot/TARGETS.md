# farmbot — energy-dump target list (researched 2026-08-02)

What the energy-dump macro should sim, for Astra (14.35M GP, Kyber, 9 GLs). Built from the A3
advisor gaps + live-verified roster ownership + farm-location research (swgoh.gg / gaming-fans,
post-Cantina-2.0 May 2026). **Only sim-able campaign nodes are in scope** — the macro cannot touch
events, shops, Conquest, or arena stores.

## Reality check — the big gaps are NOT sim-farmable
The marquee GAC-unlock gaps can't be automated here; they need manual event/shop/Conquest play:

| Gap | Where it actually comes from |
|-----|------------------------------|
| Third Sister (Reva) | Rise of the Empire TB P3 special mission (guild-gated) |
| GL Hondo / Pirate King Hondo | Galactic Ascension event (unlock reward, no shard farm) |
| SM-33 | Conquest reward |
| Jedi Master Mace Windu | Legendary event "Beset on All Sides" |
| Profundity (capital ship) | Journey Guide monthly event / crystals |

Ownership note (roster 20260731): 4-LOM, Slave I, TIE Advanced, Vane, Brutus, Captain Silvo,
Cobb Vanth are **already owned** — the advisor flagged them as "can't field the meta team," not
"unowned," so no unlock-farm applies.

## Sim-able targets (what the macro will actually farm), by priority

### 1. Mods — the active bottleneck (Mod Energy) ⭐ top priority
- **Mod Battles Tier 2** — slicing salvage (incl. the binding **T05_06 / T06_02**) + **Micro
  Attenuators** (calibration). Post-2.0, Tier 2 replaced the old Map 9. Uses the separate **Mod
  Energy** pool (cap 144 + 45 daily).
- **Mod Battles Tier 1** — 5-dot mods (10 Mod Energy/battle).
- *Highest ROI:* directly feeds the slice/promote/calibrate pipeline in `memory/notes.md`.

### 2. Cantina materials (Cantina Energy)
- **Cantina Stage 9** — Omicron materials (20 energy/battle) — best endgame use.
- **Cantina Stage 8** — Zeta materials (16 energy/battle).
- (Fallback: any active character node if a specific shard is being chased.)

### 3. Gear (Normal Energy — LS/DS Hard)
- **Stun Gun + Mk4 Comlink** combo node (Holdo / Poe — confirm exact node # on swgoh.gg at
  capture time) — two bottleneck pieces from one node.
- **Mk 12 Fusion Furnace** (LS/DS Hard) — needed ~2× the Stun Gun rate.
- **LS 7-B** — Bronzium Wiring · **LS 1-C** — Carbonite Circuit Board (relic-3 mats).
- **Fleet 3-E (Normal)** — Mk 12 Stun Gun Prototype Salvage.

### 4. Missing sim-able ship (Fleet Energy)
- **Sith Infiltrator** — **Fleet Hard 3-D** (the one missing, fleet-node-farmable ship).
- (Slave I 2-B / TIE Advanced 4-B are already owned → skip unless farming to 7★.)

## Capture / build status
- ✅ **Cantina campaign-node flow validated live** (chapter-1, Multi-Sim, energy-out→CANCEL).
- ⏳ Each target area above still needs a **capture pass** (navigate → screenshot → crop
  `campaign_*` / `node_*` / `chapter_tab_*` templates → verify), the same way Cantina 1-A was done.
- ⚙️ Likely small state-machine extensions before some areas work:
  - **Normal/Hard difficulty toggle** (LS/DS/Fleet Hard nodes).
  - **Chapter-tab scroll** (Cantina Stage 9 is beyond the visible 1–8 tabs; far nodes need scroll).
  - **Mod Battles flow** — separate area + Mod Energy; its UI may differ from the Campaigns flow.

## Recommended build order
1. **Mod Battles Tier 2** (biggest bottleneck) — explore its UI + capture + validate.
2. **Cantina Stage 8/9** — add chapter-tab (+scroll) capture.
3. **Gear nodes** (LS/DS Hard) — add the Normal/Hard toggle.
4. **Fleet Hard 3-D** (Sith Infiltrator) — Fleet area + Hard toggle.
