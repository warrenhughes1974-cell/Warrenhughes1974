from collections import Counter
from pathlib import Path

from dbfread import DBF
from data_governance.execution.runner import run_data_governance

DATA = r"Q:\CSO\CSO_Test_6_30_2026"
OUT = Path(__file__).resolve().parent / "examine_out"

# Direct QuikPlan inventory
rows = list(
    DBF(
        str(Path(DATA) / "quikplan.dbf"),
        encoding="latin-1",
        ignore_missing_memofile=True,
    )
)
print("QuikPlan rows", len(rows))

rrule = Counter(str(r.get("RRULE") or "").strip() for r in rows)
print("RRULE", dict(rrule))

suffix_bad = []
for r in rows:
    plan = str(r.get("PLAN") or "").strip().upper()
    if len(plan) >= 2 and plan[-2:] in ("PA", "XP", "XF", "XS"):
        suffix_bad.append((plan, str(r.get("DESCR") or "")[:40]))
print("PUA suffix plans", len(suffix_bad), suffix_bad)

basis_issues = []
for r in rows:
    plan = str(r.get("PLAN") or "").strip()
    basis = str(r.get("BASIS") or "").strip()
    if plan.upper().startswith("A"):
        if basis not in ("NONQ", "QUAL", "NQIA", "QLIA", "TXBL"):
            basis_issues.append((plan, basis, "A-plan invalid/blank"))
    elif basis:
        basis_issues.append((plan, basis, "non-A populated"))
print("BASIS issues", len(basis_issues))
for x in basis_issues[:20]:
    print(" ", x)

pay_both_zero = []
for r in rows:
    plan = str(r.get("PLAN") or "").strip()
    if plan.upper().startswith("5"):
        continue
    try:
        py = int(float(r.get("PAYYRS") or 0))
        pa = int(float(r.get("PAYAGE") or 0))
    except Exception:
        pay_both_zero.append((plan, r.get("PAYYRS"), r.get("PAYAGE"), "unreadable"))
        continue
    if py == 0 and pa == 0:
        pay_both_zero.append((plan, py, pa, str(r.get("DESCR") or "")[:40]))
print("PAY both zero (non-5)", len(pay_both_zero))
for x in pay_both_zero[:30]:
    print(" ", x)

# Governance run
for rid in [
    "DG-QUIKPLAN-003",
    "DG-QUIKPLAN-005",
    "DG-QUIKPLAN-010",
    "DG-QUIKPLAN-018",
]:
    result = run_data_governance(
        data_dir=DATA,
        output_dir=str(OUT),
        rule_id=rid,
        write_reports=False,
    )
    rr = result.rule_results[0]
    print("=" * 50)
    print(
        rid,
        rr.status,
        "eval",
        rr.records_evaluated,
        "pass",
        rr.passed_count,
        "findings",
        len(rr.findings),
    )
    for f in rr.findings:
        print(
            " ",
            getattr(f, "plan", None),
            getattr(f, "failure_category", None),
            getattr(f, "original_value", None),
            (f.message or "")[:80],
        )
