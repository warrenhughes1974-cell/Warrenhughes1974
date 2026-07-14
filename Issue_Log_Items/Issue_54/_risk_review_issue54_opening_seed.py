"""Issue #54 Risk re-affirm — PLOAN opening seed impact (read-only)."""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

OUT = Path("Issue_Log_Items/Issue_54/evidence")
OUT.mkdir(parents=True, exist_ok=True)

CODES_EMIT = {"0411": "10", "0412": "11", "0413": "12"}
ALL_BM = {"0411", "0412", "0413", "0414", "0415", "0416", "0417", "0451"}


def norm(c: str) -> str:
    s = "".join(ch for ch in str(c).strip() if ch.isdigit())
    if not s:
        return ""
    return s.zfill(4)[-4:]


def ymd(v: str) -> str:
    d = "".join(ch for ch in str(v) if ch.isdigit())
    return d[:8] if len(d) >= 8 else ""


def to_float(v: str) -> float | None:
    try:
        return float(str(v).replace(",", "").strip())
    except Exception:
        return None


def load_crosswalk(path: Path) -> dict[str, str]:
    m: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            a = str(row.get("Old_Value") or row.get("OLD_VALUE") or "").strip()
            b = str(row.get("New_Value") or row.get("NEW_VALUE") or "").strip()
            if a and b:
                m[a] = b
    return m


cw = load_crosswalk(Path("QLA_Migration/Mapping/Master_Crosswalk.csv"))

# --- Build Risk Option A emit: first MDATE per MPOLICY + type-10 keys ---
first_mdate: dict[str, str] = {}
type10_keys: set[tuple[str, str, str]] = set()  # MPOLICY, MDATE, amount str
emit_pols: set[str] = set()
emit_rows = 0

pactg = Path("QLA_Migration/Source/PACTG_Accounting_Extract20260630.csv")
with pactg.open(newline="", encoding="utf-8", errors="replace") as f:
    for row in csv.DictReader(f):
        cr = norm(row.get("CREDIT_CODE", ""))
        db = norm(row.get("DEBIT_CODE", ""))
        codes = {c for c in (cr, db) if c in ALL_BM}
        if not codes:
            continue
        if (row.get("REVERSAL_CODE") or "").strip().upper() == "Y":
            continue
        emit_code = None
        for c in ("0411", "0412", "0413"):
            if c in codes:
                emit_code = c
                break
        if not emit_code:
            continue
        lp = str(row.get("POLICY_NUMBER", "")).strip()
        mp = cw.get(lp, "")
        if not mp:
            continue
        dt = ymd(row.get("EFFECTIVE_DATE", ""))
        if not dt:
            continue
        amt = to_float(row.get("TRANS_AMOUNT", ""))
        amt_s = f"{abs(amt):.2f}" if amt is not None else ""
        mb = CODES_EMIT[emit_code]
        emit_rows += 1
        emit_pols.add(mp)
        if mp not in first_mdate or dt < first_mdate[mp]:
            first_mdate[mp] = dt
        if mb == "10":
            type10_keys.add((mp, dt, amt_s))

# --- PLOAN index by LifePRO policy ---
ploan_by_lp: dict[str, list[tuple[str, float]]] = {}
ploan = Path("QLA_Migration/Source/PLOAN_LoanInformation_Extract_20260630.csv")
with ploan.open(newline="", encoding="utf-8", errors="replace") as f:
    for row in csv.DictReader(f):
        lp = str(row.get("POLICY_NUMBER", "")).strip()
        dt = ymd(row.get("ACCRUAL_DATE", ""))
        bal = to_float(row.get("LOAN_BALANCE", ""))
        if not lp or not dt or bal is None:
            continue
        ploan_by_lp.setdefault(lp, []).append((dt, bal))

for lp in ploan_by_lp:
    ploan_by_lp[lp].sort(key=lambda x: x[0])

# reverse CW for LP lookup
lp_of = {v: k for k, v in cw.items()}

rules = Counter()
seed_rows: list[dict] = []
dedupe_skip = 0
largest: list[tuple[float, str, str, float]] = []

