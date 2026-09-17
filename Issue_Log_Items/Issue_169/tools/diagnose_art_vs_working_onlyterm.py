"""Issue #169 -- find the discriminator between 5667AT (reserves $0) and the
one-year-term plans QLAdmin DOES value off the net premium (MRESERVE = MTABNET/2).

Reads Warren's live 6/30 Q region. Read-only.

For every QuikValf row it recomputes the QuikNps grid address the engine must
have used (PLAN / GENDER / UWCLASS / AGE / CNTL / slot) and reports whether a
matching factor row exists in the Q region's own QuikNps.dbf. Plans whose
MTABNET is non-zero are the control; 5667AT is the subject.
"""

from __future__ import annotations

import struct
from collections import Counter, defaultdict
from pathlib import Path

Q_DIR = Path(r"Q:\CSO\CSO_Test_6_30_2026")
SUBJECT = "5667AT"
ANCHORS = {"9010800356C", "9010768802C", "9010764248C"}


def read_dbf(path: Path):
    with path.open("rb") as fh:
        header = fh.read(32)
        recs = struct.unpack_from("<I", header, 4)[0]
        hlen = struct.unpack_from("<H", header, 8)[0]
        rlen = struct.unpack_from("<H", header, 10)[0]
        fh.seek(32)
        fields = []
        while True:
            raw = fh.read(32)
            if not raw or raw[0] in (0x0D, 0x00):
                break
            name = raw[:11].split(b"\x00", 1)[0].decode("ascii", "replace").strip()
            fields.append((name, raw[16]))
        fh.seek(hlen)
        rows = []
        for _ in range(recs):
            rec = fh.read(rlen)
            if len(rec) < 2:
                break
            off = 1
            d = {}
            for name, length in fields:
                d[name] = rec[off:off + length].decode("latin-1", "replace").strip()
                off += length
            if rec[0:1] != b"*":
                rows.append(d)
    return rows, fields


def find(stem: str) -> Path:
    return next(p for p in Q_DIR.iterdir() if p.name.lower() == f"{stem.lower()}.dbf")


def num(v):
    try:
        return float(str(v).strip() or 0)
    except ValueError:
        return 0.0


def main() -> int:
    try:
        valf, valf_fields = read_dbf(find("quikvalf"))
    except PermissionError:
        print("QuikValf.dbf is locked -- close Advantage Data Architect / QLAdmin.")
        return 2

    print("=" * 90)
    print("STEP 1 -- full QuikValf record for the 667 ART anchor (every field)")
    print("=" * 90)
    anchor_rows = [r for r in valf if r.get("MPOLICY") in ANCHORS]
    for r in anchor_rows:
        print(f"\n  {r.get('MPOLICY')}  MPHASE={r.get('MPHASE')}")
        for name, _ in valf_fields:
            v = r.get(name, "")
            if v not in ("", "0", "0.00", ".00"):
                print(f"    {name:12s} = {v!r}")

    print()
    print("=" * 90)
    print("STEP 2 -- which plans did QLAdmin value off the net premium?")
    print("          (MTABNET non-zero, and does MRESERVE == MTABNET/2 ?)")
    print("=" * 90)
    per_plan = defaultdict(lambda: {"rows": 0, "tabnet_nz": 0, "res_nz": 0,
                                    "half_match": 0, "res_sum": 0.0})
    tabnet_field = "MTABNET" if any(n == "MTABNET" for n, _ in valf_fields) else None
    if tabnet_field is None:
        print("  !! QuikValf has no MTABNET field. Fields present:")
        print("    ", [n for n, _ in valf_fields])
    for r in valf:
        plan = (r.get("MPLAN") or "").strip()
        s = per_plan[plan]
        s["rows"] += 1
        res = num(r.get("MRESERVE"))
        tab = num(r.get(tabnet_field)) if tabnet_field else 0.0
        s["res_sum"] += res
        if tab:
            s["tabnet_nz"] += 1
        if res:
            s["res_nz"] += 1
        if (res or tab) and abs(res - tab / 2.0) <= 0.02:
            s["half_match"] += 1

    print(f"  {'MPLAN':<14}{'rows':>6}{'MTABNET nz':>12}{'MRESERVE nz':>12}"
          f"{'res==tab/2':>12}{'reserve total':>16}")
    for plan, s in sorted(per_plan.items(), key=lambda kv: -kv[1]["tabnet_nz"])[:25]:
        print(f"  {plan:<14}{s['rows']:>6}{s['tabnet_nz']:>12}{s['res_nz']:>12}"
              f"{s['half_match']:>12}{s['res_sum']:>16,.2f}")

    print()
    print("  Subject rows (MPLAN containing 5667AT):")
    for plan, s in sorted(per_plan.items()):
        if SUBJECT in plan:
            print(f"    {plan:<14}rows={s['rows']} MTABNET nz={s['tabnet_nz']} "
                  f"MRESERVE nz={s['res_nz']} total={s['res_sum']:,.2f}")

    print()
    print("=" * 90)
    print("STEP 3 -- Q region QuikNps / QuikTvs coverage for the subject plan")
    print("=" * 90)
    for table, pfx in (("QuikNps", "NP"), ("QuikTvs", "TV")):
        rows, _ = read_dbf(find(table))
        sub = [r for r in rows if (r.get("PLAN") or "").strip() == SUBJECT]
        gens = Counter((r.get("GENDER"), r.get("UWCLASS"), r.get("EFFDATE")) for r in sub)
        nonzero = sum(
            1 for r in sub
            if any((r.get(f"{pfx}{i}") or "").strip() not in ("", ".00", "0.00")
                   for i in range(10))
        )
        print(f"\n  {table}: {len(sub)} rows for {SUBJECT}; rows with a non-zero cell = {nonzero}")
        for k, v in sorted(gens.items()):
            print(f"    {k} -> {v}")
        hit = [r for r in sub if r.get("GENDER") == "M" and (r.get("AGE") or "").strip() == "39"
               and (r.get("CNTL") or "").strip() == "03"]
        for r in hit:
            print(f"    M AGE=39 CNTL=03 {r.get('UWCLASS')} EFF={r.get('EFFDATE')}: "
                  f"{[(r.get(f'{pfx}{i}') or '').strip() for i in range(10)]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
