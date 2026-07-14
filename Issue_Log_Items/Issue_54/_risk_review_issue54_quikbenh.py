"""Issue #54 Risk simulation — PACTG 04xx → quikbenh loan rows (read-only)."""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

OUT = Path("Issue_Log_Items/Issue_54/evidence")
OUT.mkdir(parents=True, exist_ok=True)

CODES_EMIT = {"0411": "10", "0412": "11", "0413": "12"}  # Help §6.5
CODES_EXCLUDE = {"0451"}  # offset pair
ALL_BM = {"0411", "0412", "0413", "0414", "0415", "0416", "0417", "0451"}


def norm(c: str) -> str:
    s = "".join(ch for ch in str(c).strip() if ch.isdigit())
    if not s:
        return ""
    return s.zfill(4)[-4:]


def load_crosswalk(path: Path) -> dict[str, str]:
    """Master_Crosswalk: Old_Value=LifePRO, New_Value=QLAdmin MPOLICY."""
    m: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            a = str(row.get("Old_Value", "")).strip()
            b = str(row.get("New_Value", "")).strip()
            if a and b:
                m[a] = b
    return m


# --- existing quikbenh ---
benh_path = Path("QLA_Migration/Output/quikbenh.csv")
benh_rows = list(csv.DictReader(benh_path.open(encoding="utf-8", errors="replace")))
benh_types = Counter(str(r.get("MBENTYP", "")).strip() for r in benh_rows)
benh_pols = {str(r.get("MPOLICY", "")).strip() for r in benh_rows}
loan_types_existing = sum(benh_types[t] for t in ("10", "11", "12", "20"))

print("=== Existing quikbenh.csv ===")
print("rows", len(benh_rows), "policies", len(benh_pols))
print("MBENTYP", dict(benh_types))
print("existing loan-type rows (10/11/12/20)", loan_types_existing)

# --- quikloan ---
loan_path = Path("QLA_Migration/Output/quikloan.csv")
loan_rows = list(csv.DictReader(loan_path.open(encoding="utf-8", errors="replace"))) if loan_path.exists() else []
loan_pols = {str(r.get("MPOLICY", "")).strip() for r in loan_rows}
print("=== Existing quikloan.csv ===")
print("rows", len(loan_rows), "policies", len(loan_pols))

# --- crosswalk ---
cw_path = Path("QLA_Migration/Mapping/Master_Crosswalk.csv")
cw = load_crosswalk(cw_path)
print("crosswalk entries", len(cw))

# --- PACTG scan ---
pactg = Path("QLA_Migration/Source/PACTG_Accounting_Extract20260630.csv")
emit_rows = []  # candidate Benh emits
stats = Counter()
by_code = Counter()
pols = set()
orphan = set()
rev_excluded = 0
pair0451 = 0

with pactg.open(newline="", encoding="utf-8", errors="replace") as f:
    r = csv.DictReader(f)
    for row in r:
        cr = norm(row.get("CREDIT_CODE", ""))
        db = norm(row.get("DEBIT_CODE", ""))
        codes = {c for c in (cr, db) if c in ALL_BM}
        if not codes:
            continue
        stats["bm_rows"] += 1
        if (row.get("REVERSAL_CODE") or "").strip().upper() == "Y":
            rev_excluded += 1
            stats["reversed"] += 1
            continue
        # pick emit code: prefer 0411/0412/0413 on either side; skip 0451-only
        emit_code = None
        for c in ("0411", "0412", "0413"):
            if c in codes:
                emit_code = c
                break
        if emit_code is None:
            if codes & CODES_EXCLUDE or codes <= {"0451"}:
                pair0451 += 1
                stats["excluded_0451_only"] += 1
            else:
                stats["other_bm_skipped"] += 1
            continue
        # if row is 0412+0451 pair, still emit 0412 once
        if "0451" in codes:
            stats["0412_with_0451_pair"] += 1

        pol = str(row.get("POLICY_NUMBER", "")).strip()
        amt = (row.get("TRANS_AMOUNT     ") or row.get("TRANS_AMOUNT") or "").strip()
        eff = (row.get("EFFECTIVE_DATE") or "").strip()
        mpol = cw.get(pol, "")
        if not mpol:
            # try without spaces
            mpol = cw.get(pol.strip(), "")
        if not mpol:
            orphan.add(pol)
            stats["orphan_no_crosswalk"] += 1
            continue
        try:
            amount = abs(float(amt))
        except Exception:
            stats["bad_amount"] += 1
            continue
        if not eff or not eff.isdigit():
            stats["bad_date"] += 1
            continue

        mbentyp = CODES_EMIT[emit_code]
        by_code[emit_code] += 1
        pols.add(pol)
        emit_rows.append(
            {
                "POLICY_NUMBER": pol,
                "MPOLICY": mpol,
                "MBENTYP": mbentyp,
                "MDATE": eff,
                "MBEN": f"{amount:.2f}",
                "PACTG_CODE": emit_code,
            }
        )

print("=== PACTG simulation ===")
print("bm_rows", stats["bm_rows"])
print("emit_candidates", len(emit_rows))
print("policies", len(pols))
print("by_code", dict(by_code))
print("reversed_excluded", rev_excluded)
print("0451_only_excluded", pair0451)
print("orphans", len(orphan))
print(dict(stats))

# overlap with existing benh / loan
emit_mpols = {r["MPOLICY"].strip() for r in emit_rows}
print("emit policies intersect existing benh", len(emit_mpols & benh_pols))
print("emit policies intersect quikloan", len(emit_mpols & loan_pols))
print("loan-type collisions in existing benh", loan_types_existing)

# write evidence
with (OUT / "issue54_risk_pactg_benh_summary.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["metric", "value"])
    w.writerow(["existing_quikbenh_rows", len(benh_rows)])
    w.writerow(["existing_quikbenh_policies", len(benh_pols)])
    for t, n in sorted(benh_types.items()):
        w.writerow([f"existing_MBENTYP_{t or 'BLANK'}", n])
    w.writerow(["existing_loan_type_rows_10_11_12_20", loan_types_existing])
    w.writerow(["existing_quikloan_rows", len(loan_rows)])
    w.writerow(["pactg_bm_rows", stats["bm_rows"]])
    w.writerow(["emit_candidate_rows", len(emit_rows)])
    w.writerow(["emit_policies", len(pols)])
    for c, n in sorted(by_code.items()):
        w.writerow([f"emit_{c}_to_{CODES_EMIT[c]}", n])
    w.writerow(["reversed_excluded", rev_excluded])
    w.writerow(["excluded_0451_only_rows", pair0451])
    w.writerow(["orphan_policies", len(orphan)])
    w.writerow(["intersect_existing_benh_policies", len(emit_mpols & benh_pols)])
    w.writerow(["intersect_quikloan_policies", len(emit_mpols & loan_pols)])

# sample traces for 9010331768
trace = [r for r in emit_rows if r["POLICY_NUMBER"] == "9010331768"][:30]
with (OUT / "issue54_risk_trace_9010331768.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["POLICY_NUMBER", "MPOLICY", "MBENTYP", "MDATE", "MBEN", "PACTG_CODE"])
    w.writeheader()
    w.writerows(trace)
print("trace 9010331768 rows", len([r for r in emit_rows if r["POLICY_NUMBER"] == "9010331768"]))

# proposed after row count
print("proposed quikbenh after append", len(benh_rows) + len(emit_rows), "(if no dedupe)")
print("done")
