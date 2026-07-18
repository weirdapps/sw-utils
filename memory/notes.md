# Notes — durable facts (update when they change)

## Player
- Astra · ally 145357294 · Kyber 3 (→ Kyber 2) · ~14M GP · 326 chars (314 G13+), 69 ships (10 capitals).
- 9 GLs: JMK, JML, SEE, SLKR, GL Leia, Lord Vader, GL Rey, Jabba, GL Ahsoka.

## Gaps (biggest upgrades)
- **Squad GL: GL Hondo** — leads #1 3v3 defensive wall (38% hold) + several top-4 3v3 walls. Not owned.
- **Fleet: Profundity** (CAPITALPROFUNDITY) — #1 defensive fleet (77% attacker win). Not owned. (Owns Raddus, a different ship.)
- **Non-GL wall: Third Sister** — highest-Hold% team you can't field.

## Board (Kyber, 2026-07)
- 5v5: 11 def squads + 3 fleets. 3v3: 15 def squads + 3 fleets.

## swgoh.gg season alternation
- Even season = 5v5, odd = 3v3. As of 2026-07: S80=5v5 (current), S79=latest 3v3.

## GL allocation (defense-first, but reserve attack GLs)
- Offense always: JMK, JML, SEE, SLKR. 5v5 also GL Leia (96% #1 attacker).
- Defense: Lord Vader, GL Rey, GL Ahsoka, Jabba (+ GL Leia in 3v3).

## Fleets (grounded caps from /gac/ship-counters; reinforcements = faction meta from owned ships)
- Defense: Leviathan (81%), Negotiator (87%), Home One (90%).
- Offense: Executor, Malevolence, Raddus.
- All 6 fleets share no ship (single-use). Malevolence fleet = 6 ships (all owned Separatist).

## HotUtils
- API base api.hotutils.com/Production ; squads/list, squads/upsert (create via {definition}, delete via {id,void:true}).
- Categories are free strings → used 6: GAC {5v5,3v3} - {Defense,Offense} + GAC Fleet - {Defense,Offense}.
- Session ids are ephemeral — recapture each session (browser_recipes.md §4).
