"""Issue #116 validation — quikdvdp MINTDATE/MINTYTD before vs after the 0641 cache-key fix."""
import csv
import sys
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]
BEFORE = BASE / "QLA_Migration" / "Archive" / "pre_116_117_20260725" / "quikdvdp_BEFORE.csv"
AFTER = BASE / "QLA_Migration" / "Output" / "quikdvdp.csv"
REPORT = BASE / "QLA_Migration" / "Reports" / "issue116_quikdvdp_mintdate_validation.csv"

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TODAY = date.today().strftime("%Y%m%d")


def load(path):
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as fh:
        return {r["MPOLICY"].strip(): r for r in csv.DictReader(fh)}


before, after = load(BEFORE), load(AFTER)
failures = []

if set(before) != set(after):
    failures.append(
        f"population changed: +{len(set(after) - set(before))} / -{len(set(before) - set(after))}"
    )
print(f"rows before={len(before)} after={len(after)}")

def money(val):
    try:
        return float((val or "0").strip() or 0)
    except ValueError:
        return 0.0


# QLAdmin accrues interest from MINTDATE to today. A date in the future turns that
# accrual negative — but only where there is a balance to accrue on, so the test is
# scoped to MDEPOSIT > 0 rather than to every row.
changed, future_before, future_after, deposit_drift = [], [], [], []
zero_balance_future = 0
for pol, row in after.items():
    prev = before.get(pol)
    if not prev:
        continue
    if (prev.get("MDEPOSIT") or "").strip() != (row.get("MDEPOSIT") or "").strip():
        deposit_drift.append(pol)
    mb, ma = (prev.get("MINTDATE") or "").strip(), (row.get("MINTDATE") or "").strip()
    yb, ya = (prev.get("MINTYTD") or "").strip(), (row.get("MINTYTD") or "").strip()
    has_balance = money(row.get("MDEPOSIT")) > 0
    if mb > TODAY and money(prev.get("MDEPOSIT")) > 0:
        future_before.append(pol)
    if ma > TODAY:
        if has_balance:
            future_after.append(pol)
        else:
            zero_balance_future += 1
    if mb != ma or yb != ya:
        changed.append(
            {
                "MPOLICY": pol,
                "MDEPOSIT": row.get("MDEPOSIT", ""),
                "MINTDATE_BEFORE": mb,
                "MINTDATE_AFTER": ma,
                "MINTYTD_BEFORE": yb,
                "MINTYTD_AFTER": ya,
            }
        )

print(f"MDEPOSIT drift: {len(deposit_drift)} (expected 0)")
print(f"rows changed:   {len(changed)}")
print(
    f"future MINTDATE with a balance — before: {len(future_before)}  after: {len(future_after)}"
)
print(f"future MINTDATE on zero-balance rows: {zero_balance_future} (no accrual, not a defect)")

if deposit_drift:
    failures.append(f"MDEPOSIT changed on {len(deposit_drift)} policies")
if future_after:
    failures.append(
        f"{len(future_after)} policies with a balance still carry a future MINTDATE"
    )
if not changed:
    failures.append("no rows changed — the 0641 cache still is not matching")

REPORT.parent.mkdir(parents=True, exist_ok=True)
with open(REPORT, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(
        fh,
        fieldnames=[
            "MPOLICY",
            "MDEPOSIT",
            "MINTDATE_BEFORE",
            "MINTDATE_AFTER",
            "MINTYTD_BEFORE",
            "MINTYTD_AFTER",
        ],
    )
    w.writeheader()
    w.writerows(changed)
print(f"detail -> {REPORT}")

print("\nsample:")
for r in changed[:8]:
    print(
        f"  {r['MPOLICY']}  MDEPOSIT {r['MDEPOSIT']:>10}  "
        f"MINTDATE {r['MINTDATE_BEFORE']} -> {r['MINTDATE_AFTER']}  "
        f"MINTYTD {r['MINTYTD_BEFORE']} -> {r['MINTYTD_AFTER']}"
    )

print("\nISSUE #116: " + ("PASS" if not failures else "FAIL"))
for f in failures:
    print("  - " + f)
sys.exit(1 if failures else 0)
