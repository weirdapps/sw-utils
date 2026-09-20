#!/usr/bin/env python3
"""
gac3v3_board.py: build, price and PLACE the 3v3 Grand Arena board, in banners.

WHY THIS FILE EXISTS
--------------------
The 3v3 board was built ad-hoc in a chat session on 2026-09-11 and never
committed, so the numbers behind `output/gac3v3_placement_sheet.txt` could not be
re-derived or challenged. This is that build, written down.

It also answers the owner's question of 2026-09-11 directly. He observed that the
Galactic Legends were sitting in the BACK zone, where an opponent takes both front
territories for free and then picks the back apart, and proposed a specific
structure instead. `--structure owner` implements his proposal exactly and prices
it against the free optimum, so the answer is a number, not an argument.

THE BOARD  (live: tournamentMapId 4zone_3v3_ga2_c3s1_83a, season 83, Kyber)
---------------------------------------------------------------------------
    FRONT-A  phase01_conflict01  5 squads, loc 1  -gates->  FLEET  phase02_conflict01  3 fleets
    FRONT-B  phase01_conflict02  5 squads, loc 3  -gates->  BACK-B phase02_conflict02  5 squads

A back territory is invisible and unattackable until EVERY squad in its own front
is dead. So a front squad denies its own battle banners AND, collectively with its
zone-mates, the whole lane behind it.

    hold FRONT-B  denies 260 + (260 + 5x57) = 805
    hold FRONT-A  denies 260 + (219 + 3x76) = 707
    hold a BACK   denies only its own 260

...which is why FRONT-B is the more valuable gate, and why the owner's instinct to
put the hardest walls there is right. But 707 vs 805 is only the CEILING. What the
optimiser actually maximises is EXPECTED denial, and that discounts the fleet
lane by the chance the fleet territory would have held on its own, which on the
newly-pulled fleet tier list is 47%, far higher than any 5-squad zone manages.
That discount is the whole reason front-A can be defended more cheaply.

MODEL
-----
Attacker's expected haul from one 3v3 squad zone with holds h_1..h_5:
    sum_i (1-h_i)*57  +  260 * prod_i (1-h_i)
A back zone's whole value is multiplied by prod(1-h) over its own FRONT: the gate.
Denial = (everything available) minus (attacker's expected haul). The defender
earns nothing for placing; defense pays only in denial. See gac_score.py.

SHRINKAGE
---------
swgoh.gg publishes plenty of n<500 rows and they are noise. Every rate is shrunk
toward the pool mean, adj = (n*rate + K*mean)/(n + K) with K=3000, before anything
is ranked. Without it a 35.9% hold on n=375 outranks a 25.7% on n=86.3K.

USAGE
    python3 scripts/gac3v3_board.py                       # free optimum
    python3 scripts/gac3v3_board.py --structure owner     # the owner's proposal, priced
    python3 scripts/gac3v3_board.py --compare             # every structure, side by side
    python3 scripts/gac3v3_board.py --fleets              # fleet allocation only
"""
import argparse
import itertools
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gac_score as gs  # noqa: E402
import swgoh_data as sd  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "output")

# S83 is the LIVE 3v3 season, re-pulled 2026-09-21 off 1.31M battles; the S81
# files it replaced are kept in data/meta/ for comparison. Both were pulled after
# expanding the tier bands below S: they are <details> accordions whose "Show N
# more" control is a <summary>, not a <button>, so a click loop over buttons
# expands nothing and the extractor silently returns cards with null rates.
DEF_TIERLIST = os.path.join(DATA, "meta", "tierlist_3v3_def_kyber_s83_20260921.json")
OFF_TIERLIST = os.path.join(DATA, "meta", "tierlist_3v3_off_kyber_s83_20260921.json")
FLEET_DEF = os.path.join(DATA, "meta", "tierlist_fleet_def_kyber_s82_20260911.json")
FLEET_OFF = os.path.join(DATA, "meta", "tierlist_fleet_off_kyber_s82_20260911.json")

SHRINK_K = 3000.0

# --- banner constants, from gac_score (verified against swgoh.wiki) ----------
B3 = gs.battle_banners("3v3")                    # 57, a clean full-squad 3v3 clear
BF = 76                                          # a fleet clear; see gac_score
TERR3 = gs.territory_banners("3v3", 5)           # 260
TERRF = gs.territory_banners("fleet", 3)         # 219

TOTAL_AVAILABLE = 3 * (5 * B3 + TERR3) + (3 * BF + TERRF)


# ---------------------------------------------------------------- data loading
def load_roster():
    path = sd.latest_roster_file()
    r = json.load(open(path))
    units = r["units"] if isinstance(r, dict) else r
    chars = {u["n"]: u for u in units if u.get("ct") == 1}
    ships = {u["n"]: u for u in units if u.get("ct") == 2}
    return path, chars, ships