for mp in sorted(emit_pols):
    fb = first_mdate[mp]
    lp = lp_of.get(mp, "")
    if not lp or lp not in ploan_by_lp:
        rules["NO_PLOAN"] += 1
        continue
    prior = [(d, b) for d, b in ploan_by_lp[lp] if d < fb]
    if not prior:
        rules["NO_PRIOR"] += 1
        continue
    seed_dt, seed_bal = prior[-1]
    if seed_bal <= 0:
        rules["ZERO_PRIOR"] += 1
        continue
    amt_s = f"{seed_bal:.2f}"
    # OBQ-3: skip if PACTG already has type 10 same date + same amount
    if (mp, seed_dt, amt_s) in type10_keys:
        rules["DEDUPE_SAME_DAY_10"] += 1
        dedupe_skip += 1
        continue
    # also skip if any type-10 same date (prefer PACTG) regardless of amount
    if any(k[0] == mp and k[1] == seed_dt for k in type10_keys):
        rules["DEDUPE_SAME_DAY_10_ANY_AMT"] += 1
        dedupe_skip += 1
        continue
    rules["SEED_EMIT"] += 1
    seed_rows.append(
        {
            "MPOLICY": mp,
            "LP": lp,
            "first_benh": fb,
            "seed_date": seed_dt,
            "seed_balance": amt_s,
            "MBENTYP": "10",
        }
    )
    largest.append((seed_bal, mp, seed_dt, seed_bal))

largest.sort(reverse=True)

# baselines
benh_path = Path("QLA_Migration/Output/quikbenh.csv")
with benh_path.open(encoding="utf-8", errors="replace") as f:
    benh_n = sum(1 for _ in csv.DictReader(f))
loan_path = Path("QLA_Migration/Output/quikloan.csv")
with loan_path.open(encoding="utf-8", errors="replace") as f:
    loan_n = sum(1 for _ in csv.DictReader(f))

# write evidence
seed_path = OUT / "issue54_risk_opening_seed_summary.csv"
with seed_path.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(
        f,
        fieldnames=["metric", "value"],
    )
    w.writeheader()
    metrics = {
        "existing_quikbenh_rows": benh_n,
        "existing_quikloan_rows": loan_n,
        "pactg_emit_rows_option_a": emit_rows,
        "pactg_emit_policies": len(emit_pols),
        "seed_emit_rows": rules["SEED_EMIT"],
        "seed_skip_no_ploan": rules["NO_PLOAN"],
        "seed_skip_no_prior": rules["NO_PRIOR"],
        "seed_skip_zero_prior": rules["ZERO_PRIOR"],
        "seed_skip_dedupe_same_day_10": rules["DEDUPE_SAME_DAY_10"]
        + rules["DEDUPE_SAME_DAY_10_ANY_AMT"],
        "proposed_total_new_loan_benh_rows": emit_rows + rules["SEED_EMIT"],
        "proposed_quikbenh_after_append": benh_n + emit_rows + rules["SEED_EMIT"],
    }
    for k, v in metrics.items():
        w.writerow({"metric": k, "value": v})

detail_path = OUT / "issue54_risk_opening_seed_rows.csv"
with detail_path.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(
        f, fieldnames=["MPOLICY", "LP", "first_benh", "seed_date", "seed_balance", "MBENTYP"]
    )
    w.writeheader()
    w.writerows(seed_rows)

trace_path = OUT / "issue54_risk_trace_010822238C_seed.csv"
with trace_path.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(
        f, fieldnames=["MPOLICY", "LP", "first_benh", "seed_date", "seed_balance", "MBENTYP"]
    )
    w.writeheader()
    for r in seed_rows:
        if r["MPOLICY"] == "010822238C":
            w.writerow(r)

print("=== Risk Option A baselines ===")
print("emit_rows", emit_rows, "emit_policies", len(emit_pols))
print("=== Opening seed rules ===")
print(dict(rules))
print("seed_emit", rules["SEED_EMIT"])
print("proposed_new_loan_rows", emit_rows + rules["SEED_EMIT"])
print("proposed_benh_total", benh_n + emit_rows + rules["SEED_EMIT"])
print("top 10 seeds:")
for bal, mp, dt, _ in largest[:10]:
    print(f"  {mp} {dt} {bal:.2f}")
ex = [r for r in seed_rows if r["MPOLICY"] == "010822238C"]
print("trace 010822238C", ex)
print("wrote", seed_path)
print("wrote", detail_path)
