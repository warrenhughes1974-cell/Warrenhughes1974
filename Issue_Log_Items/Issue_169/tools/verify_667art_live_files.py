"""Verify 667 ART (5667AT) net premiums on the live ShareFile / Q DBFs."""

from __future__ import annotations

import struct
from collections import defaultdict
from datetime import datetime
from pathlib import Path

PLAN = "5667AT"
# Warren's 9/16 email walk: reserve = NP x units / 2
# QuikValf duration is 1-based LifePRO; grid index is duration - 1.
ANCHORS = [
    ("9010800356C", "M", "PR", 39, 40, 200, 8239.00, 82.39),
    ("9010768802C", "F", "PR", 28, 41, 30, 490.35, 32.69),
    ("9010764248C", "F", "PR", 22, 41, 50, 474.50, 18.98),
]
FOLDERS = [
    ("ShareFile L_Rate_Setup", Path(r"S:\Shared Folders\CSO\L_Rate_Setup")),
    ("Q test region", Path(r"Q:\CSO\CSO_Test_6_30_2026")),
]


def read_dbf(path: Path) -> list[dict]:
    with path.open("rb") as fh:
        header = fh.read(32)
        recs = struct.unpack_from("<I", header, 4)[0]
        hlen = struct.unpack_from("<H", header, 8)[0]
        fh.seek(32)
        fields = []
        while True:
            raw = fh.read(32)
            if not raw or raw[0] in (0x0D, 0x00):
                break
            name = raw[:11].split(b"\x00", 1)[0].decode("ascii", "replace").strip()
            length = raw[16]
            fields.append((name, length))
        rlen = struct.unpack_from("<H", header, 10)[0]
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
    return rows


def fnum(v) -> float:
    try:
        return float(str(v or "0").strip() or 0)
    except ValueError:
        return 0.0


def lookup_np(rows, age, gender, uw, dur_index):
    cntl = str(dur_index // 10).zfill(2)
    col = f"NP{dur_index % 10}"
    age_s = str(int(age))
    hits = [
        r
        for r in rows
        if r.get("PLAN") == PLAN
        and str(int(r.get("AGE") or 0)) == age_s
        and r.get("GENDER") == gender
        and r.get("UWCLASS") == uw
        and r.get("CNTL") == cntl
    ]
    if not hits:
        return None, cntl, col
    return fnum(hits[0].get(col)), cntl, col


def find_dbf(folder: Path, stem: str) -> Path:
    return next(p for p in folder.iterdir() if p.name.lower() == f"{stem}.dbf")


def main() -> int:
    worst = 0
    for label, folder in FOLDERS:
        print("=" * 70)
        print(label)
        print(folder)
        nps_p, ptv_p = find_dbf(folder, "quiknps"), find_dbf(folder, "quikpltv")
        print(
            f"QuikNps  {nps_p.stat().st_size:,} bytes  "
            f"{round(nps_p.stat().st_size / 1024)} KB  "
            f"{datetime.fromtimestamp(nps_p.stat().st_mtime)}"
        )
        print(
            f"QuikPlTv {ptv_p.stat().st_size:,} bytes  "
            f"{datetime.fromtimestamp(ptv_p.stat().st_mtime)}"
        )
        nps = read_dbf(nps_p)
        ptv = read_dbf(ptv_p)
        art_nps = [r for r in nps if r.get("PLAN") == PLAN]
        art_ptv = [r for r in ptv if r.get("PLAN") == PLAN]
        print(f"5667AT QuikNps rows: {len(art_nps)}  (need 1,736)")
        print(f"5667AT QuikPlTv rows: {len(art_ptv)}")
        by_key = defaultdict(int)
        nz = 0
        for r in art_nps:
            by_key[(r.get("GENDER"), r.get("UWCLASS"), r.get("EFFDATE"))] += 1
            for i in range(10):
                if fnum(r.get(f"NP{i}")) != 0:
                    nz += 1
        print("  keys:", dict(by_key))
        print(f"  nonzero NP cells: {nz}")
        print("  QuikPlTv:")
        for r in art_ptv:
            print(
                f"    {r.get('GENDER')}/{r.get('UWCLASS')} EFF={r.get('EFFDATE')} "
                f"MORT={r.get('MORT')!r} RSVINT={r.get('RSVINT')!r} "
                f"RSVMETH={r.get('RSVMETH')!r}"
            )
        print()
        print("Email walk (NP x units / 2):")
        all_ok = True
        for pol, sex, uw, age, dur, units, exp_rsv, exp_np in ANCHORS:
            got, cntl, col = lookup_np(art_nps, age, sex, uw, dur - 1)
            if got is None:
                print(f"  FAIL {pol} missing AGE={age} {sex}/{uw} {cntl}/{col}")
                all_ok = False
                continue
            calc = round(got * units / 2.0, 2)
            ok = abs(got - exp_np) < 0.005 and abs(calc - exp_rsv) < 0.005
            all_ok = all_ok and ok
            print(
                f"  {'PASS' if ok else 'FAIL'} {pol} AGE={age} DUR={dur} "
                f"{sex}/{uw} {cntl}/{col} NP={got:.2f} (want {exp_np:.2f})  "
                f"{got:.2f} x {units} / 2 = {calc:.2f} (want {exp_rsv:.2f})"
            )
        present = len(art_nps) >= 1736 and all_ok
        print()
        print("667 ART PRESENT AND MATCHES EMAIL" if present else "667 ART MISSING OR WRONG")
        print()
        if not present:
            worst = 1
    return worst


if __name__ == "__main__":
    raise SystemExit(main())