def _battles(s):
    if s is None:
        return 0.0
    s = str(s).replace(",", "").strip()
    mult = 1.0
    if s.endswith("K"):
        mult, s = 1e3, s[:-1]
    elif s.endswith("M"):
        mult, s = 1e6, s[:-1]
    try:
        return float(s) * mult
    except ValueError:
        return 0.0


def shrink(rate, n, prior):
    return (n * rate + SHRINK_K * prior) / (n + SHRINK_K)


def load_squads(path, rate_key, chars, min_gear=13):
    """Fieldable squads only: every unit owned and at or above `min_gear`.

    Dedup by unit SET keeping the row with the most battles. swgoh.gg lists the
    same three units in a reversed order with a tiny sample, and a naive dict
    write keeps the wrong one (The Stranger trio: 25.7% on n=86.3K vs 16.9% on 37).
    """
    doc = json.load(open(path))
    rated = [c for c in doc["cards"] if c.get(rate_key) is not None]
    prior = sum(c[rate_key] for c in rated) / max(1, len(rated))
    best, unowned = {}, set()
    for c in rated:
        names = c["units"]
        bad = [n for n in names if n not in chars or (chars[n].get("g") or 0) < min_gear]
        if bad:
            unowned.update(bad)
            continue
        key = frozenset(names)
        n = _battles(c.get("battles"))
        if key in best and best[key]["n"] >= n:
            continue
        best[key] = {
            "names": names,
            "bases": [chars[x]["b"] for x in names],
            "leader": c.get("leader") or names[0],
            "raw": c[rate_key],
            "n": n,
            "rate": shrink(c[rate_key], n, prior) / 100.0,
            "size": len(names),
            "dc": bool(c.get("dcDependent")),
            "rank": c.get("rank"),
        }
    return sorted(best.values(), key=lambda s: -s["rate"]), prior, unowned, doc.get("title", "")


def load_fleets(path, rate_key, ships):
    doc = json.load(open(path))
    rated = [c for c in doc["cards"] if c.get(rate_key) is not None]
    prior = sum(c[rate_key] for c in rated) / max(1, len(rated))
    best = {}
    for c in rated:
        cap = c["capital"]
        if cap not in ships:
            continue
        n = _battles(c.get("battles"))
        if cap in best and best[cap]["n"] >= n:
            continue
        starters = list(c["ships"][:3])
        best[cap] = {
            "capital": cap,
            "starters": starters,
            "missing": [s for s in starters if s not in ships],
            "raw": c[rate_key],
            "n": n,
            "rate": shrink(c[rate_key], n, prior) / 100.0,
            "rank": c.get("rank"),
        }
    return sorted(best.values(), key=lambda f: -f["rate"]), prior


# --------------------------------------------------------------------- scoring
def prod(xs):
    p = 1.0
    for x in xs:
        p *= x
    return p


def zone_haul(holds, terr=TERR3, battle=B3):
    """What the attacker expects to take out of one zone, ungated."""
    fall = prod(1.0 - h for h in holds)
    return sum((1.0 - h) * battle for h in holds) + terr * fall, fall


def board_denial(fa, fb, kb, fleets):
    """Expected banners DENIED, given hold probabilities per zone."""
    sa, fall_a = zone_haul(fa)
    sf, _ = zone_haul(fleets, terr=TERRF, battle=BF)
    sb, fall_b = zone_haul(fb)
    sk, _ = zone_haul(kb)
    conceded = sa + sb + fall_a * sf + fall_b * sk
    return TOTAL_AVAILABLE - conceded


def offense_value(wins, fleet_wins, realization=1.0):
    """Expected banners EARNED, against a generic Kyber board of the same shape.

    Best five squads take one front, next five the other front, the tail is spent
    on whichever back opens. Crude, but symmetric across every allocation being
    compared, which is all it has to be.

    `realization` scales the whole thing. It exists because the published win
    rates assume every attack gets played, on the right target, at full attention.
    This account converts about 37% of the banners available to it, so the raw
    figure systematically over-rewards putting a unit on offense. Sweep it before
    trusting any offense-vs-defense verdict.
    """
    ws = sorted(wins, reverse=True)

    def zone(g):
        if not g:
            return 0.0, 0.0
        p = prod(g)
        return sum(w * B3 for w in g) + TERR3 * p, p

    s1, p1 = zone(ws[0:5])
    s2, p2 = zone(ws[5:10])
    s3, _ = zone(ws[10:15])
    pf = prod(fleet_wins) if fleet_wins else 0.0
    sf = sum(w * BF for w in fleet_wins) + TERRF * pf
    return realization * (s1 + s2 + p1 * sf + p2 * s3)


