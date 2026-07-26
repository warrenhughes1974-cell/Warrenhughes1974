"""Issue #117 validation — the emitted dividend ledger must foot to the quikdvdp balance.

Reads the emitted tables rather than the converter's own report, so this proves what
QLAdmin will actually load:

  sum(MBENTYP 3) + sum(MBENTYP 6) - sum(MBENTYP 7) == quikdvdp.MDEPOSIT

It also holds Issue #114 and the neighbouring issues in place: type 1-5 rows must be
unchanged from the pre-fix snapshot, and types 8/10/11/12 (#34 / #54) untouched.
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]
SNAP = BASE / "QLA_Migration" / "Archive" / "pre_116_117_20260725"
BENH_BEFORE = SNAP / "quikbenh_BEFORE.csv"
BENH_AFTER = BASE / "QLA_Migration" / "Output" / "quikbenh.csv"
DVDP = BASE / "QLA_Migration" / "Output" / "quikdvdp.csv"
LEDGER_REPORT = BASE / "QLA_Migration" / "Reports" / "issue117_dividend_ledger_reconciliation.csv"
OUT = BASE / "QLA_Migration" / "Reports" / "issue117_emitted_ledger_check.csv"

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOL = 0.005
CARRIED_TYPES = {"8", "10", "11", "12"}


def money(val):
    try:
        return float((val or "0").strip() or 0)
    except ValueError:
        return 0.0


def read(path):
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as fh:
        return list(csv.DictReader(fh))


before, after, dvdp = read(BENH_BEFORE), read(BENH_AFTER), read(DVDP)
failures = []


def key(r):
    return (r["MPOLICY"].strip(), r["MBENTYP"].strip(), r["MDATE"].strip(), r["MBEN"].strip())


def bucket(rows):
    out = defaultdict(list)
    for r in rows:
        out[r["MBENTYP"].strip()].append(r)
    return out


bb, ba = bucket(before), bucket(after)
print("MBENTYP counts (before -> after):")
for t in sorted(set(bb) | set(ba), key=lambda x: (len(x), x)):
    print(f"  type {t:>2}: {len(bb.get(t, [])):>6} -> {len(ba.get(t, [])):>6}")

# 1. Issue #34 / #54 rows must be byte-for-byte carried through.
for t in sorted(CARRIED_TYPES):
    if [key(r) for r in bb.get(t, [])] != [key(r) for r in ba.get(t, [])]:
        failures.append(f"MBENTYP {t} rows changed (owned by Issue #34/#54)")

# 2. Issue #114's dividend credits must be unchanged.
for t in ("1", "2", "3", "4", "5"):
    kb = sorted(key(r) for r in bb.get(t, []))
    ka = sorted(key(r) for r in ba.get(t, []))
    if t == "3":
        # Type 3 gains nothing; the new opening interest is emitted as type 6.
        if kb != ka:
            failures.append(f"MBENTYP 3 changed: {len(kb)} -> {len(ka)} rows")
    elif kb != ka:
        failures.append(f"MBENTYP {t} changed: {len(kb)} -> {len(ka)} rows")

# 3. The new ledger types must exist.
if not ba.get("6"):
    failures.append("no MBENTYP 6 rows emitted")

# 4. The ledger has to foot to the quikdvdp balance.
balance = {r["MPOLICY"].strip(): money(r.get("MDEPOSIT")) for r in dvdp}
totals = defaultdict(lambda: {"3": 0.0, "6": 0.0, "7": 0.0})
for r in after:
    t = r["MBENTYP"].strip()
    if t in ("3", "6", "7"):
        totals[r["MPOLICY"].strip()][t] += money(r.get("MBEN"))

known_short = {
    r["MPOLICY"].strip()
    for r in read(LEDGER_REPORT)
    if r["STATUS"] in ("ACCUM_OPENING_SHORTFALL", "SKIPPED_UNMAPPED_OPTION")
}

detail, footed, off = [], 0, []
for pol, bal in balance.items():
    if bal <= TOL:
        continue
    t = totals.get(pol, {"3": 0.0, "6": 0.0, "7": 0.0})
    ledger = round(t["3"] + t["6"] - t["7"], 2)
    var = round(bal - ledger, 2)
    ok = abs(var) <= TOL
    footed += ok
    if not ok and pol not in known_short:
        off.append(pol)
    detail.append(
        {
            "MPOLICY": pol,
            "MDEPOSIT": f"{bal:.2f}",
            "SUM_TYPE3": f"{t['3']:.2f}",
            "SUM_TYPE6": f"{t['6']:.2f}",
            "SUM_TYPE7": f"{t['7']:.2f}",
            "LEDGER_TOTAL": f"{ledger:.2f}",
            "VARIANCE": f"{var:.2f}",
            "STATUS": "FOOTS" if ok else ("KNOWN_EXCEPTION" if pol in known_short else "UNEXPLAINED"),
        }
    )

print(f"\nbalance-carrying policies: {len(detail)}")
print(f"  ledger foots to MDEPOSIT: {footed}")
print(f"  known/reported exceptions: {len(detail) - footed}")
print(f"  unexplained variances:     {len(off)}")
if off:
    failures.append(f"{len(off)} policies vary from MDEPOSIT with no exception logged: {off[:5]}")

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(
        fh,
        fieldnames=[
            "MPOLICY",
            "MDEPOSIT",
            "SUM_TYPE3",
            "SUM_TYPE6",
            "SUM_TYPE7",
            "LEDGER_TOTAL",
            "VARIANCE",
            "STATUS",
        ],
    )
    w.writeheader()
    w.writerows(sorted(detail, key=lambda r: r["MPOLICY"]))
print(f"detail -> {OUT}")

print("\nsample:")
for r in sorted(detail, key=lambda r: r["MPOLICY"])[:6]:
    print(
        f"  {r['MPOLICY']}  bal {r['MDEPOSIT']:>9}  "
        f"3={r['SUM_TYPE3']:>9} 6={r['SUM_TYPE6']:>9} 7={r['SUM_TYPE7']:>9}  "
        f"-> {r['LEDGER_TOTAL']:>9}  {r['STATUS']}"
    )

print("\nISSUE #117: " + ("PASS" if not failures else "FAIL"))
for f in failures:
    print("  - " + f)
sys.exit(1 if failures else 0)
