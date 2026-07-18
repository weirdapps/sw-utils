# Browser recipes (run via in-session MCP browser)

swgoh.gg is Cloudflare-gated and HotUtils needs an authenticated session, so these steps use a real
browser (chrome-devtools MCP for HotUtils; Playwright MCP works well for swgoh.gg). curl/WebFetch/`fetch`
get 403 on swgoh.gg param URLs.

Ally code: **145357294**. Replace with another player's code to reuse.

---
## §1 — Refresh roster (swgoh.gg)
Navigate to `https://swgoh.gg/p/145357294/` (base pages pass Cloudflare), then same-origin fetch:
```js
() => fetch('/api/player/145357294/',{headers:{Accept:'application/json'}}).then(r=>r.json()).then(d=>{
  const u=d.units||d.data?.units||[];
  const roster=u.map(x=>{const c=x.data||x;return {b:c.base_id,n:c.name,g:c.gear_level,rt:c.relic_tier,r:c.rarity,ct:c.combat_type,gp:c.power,z:(c.zeta_abilities||[]).length,o:(c.omicron_abilities||[]).length};});
  return {meta:{ally:d.data?.ally_code,name:d.data?.name,gp:d.data?.galactic_power,count:roster.length,pulled:'<DATE>'},units:roster};
})
```
Save to `data/roster/swgoh_roster_fresh_<YYYYMMDD>.json` (chrome-devtools evaluate_script has a `filePath` param).
Fields: `b`=base_id, `g`=gear, `rt`=relic_tier (displayed relic = rt-2), `ct`=1 char/2 ship.

---
## §2 — Live Kyber board counts (HotUtils GAC Planning)
Log in (see §4), go to `https://hotutils.com/gac/planning`, "Create new 5v5 plan" (League Override: Kyber).
The Edit-Plan dialog shows zone slots: Top Back (Ships) / Top Front / Bottom Back / Bottom Front.
- Kyber 5v5 (2026-07): Ships 3, TopFront 4, BotBack 3, BotFront 4 → **11 squads + 3 fleets**.
- Kyber 3v3: Ships 3, TopFront 5, BotBack 5, BotFront 5 → **15 squads + 3 fleets**.
Cancel the plan (no need to save). Put counts into `BOARD` in compute_teams.py.

---
## §3 — swgoh.gg GAC meta (Top Squads)
Metric: **Hold%** (defense) / **Win%** (offense). Page: `/gac/squads/`.
URL grammar: `?season_id=...SEASON_<n>` (even=5v5, odd=3v3; pick the current 5v5 + the latest 3v3),
`?perspective=attack` (offense), `?sort=percent`, `?cutoff=` (default 0.5% significance).
**Cloudflare:** the base `/gac/squads/` passes, but PARAM URLs get JS-challenged. chrome-devtools can't
solve it; **Playwright MCP passes IF you navigate the base page first (warm session) then the param URL.**
Extract (unit base IDs are in `data-unit-def-tooltip-app`, leader first):
```js
() => { const t=document.querySelector('table');
  return [...t.querySelectorAll('tbody tr')].map(tr=>{
    const units=[...tr.querySelectorAll('[data-unit-def-tooltip-app]')].map(d=>d.getAttribute('data-unit-def-tooltip-app'));
    const n=[...tr.children].slice(1).map(td=>td.textContent.trim().replace(/\s+/g,' '));
    return n[1]+'|'+n[0]+'|'+n[2]+'|'+units.join(','); // rate%|seen|banners|CSVunits
  }).join('\n'); }
```
Save 4 files to `data/meta/`: `meta_5v5_defense_s<N>.json` (or txt), `meta_off5v5.txt`, `meta_def3v3.txt`, `meta_off3v3.txt`.
(The 5v5 defense file this repo ships is JSON with `rows[].hold/seen/banners/units`; the others are the txt line format above. compute_teams.py reads both — see `META_FILES`.)
Fleet meta: `/gac/ship-counters/` — per defending capital, Seen + attacker-Win% (**lower = better hold**).
Per-capital detail (full counters) at `/gac/ship-counters/<CAPITAL_ID>/?season_id=...` (same warm-session rule).

