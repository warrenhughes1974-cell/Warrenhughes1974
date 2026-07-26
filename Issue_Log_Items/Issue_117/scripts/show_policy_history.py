"""Print a policy's dividend history as QLAdmin will show it, with the running balance."""
import csv
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]
BENH = BASE / "QLA_Migration" / "Output" / "quikbenh.csv"
DVDP = BASE / "QLA_Migration" / "Output" / "quikdvdp.csv"

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LABEL = {
    "1": "Dividend paid in cash",
    "2": "Dividend applied to premium",
    "3": "Dividends left to accumulate",
    "4": "Dividend buys paid-up additions",
    "5": "Dividend buys one-year term",
    "6": "Interest on policy funds",
    "7": "Surrendered dividend accums",
}
LEDGER_TYPES = {"3", "6", "7"}

policies = sys.argv[1:] or ["9010382426C"]

with open(BENH, newline="", encoding="utf-8-sig", errors="replace") as fh:
    benh = [r for r in csv.DictReader(fh) if r["MPOLICY"].strip() in policies]
with open(DVDP, newline="", encoding="utf-8-sig", errors="replace") as fh:
    dvdp = {r["MPOLICY"].strip(): r for r in csv.DictReader(fh) if r["MPOLICY"].strip() in policies}

for pol in policies:
    rows = sorted(
        (r for r in benh if r["MPOLICY"].strip() == pol and r["MBENTYP"].strip() in LABEL),
        key=lambda r: (r["MDATE"], r["MBENTYP"]),
    )
    d = dvdp.get(pol, {})
    print("=" * 88)
    print(f"{pol}   quikdvdp: MDEPOSIT={d.get('MDEPOSIT','-')}  MDEPINT={d.get('MDEPINT','-')}  "
          f"MINTYTD={d.get('MINTYTD','-')}  MINTDATE={d.get('MINTDATE','-')}")
    print("-" * 88)
    running = 0.0
    for r in rows:
        amt = float(r["MBEN"])
        t = r["MBENTYP"].strip()
        signed = -amt if t == "7" else amt
        if t in LEDGER_TYPES:
            running += signed
        print(
            f"  {r['MDATE']}  type {t}  {LABEL[t]:<33}{signed:>11,.2f}"
            + (f"   balance {running:>11,.2f}" if t in LEDGER_TYPES else "")
        )
    print("-" * 88)
    print(f"  ledger balance {running:>11,.2f}   vs quikdvdp MDEPOSIT {d.get('MDEPOSIT','-'):>11}")
