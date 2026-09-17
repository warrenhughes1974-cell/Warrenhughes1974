"""Issue #169 - build the client UAT test anchor list for 667 ART (5667AT).

Reads the ValX-vs-QuikValf gap population and emits the policies a tester should check
after reloading the rate tables and running a valuation, largest reserve first.
"""

import csv
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
GAP = ROOT / "docs/Valuation/analysis/reserve_gap_population.csv"
OUT = ROOT / "Issue_Log_Items/Issue_169/Issue_169_UAT_Test_Anchors.csv"

ANCHORS = {"9010764158", "9010764248", "9010768802"}  # proof anchors from Development


def num(v):
    try:
        return float(str(v or "0").replace(",", "") or 0)
    except ValueError:
        return 0.0


rows = []
with GAP.open(encoding="utf-8-sig") as fh:
    for r in csv.DictReader(fh):
        if (r.get("ql_code") or "").strip() == "5667AT":
            rows.append(r)

rows.sort(key=lambda r: -num(r["valx_reserve"]))

out = []
for r in rows:
    pol = (r["policy"] or "").strip()
    units = num(r["units"])
    out.append(
        {
            "QL policy": f"{pol}C",
            "Coverage seq": r["seq"],
            "Units": f"{units:g}",
            "Expected reserve (LifePRO)": f"{num(r['valx_reserve']):.2f}",
            "Reserve before fix": "0.00",
            "Note": (
                "zero units - NOT expected to match, separate open question"
                if units == 0
                else "proof anchor"
                if pol in ANCHORS
                else ""
            ),
        }
    )

with OUT.open("w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(out)

total = sum(num(r["valx_reserve"]) for r in rows)
print(f"wrote {OUT.relative_to(ROOT)}  ({len(out)} rows, total {total:,.2f})")
print()
print("Top 10 by reserve:")
for r in out[:10]:
    print(
        "  {:12s} seq={:2s} units={:>7s}  expect {:>10s}  {}".format(
            r["QL policy"],
            r["Coverage seq"],
            r["Units"],
            r["Expected reserve (LifePRO)"],
            r["Note"],
        )
    )
print()
print("Proof anchors:")
for r in out:
    if r["Note"] == "proof anchor":
        print(
            "  {:12s} seq={:2s} units={:>7s}  expect {:>10s}".format(
                r["QL policy"], r["Coverage seq"], r["Units"],
                r["Expected reserve (LifePRO)"])
        )
print()
print("Excluded from match expectation:")
for r in out:
    if r["Units"] == "0":
        print(
            "  {:12s} seq={:2s}  LifePRO {:>10s}  {}".format(
                r["QL policy"], r["Coverage seq"],
                r["Expected reserve (LifePRO)"], r["Note"])
        )
