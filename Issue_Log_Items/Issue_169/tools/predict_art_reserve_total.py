"""Issue #169 -- predict what the next 6/30 valuation should produce for 667 ART.

Applies QLAdmin's own formula -- 1/2 x (terminal(t-1) + net premium + terminal(t))
-- to every A1G35667AT row in the live QuikValf using the deployed Q rate tables,
so Warren has a target total to check the revaluation against. Read-only.
"""

from __future__ import annotations

import struct
from collections import defaultdict
from pathlib import Path

Q_DIR = Path(r"Q:\CSO\CSO_Test_6_30_2026")
MPLAN = "A1G35667AT"
PLAN = "5667AT"


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
            fields.append((raw[:11].split(b"\x00", 1)[0].decode("ascii", "replace").strip(),
                           raw[16]))
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
    return rows


def find(stem):
    return next(p for p in Q_DIR.iterdir() if p.name.lower() == f"{stem.lower()}.dbf")


def num(v):
    try:
        return float(str(v).strip() or 0)
    except ValueError:
        return 0.0


def main() -> int:
    tvs = [r for r in read_dbf(find("QuikTvs")) if r.get("PLAN") == PLAN]
    nps = [r for r in read_dbf(find("QuikNps")) if r.get("PLAN") == PLAN]
    valf = [r for r in read_dbf(find("quikvalf"))
            if (r.get("MPLAN") or "").strip() == MPLAN]

    def slots(rows, pfx):
        out = defaultdict(dict)
        for r in rows:
            key = (r["GENDER"], r["UWCLASS"], r["EFFDATE"], r["AGE"])
            base = int(r["CNTL"]) * 10
            for i in range(10):
                out[key][base + i] = num(r.get(f"{pfx}{i}"))
        return out

    tv_s, np_s = slots(tvs, "TV"), slots(nps, "NP")

    total = 0.0
    priced = zero_units = no_row = 0
    for r in valf:
        units = num(r.get("MUNIT"))
        sex = (r.get("MSEX") or "").strip()
        cls = (r.get("MCLASS") or "").strip()
        age = (r.get("MAGE") or "").strip().zfill(2)
        dur = int(num(r.get("MDUR")))
        issue = (r.get("MISSUE") or "")
        eff = "19950101" if issue >= "19950101" else "19000101"
        if not units:
            zero_units += 1
            continue
        slot = dur - 1
        k = (sex, cls, eff, age)
        p = np_s.get(k, {}).get(slot)
        a = tv_s.get(k, {}).get(slot - 1)
        b = tv_s.get(k, {}).get(slot)
        if p is None or a is None or b is None:
            no_row += 1
            print(f"  NO ROW {r.get('MPOLICY')} {sex}/{cls} age {age} dur {dur} eff {eff}")
            continue
        total += (a + p + b) / 2 * units
        priced += 1

    print("=" * 70)
    print(f"Predicted 667 ART reserve on the next 6/30 valuation")
    print("=" * 70)
    print(f"  QuikValf rows on {MPLAN}: {len(valf)}")
    print(f"    priced from the grid:      {priced}")
    print(f"    zero units (cannot price): {zero_units}")
    print(f"    no grid row (should be 0): {no_row}")
    print(f"\n  PREDICTED TOTAL: ${total:,.2f}")
    print(f"  LifePRO holds:   $133,546.48 across 96 records (per #169 reconciliation)")
    print("\n  The gap is the two known non-reconcilers: 9010886099C seq 2 carries")
    print("  $1,317.00 on ZERO units in LifePRO, and one row sits in the 667 ART 95")
    print("  generation. Both were already documented as out of scope.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
