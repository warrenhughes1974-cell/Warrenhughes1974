"""Diagnose why 9010800356C (667 ART, plan 5667AT) still reserves $0 after
Warren's fresh 6/30 valuation run in Q:\\CSO\\CSO_Test_6_30_2026.

Pulls the live QuikValf + quikridr rows for the policy, and re-checks whether
QuikPlTv carries TWO EFFDATE generations (19000101 and 19950101) for the same
GENDER/UWCLASS key while QuikNps only has data on one of them -- the exact
"wrong EFFDATE generation" risk flagged at Issue #169 Risk Review and never
proven against the live engine.
"""

from __future__ import annotations

import struct
from pathlib import Path

Q_DIR = Path(r"Q:\CSO\CSO_Test_6_30_2026")
PLAN = "5667AT"
POLICY = "9010800356C"


def read_dbf(path: Path) -> tuple[list[dict], list[tuple]]:
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
            length = raw[16]
            fields.append((name, length))
        fh.seek(hlen)
        rows = []
        for _ in range(recs):
            rec = fh.read(rlen)
            if len(rec) < 2:
                break
            off = 1
            d = {}
            for name, length in fields:
                d[name] = rec[off : off + length].decode("latin-1", "replace").strip()
                off += length
            rows.append(d)
    return rows, fields


def find(stem: str) -> Path:
    return next(p for p in Q_DIR.iterdir() if p.name.lower() == f"{stem.lower()}.dbf")


def main() -> int:
    print("=" * 70)
    print(f"POLICY {POLICY} on plan {PLAN}")
    print("=" * 70)

    ridr, _ = read_dbf(find("quikridr"))
    pol_rows = [r for r in ridr if r.get("MPOLICY") == POLICY]
    print(f"\nquikridr rows for {POLICY}: {len(pol_rows)}")
    for r in pol_rows:
        print(
            f"  MPHASE={r.get('MPHASE')} MPLAN={r.get('MPLAN')!r} "
            f"MSEX={r.get('MSEX')!r} MUWCLASS={r.get('MUWCLASS')!r} "
            f"MAGE={r.get('MAGE')} MUNIT={r.get('MUNIT')} "
            f"MEFFDATE={r.get('MEFFDATE')} MPHSTAT={r.get('MPHSTAT')}"
        )

    valf, valf_fields = read_dbf(find("quikvalf"))
    val_rows = [r for r in valf if r.get("MPOLICY") == POLICY]
    print(f"\nQuikValf rows for {POLICY}: {len(val_rows)}")
    key_fields = [
        "MPOLICY", "MPHASE", "MPLAN", "MAGE", "MDUR", "MSEX", "MCLASS",
        "MUNIT", "MTABNET", "MACCTBAL", "MMEAN", "MRESERVE", "MEXTCODE",
    ]
    for r in val_rows:
        for f in key_fields:
            if f in r:
                print(f"  {f:10s} = {r[f]!r}")
        print("  --")

    print("\n" + "=" * 70)
    print(f"QuikPlTv keys for {PLAN} (both EFFDATE generations)")
    print("=" * 70)
    pltv, _ = read_dbf(find("QuikPlTv"))
    for r in [x for x in pltv if x.get("PLAN") == PLAN]:
        print(
            f"  GENDER={r.get('GENDER')} UWCLASS={r.get('UWCLASS')!r} "
            f"BAND={r.get('BAND')} EFFDATE={r.get('EFFDATE')} "
            f"MORT={r.get('MORT')!r} RSVINT={r.get('RSVINT')!r} "
            f"RSVMETH={r.get('RSVMETH')!r}"
        )

    print("\n" + "=" * 70)
    print(f"QuikNps rows for {PLAN} by EFFDATE (M/PR only, count)")
    print("=" * 70)
    nps, _ = read_dbf(find("QuikNps"))
    from collections import Counter

    c = Counter(
        (r.get("GENDER"), r.get("UWCLASS"), r.get("EFFDATE"))
        for r in nps
        if r.get("PLAN") == PLAN
    )
    for k, v in sorted(c.items()):
        print(f"  {k}: {v} rows")

    print("\nDIAGNOSIS:")
    print(
        "  If QuikPlTv has BOTH EFFDATE=19000101 and EFFDATE=19950101 rows for\n"
        "  the same GENDER/UWCLASS, and QuikNps has DATA ONLY under 19000101,\n"
        "  then whichever EFFDATE QLAdmin's engine selects as 'current' for the\n"
        "  6/30/2026 valuation date determines whether net premium resolves.\n"
        "  If it picks the newest EFFDATE <= valuation date (19950101), it finds\n"
        "  an empty QuikNps grid and reserves $0 -- for EVERY policy on the plan,\n"
        "  not just ones actually issued after 1995."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
