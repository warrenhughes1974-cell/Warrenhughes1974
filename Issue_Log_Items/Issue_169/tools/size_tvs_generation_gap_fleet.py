"""Issue #169 -- size the QuikTvs generation/class gap across the fleet.

The 5667AT $0 reserve is caused by QuikNps carrying a gender/class/EFFDATE key
that QuikTvs does not, so the engine has no reachable terminal-reserve row to
anchor the mean-reserve calculation. Twelve other plans share that shape.

Cross-references the misaligned plans against Warren's live 6/30 QuikValf to
show how many policies and how much reserve are actually affected. Read-only.
"""

from __future__ import annotations

import csv
import struct
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RATES = ROOT / "QLA_Migration" / "Output" / "rates"
Q_DIR = Path(r"Q:\CSO\CSO_Test_6_30_2026")


def read_csv(table):
    with (RATES / f"{table}.csv").open(encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


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


def main() -> int:
    tv_keys, np_keys = defaultdict(set), defaultdict(set)
    # a "real" grid row is one keyed to a genuine issue age, not the AGE=00 stub
    tv_real = defaultdict(set)
    for r in read_csv("QuikTvs"):
        k = (r["GENDER"], r["UWCLASS"], r["EFFDATE"])
        tv_keys[r["PLAN"]].add(k)
        if r["AGE"] != "00":
            tv_real[r["PLAN"]].add(k)
    for r in read_csv("QuikNps"):
        np_keys[r["PLAN"]].add((r["GENDER"], r["UWCLASS"], r["EFFDATE"]))

    misaligned = {p for p in np_keys if np_keys[p] - tv_real.get(p, set())}

    valf = read_dbf(next(p for p in Q_DIR.iterdir() if p.name.lower() == "quikvalf.dbf"))
    per_plan = defaultdict(lambda: {"rows": 0, "zero": 0, "res": 0.0})
    for r in valf:
        mplan = (r.get("MPLAN") or "").strip()
        plan = mplan if len(mplan) <= 6 else mplan[4:]
        s = per_plan[plan]
        s["rows"] += 1
        res = num(r.get("MRESERVE"))
        s["res"] += res
        if not res:
            s["zero"] += 1

    print("=" * 92)
    print("Plans whose QuikNps key set is not covered by a REAL (non AGE=00) QuikTvs grid")
    print("cross-referenced to the live 6/30 QuikValf")
    print("=" * 92)
    print(f"  {'PLAN':<9}{'unmatched keys':>16}{'valf rows':>11}{'$0 rows':>9}"
          f"{'% zero':>9}{'reserve held':>16}")
    tot_rows = tot_zero = 0
    for plan in sorted(misaligned):
        missing = np_keys[plan] - tv_real.get(plan, set())
        s = per_plan.get(plan)
        if not s:
            print(f"  {plan:<9}{len(missing):>16}{'-- not in QuikValf --':>36}")
            continue
        pct = 100.0 * s["zero"] / s["rows"]
        mark = "  <-- 667 ART" if plan == "5667AT" else ""
        print(f"  {plan:<9}{len(missing):>16}{s['rows']:>11}{s['zero']:>9}"
              f"{pct:>8.1f}%{s['res']:>16,.2f}{mark}")
        tot_rows += s["rows"]
        tot_zero += s["zero"]
    print(f"  {'TOTAL':<9}{'':>16}{tot_rows:>11}{tot_zero:>9}")

    print()
    print("  Control -- plans WITH a real QuikTvs grid for every QuikNps key:")
    ok_rows = ok_zero = 0
    for plan in sorted(set(np_keys) - misaligned):
        s = per_plan.get(plan)
        if not s:
            continue
        ok_rows += s["rows"]
        ok_zero += s["zero"]
    print(f"    valf rows={ok_rows}  $0 rows={ok_zero}"
          f"  ({100.0 * ok_zero / ok_rows:.1f}% zero)" if ok_rows else "    none")
    if tot_rows:
        print(f"    misaligned plans: {100.0 * tot_zero / tot_rows:.1f}% zero")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
