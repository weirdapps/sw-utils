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
### ⭐ 2026-09-11: the TIER LISTS are the reliable path, and they are Kyber-scoped
`/gac/squads/?...` still gets a Cloudflare interstitial that does not clear. The **tier lists do not**:
`https://swgoh.gg/tier-list/gac/` (5v5 off), `?side=defense`, `/tier-list/3v3/`, `/tier-list/fleet/`,
`/tier-list/datacrons/` all load clean in chrome-devtools MCP against real Chrome, and they carry
`League Kyber` plus the sample size ("3.53M first-attempt, full-squad GAC battles").
⚠ **They are React now and there are NO `data-unit-def-tooltip-app` attributes.** Unit names live in
`img.alt`. Extractor:
⛔⛔ **"Show N more" IS A `<summary>`, NOT A `<button>`, AND THIS FAILS SILENTLY.** Each tier band
below S is a `<details>` accordion. A click loop over `button` finds nothing, expands nothing, and
the extractor then returns the ~56 S-and-A rows it can see PLUS ~100 collapsed rows with every stat
field `null`. Nothing errors. The first 3v3 pull on 2026-09-11 lost 100 of 156 rows exactly this way,
and the board built on it was missing most of the fieldable pool. **Set `.open` on the details:**
```js
// expand the ladders first: `Show N more` is a <summary> inside <details>, not a <button>
for (let p=0;p<6;p++){
  document.querySelectorAll('details').forEach(d=>{
    if(/Show \d+ more/i.test(d.querySelector('summary')?.textContent||'')) d.open=true; });
  await new Promise(r=>setTimeout(r,700));
}
document.querySelectorAll('div.flex-1.min-w-0').forEach(c=>{
  const lead=c.querySelector('div.w-12 img'); if(!lead) return;          // leader
  const rest=[...c.querySelectorAll('div.w-10 img')].map(i=>i.alt);      // members
  // walk UP to the innermost ancestor holding exactly ONE stat block, else an
  // outer container swallows several cards and you get 9 units in one "squad"
  let anc=c, txt='';
  for(let i=0;i<6&&anc;i++){
    const t=(anc.innerText||'').replace(/\s+/g,' ');
    const n=(t.match(/Hold % [\d.]+%/g)||[]).length;                     // Win % on offence
    if(n===1){ txt=t; if(t.match(/#(\d+)/)) break; }
    if(n>1) break;
    anc=anc.parentElement;
  }
});
```
✅ **Count-check every pull before you trust it**: `document.body.innerText.match(/Hold % /g).length`
must equal the highest `#N` on the page. 151 of 156 is fine (a few rows genuinely lack stats);
56 of 156 means the accordions never opened.
⛔ **Do NOT filter to a fixed squad size.** 3v3 offence has 1- and 2-unit rows and they are the TOP of
the table (SEE + Darth Bane #1). Rank and `DATACRON DEPENDENT` are on an ancestor, not the card.
⚠ **Dedup by unit SET keeping the highest `Battles`**: the same three units appear in a reversed order
with a tiny sample (The Stranger trio is 25.7% on n=86.3K and 16.9% on n=37), and a naive dict write
keeps the wrong one.
⚠ **`/tier-list/datacrons/` and `/tier-list/fleet/` are NOT format-scoped.** Both print "3.53M
first-attempt ... Season 82", the same sample as the 5v5 list, while the 3v3 list prints 4.02M. So
their numbers are the 5v5 season's. Do not quote a datacron or fleet hold rate as a 3v3 figure.

**`/gac/counters/<LEADER>/` still uses real base ids** in `data-unit-def-tooltip-app`, inside
`div.panel.panel--size-sm`. Split attacker from defender by the anchor href: `a_lead`/`a_member` vs
`d_lead`/`d_member`. A plain navigation works (it may report a nav timeout while the page is in fact
loaded); a same-origin `fetch()` of the same URL gets a 403 interstitial, so navigate, do not fetch.

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

---
## §6 — Capture the LIVE GAC board (both sides) — the input `gac_attack.py` needs
The opponent's placed defense, your own placement, the per-zone scores and the score ceiling all come
from one call. Do this at the start of every attack phase.

**⚠ `gac/*` endpoints require the `APIUserId` HEADER; `squads/list` does not.** Without it you get
`responseCode 2 / "Invalid API Request Header Values"`, which reads like an auth failure and is not.
Grab both values by hooking `fetch` before the page loads:

```js
// navigate_page(url='https://hotutils.com/gac/current', initScript=<this>)
(() => { window.__cap=[]; const of=window.fetch;
  window.fetch=function(...a){ try{ const u=String(a[0]&&a[0].url||a[0]);
    const h=(a[1]&&a[1].headers)||{}; const hh=h instanceof Headers?Object.fromEntries(h.entries()):h;
    if(u.includes('api.hotutils')) window.__cap.push({u,headers:hh,body:a[1]&&a[1].body});
  }catch(e){} return of.apply(this,a); }; })()
```
`sessionId` is also in `document.cookie` as `hotUtilsSession`; `APIUserId` only appears in the header.

```js
async () => {
  const SID="<hotUtilsSession cookie>", UID="<APIUserId header>";
  const api=(p,b={})=>fetch("https://api.hotutils.com/Production/"+p,{method:"POST",credentials:"include",
    headers:{"content-type":"application/json","APIUserId":UID},body:JSON.stringify({...b,sessionId:SID})}).then(r=>r.json());
  return await api("gac/get",{refresh:true,tournamentEventId:null,currentMatchId:null});
}
```
Save with `evaluate_script`'s `filePath` to `output/gac_current_<YYYYMMDD>.json` (~5MB), then
`python3 scripts/gac_attack.py`. Useful fields:
- `gac.tournamentMapId` — e.g. `4zone_5v5_ga2_c3s1_82a`, tells you the format.
- `gac.{home,away}.zones[]` — `zoneId` (`phase01`=front, `phase02`=back), `location` pairs a front with
  the back it gates, `squadCapacity`, `squadCount`, `defeatedSquadCount`, `state` (1 locked · 3 in
  progress · 4 cleared), and `squads[].units[].baseId/relicLevel` plus `datacron`.
- `zones[].score` on YOUR side is what YOU earned attacking the mirrored enemy zone, not what you
  conceded. Summing them reproduces the scoreline on the page.
- `gac/list` gives every past round with final scores — that is how the lane-gating rule was verified.
- `account/data/all` → `data.datacrons[]` is the live cron inventory; the affix ARRAY LENGTH is the
  cron's level, and `affix[].targetRule` names the alignment/faction/character it scopes to.

**Session capture is ephemeral and must never be committed.** Pass it as `HU_SID=<sid>` to
`upload_hotutils.py` / `push_ingame_presets.py`, which are browser-free and paced.

---
## §7 — Scrape GAC counters (feeds `gac_attack.py`'s head-to-head table)
`/gac/counters/<LEADER_BASE_ID>/?season_id=…SEASON_<n>` lists, for one defending leader, every observed
counter as attacker lineup + defender lineup + Seen + Win% + avg Banners. Same Cloudflare rule as §3:
Playwright MCP, base page first, then the parameterised URL.

Write one JSON per format into `data/meta/counters/`:
```json
{ "<DEFENDING_LEADER>": { "n": 50, "rows": [ {"A": [...], "D": [...], "seen": "14.5K", "win": 79, "avg": 48.67} ] } }
```
`gac_attack.py` indexes it two ways — exact (attacker lineup × defender lineup), then attacker lineup ×
defending LEADER — and falls back to a two-marginal model only when neither hits, printing `(model)` so
you can tell a measured 96% from a guessed one. Scrape the leaders that actually appear on opponents'
boards; ~24 per format covers the Kyber meta.
