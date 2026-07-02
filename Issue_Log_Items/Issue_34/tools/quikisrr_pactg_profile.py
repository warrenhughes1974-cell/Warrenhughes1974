"""
Issue #34 — QuikIsrr PACTG profiling (planning only).

Reads PACTG extract, profiles 561 partial surrender rows, ISWL MPLAN scope.
Does NOT emit QuikIsrr.csv or modify production outputs.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PACTG_CANDIDATES = [
    PROJECT_ROOT / "QLA_Migration" / "Source" / "PACTG_Accounting_Extract20260530.csv",
    PROJECT_ROOT / "QLA_Migration" / "Source" / "PACTG_Accounting_Extract20260427.csv",
    PROJECT_ROOT / "docs" / "claims_conversion_reference" / "PACTG_Accounting_Extract20260427.csv",
]
OUT_DIR = PROJECT_ROOT / "Issue_Log_Items" / "Issue_34" / "output" / "QuikIsrr_Planning_Profile"
DEFERRED_POLICIES = frozenset({
    "9010776027", "9010780411", "9010780591", "9011072813", "9011107796",
})
PAYOUT_PAIR_CODES = frozenset({"90", "94", "560", "567", "1020", "1900"})
ISWL_MPLANS = frozenset({
    "1658C1", "1658CS", "1659C2", "1659CR", "1659CS", "1659SR", "1669SR", "1679CS",
})
COVERAGE_TO_MPLAN = {
    "658 CEN I": "1658C1",
    "658 CEN SD": "1658CS",
    "659 CEN II": "1659C2",
    "659 CEN SR": "1659CR",
    "659 CEN SD": "1659CS",
    "659 SR GD": "1659SR",
    "669 SR GD": "1669SR",
    "679 CEN SD": "1679CS",
}


def _resolve_pactg() -> Path | None:
    for p in PACTG_CANDIDATES:
        if p.is_file():
            return p
    return None


def norm_code(value: str) -> str:
    s = (value or "").strip()
    if not s or set(s) == {"-"}:
        return ""
    digits = re.sub(r"[^0-9]", "", s)
    if digits:
        return str(int(digits))
    return s.upper()


def norm_date(value: str) -> str:
    s = (value or "").strip()
    if not s or set(s.replace(" ", "")) == {"-"}:
        return ""
    digits = re.sub(r"[^0-9]", "", s)
    return digits[:8] if len(digits) >= 8 else ""


def parse_amount(value: str) -> float | None:
    s = (value or "").strip()
    if not s or set(s.replace(" ", "")) == {"-"}:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def norm_policy(value: str) -> str:
    return re.sub(r"[^0-9]", "", (value or "").strip())


def map_mplan(plan_code: str, product_id: str) -> str:
    pc = (plan_code or "").strip()
    if pc in COVERAGE_TO_MPLAN:
        return COVERAGE_TO_MPLAN[pc]
    pid = (product_id or "").strip()
    if pid in COVERAGE_TO_MPLAN:
        return COVERAGE_TO_MPLAN[pid]
    return ""


def load_policy_status() -> dict[str, str]:
    """Best-effort policy status from quikclms vs quikmstr status report."""
    path = PROJECT_ROOT / "plan_analysis" / "status_analysis" / "quikclms_vs_quikmstr_status_report.csv"
    status: dict[str, str] = {}
    if not path.is_file():
        return status
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            pol = norm_policy(row.get("MPOLICY", ""))
            if not pol:
                continue
            st = (row.get("MSTATUS") or row.get("POLICY_STATUS_DESCRIPTION") or "").strip()
            if st and pol not in status:
                status[pol] = st
    return status


def main() -> int:
    pactg_path = _resolve_pactg()
    if not pactg_path:
        print("FAIL — PACTG extract not found")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    policy_status = load_policy_status()

    policy_codes: dict[str, set[str]] = defaultdict(set)
    policy_date_codes: dict[tuple[str, str], set[str]] = defaultdict(set)
    rows_561: list[dict] = []
    rows_560: list[dict] = []

    with open(pactg_path, encoding="latin-1", newline="") as f:
        reader = csv.DictReader(f)
        col_map = {c.strip(): c for c in reader.fieldnames or []}

        def row_dict(raw: dict) -> dict[str, str]:
            return {k.strip(): (raw[v] if v else "") for k, v in col_map.items()}

        for raw in reader:
            r = row_dict(raw)
            pol = norm_policy(r.get("POLICY_NUMBER", ""))
            if not pol:
                continue
            eff = norm_date(r.get("EFFECTIVE_DATE", ""))
            dc = norm_code(r.get("DEBIT_CODE", ""))
            cc = norm_code(r.get("CREDIT_CODE", ""))
            if dc:
                policy_codes[pol].add(dc)
                if eff:
                    policy_date_codes[(pol, eff)].add(dc)
            if cc:
                policy_codes[pol].add(cc)
                if eff:
                    policy_date_codes[(pol, eff)].add(cc)

            if dc == "561":
                amt = parse_amount(r.get("TRANS_AMOUNT", ""))
                mplan = map_mplan(r.get("PLAN_CODE", ""), r.get("PRODUCT_ID", ""))
                rows_561.append({
                    "policy_number": pol,
                    "mplan": mplan,
                    "is_iswl": mplan in ISWL_MPLANS,
                    "plan_code": (r.get("PLAN_CODE") or "").strip(),
                    "product_id": (r.get("PRODUCT_ID") or "").strip(),
                    "effective_date": eff,
                    "trans_amount": amt,
                    "term_reason": (r.get("TERM_REASON") or "").strip(),
                    "benefit_seq": (r.get("BENEFIT_SEQ") or "").strip(),
                    "record_sequence": (r.get("RECORD_SEQUENCE") or "").strip(),
                })
            elif dc == "560":
                rows_560.append({"policy_number": pol, "effective_date": eff})

    def pairing_flags(pol: str, eff: str) -> dict[str, bool]:
        same_date = policy_date_codes.get((pol, eff), set())
        all_codes = policy_codes.get(pol, set())
        codes = same_date if same_date else all_codes
        return {
            "has_560_same_or_policy": "560" in codes,
            "has_0090_same_or_policy": "90" in codes,
            "has_1020_same_or_policy": "1020" in codes,
            "has_payout_pair_same_or_policy": bool(codes & PAYOUT_PAIR_CODES),
        }

    fleet_amt = sum(r["trans_amount"] for r in rows_561 if r["trans_amount"] is not None)
    iswl_rows = [r for r in rows_561 if r["is_iswl"]]
    iswl_amt = sum(r["trans_amount"] for r in iswl_rows if r["trans_amount"] is not None)

    candidates: list[dict] = []
    deferred: list[dict] = []
    rejected_560: list[dict] = []
    pairing_rows: list[dict] = []

    for r in rows_561:
        pol, eff = r["policy_number"], r["effective_date"]
        flags = pairing_flags(pol, eff)
        status = policy_status.get(pol, "")
        terminated = any(
            x in status.upper()
            for x in ("SURRENDER", "TERMINATED", "DEATH", "MATURED")
        ) if status else bool(r["term_reason"].strip())

        entry = {
            **r,
            **flags,
            "policy_status": status,
            "terminated_flag": terminated,
            "deferred_hold": pol in DEFERRED_POLICIES or not flags["has_payout_pair_same_or_policy"],
            "missing_date": not eff,
            "missing_or_zero_amount": r["trans_amount"] is None or r["trans_amount"] == 0,
            "negative_amount": r["trans_amount"] is not None and r["trans_amount"] < 0,
        }
        pairing_rows.append({
            "policy_number": pol,
            "effective_date": eff,
            "mplan": r["mplan"],
            "trans_amount": r["trans_amount"],
            "has_560": flags["has_560_same_or_policy"],
            "has_0090": flags["has_0090_same_or_policy"],
            "has_1020": flags["has_1020_same_or_policy"],
            "has_payout_pair": flags["has_payout_pair_same_or_policy"],
            "deferred_hold": entry["deferred_hold"],
        })
        if r["is_iswl"]:
            candidates.append(entry)
            if entry["deferred_hold"]:
                deferred.append(entry)

    for r in rows_560:
        mplan = ""
        for x in rows_561:
            if x["policy_number"] == r["policy_number"]:
                mplan = x["mplan"]
                break
        if mplan in ISWL_MPLANS:
            rejected_560.append({**r, "mplan": mplan, "reason": "full_surrender_560_excluded"})

    summary = {
        "profile_date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pactg_path": str(pactg_path),
        "pactg_available": True,
        "fleet_561_rows": len(rows_561),
        "fleet_561_unique_policies": len({r["policy_number"] for r in rows_561}),
        "fleet_561_total_amount": round(fleet_amt, 2),
        "iswl_561_rows": len(iswl_rows),
        "iswl_561_unique_policies": len({r["policy_number"] for r in iswl_rows}),
        "iswl_561_total_amount": round(iswl_amt, 2),
        "iswl_rows_by_mplan": dict(Counter(r["mplan"] for r in iswl_rows)),
        "missing_effective_date": sum(1 for r in rows_561 if not r["effective_date"]),
        "missing_or_zero_amount": sum(
            1 for r in rows_561 if r["trans_amount"] is None or r["trans_amount"] == 0
        ),
        "negative_amount": sum(
            1 for r in rows_561 if r["trans_amount"] is not None and r["trans_amount"] < 0
        ),
        "iswl_missing_effective_date": sum(1 for r in iswl_rows if not r["effective_date"]),
        "iswl_missing_or_zero_amount": sum(
            1 for r in iswl_rows if r["trans_amount"] is None or r["trans_amount"] == 0
        ),
        "iswl_negative_amount": sum(
            1 for r in iswl_rows if r["trans_amount"] is not None and r["trans_amount"] < 0
        ),
        "iswl_terminated_policy_rows": sum(1 for r in candidates if r["terminated_flag"]),
        "iswl_related_560_activity_rows": sum(1 for r in candidates if r["has_560_same_or_policy"]),
        "iswl_related_0090_activity_rows": sum(1 for r in candidates if r["has_0090_same_or_policy"]),
        "iswl_related_1020_activity_rows": sum(1 for r in candidates if r["has_1020_same_or_policy"]),
        "iswl_deferred_hold_rows": len(deferred),
        "iswl_deferred_hold_policies": len({r["policy_number"] for r in deferred}),
        "deferred_policy_allowlist": sorted(DEFERRED_POLICIES),
        "recommended_status": "Research/profile complete — blocked pending SME approval",
        "sme_blockers": [
            "Q1-Q10 unanswered in Issue_34_QuikIsrr_SME_Questions.md",
            "MISWL derivation rule",
            "561 without payout-pair inclusion policy",
            "Output path confirmation",
        ],
    }

    def write_csv(name: str, fieldnames: list[str], rows: list[dict]) -> None:
        path = OUT_DIR / name
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)

    write_csv(
        "quikisrr_pactg_561_iswl_candidates.csv",
        [
            "policy_number", "mplan", "plan_code", "effective_date", "trans_amount",
            "policy_status", "terminated_flag", "has_560_same_or_policy",
            "has_0090_same_or_policy", "has_1020_same_or_policy",
            "has_payout_pair_same_or_policy", "deferred_hold",
            "missing_date", "missing_or_zero_amount", "negative_amount",
        ],
        candidates,
    )
    write_csv(
        "quikisrr_pactg_561_deferred_review.csv",
        [
            "policy_number", "mplan", "effective_date", "trans_amount",
            "has_payout_pair_same_or_policy", "deferred_hold",
        ],
        deferred,
    )
    write_csv(
        "quikisrr_pactg_561_rejected_full_surrender.csv",
        ["policy_number", "mplan", "effective_date", "reason"],
        rejected_560,
    )
    write_csv(
        "quikisrr_pactg_561_pairing_analysis.csv",
        [
            "policy_number", "effective_date", "mplan", "trans_amount",
            "has_560", "has_0090", "has_1020", "has_payout_pair", "deferred_hold",
        ],
        pairing_rows,
    )
    (OUT_DIR / "quikisrr_pactg_561_profile_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
