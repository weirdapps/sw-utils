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

Ownership note (roster 20260731): several advisor "gaps" are already owned (the advisor flags
"can't field the meta team," not "unowned"). BUT owned ≠ 7★ — units/ships **below 7 stars still
want shard farming**, which is the real top priority below.

## ⭐ Under-7★ shard farms — VERIFIED nodes (top priority)
Astra's owned-but-under-7★ units/ships, each with a live-verified (swgoh.gg, 2026-08-02) sim-able
shard node. This is the concrete list to wire once templates are captured.

| Target | Stars | Node | Energy |
|--------|-------|------|--------|
| Vane (GL Hondo crew) | 2★ | **Cantina 3-B** | Cantina |
| Captain Silvo (GL Hondo crew) | 2★ | **Cantina 6-A** | Cantina |
| Brutus (GL Hondo crew) | 2★ | **Fleet Hard 2-A** | Fleet |
| Captain Ithano | 4★ | **Fleet Hard 1-A** | Fleet |
| Quiggold | 3★ | **Fleet Hard 3-D** | Fleet |
| Raven's Claw (ship) | 6★ | **Fleet Hard 2-E** | Fleet |
| MG-100 StarFortress SF-17 (ship) | 5★ | **Fleet Hard 2-D** | Fleet |
| Kix | 4★ | **LS Hard 1-D** | Normal |
| Hyena Bomber (ship) | 6★ | **DS Hard 8-B** | Normal |
| Mara Jade Skywalker | 4★ | — pack/crystals only, **NOT sim-able** | — |

Fleet energy is the bottleneck (5 of 9). Node ids need a **final on-device confirm** at capture
time — the node's *reward icon* is the source of truth (the node's character art ≠ the shard it
drops), and early-chapter nodes require horizontal **scroll** to reach.

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
- ⚙️ State-machine extensions before some areas work:
  - **Normal/Hard difficulty toggle** (LS/DS/Fleet Hard nodes — most shard farms are Hard).
  - **Chapter-tab scroll + horizontal node scroll** (early nodes like Cantina 3-B and later tabs
    like Stage 9 are off the initial view; confirmed live on Cantina ch3 where 3-G was selected).
  - **Known-popup dismissal** — login/offer calendars auto-pop and are "unknown screens"; the
    macro halts safely on them, but unattended runs want an auto-dismiss for common popups.
  - **Mod Battles flow** — separate area + Mod Energy; its UI may differ from the Campaigns flow.

## Recommended build order
1. **Cantina shard nodes** (Vane 3-B, Silvo 6-A) — proven flow; add chapter-tab + node scroll.
2. **Fleet Hard shard nodes** (Ithano 1-A, Brutus 2-A, MG-100 2-D, Raven's Claw 2-E, Quiggold 3-D)
   — new Fleet area + Normal/Hard toggle; 5 nodes = biggest single batch of value.
3. **LS/DS Hard shard nodes** (Kix → LS Hard 1-D, Hyena Bomber → DS Hard 8-B) — Normal/Hard toggle.
4. **Materials** — Mod Battles Tier 2 (mod bottleneck) + Cantina Stage 8/9 (omicron/zeta) + gear.