# ------------------------------------------------------------- zone assignment
def split_exhaustive(holds, fleets):
    """Exact best partition of 15 holds into FA(5) / FB(5) / KB(5). 756,756 cases."""
    idx = list(range(len(holds)))
    best = (-1e9, None)
    for kb in itertools.combinations(idx, 5):
        kb_set = set(kb)
        rest = [i for i in idx if i not in kb_set]
        kb_h = [holds[i] for i in kb]
        for fa in itertools.combinations(rest, 5):
            fa_set = set(fa)
            fb = [i for i in rest if i not in fa_set]
            v = board_denial([holds[i] for i in fa], [holds[i] for i in fb], kb_h, fleets)
            if v > best[0]:
                best = (v, (list(fa), fb, list(kb)))
    return best


def split_fast(holds, fleets):
    """Good-enough partition for the inner loop of the selection search."""
    order = sorted(range(len(holds)), key=lambda i: -holds[i])
    kb, top = order[10:], order[:10]
    kb_h = [holds[i] for i in kb]
    best = (-1e9, None)
    for fa in itertools.combinations(top, 5):
        fa_set = set(fa)
        fb = [i for i in top if i not in fa_set]
        v = board_denial([holds[i] for i in fa], [holds[i] for i in fb], kb_h, fleets)
        if v > best[0]:
            best = (v, (list(fa), fb, list(kb)))
    return best


def split_owner(holds, fleets):
    """The owner's structure: hardest 5 in FRONT-B, next 5 in FRONT-A, rest BACK."""
    order = sorted(range(len(holds)), key=lambda i: -holds[i])
    fb, fa, kb = order[0:5], order[5:10], order[10:15]
    return board_denial([holds[i] for i in fa], [holds[i] for i in fb],
                        [holds[i] for i in kb], fleets), (fa, fb, kb)


def split_stacked_back(holds, fleets):
    """The board as actually set in Round 2: the best walls in the BACK zone."""
    order = sorted(range(len(holds)), key=lambda i: -holds[i])
    kb, fa, fb = order[0:5], order[5:10], order[10:15]
    return board_denial([holds[i] for i in fa], [holds[i] for i in fb],
                        [holds[i] for i in kb], fleets), (fa, fb, kb)


def split_balanced(holds, fleets):
    """Snake the top 10 across the two fronts, weakest 5 to the back."""
    order = sorted(range(len(holds)), key=lambda i: -holds[i])
    fb = [order[0], order[3], order[4], order[7], order[8]]
    fa = [order[1], order[2], order[5], order[6], order[9]]
    kb = order[10:]
    return board_denial([holds[i] for i in fa], [holds[i] for i in fb],
                        [holds[i] for i in kb], fleets), (fa, fb, kb)


def split_explicit(holds, fleets, names="", leaders=()):
    """Zone assignment dictated by name, for when the owner has decided the shape.

    `names` is 'A:leader,leader,...|B:leader,...'; whatever is left over goes to the
    back. Exists so a hand-chosen board is reproducible and priced by the same model
    as the optimiser's, instead of being typed into the game and forgotten.
    """
    want = {}
    for part in names.split("|"):
        tag, _, lst = part.partition(":")
        want[tag.strip().upper()] = [x.strip() for x in lst.split(",") if x.strip()]
    idx = {}
    for i, ldr in enumerate(leaders):
        idx.setdefault(ldr, []).append(i)
    fa, fb = [], []
    for tag, bucket in (("A", fa), ("B", fb)):
        for n in want.get(tag, []):
            if not idx.get(n):
                raise SystemExit(f"--layout: {n!r} is not on the selected board")
            bucket.append(idx[n].pop(0))
    kb = [i for i in range(len(holds)) if i not in fa and i not in fb]
    return board_denial([holds[i] for i in fa], [holds[i] for i in fb],
                        [holds[i] for i in kb], fleets), (fa, fb, kb)


SPLITTERS = {
    "free": split_exhaustive,
    "explicit": split_explicit,
    "owner": split_owner,
    "balanced": split_balanced,
    "back": split_stacked_back,
}


# The nine Galactic Legends this account owns, by the name that appears in the
# tier lists. Used only by --doctrine, which forces them onto one side or the
# other so the wall-versus-attack question is answered by a number.
GLS = ["Rey", "Supreme Leader Kylo Ren", "Leia Organa", "Lord Vader", "Ahsoka Tano",
       "Jabba the Hutt", "Sith Eternal Emperor", "Jedi Master Luke Skywalker",
       "Jedi Master Kenobi"]


def has_gl(squad):
    return any(u in GLS for u in squad["names"])


def gl_ratio_order(dpool, opool):
    """The nine GLs sorted by how much better each is at walling than attacking.

    A GL with a weak offense row is a cheap wall: GL Rey holds 31.2% and attacks
    at only 69.8%, the worst attacker of the nine, so walling her costs almost
    nothing. SEE is the mirror image, a 13.7% wall and an 89.0% attacker.
    """
    out = {}
    for gl in GLS:
        bd = max((s["rate"] for s in dpool if gl in s["names"]), default=0.0)
        bo = max((s["rate"] for s in opool if gl in s["names"]), default=0.0)
        out[gl] = (bd / bo if bo else 99.0, bd, bo)
    return sorted(GLS, key=lambda g: -out[g][0]), out


