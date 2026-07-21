"""Issue #51 validation/regression spot checks — read only."""
import csv
from pathlib import Path

repo = Path(r"C:\Users\warren\Documents\GitHub\Warrenhughes1974")
out = repo / "QLA_Migration" / "Output"
rates = out / "rates"
ev = repo / "Issue_Log_Items" / "Issue_51" / "evidence"
ev.mkdir(parents=True, exist_ok=True)

from qla_core.rate_dbf_schema import quikaint_fields

fields = quikaint_fields()
assert [f[0] for f in fields] == ["MPLAN", "MEFFDATE", "MINTRATE", "MINTRATE1"]

ridr = list(csv.DictReader((out / "quikridr.csv").open(encoding="utf-8-sig")))
targets = [r for r in ridr if r.get("MPLAN", "").strip() in ("A60MIR", "A96DAR")]

aint = list(csv.DictReader((rates / "QuikAint.csv").open(encoding="utf-8-sig")))
checks = []
for r in targets:
    plan = r["MPLAN"].strip()
    hit = next((a for a in aint if a.get("MPLAN", "").strip() == plan), None)
    checks.append(
        {
            "MPOLICY": r["MPOLICY"].strip(),
            "MPHASE": r.get("MPHASE", "").strip(),
            "MPHSTAT": r.get("MPHSTAT", "").strip(),
            "MPLAN": plan,
            "QUIKAINT_PRESENT": "Y" if hit else "N",
            "MINTRATE": hit.get("MINTRATE", "") if hit else "",
            "MINTRATE1": hit.get("MINTRATE1", "") if hit else "",
            "RESULT": "PASS" if hit and float(hit["MINTRATE"]) == 0 and float(hit["MINTRATE1"]) == 0 else "FAIL",
        }
    )

with (ev / "issue51_validation_checklist.csv").open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(checks[0].keys()))
    w.writeheader()
    w.writerows(checks)

# row counts
row_counts = []
for name in ["quikmstr", "quikridr", "quikplan", "quikprmh", "quikclid", "quikclnt", "quikdvdp", "quikmemo"]:
    p = out / f"{name}.csv"
    if not p.exists():
        continue
    n = sum(1 for _ in p.open(encoding="utf-8-sig")) - 1
    row_counts.append({"table": name, "rows": n, "notes": "policy tables untouched by #51"})

# rates delta
for name in ["QuikAint", "QuikUint", "QuikCvs", "QuikGps"]:
    p = rates / f"{name}.csv"
    if not p.exists():
        row_counts.append({"table": name, "rows": 0, "notes": "missing"})
        continue
    n = sum(1 for _ in p.open(encoding="utf-8-sig")) - 1
    note = "intentional +2" if name == "QuikAint" else "unchanged expected"
    row_counts.append({"table": f"rates/{name}", "rows": n, "notes": note})

with (ev / "issue51_regression_row_counts.csv").open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["table", "rows", "notes"])
    w.writeheader()
    w.writerows(row_counts)

# #25 sample
mstr = list(csv.DictReader((out / "quikmstr.csv").open(encoding="utf-8-sig")))
ex = next((r for r in mstr if r.get("MPOLICY", "").strip() == "010348734C"), None)
mpolicy = ex["MPOLICY"] if ex else ""
print("SCHEMA_OK", True)
print("TRACE_PASS", all(c["RESULT"] == "PASS" for c in checks), len(checks))
print("MPOLICY_LEN", len(mpolicy), repr(mpolicy))
print("A60MIR_MPREM", [(c["MPOLICY"], next(r.get("MPREM","") for r in targets if r["MPOLICY"].strip()==c["MPOLICY"] and r["MPLAN"].strip()==c["MPLAN"])) for c in checks if c["MPLAN"]=="A60MIR"][:1])
for rc in row_counts:
    print(f"ROWS {rc['table']}={rc['rows']}")
tv = out / "Test_Validation" / "rates" / "QuikAint.csv"
print("TEST_VAL", tv.exists())
