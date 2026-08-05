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
- ✅ **Full pipeline validated live across all paths** (2026-08-02): Cantina Normal Multi-Sim,
  **Fleet HARD Multi-Sim** (real sim), the full **rewards→CONTINUE→home** loop, **energy-out→CANCEL**
  (crystals safe), halt-on-unknown, campaign-menu **scroll**, and the **Hard toggle**.
- ✅ **Mod Battles is a 5th card in the Campaigns menu** (Mod Energy, 42/42 star) → the mod-material
  bottleneck is sim-able via the **same flow**, not a separate area. `campaign_mod` captured.
- ✅ Templates so far: full chrome (home/campaigns/multi_sim/sim_confirm/rewards/home_button/
  energy_out/hard_tab/chapter_tab_1/popup_close) + campaign_{cantina,light,dark,fleet,mod} +
  nodes {cantina_1-A, light_1-D (Kix), fleet_1-E}.
- ⏳ Remaining = mostly **per-node icon capture** for each target (the macro scrolls to find a node
  but needs its `node_<campaign>_<id>` icon; uncaptured → safe-halt).
- ⏳ Each target area above still needs a **capture pass** (navigate → screenshot → crop
  `campaign_*` / `node_*` / `chapter_tab_*` templates → verify), the same way Cantina 1-A was done.
- ✅ **Normal/Hard difficulty toggle** — DONE (`difficulty: "hard"` → taps `hard_tab`);
  nav validated live on LS Hard ch1.
- ✅ **Node scroll** — DONE (`SELECT_NODE` swipe-scans when a node isn't in the initial view).
- ⚙️ Still needed before some areas run:
  - **Depleted-Hard-node skip** — Hard nodes are **5 attempts/day**; when used up the panel shows
    a `1h 12m / 💎200` refresh instead of MULTI SIM. The macro **safe-halts** on it (looks for
    `multi_sim`, never taps the 💎200 refresh) — but a graceful skip-to-next-node (like energy-out)
    is wanted. **Blocked live-validation of a Hard sim today: LS Hard 1-D was already depleted.**
  - **Known-popup dismissal** — the hub is popup-prone: **3 distinct auto-popups seen in one
    session** (login calendar, era-level calendar, GoH newsletter). Each is an "unknown screen"
    the macro safe-halts on; unattended runs need an auto-dismiss (close-X) for common popups.
  - **Chapter-tab scroll** for tabs beyond the visible 1–8 (e.g. Cantina Stage 9).
  - **Mod Battles flow** — separate area + Mod Energy; its UI may differ from the Campaigns flow.

## Recommended build order
1. **Cantina shard nodes** (Vane 3-B, Silvo 6-A) — proven flow; add chapter-tab + node scroll.
2. **Fleet Hard shard nodes** (Ithano 1-A, Brutus 2-A, MG-100 2-D, Raven's Claw 2-E, Quiggold 3-D)
   — new Fleet area + Normal/Hard toggle; 5 nodes = biggest single batch of value.
3. **LS/DS Hard shard nodes** (Kix → LS Hard 1-D, Hyena Bomber → DS Hard 8-B) — Normal/Hard toggle.
4. **Materials** — Mod Battles Tier 2 (mod bottleneck) + Cantina Stage 8/9 (omicron/zeta) + gear.

---

## 2026-08-02 (session 2) — research corrections + live capture status
Corrections from a 5-agent verification workflow (swgoh.gg + gaming-fans, post-Cantina-2.0). **Confirm the reward ICON on device at capture — node art ≠ dropped shard.**

### Corrections to the list above
- ❌ **Vane is NO LONGER sim-able** — moved to Chromium packs / Shipments (Oct 2025 update); Cantina 2.0 added no node. Drop the Cantina 3-B entry.
- ✅ **DS Hard 8-B = Taris** — one Multi-Sim drops **Hyena Bomber ship + Mk3 Stun Cuffs + Comlink** (device-confirmed: red ship blueprint + Mk IV/Mk III gear). Best Normal-energy combo node.
- ➕ **NEW Cantina 2.0 Stage-9 Omicron nodes** (shards + 0.75% Omicron each): **Wampa 9-A, General Grievous 9-E, Hermit Yoda 9-G**. Top per-node Omicron farms. Zeta = **Cantina 8-F**.
- ✅ **Captain Silvo = Cantina 6-A** (GL Hondo crew, high confidence).
- ⚠️ **Fleet 2-E ambiguity**: Fleet HARD 2-E = Raven's Claw (ship); Fleet NORMAL 2-E = Mk12 Fusion Furnace (gear). Difficulty must be set per intent.
- **Mod Battles Tier 2 salvage-per-node**: T05_06 @ 2-E/2-F, T06_02 @ 2-D (confirm icons).
- Fleet-Hard character nodes (Ithano 1-A, Brutus 2-A, Quiggold 3-D) confirmed but swgoh.wiki is STALE — trust swgoh.gg + on-device.

### Captured + VALIDATED live (2026-08-02, crystals unchanged)
- **Mod Battles Tier 2 2-F** → `node_mod_2-F` + `chapter_tab_mod_2`. Dumped Mod 144→0 (8 sims, T05/T06 salvage). ✅
- **Fleet Hard 1-E** (`node_fleet_1-E`) → dumped Fleet 74→11 via engine. ✅
- **LS Hard 1-D Kix** (`node_light_1-D`) → dumped Normal 144→84 via engine. ✅
- **Cantina 1-A** (`node_cantina_1-A`) → sim via engine. ✅
- Also captured: `hard_tab` (re-captured clean), `normal_tab`, `newsletter_close`, `chapter_tab_8`, `node_dark_8-B` (DS 8-B, needs ch8-nav tuning — see below).

### Capture rules learned (IMPORTANT)
- **Capture node icons UNSELECTED.** The engine arrives with the last-played node auto-selected; a target that isn't auto-selected shows unselected, and a selected-state template (glow/border) misses. Deselect (tap another node) before cropping.
- **hard_depleted** template still needed → a depleted Hard node currently safe-HALTs (saves `halts/<ts>_OPEN_MULTISIM.png`). Crop the refresh-timer panel region (NOT just the 💎-refresh button) from that halt to enable graceful skip (unit-tested already).
- **DS/high-chapter nav** (ch8 tab + off-screen node) is finicky — the engine landed on ch6 once. Tune `chapter_tab_8` + ch8 node scroll before wiring DS 8-B and the Stage-9 Cantina Omicron nodes. Chapter-1 nodes are reliable.
