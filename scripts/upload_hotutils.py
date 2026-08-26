#!/usr/bin/env python3
"""
upload_hotutils.py — push output/upload_payload.json to HotUtils. Browser-free.

    HU_SID=<live session id> python3 scripts/upload_hotutils.py --plan
    HU_SID=<live session id> python3 scripts/upload_hotutils.py --delete-all
    HU_SID=<live session id> python3 scripts/upload_hotutils.py --create

⛔ A PARTIAL payload must pass --categories. `--sync` voids every live definition the
payload does not name, so `--sync --payload tw_upload_payload.json` without a scope
wipes the whole GAC board. With `--categories "TW "` the delete half only ever touches
definitions whose category starts with that prefix.

A previous rebuild died mid-flight after deleting 62 squads and creating 42,
because HotUtils throttles at roughly 40+ rapid calls. Two things follow, and
both are built in:
  * every call is paced and retried;
  * --create is RESUME-BY-NAME. It lists what already exists and only creates
    the missing names, so re-running after a timeout finishes the job instead of
    duplicating it.

The session id is ephemeral and is read from $HU_SID — never hardcode or commit it.
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.hotutils.com/Production/"
APIUSERID = "898a36a3-948a-4a8a-9798-7a1552b042a8"
PACE = 0.45          # seconds between calls
RETRIES = 4

BOILER = {"hasOmicron": False, "hasZeta": False, "hasUltimate": False,
          "filters": {"minGP": 1000, "gear": 0, "relic": 0, "stars": 2},
          "subsPriority": "order"}


def api(path, body, sid):
    payload = dict(body)
    payload["sessionId"] = sid
    data = json.dumps(payload).encode()
    last = None
    for attempt in range(RETRIES):
        try:
            req = urllib.request.Request(
                API + path, data=data,
                headers={"content-type": "application/json", "apiuserid": APIUSERID})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as e:
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"{path} failed after {RETRIES} tries: {last}")


def listing(sid):
    L = api("squads/list", {}, sid)
    defs = [d for g in L.get("groupings", []) for d in g.get("definitions", [])]
    return L, defs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true", help="show what would change")
    ap.add_argument("--delete-all", action="store_true")
    ap.add_argument("--create", action="store_true", help="create missing (resume-safe)")
    ap.add_argument("--sync", action="store_true",
                    help="delete stale/changed definitions, then create what is missing")
    ap.add_argument("--payload", default=os.path.join(ROOT, "output", "upload_payload.json"))
    ap.add_argument("--categories", default=None,
                    help="comma-separated category prefixes. Scopes --sync/--delete-all to "
                         "those categories only, so a PARTIAL payload cannot delete the rest "
                         "of the board. Without it --sync compares against every definition.")
    a = ap.parse_args()

    sid = os.environ.get("HU_SID")
    if not sid:
        sys.exit("set HU_SID to a live HotUtils session id")
    want = json.load(open(a.payload))

    def scoped(all_defs):
        """The definitions --sync/--delete-all are allowed to VOID.

        Without --categories that is everything, which is only safe for a whole-board
        payload. A partial payload (TW only, one RotE phase) must pass --categories or
        --sync will delete the rest of the board — the trap CLAUDE.md warns about.
        """
        if not a.categories:
            return all_defs
        pre = tuple(s.strip() for s in a.categories.split(",") if s.strip())
        return [d for d in all_defs
                if any(c.startswith(pre) for c in (d.get("category") or []))]

    _, defs = listing(sid)
    have = {d.get("name"): d for d in defs}   # every live name: --create must not duplicate
    print(f"live: {len(defs)} definitions   payload: {len(want)} definitions")
    if a.categories:
        print(f"scoped to {a.categories!r}: {len(scoped(defs))} live definitions in scope")

    if a.plan:
        missing = [w for w in want if w["n"] not in have]
        stale = [d for d in scoped(defs) if d.get("name") not in {w["n"] for w in want}]
        print(f"  would delete {len(stale)}, create {len(missing)}, keep {len(want) - len(missing)}")
        for d in stale:
            print(f"    - {d.get('category')} {d.get('name')}")
        for k, v in sorted(Counter(w["cat"] for w in want).items()):
            print(f"    {v:3}  {k}")
        return

    if a.delete_all:
        defs = scoped(defs)
        print(f"deleting {len(defs)} ...")
        for i, d in enumerate(defs, 1):
            r = api("squads/upsert", {"id": d["id"], "void": True}, sid)
            if r.get("responseCode") != 1:
                print(f"  !! {d['id']} {d.get('name')}: {r.get('responseMessage')}")
            if i % 10 == 0:
                print(f"  {i}/{len(defs)}")
            time.sleep(PACE)
        _, defs2 = listing(sid)
        print(f"done. remaining: {len(defs2)}")
        return

    if a.sync:
        # resume-by-name deliberately skips a name that already exists, which is wrong
        # when a lineup CHANGED. Delete anything stale or altered, then fall through
        # to --create, which fills the holes.
        def contents_of(d):
            c = d.get("contents")
            try:
                c = json.loads(c) if isinstance(c, str) else c
                return [u["characterId"] for u in c]
            except Exception:
                return None

        wanted = {w["n"]: [u[0] for u in w["u"]] for w in want}
        drop = [d for d in scoped(defs)
                if d.get("name") not in wanted or contents_of(d) != wanted[d["name"]]]
        print(f"stale/changed: {len(drop)}")
        for d in drop:
            print(f"  - {d.get('name')}")
            api("squads/upsert", {"id": d["id"], "void": True}, sid)
            time.sleep(PACE)
        _, defs = listing(sid)
        have = {d.get("name"): d for d in defs}
        a.create = True

    if a.create:
        todo = [w for w in want if w["n"] not in have]
        print(f"creating {len(todo)} (skipping {len(want) - len(todo)} already present) ...")
        made = 0
        for i, w in enumerate(todo, 1):
            definition = {
                "name": w["n"], "size": w["sz"], "combatType": w["ct"], "category": [w["cat"]],
                "contents": json.dumps([
                    {"id": j, "characterId": b, "characterName": nm, "requirements": BOILER}
                    for j, (b, nm) in enumerate(w["u"])]),
            }
            r = api("squads/upsert", {"definition": definition}, sid)
            if r.get("responseCode") == 1:
                made += 1
            else:
                print(f"  !! {w['n']}: rc={r.get('responseCode')} {r.get('responseMessage')} "
                      f"{r.get('errorMessage')}")
            if i % 10 == 0:
                print(f"  {i}/{len(todo)}")
            time.sleep(PACE)
        _, defs2 = listing(sid)
        print(f"created {made}. live now: {len(defs2)}")
        for k, v in sorted(Counter(c for d in defs2 for c in (d.get('category') or ['?'])).items()):
            print(f"    {v:3}  {k}")
        return

    ap.print_help()


if __name__ == "__main__":
    main()
