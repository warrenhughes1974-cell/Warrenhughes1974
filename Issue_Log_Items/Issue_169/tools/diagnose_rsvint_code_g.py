"""Issue #169 -- RULED OUT: reserve interest code RSVINT='G' is NOT the cause of
the 5667AT (667 ART) $0 reserve. Kept as the evidence trail for that dead end.

QuikValf.MPLAN is a composite valuation key: MORT(2) + RSVINT(1) + RSVMETH(1) +
plan code, so 5667AT values as 'A1G35667AT'. RSVINT='G' is a valid QLAdmin code
(6.00% -- Issue #80 code map, QLAdmin Help 6.10) and one 5667AT policy does
value on it, so the code resolves fine. 5667AT is simply the only plan on 'G',
which makes "code G fails" and "5667AT fails" the same statement.

Actual cause: the plan has no reachable QuikTvs terminal-reserve row. See
prove_mean_reserve_formula.py and confirm_art_effdate_gap.py.

Read-only.
"""

from __future__ import annotations

import struct
from collections import defaultdict
from pathlib import Path

Q_DIR = Path(r"Q:\CSO\CSO_Test_6_30_2026")


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
    valf, _ = read_dbf(find("quikvalf"))

    # MPLAN = MORT(2) + RSVINT(1) + RSVMETH(1) + plan; riders emit bare plan codes.
    by_int = defaultdict(lambda: {"rows": 0, "res_nz": 0, "sum": 0.0, "plans": set()})
    for r in valf:
        mplan = (r.get("MPLAN") or "").strip()
        if len(mplan) <= 6:
            code, plan = "(bare rider)", mplan
        else:
            code, plan = mplan[2], mplan[4:]
        s = by_int[code]
        s["rows"] += 1
        s["plans"].add(plan)
        res = num(r.get("MRESERVE"))
        s["sum"] += res
        if res:
            s["res_nz"] += 1

    print("=" * 84)
    print("Live 6/30 QuikValf -- reserve success by RSVINT code (MPLAN char 3)")
    print("=" * 84)
    print(f"  {'RSVINT':<14}{'rows':>7}{'MRESERVE nz':>13}{'% valued':>10}"
          f"{'reserve total':>18}{'plans':>7}")
    for code, s in sorted(by_int.items(), key=lambda kv: -kv[1]["rows"]):
        pct = 100.0 * s["res_nz"] / s["rows"] if s["rows"] else 0
        print(f"  {code:<14}{s['rows']:>7}{s['res_nz']:>13}{pct:>9.1f}%"
              f"{s['sum']:>18,.2f}{len(s['plans']):>7}")

    print()
    print("  Plans on each code that produced ZERO reserve on every row:")
    for code, s in sorted(by_int.items()):
        if s["res_nz"] == 0:
            print(f"    RSVINT={code!r}: {sorted(s['plans'])}")

    # Which RSVINT codes does QuikPlTv define, and do QLAdmin's interest tables
    # carry them?
    print()
    print("=" * 84)
    print("QuikPlTv RSVINT codes in the Q region (plan count per code)")
    print("=" * 84)
    pltv, _ = read_dbf(find("QuikPlTv"))
    codes = defaultdict(set)
    for r in pltv:
        codes[(r.get("RSVINT") or "").strip()].add((r.get("PLAN") or "").strip())
    for code, plans in sorted(codes.items()):
        flag = "  <-- 5667AT" if "5667AT" in plans else ""
        print(f"  RSVINT={code!r:<6} plans={len(plans):<4}{flag}")

    for tbl in ("QuikUint", "QuikAint"):
        try:
            rows, fields = read_dbf(find(tbl))
        except (StopIteration, PermissionError):
            print(f"\n  {tbl}: not present / locked in Q region")
            continue
        print(f"\n  {tbl}: {len(rows)} rows; fields = {[n for n, _ in fields]}")
        for r in rows[:20]:
            print("    ", {k: v for k, v in r.items() if v})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
