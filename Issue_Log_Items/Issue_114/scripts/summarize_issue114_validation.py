"""Issue #114 — summarize the validation report for the Validation Report doc (read-only)."""
import collections
import csv
import os

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(REPO, "QLA_Migration", "Reports", "issue114_dividend_history_validation.csv")


def f(s):
    try:
        return float(s or 0)
    except ValueError:
        return 0.0


rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig")))
print(f"validation rows: {len(rows)}")
print("status:", dict(collections.Counter(r["STATUS"] for r in rows)))
print("dividend option:", dict(sorted(collections.Counter(r["DIVIDEND_OPTION"] for r in rows).items())))
print("emitted MBENTYP:", dict(sorted(collections.Counter(
    r["MBENTYP"] for r in rows if r["STATUS"] in ("PLUG_EMITTED", "OPENING_BALANCE")).items())))

emitted = [r for r in rows if r["STATUS"] in ("PLUG_EMITTED", "OPENING_BALANCE")]
print("max |remaining variance| among emitted:",
      max(abs(f(r["REMAINING_VARIANCE"])) for r in emitted))
print(f"emitted policies: {len(emitted)}")
print(f"lifetime total  : {sum(f(r['LIFEPRO_LIFETIME']) for r in rows):,.2f}")
print(f"final total     : {sum(f(r['FINAL_TOTAL']) for r in rows):,.2f}")

def show(title, sel, n=5):
    print()
    print(title)
    for r in sel[:n]:
        print(f"  {r['MPOLICY']:>12} opt={r['DIVIDEND_OPTION'] or '-'} type={r['MBENTYP'] or '-'} "
              f"lifetime={f(r['LIFEPRO_LIFETIME']):>10,.2f} txns={r['LAYER_A_TXN_COUNT']:>3} "
              f"layerA={f(r['LAYER_A_TOTAL']):>10,.2f} plug={f(r['PLUG_AMOUNT']):>10,.2f} "
              f"final={f(r['FINAL_TOTAL']):>10,.2f} var={r['REMAINING_VARIANCE']:>6} {r['STATUS']}")

show("TOP 5 BY LIFETIME", sorted(rows, key=lambda r: -f(r["LIFEPRO_LIFETIME"])))
show("OPENING_BALANCE (plug only, no PACTG window activity)",
     [r for r in rows if r["STATUS"] == "OPENING_BALANCE"], 3)
show("PLUG_EMITTED (PACTG window + pre-2018 plug)",
     [r for r in rows if r["STATUS"] == "PLUG_EMITTED"], 3)
