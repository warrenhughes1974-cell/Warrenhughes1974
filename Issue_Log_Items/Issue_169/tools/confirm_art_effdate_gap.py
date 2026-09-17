"""Issue #169 -- clincher test for the 5667AT $0 reserve.

Diagnosis: QLAdmin resolves rate generations as "latest EFFDATE <= policy issue
date". For 5667AT:

    QuikNps generations = {19000101, 19950101}
    QuikTvs generations = {19950101}          <-- no 19000101 at all

So a policy issued before 1995 has a reachable net premium but NO reachable
terminal-reserve row, and reserves $0. A policy issued on/after 1995-01-01 can
reach the 19950101 QuikTvs generation and should value.

Live 6/30 QuikValf shows 94 rows on A1G35667AT with exactly ONE non-zero
reserve. If that one policy is the only one issued on/after 19950101, the
generation gap is the cause. Read-only.
"""

from __future__ import annotations

import struct
from pathlib import Path

Q_DIR = Path(r"Q:\CSO\CSO_Test_6_30_2026")
MPLAN = "A1G35667AT"
CUTOVER = "19950101"


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


def num(v):
    try:
        return float(str(v).strip() or 0)
    except ValueError:
        return 0.0


def find(stem):
    return next(p for p in Q_DIR.iterdir() if p.name.lower() == f"{stem.lower()}.dbf")


def main() -> int:
    valf = read_dbf(find("quikvalf"))
    rows = [r for r in valf if (r.get("MPLAN") or "").strip() == MPLAN]

    pre = [r for r in rows if (r.get("MISSUE") or "") < CUTOVER]
    post = [r for r in rows if (r.get("MISSUE") or "") >= CUTOVER]
    valued = [r for r in rows if num(r.get("MRESERVE"))]

    print("=" * 78)
    print(f"{MPLAN} in the live 6/30 QuikValf -- {len(rows)} rows")
    print("=" * 78)
    print(f"  issued BEFORE {CUTOVER} (only 19000101 generation reachable): {len(pre)}")
    print(f"    of those, non-zero reserve: {sum(1 for r in pre if num(r.get('MRESERVE')))}")
    print(f"  issued ON/AFTER {CUTOVER} (19950101 generation reachable):    {len(post)}")
    print(f"    of those, non-zero reserve: {sum(1 for r in post if num(r.get('MRESERVE')))}")

    print()
    print("  Every row with a non-zero reserve:")
    for r in valued:
        print(f"    {r.get('MPOLICY'):<14} MISSUE={r.get('MISSUE')} "
              f"{r.get('MSEX')}/{r.get('MCLASS')} age={r.get('MAGE')} dur={r.get('MDUR')} "
              f"units={r.get('MUNIT')} MRESERVE={r.get('MRESERVE')} "
              f"MTABNET={r.get('MTABNET')}")

    print()
    print("  Rows issued on/after the cutover (expected to be the only ones valued):")
    for r in post:
        print(f"    {r.get('MPOLICY'):<14} MISSUE={r.get('MISSUE')} "
              f"{r.get('MSEX')}/{r.get('MCLASS')} MRESERVE={r.get('MRESERVE')}")

    print()
    if post and len(valued) == len(post) and all(num(r.get("MRESERVE")) for r in post):
        print("  RESULT: the ONLY 667 ART policies QLAdmin valued are the ones whose issue")
        print("          date can reach the 19950101 QuikTvs generation. Every pre-1995")
        print("          policy has a net premium but no reachable terminal-reserve row")
        print("          and reserves $0. The missing 19000101 QuikTvs generation is the cause.")
    else:
        print("  RESULT: issue-date split does not fully explain the valued rows -- see above.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