# ------------------------------------------------------------------- selection
def select(def_pool, off_pool, fleets_def, fleets_off, n_def=15, n_off=15,
           passes=4, verbose=False, realization=1.0,
           ban_def=None, ban_off=None, force_def=()):
    """Greedy plus local search over which squads defend and which attack.

    Units are single-use across the WHOLE format (rule 2), so choosing a squad for
    defense can cost an attacker and vice versa. That contention is the only thing
    making this hard.
    """
    fd = [f["rate"] for f in fleets_def]
    fo = [f["rate"] for f in fleets_off]
    if ban_def:
        def_pool = [s for s in def_pool if not ban_def(s)]
    if ban_off:
        off_pool = [s for s in off_pool if not ban_off(s)]

    def obj(dsel, osel):
        v, _ = split_fast([def_pool[i]["rate"] for i in dsel], fd)
        return v + offense_value([off_pool[i]["rate"] for i in osel], fo, realization)

    # Greedy seed. The 1.9 multiplier is the gate leverage a front wall carries
    # over its own battle banners; it only orders the seed, the local search
    # re-decides everything against the real objective.
    def m_def(i):
        return def_pool[i]["rate"] * B3 * 1.9

    def m_off(i):
        return off_pool[i]["rate"] * gs.battle_banners("3v3", team_size=off_pool[i]["size"])

    # Pinned walls go down first and their units are then unavailable to offence.
    # `force_def` is a list of unit names; the best fieldable squad containing each
    # is taken. Local search below is not allowed to swap them out.
    used, dsel, osel = set(), [], []
    pinned = set()
    for want in force_def:
        cand = [i for i, s in enumerate(def_pool)
                if want in s["names"] and i not in dsel and not (used & set(s["bases"]))]
        if not cand:
            raise SystemExit(f"--pin-def {want!r}: no fieldable squad left containing it")
        i = max(cand, key=lambda j: def_pool[j]["rate"])
        dsel.append(i)
        pinned.add(len(dsel) - 1)
        used |= set(def_pool[i]["bases"])

    while len(dsel) < n_def or len(osel) < n_off:
        cand = []
        if len(dsel) < n_def:
            for i, s in enumerate(def_pool):
                if i not in dsel and not (used & set(s["bases"])):
                    cand.append((m_def(i), "d", i))
                    break
        if len(osel) < n_off:
            for i, s in enumerate(off_pool):
                if i not in osel and not (used & set(s["bases"])):
                    cand.append((m_off(i), "o", i))
                    break
        if not cand:
            break
        _, side, i = max(cand)
        (dsel if side == "d" else osel).append(i)
        used |= set((def_pool if side == "d" else off_pool)[i]["bases"])

    best = obj(dsel, osel)
    for _ in range(passes):
        improved = False
        for side, sel, pool in (("d", dsel, def_pool), ("o", osel, off_pool)):
            for pos in range(len(sel)):
                if side == "d" and pos in pinned:
                    continue
                cur = sel[pos]
                others = set()
                for j, k in enumerate(dsel):
                    if not (side == "d" and j == pos):
                        others |= set(def_pool[k]["bases"])
                for j, k in enumerate(osel):
                    if not (side == "o" and j == pos):
                        others |= set(off_pool[k]["bases"])
                for cand_i, s in enumerate(pool):
                    if cand_i == cur or cand_i in sel or (others & set(s["bases"])):
                        continue
                    sel[pos] = cand_i
                    v = obj(dsel, osel)
                    if v > best + 1e-9:
                        best, cur, improved = v, cand_i, True
                    else:
                        sel[pos] = cur
                sel[pos] = cur
        if verbose:
            print(f"    pass -> {best:.1f}")
        if not improved:
            break
    # indices are into the FILTERED pools, so hand those back with them
    return dsel, osel, best, def_pool, off_pool


# ------------------------------------------------------------ fleet allocation
def allocate_fleets(fdef, foff, p_front_a_falls=0.25):
    """Split the owned capitals between the 3 defensive and 3 offensive slots.

    Ships are single-use exactly like characters, so a capital that walls cannot
    attack. Two capitals that share a published starting-3 ship cannot both be
    fielded either.
    """
    dmap = {f["capital"]: f for f in fdef}
    omap = {f["capital"]: f for f in foff}
    caps = sorted(set(dmap) & set(omap))

    def conflict(a, b):
        return bool(set(dmap[a]["starters"] + omap[a]["starters"])
                    & set(dmap[b]["starters"] + omap[b]["starters"]))

    best = None
    for six in itertools.combinations(caps, 6):
        if any(conflict(a, b) for a, b in itertools.combinations(six, 2)):
            continue
        for d in itertools.combinations(six, 3):
            o = [c for c in six if c not in d]
            dh = [dmap[c]["rate"] for c in d]
            ow = [omap[c]["rate"] for c in o]
            haul, _ = zone_haul(dh, terr=TERRF, battle=BF)
            denial = p_front_a_falls * ((3 * BF + TERRF) - haul)
            earn = sum(w * BF for w in ow) + TERRF * prod(ow)
            v = denial + earn
            if best is None or v > best[0]:
                best = (v, list(d), list(o), denial, earn)
    return best, dmap, omap


