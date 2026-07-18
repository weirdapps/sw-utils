# SWGOH — Grand Arena team builder (Astra / Kyber 3 → Kyber 2)

Reusable pipeline that builds **grounded** GAC defense + offense squads and fleets from live
swgoh.gg meta + the player's live roster, and pushes them into **HotUtils** as organized squad groups.

"Grounded" is the whole point: every defense pick is a top-**Hold%** team on swgoh.gg and every
offense pick a top-**Win%** team — so when the player sorts swgoh.gg the same way, they see the same teams.

## Player
- **Astra** · ally **145357294** · GAC league **Kyber 3** (climbing to Kyber 2) · ~14M GP.
- **9 Galactic Legends:** JMK, JML, SEE, SLKR, GL Leia, Lord Vader, GL Rey, Jabba, GL Ahsoka.
- **Known gaps:** GL Hondo (squad — leads #1 3v3 wall), Profundity (fleet — #1 defensive fleet), Third Sister (non-GL wall).

## Live board (Kyber, read from HotUtils GAC Planning — reconfirm each season)
- **5v5:** 11 defense squads + 3 fleets. **3v3:** 15 defense squads + 3 fleets. Offense mirror-clears.
- Config lives in `scripts/compute_teams.py` (`BOARD`). Update if league/board changes.

## Rules (encoded in the scripts — don't hand-wave them)
1. Every unit **owned + G13+**. 2. **No unit repeats within a format** (3v3 and 5v5 are separate seasons, so a unit CAN appear in both; but within one format, defense + offense share no unit — defense locks & each unit attacks once). 3. **Defense first** by Hold%. 4. **Reserve the 4 pure-attack GLs** (JMK, JML, SEE, SLKR) for offense before defense claims units, or defense strands their support (e.g. JML's Cal/GMY). 5. GL Leia → offense in 5v5 (she's the #1 attacker). 6. Fleets are single-use too; the 6 fleets share no ship.

## Full workflow (re-run each GAC season / when meta shifts)
Browser steps can't be pure scripts (Cloudflare + authenticated sessions) — the JS snippets are in
`scripts/browser_recipes.md`. Run them via the in-session MCP browser.

1. **Refresh roster** → `data/roster/` (browser_recipes.md §1). Update `ROSTER_FILE` in compute_teams.py to the new filename.
2. **Read live board counts** from HotUtils GAC Planning (browser_recipes.md §2). Update `BOARD` if changed.
3. **Scrape swgoh.gg meta** → `data/meta/` (browser_recipes.md §3). 4 views: 5v5 def (JSON), 5v5 off, latest-3v3 def, latest-3v3 off (txt). Note the current season ids (even=5v5, odd=3v3).
4. **Compute:** `python3 scripts/compute_teams.py` → `data/gac_result.json`.
5. **Generate:** `python3 scripts/generate_hotutils.py` → `output/` (6 category JSONs + upload_payload.json + playbook.html). Review the FLEETS config in that script (owned ships, no-repeat).
6. **Upload to HotUtils** (browser_recipes.md §4): capture session, delete old GAC squads, base64 the upload_payload.json, create all via `squads/upsert`. Verify categories.
7. **Playbook:** open `output/playbook.html` for the human-readable plan (hold/win %, reasoning, gaps, fleets).

## HotUtils categories (the "4 groups" the player wants)
Squads: `GAC 5v5 - Defense` · `GAC 5v5 - Offense` · `GAC 3v3 - Defense` · `GAC 3v3 - Offense`.
Fleets: `GAC Fleet - Defense` · `GAC Fleet - Offense` (full ~8-ship lineups).
HotUtils accepts arbitrary category strings and shows them as filter groups.

## Conventions
- Data-driven only — NO hardcoded teams in compute (teams come from the meta files ∩ roster).
- Fleet reinforcements are standard faction-meta (swgoh.gg only publishes capital + starting-3).
- Base IDs: roster `b` field == swgoh.gg `data-unit-def-tooltip-app` == HotUtils `characterId` (all identical).
- Do NOT commit secrets. HotUtils session ids are ephemeral — never hardcode them in committed files.
