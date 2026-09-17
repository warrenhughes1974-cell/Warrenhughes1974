"""Issue #169 -- verify the deployed Q region QuikTvs.dbf can now reach every
5667AT net premium, and walk the anchor policies from the live DBFs.

Read-only against Q:\\CSO\\CSO_Test_6_30_2026.
"""

from __future__ import annotations

import struct
from collections import defaultdict
from pathlib import Path

Q_DIR = Path(r"Q:\CSO\CSO_Test_6_30_2026")
PLAN = "5667AT"

# policy, gender, class, issue age, duration, units, LifePRO reserve
ANCHORS = [
    ("9010800356C", "M", "PR", "39", 40, 200.0, 8239.00),
    ("9010768802C", "F", "PR", "28", 41, 30.0, 490.35),
    ("9010764248C", "F", "PR", "22", 41, 50.0, 474.50),
    ("9011136641C", "M", "ST", "22", 31, 25.0, 98.25),   # already valued live
]


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


def slots(rows, pfx):
    out = defaultdict(dict)
    for r in rows:
        key = (r["GENDER"], r["UWCLASS"], r["EFFDATE"], r["AGE"])
        base = int(r["CNTL"]) * 10
        for i in range(10):
            try:
                out[key][base + i] = float((r.get(f"{pfx}{i}") or "").strip() or 0)
            except ValueError:
                out[key][base + i] = 0.0
    return out


def main() -> int:
    tvs = [r for r in read_dbf(find("QuikTvs")) if r.get("PLAN") == PLAN]
    nps = [r for r in read_dbf(find("QuikNps")) if r.get("PLAN") == PLAN]

    print(f"Q region {PLAN}: QuikTvs rows={len(tvs)}  QuikNps rows={len(nps)}")
    gens = defaultdict(int)
    for r in tvs:
        gens[(r["GENDER"], r["UWCLASS"], r["EFFDATE"])] += 1
    print("  QuikTvs keys now present:")
    for k in sorted(gens):
        print(f"    {k} -> {gens[k]}")

    tv_addr = {(r["GENDER"], r["UWCLASS"], r["EFFDATE"], r["AGE"], r["CNTL"]) for r in tvs}
    np_addr = {(r["GENDER"], r["UWCLASS"], r["EFFDATE"], r["AGE"], r["CNTL"]) for r in nps}
    print(f"\n  net-premium addresses={len(np_addr)}  "
          f"without a terminal-reserve row={len(np_addr - tv_addr)}")

    tv_s, np_s = slots(tvs, "TV"), slots(nps, "NP")
    print("\n  anchor walk against the deployed DBFs (mean = (a + np + b) / 2 x units)")
    bad = 0
    for pol, sex, cls, age, dur, units, expect in ANCHORS:
        slot = dur - 1
        k = (sex, cls, "19000101", age)
        p = np_s.get(k, {}).get(slot)
        a = tv_s.get(k, {}).get(slot - 1)
        b = tv_s.get(k, {}).get(slot)
        if p is None or a is None or b is None:
            print(f"    {pol}: MISSING row (np={p} term={a}/{b})")
            bad += 1
            continue
        got = (a + p + b) / 2 * units
        ok = abs(got - expect) < 0.01
        bad += 0 if ok else 1
        print(f"    {pol} {sex}/{cls} age {age} dur {dur}: term={a:.2f}/{b:.2f} "
              f"np={p:.2f} -> {got:,.2f}  LifePRO {expect:,.2f}  "
              f"{'OK' if ok else 'MISMATCH'}")

    print()
    if bad or (np_addr - tv_addr):
        print("FAIL: Q region still cannot reach every 667 ART reserve.")
        return 1
    print("PASS: Q region QuikTvs covers every 667 ART net premium; anchors "
          "reproduce LifePRO to the cent. Ready to re-run valuation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