# ------------------------------------------------------------------ datacrons
ACCOUNT_DATA = os.path.join(OUT, "account_data_all_20260911.json")
UNIT_TAGS = os.path.join(DATA, "unit_tags.json")


def load_datacrons(path=ACCOUNT_DATA):
    """Owned datacrons, newest sets first. Affix array LENGTH is the level.

    Each affix's `targetRule` is a scope, and they nest: alignment, then faction,
    then a single character (`target_datacron_darkside`, `..._firstorder`,
    `..._kylorenunmasked`). The last one is the narrowest.
    """
    if not os.path.exists(path):
        return []
    doc = json.load(open(path))
    out = []
    for dc in doc["data"].get("datacrons", []):
        scopes = [a["targetRule"].replace("target_datacron_", "")
                  for a in dc.get("affix", []) if a.get("targetRule")]
        out.append({"id": dc["id"], "set": dc.get("setId"),
                    "level": len(dc.get("affix", [])), "scopes": scopes,
                    "narrowest": scopes[-1] if scopes else None})
    return sorted(out, key=lambda d: (-d["level"], -(d["set"] or 0)))


def _tokens(base_id, tags):
    t = tags.get(base_id, {})
    out = {base_id.lower()}
    if t.get("a"):
        out.add(t["a"].replace(" ", "").lower())
    if t.get("r"):
        out.add(t["r"].lower())
    for c in t.get("c", []):
        out.add(c.replace(" ", "").replace("-", "").replace("'", "").lower())
    return out


def assign_datacrons(squads, crons, tags):
    """Greedy: the deepest cron first, onto the squad it scopes most completely.

    A perfectly scoped cron sitting idle is free banners, and this account had a
    set-33 LEVEL 15 scoped to all five Hutt Cartel units equipped to nothing.
    """
    tok = [[_tokens(b, tags) for b in s["bases"]] for s in squads]
    taken, out = set(), {}
    for dc in crons:
        if dc["level"] < 3 or not dc["narrowest"]:
            continue
        best = None
        for i in range(len(squads)):
            if i in taken:
                continue
            hits = sum(1 for u in tok[i] if dc["narrowest"] in u)
            if hits == 0:
                continue
            depth = sum(1 for sc in dc["scopes"]
                        if all(sc in u for u in tok[i]))
            key = (hits, depth, dc["level"])
            if best is None or key > best[0]:
                best = (key, i)
        if best:
            taken.add(best[1])
            out[best[1]] = {"cron": dc, "hits": best[0][0]}
    return out


# ---------------------------------------------------------------------- report
# The in-game preset name limit is short, about 16 characters; anything longer is
# rejected outright with INVALID_SQUAD_PRESET_NAME_LENGTH_KEY. The zone tag has to
# survive, so the leader is what gets abbreviated.
LEADER_SHORT = {
    "Supreme Leader Kylo Ren": "SLKR", "Sith Eternal Emperor": "SEE",
    "Jedi Master Kenobi": "JMK", "Jedi Master Luke Skywalker": "JML",
    "Jedi Knight Luke Skywalker": "JKLS", "Lord Vader": "LordVader",
    "Leia Organa": "GL Leia", "Ahsoka Tano": "GLAhsoka", "Rey": "GL Rey",
    "Jabba the Hutt": "Jabba", "Cassian Andor (Undercover)": "Cassian",
    "Emperor Palpatine": "EmpPalp", "Stormtrooper Luke": "STLuke",
    "Great Mothers": "GreatMoms", "Major Partagaz": "Partagaz",
    "Bo-Katan (Mand'alor)": "BoKatan", "Queen Amidala": "QAmidala",
    "Dark Trooper Moff Gideon": "DTGideon", "General Skywalker": "GAS",
    "Tusken Chieftain": "Tusken", "Qui-Gon Jinn": "QuiGon",
    "Kelleran Beq": "Kelleran", "Admiral Raddus": "AdmRaddus",
    "Rotta the Hutt": "Rotta", "Great Mothers": "GreatMoms",
    "Boba Fett, Scion of Jango": "BobaSoJ",
    "The Stranger": "Stranger", "Darth Malgus": "Malgus", "Darth Traya": "Traya",
    "Baylan Skoll": "Baylan", "Cere Junda": "Cere", "Ugnaught": "Ugnaught",
}


def short_name(tag, leader, limit=16):
    base = LEADER_SHORT.get(leader) or leader.split(" (")[0]
    name = f"{tag} {base}"
    if len(name) <= limit:
        return name
    return f"{tag} {base[:limit - len(tag) - 1]}"