---
## §4 — HotUtils: login + squad API (the reliable path; skip the flaky file-upload UI)
**Login:** chrome-devtools → `https://hotutils.com/` → click "Login with Discord" (silent SSO works if the
browser profile has a Discord session; account auto-selects Astra). If it bounces to /login, tick "Remember me" and retry.

**Session capture:** open `https://hotutils.com/squads`, then read a live XHR to grab creds:
- header `apiuserid: <uuid>` and body `sessionId: <uuid>` (both on every `POST api.hotutils.com/Production/squads/list`).
- Get them from the DevTools network panel (get_network_request) or just reuse from a prior call this session.
- CORS allows `hotutils.com → api.hotutils.com`, so run `fetch` from an evaluate on a hotutils.com page.

**API helper (paste real SID/UID):**
```js
const SID="...", UID="...";
const api=(p,b)=>fetch("https://api.hotutils.com/Production/"+p,{method:"POST",credentials:"include",
  headers:{"content-type":"application/json","apiuserid":UID},body:JSON.stringify({...b,sessionId:SID})}).then(r=>r.json());
```
- **list:**  `await api("squads/list",{})` → `{groupings:[{definitions:[{id,name,size,combatType,category,contents(STRING)}]}]}`
- **create:** `await api("squads/upsert",{definition:{name,size,combatType,category:[cat],contents:JSON.stringify(arr)}})`
  where `arr=[{id:0,characterId,characterName,requirements:{hasOmicron:false,hasZeta:false,hasUltimate:false,filters:{minGP:1000,gear:0,relic:0,stars:2},subsPriority:"order"}},...]` (leader id 0). `combatType` 1=chars, 2=ships. responseCode 1 = ok.
- **delete:** `await api("squads/upsert",{id:<id>,void:true})`
- (UI delete is an antd popconfirm "Yes", NOT native confirm.)

**Rebuild flow:**
1. delete all current: `const L=await api("squads/list",{}); for (const g of L.groupings) for (const d of g.definitions) await api("squads/upsert",{id:d.id,void:true});`
2. `base64 -i output/upload_payload.json | tr -d '\n'` → inline as `B64` → `const P=JSON.parse(decodeURIComponent(escape(atob(B64))));`
3. loop `P` → create each (see generate_hotutils.py payload shape: `{n,sz,ct,cat,u:[[baseid,name],...]}`).
4. verify: list → count per `category`.

---
## §5 — Push squads INTO THE GAME (in-game squad presets)
Writes squads to the game's in-game Squad-preset system (organized in **tabs**). NOT the GAC board.
- **`squads/game/get` {sessionId}** → `{tabs:[{id,name,unique,combatType,squads:[{name,units[]}]}]}` = current in-game tabs.
- **`squads/game/set` {sessionId, tabs:[...]}** — per-tab UPSERT (tabs you don't send are preserved):
  - **create** a tab: `{id:null, name, unique:true, combatType:1, squads:[{name, unitBaseIds:[...]}]}`
  - **update** a tab: same but with the existing `id`.
  - **delete** a tab: `{id:<existing>, name, unique, combatType:1, void:true, squads:[]}` (works on non-empty tabs; to clear a stray EMPTY dup, repurpose it by id then void the other).
- **LIMITS (learned the hard way):**
  - **Fleets can't be pushed** — API errors `"Currently only character squad presets are supported"`. combatType:2 is rejected. Set fleets manually in-game.
  - **Preset NAME length is short** (~16 chars). Long names → `INVALID_SQUAD_PRESET_NAME_LENGTH_KEY`. Use short names (tab already gives format+phase), e.g. `D1 Stranger`, `O1 SEE`.
  - `id:null` always creates a NEW tab (no by-name dedup) — don't push the same tab twice or you get duplicates; update by id instead.
- Done 2026-07-18: pushed 4 char tabs (GAC 5v5/3v3 - Defense/Offense = 56 squads). Fleets left for manual in-game placement.