def fmt_squad(s, tag=""):
    return (f"{s['rate']*100:5.1f}% (raw {s['raw']:4.1f} n={int(s['n']):>7,})"
            f"{' DC' if s['dc'] else '   '} {tag} {' / '.join(s['names'])}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--structure", choices=list(SPLITTERS), default="free")
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--fleets", action="store_true")
    ap.add_argument("--doctrine", action="store_true",
                    help="price GLs-wall against GLs-attack, swept over offense realization")
    ap.add_argument("--fleets-on-defense", action="store_true",
                    help="force the three best DEFENSIVE capitals into the fleet territory")
    ap.add_argument("--layout", default="", metavar="A:...|B:...",
                    help="with --structure explicit, name the leaders in each FRONT zone; "
                         "everything else falls to the back")
    ap.add_argument("--rate-override", default="", metavar="NAME=PCT[,...]",
                    help="override a defensive squad's shrunk hold, e.g. "
                         "'Rotta the Hutt=25'. Use when the account holds a cron the published "
                         "sample does not, and SAY SO in the writeup: it is an assumption, not data")
    ap.add_argument("--pin-def", default="", metavar="NAMES",
                    help="comma-separated unit names that MUST wall (their best fieldable squad "
                         "is taken and locked, and their units are barred from offence)")
    ap.add_argument("--pin-off", default="", metavar="NAMES",
                    help="comma-separated unit names that MUST attack (barred from defence)")
    ap.add_argument("--gl-wall", type=int, default=None, metavar="K",
                    help="force the K best-walling Galactic Legends onto defense "
                         "and the rest onto offense (see --doctrine for the sweep)")
    ap.add_argument("--realization", type=float, default=1.0,
                    help="fraction of published offense actually converted (see offense_value)")
    ap.add_argument("--json", help="write the board to this path")
    ap.add_argument("--upload", metavar="PATH",
                    help="also emit a HotUtils payload (upload_hotutils.py shape). Squad names "
                         "carry the ZONE so the board can be placed straight off the pick-list, "
                         "and stay inside the ~16-char in-game preset name limit.")
    ap.add_argument("--min-gear", type=int, default=13)
    ap.add_argument("--p-front-a-falls", type=float, default=0.25)
    args = ap.parse_args()

    rpath, chars, ships = load_roster()
    dpool, dprior, _, dtitle = load_squads(DEF_TIERLIST, "hold", chars, args.min_gear)
    opool, oprior, _, otitle = load_squads(OFF_TIERLIST, "win", chars, args.min_gear)
    fdef, _ = load_fleets(FLEET_DEF, "hold", ships)
    foff, _ = load_fleets(FLEET_OFF, "win", ships)

    for spec in (s for s in args.rate_override.split(",") if s.strip()):
        name, _, pct = spec.rpartition("=")
        hits = [s for s in dpool if name.strip() in s["names"]]
        if not hits:
            sys.exit(f"--rate-override {name!r}: no fieldable defensive squad has that unit")
        for s in hits:
            s["rate"] = float(pct) / 100.0
            s["raw"] = float(pct)
        dpool.sort(key=lambda s: -s["rate"])
        print(f"OVERRIDE  {name.strip()} hold set to {float(pct):.1f}% "
              f"({len(hits)} squad(s)). This is an ASSUMPTION, not published data.")

    print(f"roster  {os.path.basename(rpath)}  ({len(chars)} characters, "
          f"{sum(1 for c in chars.values() if (c.get('g') or 0) >= 13)} at G13+)")
    print(f"def     {dtitle[:52]}  {len(dpool)} fieldable, prior {dprior:.1f}%")
    print(f"off     {otitle[:52]}  {len(opool)} fieldable, prior {oprior:.1f}%")
    print(f"board   {TOTAL_AVAILABLE} banners available to the attacker "
          f"(3 x {5*B3+TERR3} squad zones + {3*BF+TERRF} fleet)\n")

    fbest, dmap, omap = allocate_fleets(fdef, foff, args.p_front_a_falls)
    if args.fleets_on_defense:
        # the owner's ask: best possible fleet on defense, offense takes what is left
        fd_caps = [f["capital"] for f in fdef if f["capital"] in omap][:3]
        rest = [c for c in sorted(omap, key=lambda c: -omap[c]["rate"]) if c not in fd_caps]
        fo_caps = rest[:3]
        fleets_def = [dmap[c] for c in fd_caps]
        fleets_off = [omap[c] for c in fo_caps]
        haul, _ = zone_haul([f["rate"] for f in fleets_def], terr=TERRF, battle=BF)
        fden = args.p_front_a_falls * ((3 * BF + TERRF) - haul)
        ow = [f["rate"] for f in fleets_off]
        fearn = sum(w * BF for w in ow) + TERRF * prod(ow)
    elif fbest:
        _, fd_caps, fo_caps, fden, fearn = fbest
        fleets_def = [dmap[c] for c in fd_caps]
        fleets_off = [omap[c] for c in fo_caps]
    else:
        fleets_def, fleets_off, fden, fearn = fdef[:3], foff[:3], 0.0, 0.0

    print("FLEETS  (ships are single-use too, so a capital that walls cannot attack)")
    print("  defend:  " + ", ".join(
        f"{f['capital']} {f['rate']*100:.1f}% (raw {f['raw']}%, n={int(f['n']):,})"
        for f in fleets_def))
    print("  attack:  " + ", ".join(
        f"{f['capital']} {f['rate']*100:.1f}% (raw {f['raw']}%, n={int(f['n']):,})"
        for f in fleets_off))
    ph = 1 - prod(1 - f["rate"] for f in fleets_def)
    print(f"  P(fleet territory holds) = {ph*100:.0f}%   "
          f"expected denial {fden:.0f}, expected offense {fearn:.0f}\n")
    if args.fleets:
        print("  owned capitals, shrunk (off win% / def hold%):")
        for c in sorted(set(dmap) & set(omap), key=lambda c: -omap[c]["rate"]):
            miss = omap[c]["missing"] or dmap[c]["missing"]
            print(f"    {c:<12} off {omap[c]['rate']*100:5.1f}%  def {dmap[c]['rate']*100:5.1f}%"
                  f"   starters {', '.join(omap[c]['starters'])}"
                  + (f"   MISSING {miss}" if miss else ""))
        return

    fd = [f["rate"] for f in fleets_def]
    fo = [f["rate"] for f in fleets_off]

    if args.doctrine:
        # Rank the GLs by how much better they are at walling than at attacking.
        # A GL with no offense row, or a bad one, is a free wall; a GL who is a
        # 90% attacker and a 15% wall is being wasted on defense.
        order, ratio = gl_ratio_order(dpool, opool)
        print("DOCTRINE: how many Galactic Legends should WALL?")
        print("Ranked by wall-value over attack-value, best waller first:")
        for g in order:
            r_, bd, bo = ratio[g]
            print(f"    {g:<28} def {bd*100:5.1f}%  off {bo*100:5.1f}%   ratio {r_:.2f}")
        rs = (1.0, 0.8, 0.6, 0.37)
        print("\n`r` is the fraction of published offense actually converted. This "
              "account\nhistorically converts about 0.37 of the banners available to it.\n")
        print(f"  {'GLs walling':<34}" + "".join(f"   r={r:<5}" for r in rs))
        for k in range(len(order) + 1):
            wall, attack = set(order[:k]), set(order[k:])
            bd = (lambda s: any(u in attack for u in s["names"]))
            bo = (lambda s: any(u in wall for u in s["names"]))
            row = []
            for r in rs:
                ds, os_, _, dp, op = select(dpool, opool, fleets_def, fleets_off,
                                            realization=r, ban_def=bd, ban_off=bo)
                v, _ = split_exhaustive([dp[i]["rate"] for i in ds], fd)
                row.append(v + offense_value([op[i]["rate"] for i in os_], fo, r))
            label = f"{k}  ({', '.join(order[:k]) if k else 'none'})"
            print(f"  {label[:33]:<34}" + "".join(f"  {x:7.0f}" for x in row))
        print("\n  (higher is better; the column winner is the doctrine to use at that r)")
        return

    bd = bo = None
    force = [n.strip() for n in args.pin_def.split(",") if n.strip()]
    if args.gl_wall is not None:
        order, _ = gl_ratio_order(dpool, opool)
        wall, attack = set(order[:args.gl_wall]), set(order[args.gl_wall:])
        bd = lambda s: any(u in attack for u in s["names"])   # noqa: E731
        bo = lambda s: any(u in wall for u in s["names"])     # noqa: E731
        print(f"GL DOCTRINE: {args.gl_wall} wall ({', '.join(order[:args.gl_wall])}); "
              f"the other {9-args.gl_wall} attack\n")
    if args.pin_off or force:
        must_attack = {n.strip() for n in args.pin_off.split(",") if n.strip()}
        bd = lambda s: any(u in must_attack for u in s["names"])   # noqa: E731
        bo = lambda s: any(u in set(force) for u in s["names"])    # noqa: E731
        print(f"PINNED  wall: {', '.join(force) or 'none'}\n"
              f"        attack: {', '.join(sorted(must_attack)) or 'none'}\n")

    dsel, osel, _, dpool, opool = select(dpool, opool, fleets_def, fleets_off,
                                         realization=args.realization,
                                         ban_def=bd, ban_off=bo, force_def=force)
    holds = [dpool[i]["rate"] for i in dsel]

    leaders = [dpool[i]["leader"] for i in dsel]
    names = [n for n in SPLITTERS if n != "explicit"] if args.compare else [args.structure]

    def run(n):
        if n == "explicit":
            return split_explicit(holds, fd, args.layout, leaders)
        return SPLITTERS[n](holds, fd)

    results = {n: run(n) for n in names}
    offv = offense_value([opool[i]["rate"] for i in osel], fo, args.realization)

    if args.compare:
        print("STRUCTURE COMPARISON: same 15 squads, only the zone assignment changes")
        # The baseline is the `back` STRUCTURE, ie the worst case where the best walls
        # are stacked behind a front. It is NOT the live board: nothing here reads
        # gac/get. This used to print "vs the Round-2 board", which invited a session to
        # re-place 15 squads to chase a delta it had not actually measured. To compare
        # against what is really deployed, read the live zones first (browser_recipes §4
        # `gac/get`, home.zones[].squads) and check which structure they already match.
        base = results["back"][0]
        for n in ("free", "owner", "balanced", "back"):
            v, (fa, fb, kb) = results[n]
            pa = 1 - prod(1 - holds[i] for i in fa)
            pb = 1 - prod(1 - holds[i] for i in fb)
            print(f"  {n:<9} denial {v:7.0f}  ({v-base:+6.0f} vs `back`, the stacked worst case)"
                  f"   P(front-A holds) {pa*100:4.0f}%   P(front-B holds) {pb*100:4.0f}%")
        print()

    pick = "free" if args.compare else args.structure
    v, (fa, fb, kb) = results[pick]
    print(f"BOARD, structure `{pick}`   denial {v:.0f} / {TOTAL_AVAILABLE}"
          f"   offense {offv:.0f}   net {offv - (TOTAL_AVAILABLE - v):+.0f}\n")

    wall_squads = [dpool[dsel[i]] for i in range(len(dsel))]
    tags = json.load(open(UNIT_TAGS)) if os.path.exists(UNIT_TAGS) else {}
    crons = assign_datacrons(wall_squads, load_datacrons(), tags) if tags else {}

    for zname, ids, behind in (
            ("FRONT-A  phase01_conflict01  gates the 3 FLEETS", fa, TERRF + 3 * BF),
            ("FRONT-B  phase01_conflict02  gates BACK-B", fb, TERR3 + 5 * B3),
            ("BACK-B   phase02_conflict02", kb, 0)):
        p = 1 - prod(1 - holds[i] for i in ids)
        print(f"== {zname}   P(holds) {p*100:.0f}%"
              + (f", {TERR3 + behind} banners ride on it" if behind else ""))
        for r, i in enumerate(sorted(ids, key=lambda j: -holds[j]), 1):
            print("   " + fmt_squad(dpool[dsel[i]], f"[{r}]"))
            c = crons.get(i)
            if c:
                print(f"        cron {c['cron']['id']}  set {c['cron']['set']} "
                      f"L{c['cron']['level']}  scope {'>'.join(c['cron']['scopes'][-3:])}"
                      f"  ({c['hits']}/3 units)")
        print()
    print("== OFFENCE (15), unit-disjoint from every wall above")
    for r, i in enumerate(sorted(osel, key=lambda j: -opool[j]["rate"]), 1):
        s = opool[i]
        print(f"   O{r:<3}{s['rate']*100:5.1f}% (raw {s['raw']:4.1f} n={int(s['n']):>7,}) "
              f"{s['size']}u  {' / '.join(s['names'])}")

    if args.json:
        payload = {
            "structure": pick, "denial": v, "offense": offv,
            "fleets_def": [f["capital"] for f in fleets_def],
            "fleets_off": [f["capital"] for f in fleets_off],
            "zones": {
                "phase01_conflict01": [dpool[dsel[i]]["bases"] for i in fa],
                "phase01_conflict02": [dpool[dsel[i]]["bases"] for i in fb],
                "phase02_conflict02": [dpool[dsel[i]]["bases"] for i in kb],
            },
            "offence": [opool[i]["bases"] for i in osel],
        }
        json.dump(payload, open(args.json, "w"), indent=2)
        print(f"\nwrote {args.json}")

    if args.upload:
        rows = []
        for tag, ids in (("A", fa), ("B", fb), ("K", kb)):
            for r, i in enumerate(sorted(ids, key=lambda j: -holds[j]), 1):
                s = dpool[dsel[i]]
                rows.append({"n": short_name(f"{tag}{r}", s["leader"]), "sz": 3, "ct": 1,
                             "cat": "GAC 3v3 - Defense",
                             "u": list(zip(s["bases"], s["names"]))})
        for r, i in enumerate(sorted(osel, key=lambda j: -opool[j]["rate"]), 1):
            s = opool[i]
            rows.append({"n": short_name(f"O{r}", s["leader"]), "sz": s["size"], "ct": 1,
                         "cat": "GAC 3v3 - Offense",
                         "u": list(zip(s["bases"], s["names"]))})
        json.dump(rows, open(args.upload, "w"), indent=2)
        print(f"wrote {args.upload}  ({len(rows)} definitions, "
              f"longest name {max(len(r['n']) for r in rows)} chars)")


if __name__ == "__main__":
    main()
